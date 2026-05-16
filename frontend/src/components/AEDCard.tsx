import type { AED } from '../types'
import { navigationUrl } from '../lib/api'

interface AEDCardProps {
  aed: AED
  selected?: boolean
  onSelect?: (aed: AED) => void
}

function formatDistance(meters?: number | null) {
  if (meters == null) return null
  if (meters < 1000) return `${Math.round(meters)} m away`
  return `${(meters / 1000).toFixed(1)} km away`
}

export function AEDCard({ aed, selected, onSelect }: AEDCardProps) {
  const distance = formatDistance(aed.distance_meters)

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
        <div>
          <h3 className="font-semibold text-slate-900">
            {aed.address ?? `AED #${aed.id}`}
          </h3>
          {distance && <p className="text-sm font-medium text-teal-700">{distance}</p>}
        </div>
        <span
          className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
            aed.verification_status === 'verified'
              ? 'bg-emerald-100 text-emerald-800'
              : 'bg-amber-100 text-amber-800'
          }`}
        >
          {aed.verification_status}
        </span>
      </div>
      {aed.description && (
        <p className="mt-2 line-clamp-2 text-sm text-slate-600">{aed.description}</p>
      )}
      <div className="mt-3 flex gap-2">
        <a
          href={navigationUrl(aed.latitude, aed.longitude, aed.address ?? undefined)}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="flex-1 rounded-xl bg-teal-600 py-2.5 text-center text-sm font-semibold text-white hover:bg-teal-700"
        >
          Navigate
        </a>
      </div>
    </article>
  )
}
