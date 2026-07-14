import { useTranslation } from 'react-i18next'
import { IconTrend } from './icons'

export default function Brand({ withSub = true }: { withSub?: boolean }) {
  const { t } = useTranslation()
  return (
    <span className="brand">
      <span className="brand-mark">
        <IconTrend size={19} />
      </span>
      <span className="stack" style={{ lineHeight: 1.1 }}>
        <span>{t('app_name')}</span>
        {withSub && <span className="brand-sub">{t('tagline_short')}</span>}
      </span>
    </span>
  )
}
