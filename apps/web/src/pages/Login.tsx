import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import Brand from '../components/Brand'
import LanguageToggle from '../components/LanguageToggle'
import ThemeToggle from '../components/ThemeToggle'
import {
  IconArrowLeft, IconArrowRight, IconCheck, IconShield, IconWifiOff,
} from '../components/icons'

export default function Login() {
  const { t } = useTranslation()
  const { login } = useAuth()
  const navigate = useNavigate()
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(phone, password)
      navigate('/app')
    } catch {
      setError(t('login.error'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth">
      <aside className="auth-aside">
        <span className="orb orb-1" />
        <span className="orb orb-2" />
        <div>
          <Link to="/" className="row" style={{ gap: 8, color: 'rgba(255,255,255,0.85)', fontSize: 14, fontWeight: 600 }}>
            <IconArrowLeft size={16} /> {t('common.back')}
          </Link>
          <h2 style={{ marginTop: 40 }}>
            Turn a daily ledger into a bank-grade cash-flow forecast.
          </h2>
          <p className="q">
            CashFlow Sahayak gives rural micro-enterprises a credit history and their lenders a
            30-day head start on trouble.
          </p>
          <ul className="stack" style={{ gap: 14, marginTop: 30 }}>
            <AsideItem icon={<IconShield size={16} />}>Early-warning risk radar</AsideItem>
            <AsideItem icon={<IconWifiOff size={16} />}>Works fully offline</AsideItem>
            <AsideItem icon={<IconCheck size={16} />}>Bilingual — English &amp; हिन्दी</AsideItem>
          </ul>
        </div>

      </aside>

      <main className="auth-main">
        <div className="auth-card">
          <div className="row" style={{ justifyContent: 'space-between', marginBottom: 26 }}>
            <Brand withSub={false} />
            <div className="row" style={{ gap: 10 }}>
              <ThemeToggle />
              <LanguageToggle />
            </div>
          </div>

          <h1 style={{ fontSize: 26 }}>{t('login.title')}</h1>
          <p className="muted" style={{ marginTop: 6, marginBottom: 22 }}>{t('login.subtitle')}</p>

          <form onSubmit={handleSubmit}>
            <div className="field">
              <label htmlFor="phone">{t('login.phone')}</label>
              <input
                id="phone" className="input" value={phone}
                onChange={(e) => setPhone(e.target.value)}
                inputMode="numeric" autoComplete="username" autoFocus
                placeholder="9990000001"
              />
            </div>
            <div className="field">
              <label htmlFor="password">{t('login.password')}</label>
              <input
                id="password" className="input" type="password" value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password" placeholder="••••••••"
              />
            </div>
            {error && <p className="form-error">{error}</p>}
            <button type="submit" className="btn btn-primary btn-block btn-lg" disabled={loading}>
              {loading ? t('status.syncing') : t('login.submit')}
              {!loading && <IconArrowRight size={18} />}
            </button>
          </form>

          <div className="auth-demo">
            <strong>Demo logins</strong>
            <br />
            Owner — <code>9990000001</code> / <code>owner123</code>
            <br />
            Officer — <code>9990000002</code> / <code>officer123</code>
          </div>
        </div>
      </main>
    </div>
  )
}

function AsideItem({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <li className="row" style={{ gap: 12, color: 'rgba(255,255,255,0.9)', fontSize: 15 }}>
      <span
        style={{
          width: 34, height: 34, borderRadius: 10, flex: 'none',
          display: 'grid', placeItems: 'center',
          background: 'rgba(255,255,255,0.12)', border: '1px solid rgba(255,255,255,0.2)',
        }}
      >
        {icon}
      </span>
      {children}
    </li>
  )
}
