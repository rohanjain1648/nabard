import { useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import Brand from '../components/Brand'
import Counter from '../components/Counter'
import LanguageToggle from '../components/LanguageToggle'
import ThemeToggle from '../components/ThemeToggle'
import { useLandingMotion } from '../hooks/useLandingMotion'
import {
  IconArrowRight, IconBell, IconChart, IconCheck, IconGlobe, IconLayers, IconLock,
  IconMap, IconShield, IconSparkle, IconTrend, IconUsers, IconWallet, IconWifiOff,
} from '../components/icons'

const STEPS = [
  { t: 'Owners log activity', d: 'Simple income & expense entries in seconds — offline, in their own language.' },
  { t: 'Signals get fused', d: 'Entries combine with commodity prices, climate and payment-activity proxies.' },
  { t: 'Cash flow is forecast', d: 'The model projects the next 3–6 months with calibrated confidence intervals.' },
  { t: 'Risk is scored', d: 'Genuine pre-onset stress is detected and banded Green / Amber / Red.' },
  { t: 'Field officers act', d: 'A risk-ranked portfolio tells officers exactly who to visit first, and why.' },
]

const TRUST = ['Self-Help Groups', 'FPOs', 'Rural entrepreneurs', 'RRBs', 'Business Correspondents', 'MFIs', 'NABARD']

export default function Landing() {
  const { t } = useTranslation()
  const rootRef = useRef<HTMLDivElement>(null)
  const heroRef = useRef<HTMLElement>(null)
  useLandingMotion(rootRef, heroRef)

  return (
    <div className="lp" ref={rootRef}>
      <div className="scroll-progress"><div className="scroll-bar" /></div>

      {/* Nav */}
      <nav className="lp-nav">
        <div className="container lp-nav-inner">
          <Brand />
          <div className="lp-nav-links">
            <a href="#problem">Problem</a>
            <a href="#how">How it works</a>
            <a href="#features">Features</a>
            <a href="#who">Who it's for</a>
          </div>
          <div className="row" style={{ gap: 10 }}>
            <ThemeToggle />
            <LanguageToggle />
            <Link to="/login" className="btn btn-ghost btn-sm">{t('common.sign_in')}</Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <header className="hero" ref={heroRef}>
        <div className="hero-orbs">
          <span className="orb orb-1" />
          <span className="orb orb-2" />
          <span className="orb orb-3" />
        </div>
        <div className="hero-spot" />
        <div className="container hero-inner">
          <div className="reveal reveal-left in">
            <span className="hero-badge">
              <span className="dot" style={{ background: 'var(--brand-400)' }} /> NABARD hackathon · working prototype
            </span>
            <h1>
              A credit history for the{' '}
              <span className="grad-anim">55&nbsp;million</span> rural enterprises the system can't see.
            </h1>
            <p className="hero-lead">
              CashFlow Sahayak turns a shopkeeper's daily ledger into a bank-grade cash-flow
              forecast and an early-warning risk score — fusing commodity prices, climate and
              payment signals, working fully offline, in English and Hindi.
            </p>
            <div className="hero-cta">
              <Link to="/login" className="btn btn-primary btn-lg">
                {t('common.launch_app')} <IconArrowRight size={18} />
              </Link>
              <a href="#how" className="btn btn-light btn-lg">{t('common.learn_more')}</a>
            </div>
            <div className="hero-stats">
              <div className="hero-stat">
                <b><Counter to={30} suffix="+ days" /></b>
                <span>earlier stress warning</span>
              </div>
              <div className="hero-stat">
                <b>3–6 mo</b>
                <span>cash-flow horizon</span>
              </div>
              <div className="hero-stat">
                <b><Counter to={100} suffix="%" /></b>
                <span>offline capable</span>
              </div>
            </div>
          </div>

          {/* Glass mockup + floating chips */}
          <div className="reveal reveal-right in" style={{ transitionDelay: '120ms' }}>
            <div className="mock-wrap" aria-hidden="true">
              <div className="hero-chip c1">
                <span className="chip-ico" style={{ background: 'var(--green-bg)', color: 'var(--green)' }}>
                  <IconTrend size={17} />
                </span>
                <span>
                  <span className="k">+₹42,000</span>
                  <br />6-mo forecast
                </span>
              </div>
              <div className="hero-chip c2">
                <span className="chip-ico" style={{ background: 'var(--red-bg)', color: 'var(--red)' }}>
                  <IconBell size={17} />
                </span>
                <span>Risk flipped → <span style={{ color: 'var(--red)' }}>Red</span></span>
              </div>

              <div className="mock">
                <div className="mock-head">
                  <div className="row" style={{ gap: 9 }}>
                    <span className="brand-mark" style={{ width: 28, height: 28 }}><IconTrend size={16} /></span>
                    <b style={{ fontSize: 14 }}>Ramesh Dairy</b>
                  </div>
                  <span className="badge badge-red"><span className="dot" /> At risk 71</span>
                </div>
                <div className="muted" style={{ fontSize: 12, fontWeight: 600 }}>6-month forecast</div>
                <div className="mock-bars">
                  {[62, 70, 66, 54, 40, 33].map((h, i) => (
                    <span key={i} style={{ height: `${h}%` }} />
                  ))}
                </div>
                <div className="mock-row">
                  <span className="row" style={{ gap: 8 }}>
                    <IconBell size={15} style={{ color: 'var(--red)' }} /> Feed prices up 22%
                  </span>
                  <span className="muted">−30d</span>
                </div>
                <div className="mock-row">
                  <span className="row" style={{ gap: 8 }}>
                    <IconWallet size={15} style={{ color: 'var(--amber)' }} /> EMI burden rising
                  </span>
                  <span className="muted">−12d</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Marquee trust ticker */}
        <div className="trust">
          <div className="marquee">
            <div className="marquee-track">
              {[...TRUST, ...TRUST].map((x, i) => (
                <span className="marquee-item" key={i}>
                  <IconCheck size={16} /> {x}
                </span>
              ))}
            </div>
          </div>
        </div>
      </header>

      {/* Problem */}
      <section className="section" id="problem">
        <div className="container">
          <div className="section-head reveal">
            <span className="eyebrow"><IconLock size={14} /> The problem</span>
            <h2>Creditworthy, but credit-invisible</h2>
            <p>
              Rural micro-enterprises deal in cash and have no formal statements, so lenders
              can't see them and can't catch trouble until a loan is already defaulting. The data
              exists — it's just scattered, informal, and never turned into a signal.
            </p>
          </div>
          <div className="grid grid-3 stagger">
            <ProblemCard n="No paper trail" d="Cash-based ledgers mean no bank statements, no bureau score, no basis for credit." />
            <ProblemCard n="Blind spots for lenders" d="Field officers manage hundreds of accounts and only learn of stress after a missed EMI." />
            <ProblemCard n="Shocks hit hardest" d="A feed-price spike, drought or demand collapse can sink a healthy business in weeks." />
          </div>
        </div>
      </section>

      {/* How it works — timeline */}
      <section className="section section-alt" id="how">
        <div className="container">
          <div className="section-head reveal">
            <span className="eyebrow"><IconLayers size={14} /> How it works</span>
            <h2>From a daily ledger to a decision</h2>
            <p>Five steps turn simple entries into forecasts, risk scores and field action.</p>
          </div>
          <div className="timeline stagger">
            {STEPS.map((s, i) => (
              <div className="tl-node" key={i}>
                <div className="tl-dot">{i + 1}</div>
                <h3>{s.t}</h3>
                <p>{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features — bento */}
      <section className="section" id="features">
        <div className="container">
          <div className="section-head reveal">
            <span className="eyebrow"><IconSparkle size={14} /> Capabilities</span>
            <h2>An AI core built for the last mile</h2>
            <p>Everything runs on-device-friendly infrastructure and honest, calibrated models.</p>
          </div>
          <div className="bento stagger">
            <article className="bento-card wide">
              <div className="bento-body">
                <div className="feature-ico"><IconChart /></div>
                <h3 style={{ fontSize: 18, marginBottom: 8 }}>Cash-flow forecasting</h3>
                <p className="muted" style={{ fontSize: 14.5, lineHeight: 1.6 }}>
                  A pooled LightGBM forecaster blended with a seasonal baseline projects 3–6 months of
                  net cash flow with residual-calibrated P10–P90 confidence bands.
                </p>
              </div>
              <div className="mini-bars">
                {[40, 58, 48, 70, 62, 82].map((h, i) => <span key={i} style={{ height: `${h}%` }} />)}
              </div>
            </article>

            <BentoCard icon={<IconShield />} title="Early-warning radar" body="A calibrated classifier flags stress 30+ days early, banding each enterprise Green / Amber / Red." />
            <BentoCard icon={<IconSparkle />} title="Plain-language reasons" body="SHAP drivers turn model output into human sentences — bilingual, auditable, actionable." />

            <article className="bento-card wide">
              <div className="mini-offline">
                <IconWifiOff size={30} />
              </div>
              <div className="bento-body">
                <div className="feature-ico"><IconWifiOff /></div>
                <h3 style={{ fontSize: 18, marginBottom: 8 }}>Offline-first by design</h3>
                <p className="muted" style={{ fontSize: 14.5, lineHeight: 1.6 }}>
                  An IndexedDB ledger queues entries with zero connectivity and syncs idempotently the
                  moment a signal returns — verified with the network switched off.
                </p>
              </div>
            </article>

            <BentoCard icon={<IconLayers />} title="Multi-source fusion" body="Ledger entries fused with Agmarknet prices and IMD climate behind swappable adapters." />
            <BentoCard icon={<IconGlobe />} title="Bilingual & low-literacy" body="Full English / हिन्दी, big tap targets and colour-coded risk anyone can read at a glance." />
          </div>
        </div>
      </section>

      {/* Stats band */}
      <section className="section section-alt">
        <div className="container">
          <div className="stats-band stagger">
            <div className="stat-big"><b><Counter to={55} suffix="M+" /></b><span>credit-invisible enterprises</span></div>
            <div className="stat-big"><b><Counter to={5} /></b><span>sectors modelled</span></div>
            <div className="stat-big"><b><Counter to={30} suffix="+ days" /></b><span>earlier warning</span></div>
            <div className="stat-big"><b><Counter to={2} /></b><span>languages, one app</span></div>
          </div>
        </div>
      </section>

      {/* Who it's for */}
      <section className="section" id="who">
        <div className="container">
          <div className="section-head reveal">
            <span className="eyebrow"><IconUsers size={14} /> Who it's for</span>
            <h2>One platform, two front doors</h2>
          </div>
          <div className="grid grid-2 stagger">
            <div className="persona owner">
              <span className="chip"><IconWallet size={15} /> Enterprise owner</span>
              <h3>See your money before it happens</h3>
              <p className="muted">A pocket dashboard that rewards a 10-second daily habit with real foresight.</p>
              <ul>
                <PersonaItem>Log income &amp; expenses offline, in Hindi or English</PersonaItem>
                <PersonaItem>See a 6-month forecast of where cash is heading</PersonaItem>
                <PersonaItem>Get early alerts with plain-language reasons</PersonaItem>
                <PersonaItem>Build a track record that unlocks fair credit</PersonaItem>
              </ul>
            </div>
            <div className="persona officer">
              <span className="chip"><IconMap size={15} /> Field officer</span>
              <h3>Know who to visit first</h3>
              <p className="muted">A risk-ranked portfolio replaces guesswork with a prioritised worklist.</p>
              <ul>
                <PersonaItem>Portfolio sorted by risk band with a sector heatmap</PersonaItem>
                <PersonaItem>Drill into any enterprise's forecast and drivers</PersonaItem>
                <PersonaItem>Alert timeline showing how stress built up</PersonaItem>
                <PersonaItem>Intervene 30+ days before a default, not after</PersonaItem>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Tech */}
      <section className="section section-alt">
        <div className="container">
          <div className="section-head reveal">
            <span className="eyebrow"><IconChart size={14} /> Under the hood</span>
            <h2>Honest models, production-shaped architecture</h2>
          </div>
          <div className="grid grid-2 stagger">
            <Tech k="LightGBM + seasonal blend" v="Median forecaster with residual-calibrated P10/P90 intervals — chosen over deep learning for tabular, low-data reality." />
            <Tech k="Calibrated risk classifier" v="Trained on genuine pre-onset stress transitions, walk-forward backtested, isotonic-calibrated with rule-overlay floors." />
            <Tech k="React + TypeScript PWA" v="One app, two role views. Dexie / IndexedDB offline ledger with an idempotent batch sync queue." />
            <Tech k="FastAPI + SQLAlchemy" v="Modular monolith with JWT auth over SQLite, swappable to PostgreSQL via a single env var." />
            <Tech k="Adapter-based data layer" v="A deterministic simulator today; real Agmarknet, IMD and Account-Aggregator feeds drop in behind the same interfaces." />
            <Tech k="SHAP explainability" v="Every risk score ships with its top human-readable drivers, bilingual, so decisions are auditable." />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="section" style={{ paddingTop: 0 }}>
        <div className="container">
          <div className="cta-band reveal reveal-scale">
            <h2>Try the working prototype</h2>
            <p>
              Explore both role views with seeded demo data — including a live shock that flips an
              enterprise's risk band in real time.
            </p>
            <Link to="/login" className="btn btn-primary btn-lg">
              {t('common.launch_app')} <IconArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="lp-footer">
        <div className="container lp-footer-inner">
          <Brand />
          <span>© {new Date().getFullYear()} CashFlow Sahayak · AI-driven cash-flow prediction &amp; risk flagging for rural micro-enterprises</span>
        </div>
      </footer>
    </div>
  )
}

function ProblemCard({ n, d }: { n: string; d: string }) {
  return (
    <div className="bento-card">
      <h3 style={{ marginBottom: 8, fontSize: 17 }}>{n}</h3>
      <p style={{ color: 'var(--text-muted)', fontSize: 14.5, lineHeight: 1.6 }}>{d}</p>
    </div>
  )
}
function BentoCard({ icon, title, body }: { icon: React.ReactNode; title: string; body: string }) {
  return (
    <article className="bento-card">
      <div className="feature-ico">{icon}</div>
      <h3 style={{ fontSize: 17, marginBottom: 8 }}>{title}</h3>
      <p className="muted" style={{ fontSize: 14.5, lineHeight: 1.6 }}>{body}</p>
    </article>
  )
}
function PersonaItem({ children }: { children: React.ReactNode }) {
  return (
    <li>
      <IconCheck size={17} className="tick" />
      <span>{children}</span>
    </li>
  )
}
function Tech({ k, v }: { k: string; v: string }) {
  return (
    <div className="tech-item">
      <span className="brand-mark" style={{ width: 30, height: 30 }}><IconCheck size={16} /></span>
      <div>
        <div className="k">{k}</div>
        <div className="v">{v}</div>
      </div>
    </div>
  )
}
