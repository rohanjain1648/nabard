import { useTranslation } from 'react-i18next'
import { setLanguage } from '../i18n'

export default function LanguageToggle() {
  const { i18n } = useTranslation()
  const lang = i18n.language.startsWith('hi') ? 'hi' : 'en'
  return (
    <div className="seg" role="group" aria-label="Language">
      <button
        className={lang === 'en' ? 'is-active' : ''}
        onClick={() => setLanguage('en')}
        aria-pressed={lang === 'en'}
      >
        EN
      </button>
      <button
        className={lang === 'hi' ? 'is-active' : ''}
        onClick={() => setLanguage('hi')}
        aria-pressed={lang === 'hi'}
      >
        हि
      </button>
    </div>
  )
}
