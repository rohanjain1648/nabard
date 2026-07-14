import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { IconWifiOff } from './icons'

export default function OfflineBanner() {
  const { t } = useTranslation()
  const [online, setOnline] = useState(navigator.onLine)

  useEffect(() => {
    const goOnline = () => setOnline(true)
    const goOffline = () => setOnline(false)
    window.addEventListener('online', goOnline)
    window.addEventListener('offline', goOffline)
    return () => {
      window.removeEventListener('online', goOnline)
      window.removeEventListener('offline', goOffline)
    }
  }, [])

  if (online) return null
  return (
    <div className="offline-banner">
      <span className="row" style={{ gap: 8, justifyContent: 'center' }}>
        <IconWifiOff size={16} />
        {t('status.offline')}
      </span>
    </div>
  )
}
