// Every call goes to the FastAPI backend through the Vite proxy (see vite.config.js).

async function request(path, body) {
  let res;
  try {
    res = await fetch(path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : undefined);
  } catch {
    throw new Error("offline");
  }
  if (!res.ok) {
    let detail = "";
    try { const d = (await res.json()).detail; detail = typeof d === "string" ? d : d?.[0]?.msg ?? ""; } catch { /* not JSON */ }
    const err = new Error(detail || `HTTP ${res.status}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export const getDrivers = () => request("/api/v1/drivers");

export async function getFleet() {
  const [drivers, trucks, trips, summary, health] = await Promise.all([
    getDrivers(), request("/api/v1/trucks"), request("/api/v1/trips"), request("/api/v1/dashboard/summary"), request("/health"),
  ]);
  return { drivers, trucks, trips, summary, health };
}

// Fastest / balanced / greenest estimates for one trip. The backend marks these as synthetic (`is_mock`).
export const compareRoutes = (trip, truck) => request("/routes/compare", {
  source: trip.source,
  destination: trip.destination,
  vehicle_type: truck.vehicle_type,
  payload_kg: truck.Payload,
  dispatch_time: new Date().toISOString(),
  optimization_preference: "balanced",
});

// Road geometry on the backend's imported OpenStreetMap graph; answers 503 until that graph has been imported.
export const networkRoute = (source, destination, from, to) => request("/routes/network", {
  source,
  destination,
  source_latitude: from[0],
  source_longitude: from[1],
  destination_latitude: to[0],
  destination_longitude: to[1],
  preference: "fastest",
});
