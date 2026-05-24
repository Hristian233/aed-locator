import { useTranslation } from 'react-i18next'

interface ConnectionErrorViewProps {
  onRetry: () => void
}

export function ConnectionErrorView({ onRetry }: ConnectionErrorViewProps) {
  const { t } = useTranslation()

  return (
    <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-4 bg-slate-50 p-8 text-center">
      <div
        className="flex h-14 w-14 items-center justify-center rounded-full bg-red-100 text-red-600"
        aria-hidden
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="h-7 w-7"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v4m0 4h.01M5.07 19h13.86c1.54 0 2.5-1.67 1.73-3L13.73 5c-.77-1.33-2.69-1.33-3.46 0L3.34 16c-.77 1.33.19 3 1.73 3z"
          />
        </svg>
      </div>
      <div className="max-w-md space-y-2">
        <h2 className="text-lg font-semibold text-slate-900">{t('errors.serverTitle')}</h2>
        <p className="text-sm text-slate-600">{t('errors.serverMessage')}</p>
      </div>
      <button
        type="button"
        onClick={onRetry}
        className="rounded-full bg-teal-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-teal-700"
      >
        {t('errors.retry')}
      </button>
    </div>
  )
}
