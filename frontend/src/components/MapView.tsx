import { InfoWindow, Map, Marker, useMap } from "@vis.gl/react-google-maps";
import { useEffect, useMemo } from "react";
import { useTranslation } from "react-i18next";
import type { AED } from "../types";
import { hasGoogleMapsApiKey } from "../lib/google-maps";
import { AccessibilityBadge } from "./AccessibilityBadge";

const DEFAULT_CENTER = { lat: 42.6977, lng: 23.3219 };

// ~28px is a common on-map POI icon size (Google examples often use 20–32px).
const AED_MARKER_SIZE = 28;
const AED_MARKER_Z_INDEX = 1;
const USER_MARKER_Z_INDEX = 1000;

const aedMarkerIcon: google.maps.Icon = {
  url: "/aed-marker.png",
  scaledSize: { width: AED_MARKER_SIZE, height: AED_MARKER_SIZE } as google.maps.Size,
  anchor: { x: AED_MARKER_SIZE / 2, y: AED_MARKER_SIZE / 2 } as google.maps.Point,
};

function MapController({
  userPosition,
  selected,
  panToSelection,
}: {
  userPosition: [number, number] | null;
  selected?: AED | null;
  panToSelection: boolean;
}) {
  const map = useMap();

  useEffect(() => {
    if (!map || !userPosition) return;
    map.panTo({ lat: userPosition[0], lng: userPosition[1] });
  }, [map, userPosition]);

  useEffect(() => {
    if (!map || !selected || !panToSelection) return;
    map.panTo({ lat: selected.latitude, lng: selected.longitude });
  }, [
    map,
    selected?.id,
    selected?.latitude,
    selected?.longitude,
    panToSelection,
  ]);

  return null;
}

interface MapViewProps {
  aeds: AED[];
  userPosition: [number, number] | null;
  locationLoading?: boolean;
  selected?: AED | null;
  panToSelection?: boolean;
  suppressInfoWindow?: boolean;
  onSelect?: (aed: AED) => void;
  className?: string;
}

function GoogleMapView({
  aeds,
  userPosition,
  locationLoading,
  selected,
  panToSelection = false,
  suppressInfoWindow = false,
  onSelect,
  className,
}: MapViewProps) {
  const { t } = useTranslation();

  const initialCenter = useMemo<google.maps.LatLngLiteral>(() => {
    if (userPosition) return { lat: userPosition[0], lng: userPosition[1] };
    if (aeds[0]) return { lat: aeds[0].latitude, lng: aeds[0].longitude };
    return DEFAULT_CENTER;
  }, [userPosition, aeds]);

  const mapId = import.meta.env.VITE_GOOGLE_MAPS_MAP_ID;

  return (
    <div className={`relative ${className ?? "h-full w-full"}`}>
      <Map
        className="h-full w-full"
        defaultCenter={initialCenter}
        defaultZoom={14}
        gestureHandling="greedy"
        mapId={mapId || undefined}
        fullscreenControl={false}
        mapTypeControl={false}
        streetViewControl={false}
      >
        <MapController
          userPosition={userPosition}
          selected={selected}
          panToSelection={panToSelection}
        />
        {aeds.map((aed) => (
          <Marker
            key={aed.id}
            position={{ lat: aed.latitude, lng: aed.longitude }}
            icon={aedMarkerIcon}
            zIndex={AED_MARKER_Z_INDEX}
            title={aed.address ?? t("aed.fallbackName", { id: aed.id })}
            onClick={() => onSelect?.(aed)}
          />
        ))}
        {userPosition && (
          <Marker
            position={{ lat: userPosition[0], lng: userPosition[1] }}
            zIndex={USER_MARKER_Z_INDEX}
            title={t("home.youAreHere")}
          />
        )}
        {selected && !suppressInfoWindow && (
          <InfoWindow
            position={{ lat: selected.latitude, lng: selected.longitude }}
          >
            <div className="aed-map-info-window max-w-[200px] text-sm text-slate-900">
              <div className="aed-map-info-window__header">
                <p className="text-xs font-medium tabular-nums text-slate-500">
                  ID:{selected.id}
                </p>
              </div>
              <strong className="mt-1 block">
                {selected.address ?? t("aed.fallbackName", { id: selected.id })}
              </strong>
              {selected.distance_meters != null && (
                <p className="mt-1 font-medium text-teal-700">
                  {selected.distance_meters < 1000
                    ? t("aed.distanceMeters", {
                        distance: Math.round(selected.distance_meters),
                      })
                    : t("aed.distanceKm", {
                        distance: (selected.distance_meters / 1000).toFixed(1),
                      })}
                </p>
              )}
              <div className="mt-1">
                <AccessibilityBadge aed={selected} />
              </div>
            </div>
          </InfoWindow>
        )}
      </Map>
      {locationLoading && (
        <div
          className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-white/70"
          role="status"
          aria-live="polite"
          aria-label={t("home.locating")}
        >
          <div className="h-10 w-10 animate-spin rounded-full border-[3px] border-teal-600 border-t-transparent" />
          <p className="text-sm font-medium text-slate-700">
            {t("home.locating")}
          </p>
        </div>
      )}
    </div>
  );
}

export function MapView(props: MapViewProps) {
  const { t } = useTranslation();

  if (!hasGoogleMapsApiKey()) {
    return (
      <div
        className={`flex items-center justify-center bg-slate-100 p-6 text-center text-sm text-slate-600 ${props.className ?? "h-full w-full"}`}
      >
        <p>{t("maps.missingKey")}</p>
      </div>
    );
  }

  return <GoogleMapView {...props} />;
}
