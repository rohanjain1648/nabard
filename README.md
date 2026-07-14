# CashFlow Sahayak
**AI-Driven Cash Flow Prediction & Risk Flagging for Rural Micro Enterprises** — NABARD hackathon prototype.

A credit-bureau substitute + early-warning radar for SHGs, FPOs, and rural entrepreneurs: owners log simple income/expense entries (offline-first, EN/HI), the platform fuses them with UPI-style activity proxies, commodity prices, and climate signals to forecast 3–6 month cash flow, flag stress 30+ days early, and hand field officers a risk-ranked portfolio.

## Planning Documents
| Doc | What's in it |
|---|---|
| [docs/PRD.md](docs/PRD.md) | Personas, user stories, features, sector risk profiles, success metrics, scope |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System diagram, component design, ML pipeline rationale, offline-first design, path to production |
| [docs/TRD.md](docs/TRD.md) | Functional/non-functional requirements, data simulator spec, ML spec, API surface, data model, testing |
| [docs/DELIVERY-PLAN.md](docs/DELIVERY-PLAN.md) | Phase-by-phase build order with checkpoints, team split, 5-minute demo script, definition of done |

## Status: working prototype

All phases in the delivery plan are implemented and verified end-to-end (offline entry → sync → forecast/risk update → officer dashboard; live shock-injection flips an enterprise's risk band during a demo). See [backend/reports/model_eval.md](backend/reports/model_eval.md) for honest model metrics.

## Repository layout
```
backend/            Python: FastAPI app + ML pipeline + data simulator (single uv project)
  src/cashflow/
    simulator/       deterministic dataset generator (TRD.md §4)
    ml/               feature builder, forecaster + risk classifier training, inference
    api/              FastAPI app: auth, ledger/sync, enterprises, portfolio, config, admin
  data/               seeded CSVs + SQLite DB (generated, gitignored in a real repo)
  models/             trained model artifacts (generated)
  reports/            model_eval.md (generated)
apps/web/            React + Vite + TypeScript PWA (owner + officer views)
docs/                PRD, TRD, Architecture, Delivery Plan
docker-compose.yml   containerized run (see below)
```

## Run it locally (fastest path — no Docker)

**Backend** (requires [uv](https://docs.astral.sh/uv/)):
```
cd backend
uv sync
uv run python -m cashflow.simulator.generate --out data --seed 42   # generate simulated dataset
uv run python -m cashflow.ml.train_forecast --data data --models models --reports reports
uv run python -m cashflow.ml.train_risk --data data --models models --reports reports
uv run python -m cashflow.api.seed --data data                      # seed the DB
uv run uvicorn cashflow.api.main:app --port 8000                    # start the API
```
Demo logins printed by the seed command: owner `9990000001` / `owner123`, officer `9990000002` / `officer123`.

**Frontend** (in a second terminal):
```
cd apps/web
npm install
npm run dev        # http://localhost:5173, proxies /api to the backend on :8000
```

To repopulate every enterprise's forecast/risk after a fresh seed: `POST http://127.0.0.1:8000/admin/rescore`.

To fire the live "shock" demo moment: `POST /admin/inject-shock` with `{"enterprise_id": "ENT0002", "shock_type": "feed_price_spike"}` (valid shock types: `feed_price_spike`, `drought`, `demand_collapse`, `disease_outbreak`, `emi_burden`) — watch the enterprise's band flip in the officer dashboard.

## Run it with Docker
```
docker compose up --build
```
Serves the web app on `:8080` (proxying `/api` to the backend on `:8000`). Requires `backend/data` to already contain a seeded `cashflow.db` and `backend/models` to contain trained artifacts (run the local backend steps above once first) — the containers don't run the simulator/training pipeline themselves.

## Architecture at a glance
- **Client:** React PWA (one app, two role views: enterprise owner + field officer), Dexie/IndexedDB local ledger with an offline-first entry queue — verified working with the network toggled off.
- **Backend:** FastAPI modular monolith (JWT auth, idempotent batch `/sync`), SQLAlchemy over SQLite (swappable to PostgreSQL via `DATABASE_URL`).
- **ML:** pooled LightGBM — a median forecaster blended with a seasonal-naive baseline (weight chosen via cross-validation) plus residual-calibrated P10/P90 intervals; a risk classifier trained on simulator-generated stress labels (restricted to genuine pre-onset transitions, evaluated via walk-forward backtesting) with isotonic calibration, rule-overlay floors, and SHAP-driven plain-language driver explanations.
- **Data:** deterministic simulator (5 sectors × 10 enterprises × 24 months, injected shocks = ground-truth labels) behind adapter interfaces that real Agmarknet/IMD/AA-framework feeds can replace.

## Known scope cuts (hackathon timebox)
- No Workbox/service-worker app-shell caching yet — offline *data entry and sync* work today (verified), but a hard reload while fully offline needs a prior visit to have cached the page. Full PWA installability is a short follow-up (`vite-plugin-pwa` is already a dependency).
- Docker path is provided but not build-tested in this session; the local `uv` + `npm run dev` path is what's been verified end-to-end.
- Forecast point-accuracy is near parity with the (unusually strong, due to simulator determinism) seasonal-naive baseline; the risk classifier and the interval calibration are where the model demonstrably adds value today — see the eval report for the full, honest breakdown.
