import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, useParams } from 'react-router-dom'
import client from '../../api/client'
import type { Alert, EnterpriseProfile as Profile, ForecastRow, RiskScore } from '../../api/types'
import AppShell from '../../components/AppShell'
import ForecastChart from '../../components/ForecastChart'
import RiskBadge from '../../components/RiskBadge'
import {
  IconArrowLeft, IconBell, IconChart, IconMap, IconSparkle, IconWallet,
} from '../../components/icons'

export default function EnterpriseProfile() {
  const { t, i18n } = useTranslation()
  const { enterpriseId } = useParams<{ enterpriseId: string }>()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [forecast, setForecast] = useState<ForecastRow[]>([])
  const [risk, setRisk] = useState<RiskScore | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])

  useEffect(() => {
    if (!enterpriseId) return
    client.get<Profile>(`/enterprises/${enterpriseId}/profile`).then((res) => setProfile(res.data))
    client.get<ForecastRow[]>(`/enterprises/${enterpriseId}/forecast`).then((res) => setForecast(res.data))
    client.get<RiskScore | null>(`/enterprises/${enterpriseId}/risk`).then((res) => setRisk(res.data))
    client.get<Alert[]>(`/enterprises/${enterpriseId}/alerts`).then((res) => setAlerts(res.data))
  }, [enterpriseId])

  if (!profile) {
    return (
      <AppShell>
        <div className="empty">{t('enterprise.loading')}</div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <Link to="/officer" className="back-link" style={{ marginBottom: 16 }}>
        <IconArrowLeft size={16} /> {t('nav.portfolio')}
      </Link>

      <section className="card card-pad" style={{ marginTop: 12, marginBottom: 18 }}>
        <div className="owner-hero">
          <div className="row" style={{ gap: 14 }}>
            <span className="ent-avatar" style={{ width: 52, height: 52, fontSize: 20 }}>{profile.name.charAt(0)}</span>
            <div>
              <h1 style={{ fontSize: 23 }}>{profile.name}</h1>
              <div className="row muted" style={{ gap: 6, marginTop: 4, fontSize: 14 }}>
                <IconMap size={15} />
                <span style={{ textTransform: 'capitalize' }}>{profile.sector.replace(/_/g, ' ')}</span> · {profile.village}, {profile.district}, {profile.state}
              </div>
            </div>
          </div>
          {risk && <RiskBadge band={risk.band} score={risk.score} />}
        </div>

        <div className="grid grid-3" style={{ marginTop: 20 }}>
          <div className="stat">
            <div className="stat-label row" style={{ gap: 6, marginTop: 0, marginBottom: 6 }}>
              <IconWallet size={14} /> {t('enterprise.savings_balance')}
            </div>
            <div className="stat-value" style={{ fontSize: 22 }}>₹{profile.savings_balance.toLocaleString('en-IN')}</div>
          </div>
          {profile.loans.map((loan) => (
            <div className="stat" key={loan.id}>
              <div className="stat-label" style={{ marginTop: 0, marginBottom: 6 }}>{t('enterprise.loan_emi')}</div>
              <div className="stat-value" style={{ fontSize: 22 }}>
                ₹{loan.emi_amount.toLocaleString('en-IN')}
                <span className="muted" style={{ fontSize: 13, fontWeight: 600 }}> {t('enterprise.monthly')}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="officer-grid">
        <div className="stack" style={{ gap: 18 }}>
          <section className="card card-pad">
            <div className="card-title">
              <IconChart className="ico" size={18} /> {t('forecast.title')}
            </div>
            <ForecastChart data={forecast} />
          </section>

          <section className="card card-pad">
            <div className="card-title">
              <IconBell className="ico" size={18} /> {t('enterprise.alert_timeline')}
            </div>
            {alerts.length === 0 && <div className="empty">{t('alerts.none')}</div>}
            {alerts.map((a) => (
              <div key={a.id} className={`alert-item ${a.severity === 'red' ? 'alert-red' : 'alert-amber'}`}>
                <div className="list-row-sub" style={{ marginBottom: 3 }}>{new Date(a.created_at).toLocaleString()}</div>
                <div style={{ fontSize: 14, color: 'var(--ink-800)' }}>
                  {i18n.language.startsWith('hi') ? a.cause_text_hi : a.cause_text_en}
                </div>
              </div>
            ))}
          </section>
        </div>

        <aside className="card card-pad" style={{ position: 'sticky', top: 78 }}>
          <div className="card-title">
            <IconSparkle className="ico" size={18} /> {t('risk.top_drivers')}
          </div>
          {risk && risk.drivers.length > 0 ? (
            <div className="stack" style={{ gap: 2 }}>
              {risk.drivers.map((d) => (
                <div key={d.driver_key} className="list-row" style={{ fontSize: 14 }}>
                  <span style={{ color: 'var(--ink-800)' }}>{d.human_text}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty">{t('alerts.none')}</div>
          )}
        </aside>
      </div>
    </AppShell>
  )
}
