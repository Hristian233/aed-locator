import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AEDCard } from '../components/AEDCard'
import { MapView } from '../components/MapView'
import { CardSkeleton, MapSkeleton } from '../components/Skeleton'
import { api } from '../lib/api'
import { withDistancesFromUser } from '../lib/geo'
import type { AED } from '../types'

export function HomePage() {
  const { t } = useTranslation()
  const [aeds, setAeds] = useState<AED[]>([])
  const [nearest, setNearest] = useState<AED[]>([])
  const [selected, setSelected] = useState<AED | null>(null)
  const [userPosition, setUserPosition] = useState<[number, number] | null>(null)
  const [loading, setLoading] = useState(true)
  const [locationLoading, setLocationLoading] = useState(false)
  const [geoError, setGeoError] = useState<string | null>(null)
  const [panToSelection, setPanToSelection] = useState(false)

  const loadNearest = useCallback(async (lat: number, lon: number) => {
    const results = await api.nearestAeds(lat, lon)
    setNearest(results)
    if (results[0]) setSelected(results[0])
  }, [])

  const handleSelectAed = useCallback((aed: AED) => {
    setSelected(aed)
    setPanToSelection(true)
  }, [])

  useEffect(() => {
    let cancelled = false
    async function init() {
      try {
        const list = await api.listAeds()
        if (!cancelled) setAeds(list.items)

        if ('geolocation' in navigator) {
          if (!cancelled) setLocationLoading(true)
          navigator.geolocation.getCurrentPosition(
            async (pos) => {
              const lat = pos.coords.latitude
              const lon = pos.coords.longitude
              if (!cancelled) {
                setPanToSelection(false)
                setUserPosition([lat, lon])
                await loadNearest(lat, lon)
                setLocationLoading(false)
              }
            },
            () => {
              if (!cancelled) {
                setGeoError(t('home.geoError'))
                setLocationLoading(false)
              }
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
  }, [loadNearest, t])

  const displayList = useMemo(() => {
    if (userPosition) {
      const [lat, lon] = userPosition
      if (nearest.length > 0) {
        return withDistancesFromUser(nearest, lat, lon)
      }
      if (aeds.length > 0) {
        return withDistancesFromUser(aeds, lat, lon)
      }
    }
    return nearest.length > 0 ? nearest : aeds
  }, [userPosition, nearest, aeds])

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden md:flex-row">
      <section className="relative min-h-0 flex-1">
        {loading ? (
          <MapSkeleton />
        ) : (
          <MapView
            aeds={displayList}
            userPosition={userPosition}
            locationLoading={locationLoading}
            selected={selected}
            panToSelection={panToSelection}
            onSelect={handleSelectAed}
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
          {t('home.findNearest')}
        </button>
      </section>

      <aside className="flex min-h-0 w-full flex-col overflow-hidden border-t border-slate-200 bg-slate-50 md:w-96 md:shrink-0 md:border-t-0 md:border-l">
        <div className="shrink-0 border-b border-slate-200 bg-white px-4 py-3">
          <h1 className="text-lg font-bold text-slate-900">{t('home.title')}</h1>
          <p className="text-sm text-slate-500">{geoError ?? t('home.hint')}</p>
        </div>
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-4">
          {loading ? (
            <>
              <CardSkeleton />
              <CardSkeleton />
            </>
          ) : displayList.length === 0 ? (
            <p className="text-sm text-slate-600">{t('home.empty')}</p>
          ) : (
            displayList.map((aed) => (
              <AEDCard
                key={aed.id}
                aed={aed}
                selected={selected?.id === aed.id}
                onSelect={handleSelectAed}
              />
            ))
          )}
        </div>
      </aside>
    </div>
  )
}
