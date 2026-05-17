const WALKING_SPEED_M_PER_MIN = 80

export const MAX_DISPLAY_WALK_MINUTES = 15

export function shouldShowDistance(meters: number): boolean {
  return estimateWalkMinutes(meters) <= MAX_DISPLAY_WALK_MINUTES
}

export function haversineMeters(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
): number {
  const toRad = (deg: number) => (deg * Math.PI) / 180
  const R = 6371000
  const dLat = toRad(lat2 - lat1)
  const dLon = toRad(lon2 - lon1)
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

export function estimateWalkMinutes(meters: number): number {
  if (meters <= 0) return 0
  return Math.max(1, Math.ceil(meters / WALKING_SPEED_M_PER_MIN))
}

export function withDistancesFromUser(
  aeds: import('../types').AED[],
  userLat: number,
  userLon: number,
): import('../types').AED[] {
  return aeds
    .map((aed) => ({
      ...aed,
      distance_meters:
        aed.distance_meters ??
        haversineMeters(userLat, userLon, aed.latitude, aed.longitude),
    }))
    .sort((a, b) => (a.distance_meters ?? Infinity) - (b.distance_meters ?? Infinity))
}
