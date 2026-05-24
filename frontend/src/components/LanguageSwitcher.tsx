import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'

const LANGUAGES = [
  { code: 'bg', display: '🇧🇬', isText: false, labelKey: 'language.bg' as const },
  { code: 'en', display: 'EN', isText: true, labelKey: 'language.en' as const },
] as const

export function LanguageSwitcher() {
  const { i18n, t } = useTranslation()
  const [open, setOpen] = useState(false)
  const rootRef = useRef<HTMLDivElement>(null)

  const currentCode = i18n.language.startsWith('en') ? 'en' : 'bg'
  const current = LANGUAGES.find((l) => l.code === currentCode) ?? LANGUAGES[0]

  useEffect(() => {
    if (!open) return
    const onPointerDown = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [open])

  const select = (code: string) => {
    void i18n.changeLanguage(code)
    setOpen(false)
  }

  const displayClass = (isText: boolean) =>
    isText
      ? 'text-xs font-bold tracking-wide text-slate-700'
      : 'text-lg leading-none'

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-label={t('language.label')}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="flex h-9 min-w-[3.25rem] items-center justify-center gap-1 rounded-lg border border-slate-200 bg-white px-2 hover:bg-slate-50"
      >
        <span aria-hidden className={displayClass(current.isText)}>
          {current.display}
        </span>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 20 20"
          fill="currentColor"
          className={`h-4 w-4 shrink-0 text-slate-500 transition ${open ? 'rotate-180' : ''}`}
          aria-hidden
        >
          <path
            fillRule="evenodd"
            d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.94a.75.75 0 111.08 1.04l-4.24 4.5a.75.75 0 01-1.08 0l-4.24-4.5a.75.75 0 01.02-1.06z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {open && (
        <ul
          role="listbox"
          aria-label={t('language.label')}
          className="absolute right-0 z-50 mt-1 min-w-full overflow-hidden rounded-lg border border-slate-200 bg-white py-1 shadow-lg"
        >
          {LANGUAGES.map(({ code, display, isText, labelKey }) => (
            <li key={code} role="option" aria-selected={code === currentCode}>
              <button
                type="button"
                aria-label={t(labelKey)}
                onClick={() => select(code)}
                className={`flex w-full items-center justify-center px-3 py-2 hover:bg-slate-50 ${
                  code === currentCode ? 'bg-teal-50' : ''
                }`}
              >
                <span aria-hidden className={displayClass(isText)}>
                  {display}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
