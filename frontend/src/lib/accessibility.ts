import type { AED } from '../types'

export type AccessibilityVisualStatus = 'accessible' | 'closed' | 'limited'

export interface AccessibilityInfo {
  labelKey: 'aed.accessibility.24_7' | 'aed.accessibility.openNow' | 'aed.accessibility.closed' | 'aed.accessibility.restricted'
  status: AccessibilityVisualStatus
}

const DAY_KEYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'] as const

type DayHours = { open: string; close: string } | null

function parseTime(value: string): number {
  const [h, m] = value.split(':').map(Number)
  return h * 60 + (m || 0)
}

function hoursForToday(openingHours: string | null | undefined): DayHours {
  if (!openingHours) return null
  try {
    const data = JSON.parse(openingHours) as Record<string, unknown>
    const dayKey = DAY_KEYS[new Date().getDay()]
    const longNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    const raw =
      data[dayKey] ??
      data[longNames[new Date().getDay()]] ??
      data[dayKey.toUpperCase()]
    if (!raw) return null
    if (typeof raw === 'object' && raw !== null && 'open' in raw && 'close' in raw) {
      const period = raw as { open: string; close: string }
      return { open: period.open, close: period.close }
    }
    return null
  } catch {
    return null
  }
}

function isWithinHours(period: DayHours, now = new Date()): boolean {
  if (!period) return false
  const minutes = now.getHours() * 60 + now.getMinutes()
  const open = parseTime(period.open)
  const close = parseTime(period.close)
  if (close > open) return minutes >= open && minutes < close
  return minutes >= open || minutes < close
}

export function getAccessibilityInfo(aed: AED): AccessibilityInfo {
  const type = aed.accessibility_type ?? '24_7'

  if (type === '24_7') {
    return { labelKey: 'aed.accessibility.24_7', status: 'accessible' }
  }

  if (type === 'restricted_access') {
    return { labelKey: 'aed.accessibility.restricted', status: 'limited' }
  }

  const today = hoursForToday(aed.opening_hours)
  if (!today) {
    return { labelKey: 'aed.accessibility.closed', status: 'closed' }
  }

  if (isWithinHours(today)) {
    return { labelKey: 'aed.accessibility.openNow', status: 'accessible' }
  }

  return { labelKey: 'aed.accessibility.closed', status: 'closed' }
}

export const accessibilityStatusClasses: Record<AccessibilityVisualStatus, string> = {
  accessible: 'bg-emerald-100 text-emerald-800',
  closed: 'bg-red-100 text-red-800',
  limited: 'bg-amber-100 text-amber-900',
}
