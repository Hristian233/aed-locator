import { InfoWindow, Map, Marker, useMap } from '@vis.gl/react-google-maps'
import { useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import type { AED } from '../types'
import { hasGoogleMapsApiKey } from '../lib/google-maps'
import { AccessibilityBadge } from './AccessibilityBadge'

const DEFAULT_CENTER = { lat: 42.6977, lng: 23.3219 }

const aedMarkerIcon: google.maps.Icon = {
  url:
    'data:image/svg+xml;charset=UTF-8,' +
    encodeURIComponent(
      '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28">' +
        '<circle cx="14" cy="14" r="11" fill="#0d9488" stroke="white" stroke-width="3"/>' +
        '<text x="14" y="18" text-anchor="middle" fill="white" font-size="12" font-weight="700">+</text>' +
        '</svg>',
    ),
  scaledSize: { width: 28, height: 28 } as google.maps.Size,
  anchor: { x: 14, y: 14 } as google.maps.Point,
}

function MapController({
  center,
  selectedId,
}: {
  center: google.maps.LatLngLiteral
  selectedId?: number
}) {
  const map = useMap()
  useEffect(() => {
    if (!map) return
    map.panTo(center)
  }, [center, map, selectedId])
  return null
}

interface MapViewProps {
  aeds: AED[]
  userPosition: [number, number] | null
  selected?: AED | null
  onSelect?: (aed: AED) => void
  className?: string
}

function GoogleMapView({ aeds, userPosition, selected, onSelect, className }: MapViewProps) {
  const { t } = useTranslation()

  const center = useMemo<google.maps.LatLngLiteral>(() => {
    if (selected) return { lat: selected.latitude, lng: selected.longitude }
    if (userPosition) return { lat: userPosition[0], lng: userPosition[1] }
    if (aeds[0]) return { lat: aeds[0].latitude, lng: aeds[0].longitude }
    return DEFAULT_CENTER
  }, [selected, userPosition, aeds])

  const mapId = import.meta.env.VITE_GOOGLE_MAPS_MAP_ID

  return (
    <Map
      className={className ?? 'h-full w-full'}
      defaultCenter={DEFAULT_CENTER}
      defaultZoom={14}
      center={center}
      zoom={14}
      gestureHandling="greedy"
      mapId={mapId || undefined}
      fullscreenControl={false}
      mapTypeControl={false}
      streetViewControl={false}
    >
      <MapController center={center} selectedId={selected?.id} />
      {userPosition && (
        <Marker
          position={{ lat: userPosition[0], lng: userPosition[1] }}
          title={t('home.youAreHere')}
        />
      )}
      {aeds.map((aed) => (
        <Marker
          key={aed.id}
          position={{ lat: aed.latitude, lng: aed.longitude }}
          icon={aedMarkerIcon}
          title={aed.address ?? t('aed.fallbackName', { id: aed.id })}
          onClick={() => onSelect?.(aed)}
        />
      ))}
      {selected && (
        <InfoWindow position={{ lat: selected.latitude, lng: selected.longitude }}>
          <div className="max-w-[200px] text-sm text-slate-900">
            <strong>{selected.address ?? t('aed.fallbackName', { id: selected.id })}</strong>
            {selected.distance_meters != null && (
              <p className="mt-1 font-medium text-teal-700">
                {selected.distance_meters < 1000
                  ? t('aed.distanceMeters', { distance: Math.round(selected.distance_meters) })
                  : t('aed.distanceKm', {
                      distance: (selected.distance_meters / 1000).toFixed(1),
                    })}
              </p>
            )}
            <div className="mt-1">
              <AccessibilityBadge aed={selected} compact />
            </div>
          </div>
        </InfoWindow>
      )}
    </Map>
  )
}

export function MapView(props: MapViewProps) {
  const { t } = useTranslation()

  if (!hasGoogleMapsApiKey()) {
    return (
      <div
        className={`flex items-center justify-center bg-slate-100 p-6 text-center text-sm text-slate-600 ${props.className ?? 'h-full w-full'}`}
      >
        <p>{t('maps.missingKey')}</p>
      </div>
    )
  }

  return <GoogleMapView {...props} />
}
