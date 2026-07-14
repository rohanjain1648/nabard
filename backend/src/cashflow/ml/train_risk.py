"""Train the risk classifier: will this enterprise be stressed within the next 3 months?

Ground truth comes from the simulator's injected shocks (monthly_labels.csv,
TRD.md §4). Training/evaluation is restricted to "pre-onset" rows (enterprise not
already in a stressed month) so the model must show genuine anticipatory signal
rather than trivially predicting "still stressed next month" during an ongoing
30-90 day shock window.

Because stress onsets are rare (~a few dozen episodes across the whole
simulated population), a single time-based holdout leaves too few positive
examples to evaluate reliably. Evaluation instead uses walk-forward backtesting
across the full 24 months, pooling out-of-fold predictions from every fold to
compute AUC, recall-at-FPR-budget, and the early-warning lead-time distribution
(TRD.md §5.2, §8). The deployed model is retrained on the entire dataset.

Usage: python -m cashflow.ml.train_risk --data backend/data --models backend/models --reports backend/reports
"""
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import roc_auc_score, roc_curve

from .features import FEATURE_COLUMNS, build_feature_table

LOOKAHEAD_MONTHS = 3
MIN_TRAIN_MONTHS = 6      # first backtest fold trains on months [0, 6) - kept small since positive
                          # (pre-onset) examples are rare and concentrated early in the simulated window
FOLD_WIDTH_MONTHS = 2     # each backtest fold evaluates the next 2 months
TARGET_FPR_BUDGET = 0.20
MODEL_VERSION = "risk-v1"


def build_risk_dataset(data_dir: Path) -> pd.DataFrame:
    features = build_feature_table(data_dir)
    months_sorted = sorted(features["month"].unique())
    month_index = {m: i for i, m in enumerate(months_sorted)}
    features["month_idx"] = features["month"].map(month_index)

    labels = pd.read_csv(data_dir / "monthly_labels.csv")
    labels["month"] = pd.PeriodIndex(labels["month"], freq="M")
    labels = labels.sort_values(["enterprise_id", "month"])

    # forward-looking label: stressed in any of the next LOOKAHEAD_MONTHS months
    labels["stressed_next_k"] = (
        labels.groupby("enterprise_id")["stressed"]
        .transform(lambda s: s.shift(-1).rolling(LOOKAHEAD_MONTHS, min_periods=1).max())
    )

    def _months_to_next_stress(s: pd.Series) -> pd.Series:
        stressed_idx = np.where(s.values == 1)[0]
        out = np.full(len(s), np.nan)
        for i in range(len(s)):
            future = stressed_idx[stressed_idx > i]
            if len(future):
                out[i] = future[0] - i
        return pd.Series(out, index=s.index)

    labels["months_to_next_stress"] = labels.groupby("enterprise_id")["stressed"].transform(_months_to_next_stress)

    df = features.merge(labels[["enterprise_id", "month", "stressed", "stressed_next_k", "months_to_next_stress"]],
                         on=["enterprise_id", "month"], how="inner")
    df["sector"] = df["sector"].astype("category")
    df = df.dropna(subset=["stressed_next_k"])

    # Restrict to genuine "pre-onset" rows: a shock persists 30-90 days, so a month
    # that's already stressed trivially predicts "still stressed next month" - that's
    # not early warning, it's confirming an ongoing crisis. Training/evaluating only on
    # currently-not-stressed months isolates the model's real anticipatory signal and
    # keeps the lead-time metric meaningful (TRD.md §5.2, PRD.md early-warning goal).
    return df[df["stressed"] == 0].drop(columns=["stressed"])


def _fit_classifier(X: pd.DataFrame, y: pd.Series) -> lgb.LGBMClassifier:
    model = lgb.LGBMClassifier(
        n_estimators=200, num_leaves=7, learning_rate=0.05,
        min_child_samples=20, reg_lambda=1.0, class_weight="balanced", verbosity=-1,
    )
    model.fit(X, y, categorical_feature=["sector"])
    return model


def _walk_forward_backtest(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """Train on an expanding window, evaluate on the next fold, roll forward. Returns
    a dataframe of pooled out-of-fold predictions across every fold."""
    max_month = int(df["month_idx"].max())
    oof_rows = []
    fold_start = MIN_TRAIN_MONTHS
    while fold_start < max_month:
        fold_end = min(fold_start + FOLD_WIDTH_MONTHS, max_month + 1)
        train_fold = df[df["month_idx"] < fold_start]
        test_fold = df[(df["month_idx"] >= fold_start) & (df["month_idx"] < fold_end)]
        if len(train_fold) < 30 or test_fold.empty or train_fold["stressed_next_k"].nunique() < 2:
            fold_start += FOLD_WIDTH_MONTHS
            continue
        model = _fit_classifier(train_fold[feature_cols], train_fold["stressed_next_k"])
        raw_pred = model.predict_proba(test_fold[feature_cols])[:, 1]
        fold_result = test_fold[["stressed_next_k", "months_to_next_stress"]].copy()
        fold_result["raw_pred"] = raw_pred
        oof_rows.append(fold_result)
        fold_start += FOLD_WIDTH_MONTHS
    return pd.concat(oof_rows, ignore_index=True) if oof_rows else pd.DataFrame()


def train(data_dir: Path, models_dir: Path, reports_dir: Path) -> dict:
    df = build_risk_dataset(data_dir)
    feature_cols = FEATURE_COLUMNS

    models_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    # ---- walk-forward backtest across the full 24 months, pooling out-of-fold predictions ----
    oof = _walk_forward_backtest(df, feature_cols)

    # ---- calibrator fit on the pooled out-of-fold predictions ----
    calibrator = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
    calibrator.fit(oof["raw_pred"], oof["stressed_next_k"])
    with open(models_dir / "risk_calibrator.pkl", "wb") as f:
        pickle.dump(calibrator, f)
    oof["calibrated_pred"] = calibrator.predict(oof["raw_pred"])

    y_oof = oof["stressed_next_k"].values
    auc = float(roc_auc_score(y_oof, oof["calibrated_pred"]))
    fpr, tpr, thresholds = roc_curve(y_oof, oof["calibrated_pred"])
    eligible = fpr <= TARGET_FPR_BUDGET
    if eligible.any():
        best_idx = np.argmax(tpr * eligible)
        chosen_threshold = float(thresholds[best_idx])
        recall_at_budget = float(tpr[best_idx])
        fpr_at_budget = float(fpr[best_idx])
    else:
        chosen_threshold, recall_at_budget, fpr_at_budget = 0.5, float("nan"), float("nan")

    predicted_positive = oof["calibrated_pred"] >= chosen_threshold
    lead_times = oof.loc[predicted_positive & (y_oof == 1), "months_to_next_stress"]
    lead_time_stats = {
        "mean_months": float(lead_times.mean()) if len(lead_times) else None,
        "median_months": float(lead_times.median()) if len(lead_times) else None,
        "min_months": float(lead_times.min()) if len(lead_times) else None,
        "n_true_positives_with_lead_time": int(lead_times.notna().sum()),
    }

    # ---- final deployed model: trained on the entire dataset ----
    final_model = _fit_classifier(df[feature_cols], df["stressed_next_k"])
    final_model.booster_.save_model(str(models_dir / "risk.txt"))

    metrics = {
        "n_rows_total": len(df),
        "n_oof_predictions": len(oof),
        "oof_positive_rate": float(y_oof.mean()),
        "auc": auc,
        "decision_threshold": chosen_threshold,
        "recall_at_fpr_budget": recall_at_budget,
        "fpr_at_chosen_threshold": fpr_at_budget,
        "fpr_budget": TARGET_FPR_BUDGET,
        "lead_time": lead_time_stats,
        "model_version": MODEL_VERSION,
    }

    with open(models_dir / "risk_feature_spec.json", "w") as f:
        json.dump({
            "feature_columns": feature_cols, "model_version": MODEL_VERSION,
            "decision_threshold": chosen_threshold, "lookahead_months": LOOKAHEAD_MONTHS,
            "sector_categories": df["sector"].cat.categories.tolist(),
        }, f, indent=2)

    _append_report(metrics, reports_dir / "model_eval.md")
    print(json.dumps(metrics, indent=2, default=str))
    return metrics


def _append_report(metrics: dict, path: Path) -> None:
    lines = ["\n## Risk classifier (LightGBM, stress-within-3-months, isotonic-calibrated)\n"]
    lines.append(
        f"- {metrics['n_rows_total']} pre-onset enterprise-months total; "
        f"{metrics['n_oof_predictions']} pooled out-of-fold predictions from walk-forward backtesting "
        f"(expanding-window folds across the full 24 months - a single holdout left too few stress "
        f"onsets to evaluate reliably). Deployed model is retrained on the full dataset."
    )
    lines.append(f"- Out-of-fold positive rate (transitions into stress within 3mo): {metrics['oof_positive_rate']:.3f}")
    lines.append(f"- **AUC: {metrics['auc']:.3f}** (target: >= 0.80)")
    lines.append(f"- Recall at FPR <= {metrics['fpr_budget']:.0%} budget: {metrics['recall_at_fpr_budget']:.3f} "
                 f"(actual FPR at chosen threshold: {metrics['fpr_at_chosen_threshold']:.3f}; target recall: >= 0.80)")
    lt = metrics["lead_time"]
    if lt["mean_months"] is not None:
        lines.append(f"- Early-warning lead time (correctly-flagged cases): mean {lt['mean_months']:.1f}mo, "
                      f"median {lt['median_months']:.1f}mo, min {lt['min_months']:.1f}mo, n={lt['n_true_positives_with_lead_time']}")
    else:
        lines.append("- Early-warning lead time: no true positives at the chosen threshold in this backtest")
    lines.append("")
    lines.append(
        "Note: labels are grounded in the simulator's injected shock events (30-90 day windows of "
        "depressed income / inflated costs). Restricting to pre-onset months (excluding already-"
        "stressed months) forces the model to show genuine anticipatory signal rather than trivially "
        "predicting 'still stressed next month' during an ongoing shock."
    )
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--models", type=Path, default=Path("models"))
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    args = parser.parse_args()
    train(args.data, args.models, args.reports)


if __name__ == "__main__":
    main()
