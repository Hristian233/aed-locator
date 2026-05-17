import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import bg from '../locales/bg/translation.json'
import en from '../locales/en/translation.json'

const STORAGE_KEY = 'aed_locale'

function detectLanguage(): string {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'bg' || stored === 'en') return stored
  return 'bg'
}

void i18n.use(initReactI18next).init({
  resources: {
    bg: { translation: bg },
    en: { translation: en },
  },
  lng: detectLanguage(),
  fallbackLng: 'bg',
  interpolation: { escapeValue: false },
})

i18n.on('languageChanged', (lng) => {
  localStorage.setItem(STORAGE_KEY, lng)
  document.documentElement.lang = lng
})

document.documentElement.lang = detectLanguage()

export default i18n
