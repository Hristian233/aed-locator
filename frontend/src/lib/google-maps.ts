export const googleMapsApiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY

export function hasGoogleMapsApiKey(): boolean {
  return Boolean(googleMapsApiKey)
}
