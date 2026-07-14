import { useTheme } from '../theme/ThemeContext'
import { IconMoon, IconSun } from './icons'

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'
  return (
    <button
      className="pill theme-toggle"
      onClick={toggleTheme}
      aria-label={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
      title={isDark ? 'Switch to light theme' : 'Switch to dark theme'}
    >
      {isDark ? <IconMoon size={15} /> : <IconSun size={15} />}
    </button>
  )
}
