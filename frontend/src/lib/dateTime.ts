function resolveDateLocale(language: string): string {
  if (language.startsWith('bg')) return 'bg-BG'
  return 'en-GB'
}

/** Format as `dd - month name - yyyy HH:mm:ss` (24-hour clock). */
export function formatEuropeanDateTime(
  value: string | Date,
  language = 'en',
): string {
  const date = typeof value === 'string' ? new Date(value) : value
  const parts = new Intl.DateTimeFormat(resolveDateLocale(language), {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(date)

  const get = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((part) => part.type === type)?.value ?? ''

  return `${get('day')} ${get('month')} ${get('year')} ${get('hour')}:${get('minute')}:${get('second')}`
}
