import type { AED } from '../types'

type AedLabelFields = Pick<AED, 'id' | 'location_name' | 'address'>

export function formatAedPrimaryName(
  aed: AedLabelFields,
  t: (key: string, options?: Record<string, unknown>) => string,
): string {
  return aed.location_name || aed.address || t('aed.fallbackName', { id: aed.id })
}

export function formatAedOptionLabel(
  aed: AedLabelFields,
  t: (key: string, options?: Record<string, unknown>) => string,
): string {
  return `#${aed.id} — ${formatAedPrimaryName(aed, t)}`
}

export function aedMatchesSearch(
  aed: AED,
  query: string,
  t: (key: string, options?: Record<string, unknown>) => string,
): boolean {
  const normalized = query.trim().toLowerCase()
  if (!normalized) return true

  const haystack = [
    String(aed.id),
    aed.location_name ?? '',
    aed.address ?? '',
    aed.description ?? '',
    formatAedOptionLabel(aed, t),
  ]
    .join(' ')
    .toLowerCase()

  return haystack.includes(normalized)
}
