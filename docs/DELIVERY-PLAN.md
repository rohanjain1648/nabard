# Delivery Plan — CashFlow Sahayak (Hackathon)

Build order is chosen so that **the demo works end-to-end at every checkpoint** — you can stop after any phase and still have something to show.

## Phase 0 — Scaffold (~2–3 h)
- Repo layout: `apps/web` (Vite PWA), `apps/api` (FastAPI), `packages/simulator`, `packages/ml`, `docs/`.
- Docker Compose + no-Docker local path; CI-less, `make` targets: `seed`, `dev`, `demo-reset`, `train`, `eval`.
- Auth stub (2 hardcoded-seed users: 1 owner, 1 officer).

**Checkpoint:** blank app logs in as both roles.

## Phase 1 — Simulator + seeded DB (~4–6 h) ← highest-leverage piece
- Implement TRD §4 generator (5 sectors × 10 enterprises × 24 months, shocks, defects).
- Seed script + CSV export. Sanity notebook: plot 3 enterprises per sector, verify seasonality/shocks are visible to the naked eye.

**Checkpoint:** `make seed` produces a believable dataset; charts look like real rural businesses.

## Phase 2 — Ledger + owner entry UI + offline sync (~6–8 h)
- Entries API + idempotent `/sync`; Dexie local store; Workbox background sync.
- Owner entry screen (sector categories, 3-tap flow), history list, EN+HI strings.

**Checkpoint:** airplane-mode demo works (enter offline → reconnect → row appears server-side).

## Phase 3 — ML v1 (~6–8 h)
- Feature builder → LightGBM quantile forecaster + risk classifier per TRD §5; train on simulator, commit eval report.
- Batch job wired to sync + `/admin/rescore`. Baseline fallback for cold start.

**Checkpoint:** `reports/model_eval.md` beats seasonal-naive; scores populate for all 50 enterprises.

## Phase 4 — Owner insights + alerts (~4–6 h)
- Forecast chart (P10–P90 band), savings runway, obligations strip.
- Alert cards with driver text + suggestion (YAML library, EN+HI).
- Local offline rule subset.

**Checkpoint:** Sunita's phone shows "Red: milk price falling + EMI due — suggested action" in Hindi.

## Phase 5 — Officer dashboard (~5–7 h)
- Portfolio list (filters/sort), enterprise profile (forecast + drivers + alert timeline), risk panel (G/A/R, sector heatmap, alert feed).

**Checkpoint:** Rajesh finds the 6 red enterprises in under 10 seconds.

## Phase 6 — Demo polish (~3–4 h)
- `/admin/inject-shock` live-demo control; `make demo-reset`.
- PWA install prompt, icons, loading states; public deploy (Render/Fly) if time.
- Rehearse the 5-minute script below.

## Stretch (only if all above is green)
- SMS-format alert preview · voice entry · third language · officer intervention logging · district heatmap map view.

## 5-Minute Demo Script
1. **Hook (30s):** the credit-invisibility problem; show portfolio dashboard — 50 real-looking enterprises.
2. **Owner flow (90s):** phone in airplane mode → add expense in Hindi → reconnect → sync badge → forecast chart with uncertainty band.
3. **The money moment (90s):** `inject-shock` feed-price spike → dairy enterprise flips Amber live → alert explains *why* in plain language + suggestion.
4. **Officer flow (60s):** Rajesh's risk panel catches the same flip; drill into drivers; "this is a 30-day head start on a default."
5. **Close (30s):** eval numbers on screen (recall/lead-time), production path slide (AA framework, Agmarknet, IMD), NABARD value framing.

## Team Split (assuming 3–4 people)
| Track | Owner | Phases |
|---|---|---|
| Data + ML | 1 person | 1, 3, eval report |
| Backend + sync | 1 person | 0, 2(api), 4(alerts), 6(demo controls) |
| Frontend | 1–2 people | 2(ui), 4(ui), 5 |

## Definition of Done (judge-facing)
- [ ] Offline entry → sync round-trip live on a phone
- [ ] 6-month forecast with uncertainty band, per enterprise
- [ ] Risk bands + top-3 plain-language drivers + suggestion on every Amber/Red
- [ ] Live shock injection changes a risk band during the demo
- [ ] Officer portfolio + profile + risk panel
- [ ] EN + HI toggle
- [ ] `model_eval.md` with metrics vs baseline
- [ ] One-command reset + seed
