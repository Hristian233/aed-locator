import { useCallback, useEffect, useState } from 'react'
import { AEDCard } from '../components/AEDCard'
import { MapView } from '../components/MapView'
import { CardSkeleton, MapSkeleton } from '../components/Skeleton'
import { api } from '../lib/api'
import type { AED } from '../types'

export function HomePage() {
  const [aeds, setAeds] = useState<AED[]>([])
  const [nearest, setNearest] = useState<AED[]>([])
  const [selected, setSelected] = useState<AED | null>(null)
  const [userPosition, setUserPosition] = useState<[number, number] | null>(null)
  const [loading, setLoading] = useState(true)
  const [geoError, setGeoError] = useState<string | null>(null)

  const loadNearest = useCallback(async (lat: number, lon: number) => {
    const results = await api.nearestAeds(lat, lon)
    setNearest(results)
    if (results[0]) setSelected(results[0])
  }, [])

  useEffect(() => {
    let cancelled = false
    async function init() {
      try {
        const list = await api.listAeds()
        if (!cancelled) setAeds(list.items)

        if ('geolocation' in navigator) {
          navigator.geolocation.getCurrentPosition(
            async (pos) => {
              const lat = pos.coords.latitude
              const lon = pos.coords.longitude
              if (!cancelled) {
                setUserPosition([lat, lon])
                await loadNearest(lat, lon)
              }
            },
            () => {
              if (!cancelled) setGeoError('Location unavailable — showing all verified AEDs.')
            },
            { enableHighAccuracy: true, timeout: 10000 },
          )
        }
      } catch (err) {
        console.error(err)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    init()
    return () => {
      cancelled = true
    }
  }, [loadNearest])

  const displayList = nearest.length > 0 ? nearest : aeds

  return (
    <div className="flex flex-1 flex-col md:flex-row">
      <section className="relative h-[45vh] md:h-auto md:min-h-[calc(100vh-57px)] md:flex-1">
        {loading ? (
          <MapSkeleton />
        ) : (
          <MapView
            aeds={displayList}
            userPosition={userPosition}
            selected={selected}
            onSelect={setSelected}
            className="h-full w-full"
          />
        )}
        <button
          type="button"
          className="absolute bottom-4 right-4 z-[1000] rounded-full bg-white px-4 py-2 text-sm font-semibold shadow-lg ring-1 ring-slate-200 md:hidden"
          onClick={() => {
            if (userPosition) loadNearest(userPosition[0], userPosition[1])
          }}
        >
          Find nearest
        </button>
      </section>

      <aside className="flex w-full flex-col border-t border-slate-200 bg-slate-50 md:w-96 md:border-t-0 md:border-l">
        <div className="border-b border-slate-200 bg-white px-4 py-3">
          <h1 className="text-lg font-bold text-slate-900">Nearest AEDs</h1>
          <p className="text-sm text-slate-500">
            {geoError ?? 'Tap a marker or card for details and navigation.'}
          </p>
        </div>
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {loading ? (
            <>
              <CardSkeleton />
              <CardSkeleton />
            </>
          ) : displayList.length === 0 ? (
            <p className="text-sm text-slate-600">No verified AEDs in this area yet.</p>
          ) : (
            displayList.map((aed) => (
              <AEDCard
                key={aed.id}
                aed={aed}
                selected={selected?.id === aed.id}
                onSelect={setSelected}
              />
            ))
          )}
        </div>
      </aside>
    </div>
  )
}
