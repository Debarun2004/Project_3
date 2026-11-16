import { useEffect, useMemo, useState } from "react";
import { networkRoute } from "./api";
import { locate } from "./data/places";

// One request per distinct key for the life of the page; a failed request is forgotten so it can be retried.
const cache = new Map();
function cached(key, load) {
  let p = cache.get(key);
  if (!p) {
    p = load();
    cache.set(key, p);
    p.catch(() => cache.delete(key));
  }
  return p;
}
function useCached(key, load) {
  const [state, setState] = useState({ key: null });
  useEffect(() => {
    if (!key) return;
    let live = true;
    cached(key, load).then((data) => live && setState({ key, data }), (error) => live && setState({ key, error }));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `key` encodes everything `load` reads
  }, [key]);
  return state.key === key ? state : {};
}

// Route options in slider order, and the colour each is drawn in.
export const PREFS = ["fastest", "balanced", "greenest"];
export const PREF_COLOR = { fastest: "#C2185B", balanced: "#3F51B5", greenest: "#0E8A7D" };

/* ---------- candidate roads ---------- */

const OSRM = "https://router.project-osrm.org/route/v1/driving/";
const toLine = (coords) => coords.map(([lng, lat]) => [lat, lng]);

async function osrm(points, alternatives = false) {
  const path = points.map(([lat, lng]) => `${lng},${lat}`).join(";");
  const res = await fetch(`${OSRM}${path}?overview=full&geometries=geojson${alternatives ? "&alternatives=3" : ""}`);
  const json = await res.json();
  if (json.code !== "Ok") throw new Error(json.code);
  return json.routes.map((r) => ({ line: toLine(r.geometry.coordinates), km: r.distance / 1000, min: r.duration / 60 }));
}

// A point beside the midpoint of from→to, `off` × the trip's length to one side (negative: the other side),
// so a route forced through it takes a different road.
function detour(from, to, off) {
  const k = Math.cos(((from[0] + to[0]) / 2) * Math.PI / 180); // degrees of longitude shrink away from the equator
  const dy = to[0] - from[0], dx = (to[1] - from[1]) * k;
  return [(from[0] + to[0]) / 2 + off * dx, (from[1] + to[1]) / 2 - (off * dy) / k];
}

const haversine = (a, b) => {
  const r = Math.PI / 180, s = Math.sin((b[0] - a[0]) * r / 2) ** 2 + Math.cos(a[0] * r) * Math.cos(b[0] * r) * Math.sin((b[1] - a[1]) * r / 2) ** 2;
  return 12742 * Math.asin(Math.sqrt(s));
};

// Up to three genuinely different roads between two places, fastest first.
async function loadCandidates(trip, from, to) {
  let via = "backend", found;
  try {
    // The backend's imported OpenStreetMap graph, when there is one: its fastest and its shortest road.
    const got = await Promise.all(["fastest", "shortest"].map((p) => networkRoute(trip.source, trip.destination, from, to, p)));
    found = got.map((r) => ({ line: r.geometry, km: r.distance_km, min: r.posted_speed_travel_time_minutes }));
  } catch {
    via = "osrm";
    // The router's own alternatives plus detours to either side; a second, wider and narrower round only if needed.
    const ask = (offs, alt) => Promise.allSettled([...(alt ? [osrm([from, to], true)] : []), ...offs.map((o) => osrm([from, detour(from, to, o), to]))])
      .then((tries) => tries.flatMap((x) => (x.status === "fulfilled" ? x.value : [])));
    found = await ask([0.12, -0.12], true);
    if (distinct(found).length < 3) found = found.concat(await ask([0.05, -0.05, 0.22, -0.22]));
  }
  if (!found.length) {
    const km = haversine(from, to) * 1.3; // rough road length when no router answers
    return { via: "straight", roads: [{ line: [from, to], km, min: (km / 40) * 60 }] };
  }
  return { via, roads: distinct(found).slice(0, 3) };
}

// Fastest first, without near-duplicates or roads far longer or slower than the fastest.
function distinct(found) {
  const sorted = [...found].sort((a, b) => a.min - b.min), best = sorted[0], roads = [];
  for (const r of sorted) {
    const same = roads.some((x) => Math.abs(x.km - r.km) / x.km < 0.015 && Math.abs(x.min - r.min) / x.min < 0.015);
    if (!same && r.km <= best.km * 1.4 && r.min <= best.min * 1.6) roads.push(r);
  }
  return roads;
}

/* ---------- time, fuel and CO₂ per option ---------- */

// Litres per km for an empty vehicle at a steady 50 km/h; payload and speed scale it.
const BASE_RATE = { mini_truck: 0.08, van: 0.09, truck: 0.2 };
const CO2_PER_LITRE = 2.68; // kg CO₂ per litre of diesel
// How each option is driven: a speed cap, a smooth-driving fuel factor, and the extra time that smoother driving costs.
const STYLE = {
  fastest: { cap: Infinity, eco: 1, slow: 1 },
  balanced: { cap: 70, eco: 0.96, slow: 1.03 },
  greenest: { cap: 55, eco: 0.9, slow: 1.06 },
};

function drive(road, truck, pref) {
  const s = STYLE[pref];
  const v = Math.min(Math.max(road.km / (road.min / 60), 10), s.cap); // average km/h
  const rate = (BASE_RATE[truck?.vehicle_type] ?? 0.15) * (1 + (truck?.Payload ?? 0) / 30000);
  const fuel = road.km * rate * (1 + 0.00012 * (v - 50) ** 2) * s.eco; // fuel use per km is lowest near 50 km/h
  const minutes = (road.km / v) * 60 * s.slow;
  return {
    pref, line: road.line,
    raw: { min: minutes, co2: fuel * CO2_PER_LITRE }, // unrounded, for comparing options
    km: +road.km.toFixed(1),
    min: Math.round(minutes),
    fuel: +fuel.toFixed(1),
    co2: +(fuel * CO2_PER_LITRE).toFixed(1),
  };
}

// Picks a road for each option. Fastest is the quickest road driven normally. Every way of giving the roads to balanced
// and greenest is tried; only orders that stay honest count (CO₂ falls and time rises from fastest → balanced → greenest),
// and among those the one using the most different roads wins, then the one saving the most CO₂.
// Driving the fastest road more gently always qualifies, so there is always an answer.
function buildOptions(roads, truck) {
  const fastest = drive(roads[0], truck, "fastest");
  let best = null;
  roads.forEach((rb, b) => roads.forEach((rg, g) => {
    const balanced = drive(rb, truck, "balanced"), greenest = drive(rg, truck, "greenest");
    const [f, m, l] = [fastest.raw, balanced.raw, greenest.raw];
    const honest = f.co2 > m.co2 && m.co2 > l.co2 && f.min <= m.min && m.min <= l.min;
    if (!honest) return;
    const score = new Set([0, b, g]).size * 1000 + (f.co2 - l.co2) / f.co2;
    if (!best || score > best.score) best = { score, balanced, greenest };
  }));
  best ??= { balanced: drive(roads[0], truck, "balanced"), greenest: drive(roads[0], truck, "greenest") };
  return { fastest, balanced: best.balanced, greenest: best.greenest };
}

export const option = (data, pref) => data.options[pref];

/** Candidate roads for a trip, plus fastest / balanced / greenest options worked out for its truck. */
export function loadRoutes(trip, truck) {
  const from = locate(trip?.source), to = locate(trip?.destination);
  if (!from || !to || String(from) === String(to)) return Promise.resolve(null);
  return cached(`roads|${from}|${to}`, () => loadCandidates(trip, from, to))
    .then(({ via, roads }) => ({ from, to, via, roads, options: buildOptions(roads, truck) }));
}

// The same, as a hook. Returns null when the trip's places can't be located; `data` is missing while roads load.
export function useRoutes(trip, truck) {
  const from = locate(trip?.source), to = locate(trip?.destination);
  const ok = from && to && String(from) !== String(to);
  const { data: found, error } = useCached(ok ? `roads|${from}|${to}` : null, () => loadCandidates(trip, from, to));
  const vt = truck?.vehicle_type, payload = truck?.Payload;
  return useMemo(() => {
    if (!ok) return null;
    if (!found) return { from, to, via: error ? "straight" : "loading", roads: [{ line: [from, to] }], error };
    return { from, to, via: found.via, roads: found.roads, options: buildOptions(found.roads, { vehicle_type: vt, Payload: payload }) };
  }, [ok, from, to, found, error, vt, payload]);
}
