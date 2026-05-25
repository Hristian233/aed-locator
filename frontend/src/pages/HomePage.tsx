import { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AEDCard } from '../components/AEDCard'
import { ConnectionErrorView } from '../components/ConnectionErrorView'
import { MapView } from '../components/MapView'
import { NearestAedPanel } from '../components/NearestAedPanel'
import { CardSkeleton, MapSkeleton } from '../components/Skeleton'
import { api, isServerConnectionError } from '../lib/api'
import { filterReachableAeds } from '../lib/reachability'
import {
  getGeolocationPermissionState,
  requestUserLocation,
  withDistancesFromUser,
  type GeolocationFailureReason,
} from '../lib/geo'
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
  const [showNearestPanel, setShowNearestPanel] = useState(false)
  const [findingNearest, setFindingNearest] = useState(false)

  const loadNearest = useCallback(async (lat: number, lon: number) => {
    try {
      const results = await api.nearestAeds(lat, lon)
      const withDistance = withDistancesFromUser(results, lat, lon)
      const reachable = filterReachableAeds(withDistance)
      setNearest(reachable)
      setNearestError(null)
      return reachable
    } catch (err) {
      if (isServerConnectionError(err)) {
        throw err
      }
      console.error(err)
      setNearestError(t('errors.nearestFailed'))
    }
  }, [t])

  const geoErrorMessage = useCallback(
    (reason: GeolocationFailureReason) => {
      switch (reason) {
        case 'denied':
          return t('home.geoDenied')
        case 'timeout':
          return t('home.geoTimeout')
        default:
          return t('home.geoError')
      }
    },
    [t],
  )

  const applyUserLocation = useCallback(
    async (lat: number, lon: number) => {
      setPanToSelection(false)
      setUserPosition([lat, lon])
      setGeoError(null)
      try {
        await loadNearest(lat, lon)
      } catch (err) {
        if (isServerConnectionError(err)) {
          setServerUnavailable(true)
        }
      }
    },
    [loadNearest],
  )

  const refreshLocation = useCallback(async () => {
    setLocationLoading(true)
    setGeoError(null)
    try {
      const coords = await requestUserLocation()
      await applyUserLocation(coords.latitude, coords.longitude)
    } catch (reason) {
      setGeoError(geoErrorMessage(reason as GeolocationFailureReason))
    } finally {
      setLocationLoading(false)
    }
  }, [applyUserLocation, geoErrorMessage])

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
      const permission = await getGeolocationPermissionState()
      if (permission === 'granted') {
        setLocationLoading(true)
        try {
          const coords = await requestUserLocation()
          await applyUserLocation(coords.latitude, coords.longitude)
        } catch (reason) {
          setGeoError(geoErrorMessage(reason as GeolocationFailureReason))
        } finally {
          setLocationLoading(false)
        }
      }
    } catch (err) {
      console.error(err)
      if (isServerConnectionError(err)) {
        setServerUnavailable(true)
      }
    } finally {
      setLoading(false)
    }
  }, [loadAeds, applyUserLocation, geoErrorMessage])

  useEffect(() => {
    init()
  }, [init])

  const handleSelectAed = useCallback((aed: AED) => {
    setSelected(aed)
    setPanToSelection(true)
    setShowNearestPanel(false)
  }, [])

  const handleFindNearest = useCallback(async () => {
    if (!userPosition) return
    setFindingNearest(true)
    setShowNearestPanel(false)
    setNearestError(null)
    try {
      const results = await api.nearestAeds(userPosition[0], userPosition[1], {
        limit: 1,
        reachableOnly: false,
      })
      if (results.length > 0) {
        const [closest] = withDistancesFromUser(results, userPosition[0], userPosition[1])
        setSelected(closest)
        setPanToSelection(true)
        setShowNearestPanel(true)
      } else {
        setSelected(null)
        setNearestError(t('home.noNearestFound'))
      }
    } catch (err) {
      if (isServerConnectionError(err)) {
        setServerUnavailable(true)
      } else {
        console.error(err)
        setNearestError(t('errors.nearestFailed'))
      }
    } finally {
      setFindingNearest(false)
    }
  }, [userPosition, t])

  const displayList = useMemo(() => {
    const source = nearest.length > 0 ? nearest : aeds
    const withDistance = userPosition
      ? withDistancesFromUser(source, userPosition[0], userPosition[1])
      : source
    return filterReachableAeds(withDistance)
  }, [userPosition, nearest, aeds])

  const mapAeds = useMemo(() => {
    if (!selected || displayList.some((aed) => aed.id === selected.id)) {
      return displayList
    }
    return userPosition
      ? withDistancesFromUser([selected, ...displayList], userPosition[0], userPosition[1])
      : [selected, ...displayList]
  }, [displayList, selected, userPosition])

  const selectedVisible = selected

  const sidebarHint = serverUnavailable
    ? null
    : nearestError ?? geoError ?? (userPosition ? t('home.hint') : t('home.noLocationHint'))

  if (!loading && serverUnavailable) {
    return <ConnectionErrorView onRetry={init} />
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden md:flex-row">
      <section className="relative min-h-0 w-full flex-[1_1_50%] md:flex-1">
        {loading ? (
          <MapSkeleton />
        ) : (
          <MapView
            aeds={mapAeds}
            userPosition={userPosition}
            locationLoading={locationLoading}
            selected={selectedVisible}
            panToSelection={panToSelection}
            suppressInfoWindow={showNearestPanel}
            onSelect={handleSelectAed}
            className="h-full w-full"
          />
        )}
        {!loading && showNearestPanel && selectedVisible && (
          <div className="absolute bottom-20 left-3 right-3 z-[1000] max-h-[45%] overflow-y-auto md:bottom-32 md:left-auto md:right-4 md:max-h-none md:w-auto">
            <NearestAedPanel
              aed={selectedVisible}
              onClose={() => setShowNearestPanel(false)}
            />
          </div>
        )}
        {!loading && (
          <div className="absolute bottom-2 right-2 z-[1000] flex max-w-[calc(100%-1rem)] flex-col items-stretch gap-1.5 sm:bottom-4 sm:right-4 sm:gap-2">
            <button
              type="button"
              aria-label={userPosition ? t('home.myLocationAria') : t('home.shareLocationAria')}
              disabled={locationLoading}
              onClick={refreshLocation}
              className="w-full rounded-full bg-white px-4 py-2.5 text-center text-sm font-semibold text-slate-800 shadow-lg ring-1 ring-slate-200 hover:bg-slate-50 disabled:opacity-60"
            >
              {userPosition ? t('home.updateLocation') : t('home.shareLocation')}
            </button>
            <button
              type="button"
              className="w-full rounded-full bg-teal-600 px-4 py-2.5 text-center text-sm font-semibold text-white shadow-lg hover:bg-teal-700 disabled:opacity-60"
              disabled={!userPosition || locationLoading || findingNearest}
              onClick={handleFindNearest}
            >
              {findingNearest ? t('common.loading') : t('home.findNearest')}
            </button>
          </div>
        )}
      </section>

      <aside className="flex min-h-0 w-full flex-[1_1_50%] flex-col overflow-hidden border-t border-slate-200 bg-slate-50 md:w-96 md:max-w-96 md:flex-none md:shrink-0 md:grow-0 md:border-t-0 md:border-l">
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
