import { useTranslation } from 'react-i18next'
import type { AED } from '../types'
import { navigationUrl } from '../lib/api'
import { estimateWalkMinutes, shouldShowDistance } from '../lib/geo'
import { AccessibilityBadge } from './AccessibilityBadge'

interface AEDCardProps {
  aed: AED
  selected?: boolean
  onSelect?: (aed: AED) => void
}

export function AEDCard({ aed, selected, onSelect }: AEDCardProps) {
  const { t } = useTranslation()

  const showDistance =
    aed.distance_meters != null && shouldShowDistance(aed.distance_meters)

  const distanceLabel = showDistance
    ? aed.distance_meters! < 1000
      ? t('aed.distanceMeters', { distance: Math.round(aed.distance_meters!) })
      : t('aed.distanceKm', { distance: (aed.distance_meters! / 1000).toFixed(1) })
    : null

  const walkLabel = showDistance
    ? (() => {
        const minutes = estimateWalkMinutes(aed.distance_meters!)
        return minutes < 1 ? t('aed.walkLessThanMinute') : t('aed.walkMinutes', { minutes })
      })()
    : null
  const statusKey = `aed.status.${aed.verification_status}` as const
  const title = aed.address ?? t('aed.fallbackName', { id: aed.id })

  return (
    <article
      role="button"
      tabIndex={0}
      onClick={() => onSelect?.(aed)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') onSelect?.(aed)
      }}
      className={`cursor-pointer rounded-2xl bg-white p-4 shadow-sm ring-1 transition ${
        selected ? 'ring-2 ring-teal-500' : 'ring-slate-200 hover:ring-teal-300'
      }`}
      aria-pressed={selected}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <h3 className="truncate font-semibold text-slate-900">{title}</h3>
          {distanceLabel && (
            <p className="mt-0.5 text-base font-semibold text-teal-700">{distanceLabel}</p>
          )}
          {walkLabel && distanceLabel && (
            <p className="text-xs text-slate-500">{walkLabel}</p>
          )}
          <div className="mt-1.5">
            <AccessibilityBadge aed={aed} compact />
          </div>
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
            aed.verification_status === 'verified'
              ? 'bg-emerald-100 text-emerald-800'
              : 'bg-amber-100 text-amber-800'
          }`}
        >
          {t(statusKey, { defaultValue: aed.verification_status })}
        </span>
      </div>
      {aed.description && (
        <p className="mt-2 line-clamp-2 text-sm text-slate-600">{aed.description}</p>
      )}
      <div className="mt-3">
        <a
          href={navigationUrl(aed.latitude, aed.longitude, aed.address ?? undefined)}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="block w-full rounded-xl bg-teal-600 py-2.5 text-center text-sm font-semibold text-white hover:bg-teal-700"
        >
          {t('aed.navigate')}
        </a>
      </div>
    </article>
  )
}
