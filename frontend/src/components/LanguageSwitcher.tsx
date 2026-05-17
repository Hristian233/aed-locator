import { useTranslation } from 'react-i18next'

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation()

  return (
    <label className="flex items-center gap-1.5 text-sm text-slate-600">
      <span className="sr-only">{t('language.label')}</span>
      <select
        value={i18n.language.startsWith('en') ? 'en' : 'bg'}
        onChange={(e) => void i18n.changeLanguage(e.target.value)}
        className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-sm font-medium text-slate-700"
        aria-label={t('language.label')}
      >
        <option value="bg">{t('language.bg')}</option>
        <option value="en">{t('language.en')}</option>
      </select>
    </label>
  )
}
