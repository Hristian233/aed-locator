import type { ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { AccessibilityBadge } from './AccessibilityBadge'
import type { AED } from '../types'

type AedReadOnlySummaryProps = {
  aed: AED
}

function SummaryRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <dt className="text-xs font-medium text-slate-500">{label}</dt>
      <dd className="mt-0.5 text-sm text-slate-900">{value}</dd>
    </div>
  )
}

export function AedReadOnlySummary({ aed }: AedReadOnlySummaryProps) {
  const { t } = useTranslation()
  const empty = t('report.selectedAedNoValue')
  const imageUrls = aed.image_urls?.length
    ? aed.image_urls
    : aed.image_url
      ? [aed.image_url]
      : []

  const formatText = (value: string | null | undefined) =>
    value?.trim() ? value.trim() : empty

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      <dl className="space-y-3">
        <SummaryRow label={t('report.selectedAedId')} value={`#${aed.id}`} />
        <SummaryRow
          label={t('report.selectedAedLocationName')}
          value={formatText(aed.location_name)}
        />
        <SummaryRow label={t('report.selectedAedAddress')} value={formatText(aed.address)} />
        <SummaryRow
          label={t('report.selectedAedCoordinates')}
          value={`${aed.latitude.toFixed(5)}, ${aed.longitude.toFixed(5)}`}
        />
        <SummaryRow
          label={t('report.selectedAedDescription')}
          value={formatText(aed.description)}
        />
        <div>
          <dt className="text-xs font-medium text-slate-500">
            {t('report.selectedAedAccessibility')}
          </dt>
          <dd className="mt-0.5">
            <AccessibilityBadge aed={aed} compact />
          </dd>
        </div>
        <SummaryRow
          label={t('report.selectedAedOpeningHours')}
          value={formatText(aed.opening_hours)}
        />
        <SummaryRow
          label={t('report.selectedAedRestrictedAccess')}
          value={
            aed.is_restricted_access
              ? t('report.accessTypes.restricted')
              : t('report.accessTypes.free')
          }
        />
        {imageUrls.length > 0 && (
          <div>
            <dt className="text-xs font-medium text-slate-500">{t('report.selectedAedPhotos')}</dt>
            <dd className="mt-2 flex flex-wrap gap-2">
              {imageUrls.map((url) => (
                <img
                  key={url}
                  src={url}
                  alt={t('report.selectedAedPhoto')}
                  className="max-h-32 rounded-lg object-cover"
                />
              ))}
            </dd>
          </div>
        )}
      </dl>
    </div>
  )
}
