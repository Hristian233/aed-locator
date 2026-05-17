import { InfoWindow, Map, Marker, useMap } from '@vis.gl/react-google-maps'
import { useEffect, useMemo } from 'react'
import type { AED } from '../types'
import { hasGoogleMapsApiKey } from '../lib/google-maps'

const DEFAULT_CENTER = { lat: -33.8688, lng: 151.2093 }

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
        <Marker position={{ lat: userPosition[0], lng: userPosition[1] }} title="You are here" />
      )}
      {aeds.map((aed) => (
        <Marker
          key={aed.id}
          position={{ lat: aed.latitude, lng: aed.longitude }}
          icon={aedMarkerIcon}
          title={aed.address ?? `AED #${aed.id}`}
          onClick={() => onSelect?.(aed)}
        />
      ))}
      {selected && (
        <InfoWindow position={{ lat: selected.latitude, lng: selected.longitude }}>
          <div className="text-sm text-slate-900">
            <strong>{selected.address ?? `AED #${selected.id}`}</strong>
            {selected.distance_meters != null && (
              <p className="mt-1 text-slate-600">{Math.round(selected.distance_meters)} m away</p>
            )}
          </div>
        </InfoWindow>
      )}
    </Map>
  )
}

export function MapView(props: MapViewProps) {
  if (!hasGoogleMapsApiKey()) {
    return (
      <div
        className={`flex items-center justify-center bg-slate-100 p-6 text-center text-sm text-slate-600 ${props.className ?? 'h-full w-full'}`}
      >
        <p>
          Set <code className="rounded bg-slate-200 px-1">VITE_GOOGLE_MAPS_API_KEY</code> in{' '}
          <code className="rounded bg-slate-200 px-1">frontend/.env</code> to load Google Maps.
        </p>
      </div>
    )
  }

  return <GoogleMapView {...props} />
}
