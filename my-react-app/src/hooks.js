import { useEffect, useMemo, useState } from "react";
import { compareRoutes, networkRoute } from "./api";
import { locate } from "./data/places";

// One request per distinct key for the life of the page; a failed request is forgotten so it can be retried.
const cache = new Map();
function useCached(key, load) {
  const [state, setState] = useState({ key: null });
  useEffect(() => {
    if (!key) return;
    let live = true, p = cache.get(key);
    if (!p) {
      p = load();
      cache.set(key, p);
      p.catch(() => cache.delete(key));
    }
    p.then((data) => live && setState({ key, data }), (error) => live && setState({ key, error }));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `key` encodes everything `load` reads
  }, [key]);
  return state.key === key ? state : {};
}

// { data, error } for the backend's fastest / balanced / greenest comparison of a trip; both empty while loading.
export const useCompare = (trip, truck) => useCached(
  trip && truck ? `cmp|${trip.source}|${trip.destination}|${truck.vehicle_type}|${truck.Payload}` : null,
  () => compareRoutes(trip, truck),
);

async function loadRoad(trip, from, to) {
  try {
    const r = await networkRoute(trip.source, trip.destination, from, to);
    return { line: r.geometry, km: r.distance_km, min: r.posted_speed_travel_time_minutes, via: "backend" };
  } catch { /* road graph not imported, or no route: fall through */ }
  try {
    const res = await fetch(`https://router.project-osrm.org/route/v1/driving/${from[1]},${from[0]};${to[1]},${to[0]}?overview=full&geometries=geojson`);
    const json = await res.json();
    const r = json.routes[0];
    return { line: r.geometry.coordinates.map(([lng, lat]) => [lat, lng]), km: r.distance / 1000, min: r.duration / 60, via: "osrm" };
  } catch {
    return { line: [from, to], via: "straight" };
  }
}

// Line to draw for a trip: the backend's OSM route when it has one, else the public OSRM demo server, else a straight line.
// Returns null when the trip's place names can't be located.
export function useRoad(trip) {
  const from = locate(trip?.source), to = locate(trip?.destination);
  const ok = from && to && String(from) !== String(to);
  const straight = useMemo(() => [from, to], [from, to]);
  const { data } = useCached(ok ? `road|${from}|${to}` : null, () => loadRoad(trip, from, to));
  return useMemo(() => (ok ? { from, to, ...(data ?? { line: straight, via: "loading" }) } : null), [ok, from, to, data, straight]);
}

// Route options the backend compares, in slider order, and the key each one has in its response.
export const PREFS = ["fastest", "balanced", "greenest"];
export const PREF_COLOR = { fastest: "#C2185B", balanced: "#3F51B5", greenest: "#0E8A7D" };
export const option = (data, pref) => {
  const m = data[`${pref}_route`];
  return { pref, min: m.estimated_travel_time_minutes, km: m.estimated_distance_km, fuel: m.estimated_fuel_consumption_liters, co2: m.estimated_co2_emissions_kg };
};
