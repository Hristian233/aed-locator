import { APIProvider } from '@vis.gl/react-google-maps'
import type { ReactNode } from 'react'
import { googleMapsApiKey } from '../lib/google-maps'

interface GoogleMapsProviderProps {
  children: ReactNode
}

export function GoogleMapsProvider({ children }: GoogleMapsProviderProps) {
  if (!googleMapsApiKey) return children
  return <APIProvider apiKey={googleMapsApiKey}>{children}</APIProvider>
}
