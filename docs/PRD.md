# PRD — CashFlow Sahayak
### AI-Driven Cash Flow Prediction & Risk Flagging for Rural Micro Enterprises

| | |
|---|---|
| **Version** | 0.1 (Hackathon MVP) |
| **Date** | 2026-07-14 |
| **Sponsor context** | NABARD hackathon problem statement |
| **Companion docs** | [TRD.md](TRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [DELIVERY-PLAN.md](DELIVERY-PLAN.md) |

---

## 1. Problem & Vision

**Problem.** Millions of rural micro enterprises (SHGs, FPOs, individual entrepreneurs) lack formal credit histories. Financial-health monitoring is manual, so early warning signs of stress are missed — leading to delayed interventions, liquidity crunches, and credit risk. Meanwhile UPI adoption, commodity price feeds, weather data, and seasonal patterns form a rich but unused signal ecosystem.

**Vision.** A single platform where:
- an **enterprise owner** records simple income/expense/savings/loan entries (even offline, in their own language) and receives a 3–6 month cash-flow forecast, plain-language risk alerts, and actionable suggestions;
- a **field officer** sees a risk-ranked portfolio of enterprises, drills into any profile, and intervenes *before* stress becomes default.

**One-line pitch:** *"A credit bureau substitute + early-warning radar for the 60M+ rural enterprises that banks can't see."*

## 2. Goals & Non-Goals

### Goals (MVP)
1. Predict monthly net cash flow per enterprise over a **3–6 month horizon** with uncertainty bands.
2. Produce a **risk score (Green / Amber / Red)** with explainable, plain-language reasons.
3. **Early warning system**: alert when forecasted liquidity falls below obligations (loan EMI, recurring expenses) or when behavioral signals degrade.
4. Integrate **multi-source signals**: financial records, UPI-style transaction proxies, commodity prices, weather/climate, and sector seasonality — using **simulated datasets**.
5. Two working interfaces: enterprise PWA (offline-capable) and field-officer dashboard.
6. Sector-specific risk modeling for **dairy, poultry, food processing, handicrafts, rural retail**.

### Non-Goals (explicitly out of scope for MVP)
- Real UPI/AA (Account Aggregator) integration — simulated feeds only.
- Actual loan origination / disbursement workflows.
- KYC, Aadhaar, or any sensitive personal data handling.
- Native mobile apps (PWA covers mobile).
- Production-grade multi-tenancy and RBAC beyond two roles.

## 3. Users & Personas

### P1 — Enterprise Owner ("Sunita", SHG dairy entrepreneur)
- Smartphone user, comfortable with UPI, low comfort with English/finance jargon.
- Intermittent 2G/3G connectivity; often offline for hours.
- **Needs:** dead-simple data entry (< 30 seconds per entry), "will I have enough money in October?", "what should I do about it?" in Hindi/local language.

### P2 — Field Officer ("Rajesh", bank/NABARD-affiliated BC covering 150 enterprises)
- Laptop/tablet at branch, smartphone in field.
- **Needs:** which of my 150 enterprises need attention *this week*; evidence to justify intervention or credit recommendation; portfolio-level view for reporting.

### P3 (stretch) — Institution Admin
- Aggregate dashboards, sector/region heatmaps, export for credit appraisal.

## 4. User Stories & Acceptance Criteria

### Enterprise Owner
| ID | Story | Acceptance criteria |
|----|-------|---------------------|
| E1 | Record income/expense/savings/loan-repayment in < 30s | Big-button category picker, amount, optional note; works fully offline; syncs when online |
| E2 | See my cash-flow forecast | Chart of next 3–6 months net cash flow with confidence band; current balance trajectory; readable on 5" screen |
| E3 | Get risk alerts I understand | Alert card: severity color, one-sentence cause ("Milk prices falling + your loan EMI due"), one suggested action |
| E4 | Get actionable suggestions | ≥ 1 concrete suggestion per amber/red state (e.g., "delay ₹X purchase to Sept", "build ₹Y buffer before monsoon") |
| E5 | Use it in my language | UI strings externalized; ship English + Hindi; icons carry meaning without text |

### Field Officer
| ID | Story | Acceptance criteria |
|----|-------|---------------------|
| F1 | Risk-ranked enterprise list | Sortable/filterable by risk level, sector, village; red items pinned top |
| F2 | Enterprise profile drill-down | Financial summary, entry history, forecast chart, risk factor breakdown, alert timeline |
| F3 | Cash-flow forecast view | Same forecast as owner sees, plus model drivers (top contributing factors) |
| F4 | Risk panel | Portfolio distribution (G/A/R counts), sector risk heat, trend vs last month, alert feed |
| F5 | Log an intervention (stretch) | Mark alert as "contacted / resolved / escalated" |

## 5. Core Features

### 5.1 Data entry (enterprise)
- Categories tuned per sector (dairy: milk sales, fodder, vet; retail: stock purchase, daily sales…).
- Quick-add presets; voice note attachment (stretch).
- Savings balance, loan details (principal, EMI, due day) captured at onboarding.

### 5.2 Forecast engine
- Monthly net cash-flow forecast, horizon 3–6 months, P10/P50/P90 bands.
- Blends: enterprise's own history + sector seasonality curve + commodity price outlook + weather/climate index. Cold-start supported via sector priors (works from day 1 with < 3 months of data).

### 5.3 Risk scoring & early warning
- Composite 0–100 score → Green (≥70) / Amber (40–69) / Red (<40).
- Signal families: **liquidity** (forecast balance vs obligations), **behavioral** (entry regularity, UPI-proxy velocity drop), **repayment** (EMI coverage ratio, missed payments), **market** (commodity price shock for the sector), **climate** (rainfall anomaly, heat stress index), **seasonal** (known lean months).
- Every score change ships with top-3 explainable drivers in plain language.

### 5.4 Alerts & suggestions
- Rule + model hybrid: model flags, rules translate to human actions.
- Suggestion library keyed by (sector × risk driver) — e.g., dairy + fodder-price spike → "lock fodder purchase now / consider silage".
- Delivery: in-app; SMS-format text preview (stretch).

### 5.5 Dashboards
- Officer: portfolio KPIs, risk distribution, sector heatmap, watchlist, alert feed.
- Owner: "this month vs typical month", savings runway, upcoming obligations.

### 5.6 Offline-first
- Full data-entry and last-synced forecast/alerts available offline (PWA + local store).
- Background sync with conflict-free merge (append-only ledger entries).

### 5.7 Multilingual (optional → shipped as EN+HI)
- i18n framework in from day 1; string files for others later.

## 6. Sector Risk Profiles (built into simulator + model)

| Sector | Income pattern | Key risks modeled |
|--------|----------------|-------------------|
| Dairy | Daily, stable-ish; dips in summer (heat → yield drop) | Fodder price, heat stress, milk procurement price |
| Poultry | Batch cycles (~6–8 wks) | Feed (maize/soy) price, disease shock, festival demand swings |
| Food processing | Post-harvest seasonal | Raw commodity price, storage, demand seasonality |
| Handicrafts | Festival/export spikes, long dry spells | Demand seasonality, input cost, order concentration |
| Rural retail | Steady with harvest-linked peaks | Rural purchasing power (crop income proxy), credit sales exposure |

## 7. Success Metrics (hackathon judging + product)

| Metric | Target |
|--------|--------|
| Forecast quality on simulated holdout | MAPE ≤ 20% at 3-month horizon (P50) |
| Early-warning lead time | Red flag ≥ 30 days before simulated stress event, ≥ 80% recall |
| False alarm rate | ≤ 20% of red flags are false positives |
| Offline entry → sync round-trip | Works with network toggled off in demo |
| Entry friction | ≤ 3 taps + amount for a transaction |
| Demo coverage | 5 sectors × ~10 enterprises with 18–24 months simulated history |

## 8. Assumptions & Constraints
- All data **simulated** (see TRD §4 for simulator spec); no sensitive personal information; UPI proxies are aggregate patterns (counts, volumes), never counterparty identities.
- Must run in low-network conditions; demo must survive airplane-mode toggle.
- Single deployable prototype (one backend, one web app with two role views) — hackathon timebox.

## 9. Risks & Mitigations
| Risk | Mitigation |
|------|-----------|
| Simulated data too clean → model looks fake-good | Inject noise, shocks, missingness, irregular entries into simulator |
| ML overreach in timebox | Ship baseline (seasonal-naive + gradient boosting) first; fancy models only if time remains |
| Offline sync complexity eats the schedule | Append-only ledger design = trivial merge; forecasts are server-computed and cached |
| Judges ask "where does real UPI data come from?" | Documented adapter interface + AA-framework/NPCI-aggregate answer in ARCHITECTURE §7 |

## 10. Value for NABARD (framing for pitch)
1. **Credit flow**: cash-flow-based appraisal for the credit-invisible → bankable dossiers.
2. **Grant-to-credit bridge**: demonstrated repayment capacity moves beneficiaries from grants to institutional finance.
3. **Digital public good**: open, sector-extensible profiling + risk rails any RRB/cooperative can adopt.
4. **Beneficiary outcomes**: owners get foresight, not just hindsight.
