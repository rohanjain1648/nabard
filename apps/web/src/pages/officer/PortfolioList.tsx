import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import client from '../../api/client'
import type { Band, PortfolioItem, PortfolioSummary } from '../../api/types'
import AppShell from '../../components/AppShell'
import RiskBadge from '../../components/RiskBadge'
import { IconArrowRight, IconMap, IconSearch, IconShield } from '../../components/icons'

const BANDS: Band[] = ['red', 'amber', 'green']

export default function PortfolioList() {
  const { t } = useTranslation()
  const [summary, setSummary] = useState<PortfolioSummary | null>(null)
  const [items, setItems] = useState<PortfolioItem[]>([])
  const [bandFilter, setBandFilter] = useState<string>('')
  const [sectorFilter, setSectorFilter] = useState<string>('')
  const [query, setQuery] = useState('')

  useEffect(() => {
    client.get<PortfolioSummary>('/portfolio/summary').then((res) => setSummary(res.data))
  }, [])

  useEffect(() => {
    client.get<PortfolioItem[]>('/portfolio', {
      params: { band: bandFilter || undefined, sector: sectorFilter || undefined, q: query || undefined },
    }).then((res) => setItems(res.data))
  }, [bandFilter, sectorFilter, query])

  const sectors = summary ? Object.keys(summary.sector_heatmap) : []

  return (
    <AppShell>
      <div className="page-head">
        <div>
          <div className="eyebrow" style={{ marginBottom: 6 }}>
            <IconShield size={14} /> {t('risk_panel.title')}
          </div>
          <h1 style={{ fontSize: 26 }}>{t('portfolio.title')}</h1>
          <p className="muted" style={{ marginTop: 4 }}>{t('portfolio.subtitle')}</p>
        </div>
      </div>

      {summary && (
        <div className="grid grid-4" style={{ marginBottom: 18 }}>
          <BandStat label={t('band.red')} value={summary.red} cls="badge-red" active={bandFilter === 'red'} onClick={() => setBandFilter(bandFilter === 'red' ? '' : 'red')} />
          <BandStat label={t('band.amber')} value={summary.amber} cls="badge-amber" active={bandFilter === 'amber'} onClick={() => setBandFilter(bandFilter === 'amber' ? '' : 'amber')} />
          <BandStat label={t('band.green')} value={summary.green} cls="badge-green" active={bandFilter === 'green'} onClick={() => setBandFilter(bandFilter === 'green' ? '' : 'green')} />
          <BandStat label={t('risk_panel.total')} value={summary.total} cls="badge-soft" active={bandFilter === ''} onClick={() => setBandFilter('')} />
        </div>
      )}

      <div className="officer-grid">
        {/* Enterprise list */}
        <section className="card card-pad">
          <div className="filters">
            <div className="search-wrap">
              <IconSearch className="ico" size={17} />
              <input
                className="input" placeholder={t('portfolio.search')}
                value={query} onChange={(e) => setQuery(e.target.value)}
              />
            </div>
            <select className="select" style={{ flex: 1, minWidth: 130 }} value={bandFilter} onChange={(e) => setBandFilter(e.target.value)}>
              <option value="">{t('portfolio.filter_band')}: {t('portfolio.all')}</option>
              {BANDS.map((b) => <option key={b} value={b}>{t(`band.${b}`)}</option>)}
            </select>
            <select className="select" style={{ flex: 1, minWidth: 130 }} value={sectorFilter} onChange={(e) => setSectorFilter(e.target.value)}>
              <option value="">{t('portfolio.filter_sector')}: {t('portfolio.all')}</option>
              {sectors.map((s) => <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>)}
            </select>
          </div>

          <p className="muted" style={{ fontSize: 12.5, margin: '4px 0 14px' }}>
            {t('portfolio.results', { count: items.length })}
          </p>

          {items.length === 0 && <div className="empty">{t('portfolio.no_results')}</div>}

          {items.map((item) => (
            <Link key={item.enterprise_id} to={`/officer/enterprise/${item.enterprise_id}`}>
              <div className="ent-row">
                <div className="row" style={{ gap: 12, minWidth: 0 }}>
                  <span className="ent-avatar">{item.name.charAt(0)}</span>
                  <div style={{ minWidth: 0 }}>
                    <div className="list-row-title" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {item.name}
                    </div>
                    <div className="list-row-sub row" style={{ gap: 5 }}>
                      <IconMap size={13} />
                      {item.sector.replace(/_/g, ' ')} · {item.village}, {item.district}
                    </div>
                  </div>
                </div>
                <div className="row" style={{ gap: 12, flex: 'none' }}>
                  <div className="stack" style={{ alignItems: 'flex-end', gap: 4 }}>
                    <RiskBadge band={item.band} score={item.score} />
                    <span className="list-row-sub">{t('portfolio.last_entry')}: {item.last_entry_at ?? '—'}</span>
                  </div>
                  <IconArrowRight size={18} style={{ color: 'var(--ink-300)' }} />
                </div>
              </div>
            </Link>
          ))}
        </section>

        {/* Sector heatmap */}
        {summary && (
          <aside className="card card-pad" style={{ position: 'sticky', top: 78 }}>
            <div className="card-title">
              <IconShield className="ico" size={18} /> {t('risk_panel.sector_heatmap')}
            </div>
            <table className="heat">
              <thead>
                <tr>
                  <th>Sector</th>
                  <th className="n" style={{ color: 'var(--red)' }}>●</th>
                  <th className="n" style={{ color: 'var(--amber)' }}>●</th>
                  <th className="n" style={{ color: 'var(--green)' }}>●</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(summary.sector_heatmap).map(([sector, counts]) => (
                  <tr key={sector}>
                    <td style={{ textTransform: 'capitalize' }}>{sector.replace(/_/g, ' ')}</td>
                    <td className="n" style={{ color: 'var(--red)', opacity: counts.red ? 1 : 0.3 }}>{counts.red ?? 0}</td>
                    <td className="n" style={{ color: 'var(--amber)', opacity: counts.amber ? 1 : 0.3 }}>{counts.amber ?? 0}</td>
                    <td className="n" style={{ color: 'var(--green)', opacity: counts.green ? 1 : 0.3 }}>{counts.green ?? 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </aside>
        )}
      </div>
    </AppShell>
  )
}

function BandStat({ label, value, cls, active, onClick }: {
  label: string; value: number; cls: string; active: boolean; onClick: () => void
}) {
  return (
    <button className="stat" onClick={onClick} style={{ textAlign: 'left', cursor: 'pointer', outline: active ? '2px solid var(--brand-500)' : 'none', outlineOffset: 2 }}>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <span className="stat-value">{value}</span>
        <span className={`badge ${cls}`} style={{ padding: '3px 8px' }}><span className="dot" /></span>
      </div>
      <div className="stat-label">{label}</div>
    </button>
  )
}
