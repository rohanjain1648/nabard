import { useTranslation } from 'react-i18next'
import type { Band } from '../api/types'

const CLASS: Record<Band, string> = {
  green: 'badge badge-green',
  amber: 'badge badge-amber',
  red: 'badge badge-red',
  unknown: 'badge badge-unknown',
}

export default function RiskBadge({ band, score }: { band: Band; score?: number }) {
  const { t } = useTranslation()
  const cls = CLASS[band] ?? CLASS.unknown
  return (
    <span className={cls}>
      <span className="dot" />
      {t(`band.${band}`)}
      {typeof score === 'number' && (
        <span style={{ opacity: 0.75, fontWeight: 600 }}>{Math.round(score)}</span>
      )}
    </span>
  )
}
