import { useTranslation } from 'react-i18next'
import {
  accessibilityStatusClasses,
  getAccessibilityInfo,
} from '../lib/accessibility'
import type { AED } from '../types'

interface AccessibilityBadgeProps {
  aed: AED
  compact?: boolean
}

export function AccessibilityBadge({ aed, compact }: AccessibilityBadgeProps) {
  const { t } = useTranslation()
  const info = getAccessibilityInfo(aed)

  const dotClass =
    info.status === 'accessible'
      ? 'bg-emerald-600'
      : info.status === 'closed'
        ? 'bg-red-600'
        : 'bg-amber-600'

  return (
    <span
      className={`inline-flex flex-col items-start gap-0.5 ${compact ? '' : 'mt-1'}`}
    >
      <span
        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${accessibilityStatusClasses[info.status]}`}
      >
        <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${dotClass}`} aria-hidden />
        {t(info.labelKey)}
      </span>
      {info.showArrivalWarning && !compact && (
        <span className="text-xs text-amber-800">{t('aed.mayCloseBeforeArrival')}</span>
      )}
    </span>
  )
}
