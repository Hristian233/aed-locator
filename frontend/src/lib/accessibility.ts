import type { AED } from '../types'
import {
  getReachabilityStatus,
  isOpenNow,
  type ReachabilityStatus,
} from './reachability'

export type AccessibilityVisualStatus = 'accessible' | 'closing_soon' | 'closed' | 'limited'

export interface AccessibilityInfo {
  labelKey:
    | 'aed.accessibility.24_7'
    | 'aed.accessibility.openNow'
    | 'aed.accessibility.closingSoon'
    | 'aed.accessibility.closed'
    | 'aed.accessibility.restricted'
  status: AccessibilityVisualStatus
  reachability: ReachabilityStatus
  showArrivalWarning: boolean
}

export function filterAvailableAeds(aeds: AED[]): AED[] {
  return aeds.filter((aed) => getReachabilityStatus(aed) !== 'unreachable')
}

export function getAccessibilityInfo(aed: AED): AccessibilityInfo {
  const type = aed.accessibility_type ?? '24_7'
  const reachability = getReachabilityStatus(aed)

  if (type === '24_7') {
    return {
      labelKey: 'aed.accessibility.24_7',
      status: 'accessible',
      reachability,
      showArrivalWarning: false,
    }
  }

  if (type === 'restricted_access') {
    return {
      labelKey: 'aed.accessibility.restricted',
      status: 'limited',
      reachability,
      showArrivalWarning: false,
    }
  }

  if (!isOpenNow(aed.opening_hours)) {
    return {
      labelKey: 'aed.accessibility.closed',
      status: 'closed',
      reachability: 'unreachable',
      showArrivalWarning: false,
    }
  }

  if (reachability === 'closing_soon') {
    return {
      labelKey: 'aed.accessibility.closingSoon',
      status: 'closing_soon',
      reachability,
      showArrivalWarning: true,
    }
  }

  return {
    labelKey: 'aed.accessibility.openNow',
    status: 'accessible',
    reachability,
    showArrivalWarning: false,
  }
}

export const accessibilityStatusClasses: Record<AccessibilityVisualStatus, string> = {
  accessible: 'bg-emerald-100 text-emerald-800',
  closing_soon: 'bg-amber-100 text-amber-900',
  closed: 'bg-red-100 text-red-800',
  limited: 'bg-amber-100 text-amber-900',
}
