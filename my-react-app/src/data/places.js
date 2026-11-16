// The backend stores trip ends as place names only, and its road-network endpoint expects the frontend to supply coordinates.
// This is the list of West Bengal towns the map can place, as [lat, lng], grouped by the kind of country they sit in.
// A place name is matched if it contains one of these keys; longer keys are tried first.
const PLACES = {
  kolkata: { at: [22.5726, 88.3639], region: "urban" },
  howrah: { at: [22.5839, 88.3426], region: "urban" },
  "new town": { at: [22.5806, 88.4602], region: "urban" },
  newtown: { at: [22.5806, 88.4602], region: "urban" },
  durgapur: { at: [23.5204, 87.3119], region: "industrial" },
  asansol: { at: [23.6739, 86.9524], region: "industrial" },
  bankura: { at: [23.2324, 87.0746], region: "rural" },
  purulia: { at: [23.3322, 86.3616], region: "rural" },
  kalimpong: { at: [27.0594, 88.4695], region: "hilly" },
  darjeeling: { at: [27.041, 88.2663], region: "hilly" },
};
const KEYS = Object.keys(PLACES).sort((a, b) => b.length - a.length);
const find = (label) => {
  const s = String(label ?? "").toLowerCase(), k = KEYS.find((key) => s.includes(key));
  return k ? PLACES[k] : null;
};

export const locate = (label) => find(label)?.at ?? null;
// urban | industrial | rural | hilly, taken from where the trip ends (else where it starts); null if neither is known.
export const regionOf = (trip) => (find(trip?.destination) ?? find(trip?.source))?.region ?? null;

// The trip a driver is on now, else the next planned one, else the most recent.
export const tripFor = (trips, driver_id) => {
  const mine = trips.filter((x) => x.driver_id === driver_id);
  return mine.find((x) => x.status === "in_progress") ?? mine.find((x) => x.status === "planned") ?? mine[mine.length - 1] ?? null;
};
