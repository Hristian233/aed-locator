import L from 'leaflet'
import { useEffect, useMemo } from 'react'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import type { AED } from '../types'

import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

const defaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})
L.Marker.prototype.options.icon = defaultIcon

const aedIcon = L.divIcon({
  className: '',
  html: `<div style="background:#0d9488;width:28px;height:28px;border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,.3);display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:12px;">+</div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14],
})

function MapController({
  center,
  selectedId,
}: {
  center: [number, number]
  selectedId?: number
}) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, map.getZoom())
  }, [center, map])
  useEffect(() => {
    if (selectedId) map.panTo(center)
  }, [selectedId, center, map])
  return null
}

interface MapViewProps {
  aeds: AED[]
  userPosition: [number, number] | null
  selected?: AED | null
  onSelect?: (aed: AED) => void
  className?: string
}

export function MapView({ aeds, userPosition, selected, onSelect, className }: MapViewProps) {
  const center = useMemo<[number, number]>(() => {
    if (selected) return [selected.latitude, selected.longitude]
    if (userPosition) return userPosition
    if (aeds[0]) return [aeds[0].latitude, aeds[0].longitude]
    return [-33.8688, 151.2093]
  }, [selected, userPosition, aeds])

  return (
    <MapContainer
      center={center}
      zoom={14}
      className={className ?? 'h-full w-full'}
      scrollWheelZoom
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <MapController center={center} selectedId={selected?.id} />
      {userPosition && (
        <Marker position={userPosition}>
          <Popup>You are here</Popup>
        </Marker>
      )}
      {aeds.map((aed) => (
        <Marker
          key={aed.id}
          position={[aed.latitude, aed.longitude]}
          icon={aedIcon}
          eventHandlers={{ click: () => onSelect?.(aed) }}
        >
          <Popup>
            <strong>{aed.address ?? `AED #${aed.id}`}</strong>
            {aed.distance_meters != null && (
              <p>{Math.round(aed.distance_meters)} m away</p>
            )}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  )
}
