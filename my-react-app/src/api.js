// Calls go to the FastAPI backend. In development the Vite proxy forwards them (see vite.config.js);
// a deployed build has no proxy, so set VITE_API_URL to the backend's public address when building.
const BASE = (import.meta.env.VITE_API_URL ?? "").replace(/\/+$/, "");

async function request(path, body) {
  let res;
  try {
    res = await fetch(BASE + path, body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : undefined);
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
  return res.status === 204 ? null : res.json();
}

export const getDrivers = () => request("/api/v1/drivers");

export async function getFleet() {
  const [drivers, trucks, trips, summary, health] = await Promise.all([
    getDrivers(), request("/api/v1/trucks"), request("/api/v1/trips"), request("/api/v1/dashboard/summary"), request("/health"),
  ]);
  return { drivers, trucks, trips, summary, health };
}

// Road geometry on the backend's imported OpenStreetMap graph; answers 503 until that graph has been imported.
export const networkRoute = (source, destination, from, to, preference = "fastest") => request("/routes/network", {
  source,
  destination,
  source_latitude: from[0],
  source_longitude: from[1],
  destination_latitude: to[0],
  destination_longitude: to[1],
  preference,
});

// Control-room messages and the route option assigned to each driver; `driverId` limits both to one driver.
export const getDispatch = (driverId) => request(`/api/v1/dispatch${driverId ? `?driver_id=${encodeURIComponent(driverId)}` : ""}`);
export const sendMessage = (driver_id, text) => request("/api/v1/messages", { driver_id, text });
export const markRead = (driver_id) => request("/api/v1/messages/read", { driver_id });
export const setPlan = (driver_id, pref) => request("/api/v1/plans", { driver_id, pref });
