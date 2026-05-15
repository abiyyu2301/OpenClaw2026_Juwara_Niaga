import { useEffect, useRef, useState } from "react";
import { useI18n } from "../lib/i18n";

declare global {
  interface Window {
    google?: any;
    initNiagaMaps?: () => void;
  }
}

interface GeoPickerProps {
  mapsKey: string | null;
  placeName: string;
  radiusKm: number;
  manualGeography: string;
  onPlace: (p: { placeName: string; lat: number; lng: number }) => void;
  onRadius: (km: number) => void;
  onManual: (text: string) => void;
}

function loadMapsScript(key: string, failMsg: string): Promise<void> {
  if (window.google?.maps?.places) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const id = "niaga-maps-script";
    if (document.getElementById(id)) {
      const t = setInterval(() => {
        if (window.google?.maps?.places) {
          clearInterval(t);
          resolve();
        }
      }, 100);
      return;
    }
    window.initNiagaMaps = () => resolve();
    const s = document.createElement("script");
    s.id = id;
    s.async = true;
    s.src = `https://maps.googleapis.com/maps/api/js?key=${key}&libraries=places&callback=initNiagaMaps`;
    s.onerror = () => reject(new Error(failMsg));
    document.head.appendChild(s);
  });
}

export function GeoPicker({
  mapsKey,
  placeName,
  radiusKm,
  manualGeography,
  onPlace,
  onRadius,
  onManual,
}: GeoPickerProps) {
  const { t } = useI18n();
  const inputRef = useRef<HTMLInputElement>(null);
  const [mapsReady, setMapsReady] = useState(false);
  const [loadErr, setLoadErr] = useState<string | null>(null);

  useEffect(() => {
    if (!mapsKey) return;
    loadMapsScript(mapsKey, t("geo_maps_fail"))
      .then(() => setMapsReady(true))
      .catch((e) => setLoadErr(String(e)));
  }, [mapsKey, t]);

  useEffect(() => {
    if (!mapsReady || !inputRef.current || !window.google) return;
    const ac = new window.google.maps.places.Autocomplete(inputRef.current, {
      componentRestrictions: { country: "id" },
      fields: ["name", "geometry", "formatted_address"],
    });
    ac.addListener("place_changed", () => {
      const place = ac.getPlace();
      const loc = place.geometry?.location;
      if (!loc) return;
      const name = place.formatted_address || place.name || "";
      onPlace({ placeName: name, lat: loc.lat(), lng: loc.lng() });
    });
  }, [mapsReady, onPlace]);

  return (
    <div className="space-y-3">
      {mapsKey ? (
        <>
          <label className="block text-sm font-medium text-sandstone-800">
            {t("geo_maps_title")}
          </label>
          <p className="text-xs text-sandstone-500 mb-1">{t("geo_maps_hint")}</p>
          {loadErr && <p className="text-xs text-amber-700">{loadErr}</p>}
          <input
            ref={inputRef}
            className="input"
            placeholder={t("ph_geo_search")}
            defaultValue={placeName}
          />
          <div className="flex items-center gap-3">
            <span className="text-sm text-sandstone-700 shrink-0">{t("geo_radius")}</span>
            <input
              type="range"
              min={5}
              max={200}
              step={5}
              value={radiusKm}
              onChange={(e) => onRadius(Number(e.target.value))}
              className="flex-1"
            />
            <span className="text-sm font-mono-feed text-sandstone-800 w-16 text-right">
              {radiusKm} km
            </span>
          </div>
        </>
      ) : (
        <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded p-2">
          {t("geo_maps_missing")}
        </p>
      )}
      <label className="block">
        <span className="block text-sm font-medium text-sandstone-800 mb-0.5">
          {t("geo_manual")}
        </span>
        <input
          className="input"
          placeholder={t("ph_geo_manual")}
          value={manualGeography}
          onChange={(e) => onManual(e.target.value)}
        />
      </label>
    </div>
  );
}
