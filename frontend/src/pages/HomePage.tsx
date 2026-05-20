import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AEDCard } from '../components/AEDCard'
import { ConnectionErrorView } from '../components/ConnectionErrorView'
import { MapView } from '../components/MapView'
import { CardSkeleton, MapSkeleton } from '../components/Skeleton'
import { api, isServerConnectionError } from '../lib/api'
import { filterReachableAeds } from '../lib/reachability'
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
  const [serverUnavailable, setServerUnavailable] = useState(false)
  const [nearestError, setNearestError] = useState<string | null>(null)
  const [panToSelection, setPanToSelection] = useState(false)

  const loadNearest = useCallback(async (lat: number, lon: number) => {
    try {
      const results = await api.nearestAeds(lat, lon)
      const withDistance = withDistancesFromUser(results, lat, lon)
      const reachable = filterReachableAeds(withDistance)
      setNearest(reachable)
      setSelected(reachable[0] ?? null)
      setNearestError(null)
    } catch (err) {
      if (isServerConnectionError(err)) {
        throw err
      }
      console.error(err)
      setNearestError(t('errors.nearestFailed'))
    }
  }, [t])

  const refreshLocation = useCallback(() => {
    if (!('geolocation' in navigator)) {
      setGeoError(t('home.geoError'))
      return
    }
    setLocationLoading(true)
    setGeoError(null)
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude
        const lon = pos.coords.longitude
        setPanToSelection(false)
        setUserPosition([lat, lon])
        try {
          await loadNearest(lat, lon)
        } catch (err) {
          if (isServerConnectionError(err)) {
            setServerUnavailable(true)
          }
        } finally {
          setLocationLoading(false)
        }
      },
      () => {
        setGeoError(t('home.geoError'))
        setLocationLoading(false)
      },
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }, [loadNearest, t])

  const loadAeds = useCallback(async () => {
    const list = await api.listAeds()
    setAeds(list.items)
    setServerUnavailable(false)
  }, [])

  const init = useCallback(async () => {
    setLoading(true)
    setServerUnavailable(false)
    setNearestError(null)
    try {
      await loadAeds()
      if ('geolocation' in navigator) {
        setLocationLoading(true)
        navigator.geolocation.getCurrentPosition(
          async (pos) => {
            const lat = pos.coords.latitude
            const lon = pos.coords.longitude
            setPanToSelection(false)
            setUserPosition([lat, lon])
            try {
              await loadNearest(lat, lon)
            } catch (err) {
              if (isServerConnectionError(err)) {
                setServerUnavailable(true)
              }
            } finally {
              setLocationLoading(false)
            }
          },
          () => {
            setGeoError(t('home.geoError'))
            setLocationLoading(false)
          },
          { enableHighAccuracy: true, timeout: 10000 },
        )
      }
    } catch (err) {
      console.error(err)
      if (isServerConnectionError(err)) {
        setServerUnavailable(true)
      }
    } finally {
      setLoading(false)
    }
  }, [loadAeds, loadNearest, t])

  useEffect(() => {
    init()
  }, [init])

  const handleSelectAed = useCallback((aed: AED) => {
    setSelected(aed)
    setPanToSelection(true)
  }, [])

  const displayList = useMemo(() => {
    const source = nearest.length > 0 ? nearest : aeds
    const withDistance = userPosition
      ? withDistancesFromUser(source, userPosition[0], userPosition[1])
      : source
    return filterReachableAeds(withDistance)
  }, [userPosition, nearest, aeds])

  const selectedVisible = useMemo(
    () => (selected && displayList.some((a) => a.id === selected.id) ? selected : null),
    [selected, displayList],
  )

  const sidebarHint = serverUnavailable ? null : nearestError ?? geoError ?? t('home.hint')

  if (!loading && serverUnavailable) {
    return <ConnectionErrorView onRetry={init} />
  }

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
            selected={selectedVisible}
            panToSelection={panToSelection}
            onSelect={handleSelectAed}
            className="h-full w-full"
          />
        )}
        {!loading && (
          <div className="absolute bottom-4 right-4 z-[1000] flex flex-col items-end gap-2">
            <button
              type="button"
              title={t('home.myLocation')}
              aria-label={t('home.myLocationAria')}
              disabled={locationLoading}
              onClick={refreshLocation}
              className="flex h-11 w-11 items-center justify-center rounded-full bg-white text-teal-700 shadow-lg ring-1 ring-slate-200 hover:bg-slate-50 disabled:opacity-60"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="h-5 w-5"
                aria-hidden
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48 2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48 2.83-2.83"
                />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </button>
            <button
              type="button"
              className="rounded-full bg-white px-4 py-2 text-sm font-semibold shadow-lg ring-1 ring-slate-200 hover:bg-slate-50 disabled:opacity-60"
              disabled={!userPosition || locationLoading}
              onClick={async () => {
                if (!userPosition) return
                try {
                  await loadNearest(userPosition[0], userPosition[1])
                } catch (err) {
                  if (isServerConnectionError(err)) {
                    setServerUnavailable(true)
                  }
                }
              }}
            >
              {t('home.findNearest')}
            </button>
          </div>
        )}
      </section>

      <aside className="flex min-h-0 w-full flex-col overflow-hidden border-t border-slate-200 bg-slate-50 md:w-96 md:shrink-0 md:border-t-0 md:border-l">
        <div className="shrink-0 border-b border-slate-200 bg-white px-4 py-3">
          <h1 className="text-lg font-bold text-slate-900">{t('home.title')}</h1>
          <p className="text-sm text-slate-500">{sidebarHint}</p>
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
                selected={selectedVisible?.id === aed.id}
                onSelect={handleSelectAed}
              />
            ))
          )}
        </div>
      </aside>
    </div>
  )
}
