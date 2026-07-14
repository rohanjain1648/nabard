# TRD — CashFlow Sahayak

Technical requirements for the MVP defined in [PRD.md](PRD.md); design rationale in [ARCHITECTURE.md](ARCHITECTURE.md).

## 1. Tech Stack (decided)

| Layer | Choice | Rationale |
|---|---|---|
| Client | React 18 + Vite + TypeScript, Tailwind, Recharts, i18next, Workbox | PWA offline-first, fast build, one codebase for both roles |
| Local store | IndexedDB via `Dexie` | Structured queries over the local ledger |
| API | FastAPI + Pydantic v2 + SQLAlchemy 2 | Velocity, auto OpenAPI docs, async |
| DB | PostgreSQL 16 (SQLite fallback) | SQLAlchemy keeps both paths alive |
| ML | pandas + LightGBM + shap; scikit-learn for eval | Pooled tabular learning, quantiles, explainability, CPU-fast |
| Auth | JWT (pyjwt), bcrypt | Two roles, prototype-grade |
| Packaging | Docker Compose (`web`, `api`, `db`) + local no-Docker path | Judge-machine resilience |

## 2. Functional Requirements

### FR-1 Ledger & entries
- FR-1.1 Entry = `{id: client-UUID, enterprise_id, type: income|expense|savings_deposit|savings_withdrawal|loan_repayment, category, amount (INR, int paise not required — rupees, 2dp), note?, occurred_at, created_at, device_id}`. Immutable; corrections via reversal entries.
- FR-1.2 Sync endpoint `POST /sync` accepts ≤ 500 entries/batch; idempotent on entry `id`; response includes fresh forecast/score/alerts since client's `last_sync_at`.
- FR-1.3 Category sets are sector-scoped (served from config, not hardcoded in client).

### FR-2 Enterprise profile
- FR-2.1 `{id, name, sector, village, district, state, onboarded_at, savings_balance, loans[]}`; loan = `{principal, outstanding, emi_amount, emi_due_day, start_date, term_months}`.
- FR-2.2 Officer↔enterprise assignment table drives portfolio scoping.

### FR-3 Forecasting
- FR-3.1 Output per enterprise per future month `m ∈ [1..6]`: `{net_cashflow_p10, p50, p90, inflow_p50, outflow_p50, projected_balance_p50, model_version, generated_at}`.
- FR-3.2 Cold start (< 2 months of entries): sector seasonal baseline scaled by enterprise's observed daily average; flagged `method: "baseline"`.
- FR-3.3 Retrain: simulator-trained model ships pre-trained; per-enterprise inference re-runs after each sync and nightly.

### FR-4 Risk scoring & alerts
- FR-4.1 Score 0–100; bands Green ≥ 70, Amber 40–69, Red < 40; stored with `top_drivers: [{feature, direction, weight, human_text}]` (top 3).
- FR-4.2 Rule overlay (applied after model, floors only — rules can lower, never raise):
  - missed EMI in last 60 days → cap at 65 (Amber)
  - projected_balance_p50 < next 2 months' obligations → cap at 39 (Red)
  - no entries for 30+ days (disengagement) → cap at 65
- FR-4.3 Alert emitted on band downgrade, new rule trigger, or external shock affecting the sector (commodity move > 2σ, rainfall anomaly beyond threshold). Alert = `{severity, cause_text, suggestion_id, created_at, status: open|acknowledged|resolved}`.
- FR-4.4 Offline: client re-evaluates a shipped subset of static rules against the local ledger (EMI-due proximity, cached-balance floor) and can raise local alerts marked "offline estimate".

### FR-5 Suggestions
- FR-5.1 Suggestion library: YAML keyed by `(sector, driver)` → `{text_en, text_hi, action_type}`; ≥ 2 entries per (sector × top-3 drivers) at ship.
- FR-5.2 Every Amber/Red alert must resolve to ≥ 1 suggestion.

### FR-6 Officer dashboard
- FR-6.1 Portfolio list: filter by band/sector/village, sort by score, score-delta-30d, last-entry recency.
- FR-6.2 Profile page: ledger summary, forecast chart (bands), score history sparkline, driver breakdown, alert timeline.
- FR-6.3 Risk panel: G/A/R counts + 30-day trend, sector × band heatmap, live alert feed.

### FR-7 i18n
- FR-7.1 All UI strings via i18next resource files; ship `en`, `hi`. Number/currency formatted per locale (₹, Indian digit grouping).

## 3. Non-Functional Requirements

| NFR | Requirement |
|---|---|
| Offline | Entry, cached forecast/alerts, local rules fully functional with network off; demo: airplane-mode toggle mid-flow |
| Sync | Single POST round-trip; tolerates 2G latency (10s timeout, exponential retry via Workbox Background Sync) |
| Performance | Officer list ≤ 2s for 200 enterprises; per-enterprise inference ≤ 1s; full 50-enterprise rescore ≤ 60s |
| Footprint | PWA initial load ≤ 500KB gzipped (code-split officer bundle) |
| Privacy | No PII beyond name/village; UPI proxies aggregate-only; constraint from brief is a hard requirement |
| Portability | `docker-compose up` AND no-Docker local path both green |
| Accessibility | Owner UI: icon+color+text triple-coding (never color alone), large tap targets, works at 320px width |

## 4. Data Simulator Spec (the moat of the demo)

Deterministic (seeded) generator producing:

- **Entities:** 50 enterprises = 10 × {dairy, poultry, food_processing, handicrafts, rural_retail}, spread over 3 simulated districts.
- **History:** 24 months of daily entries per enterprise.
- **Income model:** `base_level(enterprise) × sector_seasonality(month) × commodity_link(price_t) × climate_effect(weather_t) × noise(lognormal)`; poultry uses 7-week batch-cycle pulses; handicrafts add festival spikes (Diwali, wedding seasons).
- **Expense model:** fixed recurring (rent-like) + variable input costs linked to commodity series + EMI schedule.
- **External series (daily→monthly):** commodity prices per sector key input/output (mean-reverting with jumps), rainfall (monsoon-shaped + anomaly), heat index.
- **Shock injection (labels!):** per enterprise, 0–2 shock events in 24 months: `{feed_price_spike, drought, demand_collapse, disease_outbreak, emi_burden}` → depressed income / inflated costs for 1–3 months. **Ground truth stress label** = month where balance < obligations. Target base rate ≈ 12–18% of enterprise-months.
- **Realism defects:** 5–15% missing entry days, entry clumping (owner logs 3 days at once), amount rounding, 2 enterprises that stop logging (disengagement case).
- **Outputs:** SQL seed + CSVs (`enterprises.csv`, `entries.csv`, `external_daily.csv`, `shocks.csv`) so the ML notebook and the app share one source.

## 5. ML Specification

### 5.1 Feature set (monthly grain, per enterprise-month)
- Lags of net flow (1,2,3,6,12), rolling mean/std (3,6), inflow/outflow ratio, entry-count & entry-regularity (proxy for UPI activity/engagement), savings runway (balance ÷ avg monthly outflow), EMI coverage (net flow ÷ EMI), days-since-last-entry.
- Sector one-hot, sector seasonal index for target month, months-to-nearest-festival-peak.
- Commodity: level z-score, 3-month momentum, 30-day volatility for sector-linked series.
- Climate: rainfall anomaly (vs seeded climatology), heat-index percentile, monsoon-phase flag.

### 5.2 Models
| Task | Model | Target | Eval |
|---|---|---|---|
| Forecast | LightGBM ×3 (quantile α=0.1/0.5/0.9) | net cash flow at horizons 1–6 (multi-horizon via `horizon` feature) | MAPE/WAPE on last-6-months holdout; pinball loss; vs seasonal-naive baseline (must beat by ≥ 15% WAPE) |
| Risk | LightGBM binary | stress within next 3 months | AUC ≥ 0.80; recall ≥ 0.80 at ≤ 20% FPR; lead-time distribution report |

- Split: time-based (train ≤ month 18, test 19–24); no enterprise leakage across the time cut.
- Calibration: isotonic on classifier output → probability → score = `100 × (1 − p_calibrated)` before rule caps.
- Explainability: SHAP top-3 per prediction → mapped to human-text templates (`shap_feature → driver_key → suggestion library`).

### 5.3 Artifacts
- `models/forecaster_{p10,p50,p90}.txt`, `models/risk.txt`, `models/calibrator.pkl`, `feature_spec.json` (versioned; API refuses mismatched versions).

## 6. API Surface (v1)

```
POST /auth/login                      → {token, role}
GET  /me/enterprise                   → profile + loans + savings
POST /sync                            → {entries[]} ⇒ {accepted_ids[], forecast, score, alerts[], suggestions[]}
GET  /enterprises/{id}/forecast       → 6-month rows (officer or own)
GET  /enterprises/{id}/risk           → score, band, drivers, history
GET  /enterprises/{id}/alerts         → paginated
POST /alerts/{id}/ack                 → officer/owner acknowledge
GET  /portfolio                       → officer list w/ filters (band, sector, q, sort)
GET  /portfolio/summary               → G/A/R counts, trends, sector heatmap
GET  /config/categories?sector=       → entry category sets
GET  /config/i18n/{lang}              → string bundle
POST /admin/rescore                   → trigger ML batch (demo control)
POST /admin/inject-shock              → demo control: fire a shock, show alert appearing
```

`/admin/inject-shock` is deliberate demo theater: judge watches a feed-price spike turn a Green dairy enterprise Amber with a readable explanation, live.

## 7. Data Model (core tables)

```
enterprises(id, name, sector, village, district, state, onboarded_at, savings_balance)
loans(id, enterprise_id, principal, outstanding, emi_amount, emi_due_day, start_date, term_months)
entries(id UUID PK, enterprise_id, type, category, amount, note, occurred_at, created_at, device_id)
external_signals(date, series_key, region, value)          -- commodity/weather/upi-proxy
forecasts(enterprise_id, target_month, horizon, p10, p50, p90, projected_balance, method, model_version, generated_at)
risk_scores(enterprise_id, as_of, score, band, drivers JSONB, model_version)
alerts(id, enterprise_id, severity, cause_key, cause_text, suggestion_id, status, created_at)
suggestions(id, sector, driver_key, text_en, text_hi, action_type)
officers(id, name); officer_assignments(officer_id, enterprise_id)
users(id, role, enterprise_id?, officer_id?, phone, password_hash)
```

Indexes: `entries(enterprise_id, occurred_at)`, `risk_scores(enterprise_id, as_of DESC)`, `alerts(enterprise_id, status)`.

## 8. Testing & Demo-Readiness
- Unit: simulator determinism (seeded), feature builder golden-file test, rule overlay truth table, sync idempotency (replay same batch ⇒ no dupes).
- ML: eval script prints the §5.2 metric table; committed as `reports/model_eval.md` for judges.
- E2E happy path (Playwright, 1 script): offline entry → reconnect → sync → alert appears → officer sees band change.
- Demo script safety: seeded DB snapshot restorable in one command (`make demo-reset`).
