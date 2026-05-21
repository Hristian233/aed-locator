import { useTranslation } from 'react-i18next'
import { AccessibilityBadge } from './AccessibilityBadge'
import { navigationUrl } from '../lib/api'
import { estimateWalkMinutes } from '../lib/geo'
import type { AED } from '../types'

interface NearestAedPanelProps {
  aed: AED
  onClose?: () => void
}

export function NearestAedPanel({ aed, onClose }: NearestAedPanelProps) {
  const { t } = useTranslation()

  const distanceLabel =
    aed.distance_meters == null
      ? null
      : aed.distance_meters < 1000
        ? t('aed.distanceMeters', { distance: Math.round(aed.distance_meters) })
        : t('aed.distanceKm', { distance: (aed.distance_meters / 1000).toFixed(1) })

  const etaMinutes =
    aed.distance_meters != null ? estimateWalkMinutes(aed.distance_meters) : null

  const etaLabel =
    etaMinutes == null
      ? null
      : etaMinutes < 1
        ? t('aed.walkLessThanMinute')
        : t('home.etaMinutes', { minutes: etaMinutes })

  const title = aed.address ?? t('aed.fallbackName', { id: aed.id })

  return (
    <div
      className="w-full max-w-sm rounded-2xl bg-white p-4 shadow-xl ring-1 ring-slate-200"
      role="dialog"
      aria-label={t('home.nearestPanelTitle')}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-base font-semibold text-slate-900">{title}</h3>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="shrink-0 rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label={t('home.closePanel')}
          >
            <span aria-hidden>×</span>
          </button>
        )}
      </div>

      <dl className="mt-3 space-y-2 text-sm">
        {distanceLabel && (
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">{t('home.distanceLabel')}</dt>
            <dd className="font-semibold text-teal-700">{distanceLabel}</dd>
          </div>
        )}
        {etaLabel && (
          <div className="flex justify-between gap-4">
            <dt className="text-slate-500">{t('home.etaLabel')}</dt>
            <dd className="font-medium text-slate-900">{etaLabel}</dd>
          </div>
        )}
        <div className="flex justify-between gap-4">
          <dt className="shrink-0 text-slate-500">{t('home.availabilityLabel')}</dt>
          <dd className="text-right">
            <AccessibilityBadge aed={aed} compact />
          </dd>
        </div>
      </dl>

      <a
        href={navigationUrl(aed.latitude, aed.longitude, aed.address ?? undefined)}
        target="_blank"
        rel="noopener noreferrer"
        className="mt-4 block w-full rounded-xl bg-teal-600 py-3 text-center text-base font-semibold text-white hover:bg-teal-700"
      >
        {t('aed.navigate')}
      </a>
    </div>
  )
}
