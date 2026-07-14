import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../auth/AuthContext'
import Brand from './Brand'
import LanguageToggle from './LanguageToggle'
import OfflineBanner from './OfflineBanner'
import ThemeToggle from './ThemeToggle'
import { IconLogout } from './icons'

export default function AppShell({
  children,
  showOffline = false,
}: {
  children: ReactNode
  showOffline?: boolean
}) {
  const { t } = useTranslation()
  const { logout } = useAuth()

  return (
    <div className="app">
      {showOffline && <OfflineBanner />}
      <header className="appbar">
        <div className="container appbar-inner">
          <Brand />
          <div className="row" style={{ gap: 10 }}>
            <ThemeToggle />
            <LanguageToggle />
            <button className="pill" onClick={logout}>
              <IconLogout size={15} />
              <span className="logout-label">{t('nav.logout')}</span>
            </button>
          </div>
        </div>
      </header>
      <main className="app-main">
        <div className="container">{children}</div>
      </main>
    </div>
  )
}
