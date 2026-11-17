import { useCallback, useEffect, useRef, useState } from "react";
import { Leaf, PackageCheck } from "lucide-react";
import { tripFor } from "../data/places";
import { loadRoutes } from "../hooks";
import { useT } from "../i18n";

const SHOW_MS = 7000;
const FIRST_MS = 6000;
const gap = () => 20000 + Math.random() * 20000; // 20–40 s between pop-ups, so they don't feel mechanical
const kg = (n) => (n < 1 ? n.toFixed(2) : n.toFixed(1));

// Control-room pop-ups about CO₂ saved by the route options drivers were given.
// - When a driver hands over a parcel, a pop-up says right away what that delivery saved against the fastest option
//   (or, on the fastest route, what the greenest one would have saved).
// - Every 20–40 s a pop-up goes through the drivers in turn: CO₂ saved on their trip so far, from the delivery log;
//   for a driver on a greener option with nothing delivered on it yet, what the parcels left will save; then the fleet total.
// Pop-ups are kept as data and worded at render time, so switching language rewords them without restarting the timer.
export default function CarbonToasts({ drivers, trips, trucks, plans, deliveries }) {
  const t = useT();
  const [shown, setShown] = useState(null); // { id, line }
  const hide = useRef(null);
  const show = useCallback((line) => {
    clearTimeout(hide.current);
    setShown({ id: `${Date.now()}-${Math.random()}`, line });
    hide.current = setTimeout(() => setShown(null), SHOW_MS);
  }, []);
  useEffect(() => () => clearTimeout(hide.current), []);

  const driverOf = (id) => drivers.find((d) => d.id === id);
  const tripOf = (id) => trips.find((x) => x.id === id);

  // Each driver's current trip and its route options, for projections and the "greenest would save" hint.
  const active = drivers.map((d) => {
    const trip = tripFor(trips, d.id), truck = trip && trucks.find((x) => x.id === (trip.truck_id ?? d.truck_id));
    return trip && truck && trip.status !== "cancelled" ? { d, trip, truck } : null;
  }).filter(Boolean);
  const [opts, setOpts] = useState({}); // trip id → { fastest, balanced, greenest }
  const key = active.map((x) => `${x.trip.id}:${x.truck.id}`).join("|");
  useEffect(() => {
    let live = true;
    Promise.all(active.map((x) => loadRoutes(x.trip, x.truck).then((r) => [x.trip.id, r?.options ?? null], () => [x.trip.id, null])))
      .then((all) => live && setOpts(Object.fromEntries(all)));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `key` captures which trips and trucks matter
  }, [key]);

  // CO₂ saved per trip, and the option of its latest delivery, from the delivery log.
  const savedOn = {}, lastPref = {};
  for (const x of [...(deliveries ?? [])].reverse()) { // oldest first, so the latest option wins
    savedOn[x.trip_id] = (savedOn[x.trip_id] ?? 0) + x.co2_saved_kg;
    lastPref[x.trip_id] = x.pref;
  }

  const lines = [];
  for (const { d, trip } of active) {
    const pref = plans[d.id] ?? "fastest", o = opts[trip.id], saved = savedOn[trip.id] ?? 0;
    const left = trip.parcels_total - trip.parcels_delivered;
    if (saved > 0.0005) lines.push({ kind: "saved", driverId: d.id, tripId: trip.id, pref: lastPref[trip.id], kg: saved });
    else if (pref !== "fastest" && o && left > 0 && o.fastest.co2 > o[pref].co2) {
      lines.push({ kind: "plan", driverId: d.id, tripId: trip.id, pref, kg: ((o.fastest.co2 - o[pref].co2) * left) / trip.parcels_total, left });
    }
  }
  const savedTrips = Object.values(savedOn).filter((v) => v > 0.0005);
  if (savedTrips.length) lines.push({ kind: "total", kg: savedTrips.reduce((s, v) => s + v, 0), n: savedTrips.length });
  if (!lines.length) lines.push({ kind: "none" });

  // The timer reads the latest lines when it fires, so new data never restarts it.
  const latest = useRef(lines);
  useEffect(() => { latest.current = lines; });
  useEffect(() => {
    let i = 0, next;
    const pop = () => {
      const all = latest.current;
      show(all[i % all.length]);
      i += 1;
      next = setTimeout(pop, SHOW_MS + gap());
    };
    next = setTimeout(pop, FIRST_MS);
    return () => clearTimeout(next);
  }, [show]);

  // A pop-up for each new delivery. Deliveries already in the log when the page loaded are not news.
  const seen = useRef(null);
  useEffect(() => {
    if (!deliveries) return;
    if (!seen.current) { seen.current = new Set(deliveries.map((x) => x.id)); return; }
    const fresh = deliveries.filter((x) => !seen.current.has(x.id));
    fresh.forEach((x) => seen.current.add(x.id));
    if (!fresh.length) return;
    const x = fresh[0]; // newest first
    const total = deliveries.filter((y) => y.trip_id === x.trip_id).reduce((s, y) => s + y.co2_saved_kg, 0);
    const timer = setTimeout(() => show({ kind: "delivery", ...x, total }), 0);
    return () => clearTimeout(timer);
  }, [deliveries, show]);

  const say = (x) => {
    if (x.kind === "none") return t("co2.none");
    if (x.kind === "total") return t(x.n === 1 ? "co2.total1" : "co2.total", { kg: kg(x.kg), n: x.n });
    const d = driverOf(x.driverId ?? x.driver_id), trip = tripOf(x.tripId ?? x.trip_id);
    if (!d || !trip) return null;
    const who = { id: d.id, name: t.d(d.name), route: t.d(trip.route_name), pref: t(`pref.${x.pref}`).toLowerCase() };
    if (x.kind === "saved") return t("co2.saved", { ...who, kg: kg(x.kg), d: trip.parcels_delivered, n: trip.parcels_total });
    if (x.kind === "plan") return t("co2.plan", { ...who, kg: kg(x.kg), left: x.left });
    // A delivery.
    const n = trip.parcels_total;
    if (x.pref === "fastest" || x.co2_saved_kg <= 0) {
      const o = opts[trip.id], could = o && n ? (o.fastest.co2 - o.greenest.co2) / n : 0;
      return t("co2.fastest", { ...who, i: x.parcel, n }) + (could > 0 ? ` ${t("co2.could", { kg: kg(could) })}` : "");
    }
    if (x.parcel >= n) return t("co2.completed", { ...who, total: kg(x.total) });
    return t("co2.delivered", { ...who, i: x.parcel, n, kg: kg(x.co2_saved_kg), total: kg(x.total) });
  };

  const text = shown && say(shown.line);
  if (!text) return null;
  const delivery = shown.line.kind === "delivery";
  return (
    <div className="toast eco" role="status" key={shown.id}>
      <span className="toast-ic">{delivery ? <PackageCheck size={18} /> : <Leaf size={18} />}</span>
      <div><small>{t(delivery ? "co2.delivTitle" : "co2.title")}</small><p>{text}</p></div>
      <button className="toast-x" onClick={() => setShown(null)} aria-label={t("close")}>×</button>
      <i className="toast-timer" style={{ animationDuration: `${SHOW_MS}ms` }} />
    </div>
  );
}
