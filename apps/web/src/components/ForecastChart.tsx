import {
  Area, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import { useTranslation } from 'react-i18next'
import type { ForecastRow } from '../api/types'

export default function ForecastChart({ data }: { data: ForecastRow[] }) {
  const { t } = useTranslation()
  if (!data.length) {
    return <div className="empty">{t('forecast.empty')}</div>
  }
  const chartData = data.map((row) => ({
    month: row.target_month,
    p50: row.p50,
    p10: row.p10,
    p90: row.p90,
  }))

  return (
    <ResponsiveContainer width="100%" height={250}>
      <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -8, bottom: 0 }}>
        <defs>
          <linearGradient id="bandFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#14b8a6" stopOpacity={0.28} />
            <stop offset="100%" stopColor="#14b8a6" stopOpacity={0.06} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
        <XAxis
          dataKey="month" fontSize={11.5} stroke="var(--text-muted)"
          tickLine={false} axisLine={{ stroke: 'var(--border)' }}
        />
        <YAxis
          fontSize={11.5} stroke="var(--text-muted)" tickLine={false} axisLine={false}
          tickFormatter={(v: number) => `₹${Math.round(v / 1000)}k`}
          width={48}
        />
        <Tooltip
          contentStyle={{
            borderRadius: 12, border: '1px solid var(--border)', background: 'var(--surface)',
            boxShadow: '0 4px 14px rgba(15,23,42,0.16)', fontSize: 13, color: 'var(--text)',
          }}
          labelStyle={{ color: 'var(--heading)' }}
          formatter={(value, name) => [`₹${Math.round(Number(value)).toLocaleString('en-IN')}`, String(name)]}
        />
        {/* P10-P90 band: two non-stacked areas from y=0, inner painted with the card's
            surface color on top, so only the P10-P90 range shows through in either theme. */}
        <Area type="monotone" dataKey="p90" stroke="none" fill="url(#bandFill)" isAnimationActive={false} />
        <Area type="monotone" dataKey="p10" stroke="none" fill="var(--surface)" fillOpacity={1} isAnimationActive={false} />
        <Line
          type="monotone" dataKey="p50" stroke="#0d9488" strokeWidth={2.4}
          dot={{ r: 3, fill: '#0d9488', strokeWidth: 0 }}
          activeDot={{ r: 5 }} name={t('forecast.median')}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}
