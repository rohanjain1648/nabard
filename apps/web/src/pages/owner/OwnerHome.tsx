import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import client from '../../api/client'
import type {
  Alert, Categories, EnterpriseProfile, EntryIn, EntryType, ForecastRow, RiskScore,
} from '../../api/types'
import AppShell from '../../components/AppShell'
import ForecastChart from '../../components/ForecastChart'
import RiskBadge from '../../components/RiskBadge'
import {
  IconBell, IconChart, IconCheck, IconCloud, IconMap, IconPlus, IconWallet,
} from '../../components/icons'
import { getCached, getDeviceId } from '../../offline/db'
import { getLocalEntries, queueEntry, syncNow } from '../../offline/sync'

const ENTRY_TYPES: EntryType[] = ['income', 'expense', 'savings_deposit', 'savings_withdrawal', 'loan_repayment']

export default function OwnerHome() {
  const { t, i18n } = useTranslation()

  const [profile, setProfile] = useState<EnterpriseProfile | null>(null)
  const [categories, setCategories] = useState<Categories | null>(null)
  const [forecast, setForecast] = useState<ForecastRow[]>([])
  const [risk, setRisk] = useState<RiskScore | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [localEntries, setLocalEntries] = useState<EntryIn[]>([])
  const [pendingCount, setPendingCount] = useState(0)
  const [syncing, setSyncing] = useState(false)

  const [entryType, setEntryType] = useState<EntryType>('income')
  const [category, setCategory] = useState('')
  const [amount, setAmount] = useState('')
  const [note, setNote] = useState('')
  const [savedMessage, setSavedMessage] = useState(false)

  async function refreshLocalState() {
    const entries = await getLocalEntries()
    setLocalEntries(entries)
    setPendingCount(entries.filter((e) => !(e as EntryIn & { synced?: number }).synced).length)
    const cachedForecast = await getCached<ForecastRow[]>('forecast')
    if (cachedForecast) setForecast(cachedForecast.value)
    const cachedRisk = await getCached<RiskScore | null>('risk')
    if (cachedRisk) setRisk(cachedRisk.value)
    const cachedAlerts = await getCached<Alert[]>('alerts')
    if (cachedAlerts) setAlerts(cachedAlerts.value)
  }

  async function doSync() {
    setSyncing(true)
    const result = await syncNow()
    if (result) {
      setForecast(result.forecast)
      setRisk(result.risk)
      setAlerts(result.alerts)
    }
    await refreshLocalState()
    setSyncing(false)
  }

  useEffect(() => {
    client.get<EnterpriseProfile>('/me/enterprise').then((res) => setProfile(res.data)).catch(() => {})
    refreshLocalState()
    doSync()

    const onOnline = () => doSync()
    window.addEventListener('online', onOnline)
    return () => window.removeEventListener('online', onOnline)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!profile) return
    client.get<Categories>('/config/categories', { params: { sector: profile.sector } })
      .then((res) => setCategories(res.data))
      .catch(() => {})
  }, [profile])

  const categoryOptions = useMemo(() => categories?.[entryType] ?? [], [categories, entryType])

  useEffect(() => {
    setCategory(categoryOptions[0] ?? '')
  }, [categoryOptions])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!amount || !category) return
    const deviceId = await getDeviceId()
    const entry: EntryIn = {
      id: crypto.randomUUID(),
      type: entryType,
      category,
      amount: parseFloat(amount),
      note: note || null,
      occurred_at: new Date().toISOString().slice(0, 10),
      device_id: deviceId,
    }
    await queueEntry(entry)
    setAmount('')
    setNote('')
    setSavedMessage(true)
    setTimeout(() => setSavedMessage(false), 2000)
    await refreshLocalState()
    doSync()
  }

  const syncLabel = syncing
    ? t('status.syncing')
    : pendingCount > 0
      ? t('status.sync_pending', { count: pendingCount })
      : t('status.synced')

  return (
    <AppShell showOffline>
      {/* Hero row: enterprise identity + risk + sync state */}
      <section className="card card-pad" style={{ marginBottom: 18 }}>
        <div className="owner-hero">
          <div>
            <div className="eyebrow" style={{ marginBottom: 6 }}>
              <IconWallet size={14} /> {t('owner.greeting')}
            </div>
            <h1 style={{ fontSize: 24 }}>{profile?.name ?? t('app_name')}</h1>
            {profile && (
              <div className="row muted" style={{ gap: 6, marginTop: 4, fontSize: 14 }}>
                <IconMap size={15} />
                {profile.village}, {profile.district}
              </div>
            )}
          </div>
          <div className="stack" style={{ alignItems: 'flex-end', gap: 10 }}>
            {risk ? <RiskBadge band={risk.band} score={risk.score} /> : <RiskBadge band="unknown" />}
            <span className={`sync-chip ${pendingCount > 0 && !syncing ? 'is-pending' : ''}`}>
              <IconCloud size={14} /> {syncLabel}
            </span>
          </div>
        </div>
      </section>

      <div className="owner-grid">
        {/* Left column */}
        <div className="stack" style={{ gap: 18 }}>
          <section className="card card-pad">
            <div className="card-title">
              <IconChart className="ico" size={18} /> {t('forecast.title')}
            </div>
            <p className="muted" style={{ fontSize: 13, marginTop: -8, marginBottom: 12 }}>
              {t('forecast.subtitle')}
            </p>
            <ForecastChart data={forecast} />
          </section>

          <section className="card card-pad">
            <div className="card-title">
              <IconBell className="ico" size={18} /> {t('alerts.title')}
            </div>
            {alerts.length === 0 && (
              <div className="empty">
                <IconCheck size={22} style={{ color: 'var(--green)', margin: '0 auto 8px' }} />
                {t('alerts.none')}
              </div>
            )}
            {alerts.map((a) => (
              <div key={a.id} className={`alert-item ${a.severity === 'red' ? 'alert-red' : 'alert-amber'}`}>
                <div style={{ fontSize: 14, color: 'var(--ink-800)' }}>
                  {i18n.language.startsWith('hi') ? a.cause_text_hi : a.cause_text_en}
                </div>
              </div>
            ))}
          </section>
        </div>

        {/* Right column */}
        <div className="stack" style={{ gap: 18 }}>
          <section className="card card-pad">
            <div className="card-title">
              <IconPlus className="ico" size={18} /> {t('entry.add_entry')}
            </div>
            <form onSubmit={handleSubmit}>
              <div className="type-grid">
                {ENTRY_TYPES.map((type) => (
                  <button
                    type="button" key={type} onClick={() => setEntryType(type)}
                    className={`pill ${entryType === type ? 'is-active' : ''}`}
                  >
                    {t(`entry.${type}`)}
                  </button>
                ))}
              </div>
              <div className="field">
                <label>{t('entry.category')}</label>
                <select className="select" value={category} onChange={(e) => setCategory(e.target.value)}>
                  {categoryOptions.map((c) => <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>)}
                </select>
              </div>
              <div className="field">
                <label>{t('entry.amount')}</label>
                <input
                  className="input" type="number" inputMode="decimal" value={amount}
                  onChange={(e) => setAmount(e.target.value)} required min={0} placeholder="0"
                />
              </div>
              <div className="field">
                <label>{t('entry.note')}</label>
                <input className="input" value={note} onChange={(e) => setNote(e.target.value)} />
              </div>
              <button type="submit" className="btn btn-primary btn-block">
                {t('entry.save')}
              </button>
              {savedMessage && (
                <p className="row" style={{ gap: 6, color: 'var(--green)', fontSize: 13, marginTop: 10, fontWeight: 600 }}>
                  <IconCheck size={15} /> {t('entry.saved_offline')}
                </p>
              )}
            </form>
          </section>

          <section className="card card-pad">
            <div className="card-title">{t('entry.recent_entries')}</div>
            {localEntries.length === 0 && <div className="empty">{t('entry.no_entries')}</div>}
            {localEntries.slice(0, 8).map((e) => {
              const outflow = e.type === 'expense' || e.type === 'loan_repayment' || e.type === 'savings_withdrawal'
              return (
                <div key={e.id} className="list-row">
                  <div>
                    <div className="list-row-title" style={{ fontSize: 14 }}>{t(`entry.${e.type}`)}</div>
                    <div className="list-row-sub">{e.category.replace(/_/g, ' ')} · {e.occurred_at}</div>
                  </div>
                  <span style={{ fontWeight: 700, color: outflow ? 'var(--red)' : 'var(--green)', fontVariantNumeric: 'tabular-nums' }}>
                    {outflow ? '−' : '+'}₹{e.amount.toLocaleString('en-IN')}
                  </span>
                </div>
              )
            })}
          </section>
        </div>
      </div>
    </AppShell>
  )
}
