import type { AED } from '../types'
import { estimateWalkMinutes } from './geo'

/** Extra minutes assumed for locating the AED on site (stairs, security, etc.). */
export const ARRIVAL_BUFFER_MINUTES = 2

export type ReachabilityStatus = 'reachable' | 'closing_soon' | 'unreachable'

const DAY_KEYS = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'] as const
const LONG_DAY_NAMES = [
  'sunday',
  'monday',
  'tuesday',
  'wednesday',
  'thursday',
  'friday',
  'saturday',
] as const

type DayHours = { open: string; close: string }

function parseTime(value: string): number {
  const [h, m] = value.split(':').map(Number)
  return h * 60 + (m || 0)
}

export function hoursForToday(
  openingHours: string | null | undefined,
  now = new Date(),
): DayHours | null {
  if (!openingHours) return null
  try {
    const data = JSON.parse(openingHours) as Record<string, unknown>
    const dayIndex = now.getDay()
    const dayKey = DAY_KEYS[dayIndex]
    const raw =
      data[dayKey] ?? data[LONG_DAY_NAMES[dayIndex]] ?? data[dayKey.toUpperCase()]
    if (!raw || typeof raw !== 'object' || !('open' in raw) || !('close' in raw)) return null
    const period = raw as { open: string; close: string }
    return { open: period.open, close: period.close }
  } catch {
    return null
  }
}

export function isOpenNow(
  openingHours: string | null | undefined,
  now = new Date(),
): boolean {
  const period = hoursForToday(openingHours, now)
  if (!period) return false
  const minutes = now.getHours() * 60 + now.getMinutes()
  const open = parseTime(period.open)
  const close = parseTime(period.close)
  if (close > open) return minutes >= open && minutes < close
  return minutes >= open || minutes < close
}

/** Minutes until today's closing time while the location is currently open. */
export function remainingOpenMinutes(
  openingHours: string | null | undefined,
  now = new Date(),
): number | null {
  const period = hoursForToday(openingHours, now)
  if (!period || !isOpenNow(openingHours, now)) return null
  const minutes = now.getHours() * 60 + now.getMinutes()
  const open = parseTime(period.open)
  const close = parseTime(period.close)
  if (close > open) return close - minutes
  if (minutes >= open) return 24 * 60 - minutes + close
  return close - minutes
}

export function getReachabilityStatus(
  aed: AED,
  options?: { distanceMeters?: number | null; now?: Date },
): ReachabilityStatus {
  const now = options?.now ?? new Date()
  const type = aed.accessibility_type ?? '24_7'

  if (type === '24_7' || type === 'restricted_access') return 'reachable'

  if (!isOpenNow(aed.opening_hours, now)) return 'unreachable'

  const distance = options?.distanceMeters ?? aed.distance_meters
  if (distance == null) return 'reachable'

  const remaining = remainingOpenMinutes(aed.opening_hours, now)
  if (remaining == null) return 'unreachable'

  const eta = estimateWalkMinutes(distance)
  if (eta >= remaining) return 'unreachable'
  if (eta + ARRIVAL_BUFFER_MINUTES >= remaining) return 'closing_soon'
  return 'reachable'
}

export function filterReachableAeds(aeds: AED[]): AED[] {
  return aeds.filter((aed) => getReachabilityStatus(aed) !== 'unreachable')
}
