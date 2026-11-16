import { useEffect, useMemo, useState } from "react";
import { Maximize2, Minimize2 } from "lucide-react";
import { MapContainer, TileLayer, Polyline, Marker, Tooltip, ZoomControl, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { PREF_COLOR, useRoutes } from "../hooks";
import { useT } from "../i18n";

const TILES = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const ATTRIB = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
const TRUCK_SVG = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.62l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/></svg>';

// Point a fraction `f` of the way along a polyline, measured by distance.
const along = (pts, f) => {
  const seg = pts.slice(1).map((p, i) => L.latLng(pts[i]).distanceTo(p));
  let d = seg.reduce((a, b) => a + b, 0) * Math.min(Math.max(f, 0), 1);
  for (let i = 0; i < seg.length; i++) {
    if (d <= seg[i]) {
      const k = seg[i] ? d / seg[i] : 0;
      return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k];
    }
    d -= seg[i];
  }
  return pts[pts.length - 1];
};

const pin = (cls, html = "", size = 26) => L.divIcon({ className: "", html: `<div class="mk ${cls}">${html}</div>`, iconSize: [size, size], iconAnchor: [size / 2, size / 2] });

// Keep the visible routes framed, including after the container resizes (e.g. the layout collapsing to one column).
function Frame({ lines }) {
  const map = useMap();
  useEffect(() => {
    const fit = () => { map.invalidateSize(); map.fitBounds(L.latLngBounds(lines.flat()), { padding: [28, 28] }); };
    fit();
    const ro = new ResizeObserver(fit);
    ro.observe(map.getContainer());
    return () => ro.disconnect();
  }, [map, lines]);
  return null;
}

// `big` is the driver's map: taller, larger pins, and it can fill the whole screen. `banner` is overlaid at the top.
// Wheel zoom is only on while the map is full screen, so it never hijacks page scrolling.
function WheelZoom({ on }) {
  const map = useMap();
  useEffect(() => { on ? map.scrollWheelZoom.enable() : map.scrollWheelZoom.disable(); }, [map, on]);
  return null;
}

const COLOR = "#3F51B5";

// Draws one trip from its source to its destination, with the truck `progress` (0–1) of the way along.
// Every candidate road is drawn faintly; the one for `pref` (fastest / balanced / greenest) is drawn on top in its colour.
export default function RouteMap({ trip, truck, pref, progress = 0, big = false, banner }) {
  const t = useT();
  const [full, setFull] = useState(false);
  useEffect(() => {
    if (!full) return;
    const onKey = (e) => e.key === "Escape" && setFull(false);
    document.body.style.overflow = "hidden"; // the page behind must not scroll under the full-screen map
    window.addEventListener("keydown", onKey);
    return () => { document.body.style.overflow = ""; window.removeEventListener("keydown", onKey); };
  }, [full]);
  const k = big ? 1.3 : 1; // pin scale
  const road = useRoutes(trip, truck);
  const roads = road?.roads;
  const lines = useMemo(() => (roads ? roads.map((r) => r.line) : []), [roads]);

  if (!road) return <p className="empty">{t("map.unknown")}</p>;
  const loose = road.via === "straight" || road.via === "loading"; // not following roads
  const shown = road.options?.[pref ?? "fastest"];
  const line = shown?.line ?? lines[0];
  const color = pref ? PREF_COLOR[pref] : COLOR;

  return (
    <div className={`map-wrap ${big ? "big" : ""} ${full ? "full" : ""}`}>
      <MapContainer className="map" center={road.from} zoom={11} scrollWheelZoom={full} zoomSnap={0.25} zoomControl={false}>
        <TileLayer url={TILES} attribution={ATTRIB} maxZoom={19} />
        <ZoomControl key={t.lang} position="bottomright" zoomInTitle={t("map.zoomIn")} zoomOutTitle={t("map.zoomOut")} />
        <WheelZoom on={full} />
        <Frame lines={lines} />

        {lines.filter((l) => l !== line).map((l, i) => (
          <Polyline key={i} positions={l} pathOptions={{ color: "#6E6A80", weight: 4, opacity: 0.45, dashArray: "6 8" }} interactive={false} />
        ))}
        <Polyline positions={line} pathOptions={{ color: "#fff", weight: 10, opacity: 0.9 }} interactive={false} />
        <Polyline key={`${pref}|${line.length}`} positions={line} pathOptions={{ color, weight: 6, dashArray: loose ? "2 10" : null, lineCap: "round" }}>
          <Tooltip sticky>{t.d(trip.route_name)}{shown ? ` · ${t(`pref.${shown.pref}`)} · ${t("km", { n: shown.km })} · ${t("min", { n: shown.min })}` : ""}</Tooltip>
        </Polyline>

        <Marker position={road.from} icon={pin("mk-hub", "H", 28)}><Tooltip>{t("map.hub")} · {t.d(trip.source)}</Tooltip></Marker>
        <Marker position={road.to} icon={pin("mk-drop", "◆", 28)}><Tooltip>{t("map.last")} · {t.d(trip.destination)}</Tooltip></Marker>
        <Marker position={along(line, progress)} zIndexOffset={1000} icon={pin("mk-truck", TRUCK_SVG, 34 * k)} keyboard={false}>
          <Tooltip>{t("map.truck")}</Tooltip>
        </Marker>
      </MapContainer>

      {(banner || big) && (
        <div className="map-top">
          {banner}
          {big && (
            <button type="button" className="map-btn" onClick={() => setFull(!full)} aria-label={t(full ? "map.shrink" : "map.expand")} title={t(full ? "map.shrink" : "map.expand")}>
              {full ? <Minimize2 size={19} /> : <Maximize2 size={19} />}
            </button>
          )}
        </div>
      )}

      <div className="map-legend">
        {shown && !loose && <span><i className="sw" style={{ background: color }} /><b>{t(`pref.${shown.pref}`)}</b> · {t("km", { n: shown.km })} · {t("min", { n: shown.min })}</span>}
        {lines.length > 1 && <span><i className="sw alt" />{t("map.others", { n: lines.length - 1 })}</span>}
        <span><i className={`sw ${loose ? "dots" : ""}`} style={loose ? undefined : { background: "#9a96a8" }} />{t(`map.via.${road.via}`)}</span>
      </div>
    </div>
  );
}
