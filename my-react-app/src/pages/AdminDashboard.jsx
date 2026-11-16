import { useRef, useState } from "react";
import { ClipboardList, Info, Navigation, PackageCheck, Route, Star, Truck, Users, Warehouse } from "lucide-react";
import { regionOf, tripFor } from "../data/places";
import PlannerPanel from "../components/PlannerPanel";
import TableTools from "../components/TableTools";
import { Title, Stat, Status, Region } from "../components/ui";
import { useT } from "../i18n";

const TABS = ["overview", "drivers", "trucks", "trips"];
const STATUSES = { drivers: ["on_duty", "off_duty"], trucks: ["on_road", "garage", "idle"], trips: ["planned", "in_progress", "completed", "cancelled"] };
const initials = (name) => name.split(" ").map((w) => w[0]).join("");
const matches = (q, ...fields) => !q || fields.some((f) => f && String(f).toLowerCase().includes(q));
const pct = (x) => (x.parcels_total ? (x.parcels_delivered / x.parcels_total) * 100 : 0);
const dash = <span className="dash">—</span>;

// Every record shown here comes from the backend; ids on a trip may point at a driver or truck that isn't in the lists.
export default function AdminDashboard({ drivers, trucks, trips, summary, plans, assignPlan, notes, sendNote }) {
  const t = useT();
  const [tab, setTab] = useState("overview");
  const [planFor, setPlanFor] = useState(() => (drivers.find((d) => tripFor(trips, d.id)) ?? drivers[0])?.id); // driver shown in the planning panel
  const panel = useRef(null);
  const [query, setQuery] = useState("");
  const [only, setOnly] = useState("all");
  const openTab = (k) => { setTab(k); setQuery(""); setOnly("all"); };

  const running = trips.filter((x) => x.status === "in_progress");
  const onboard = running.reduce((s, x) => s + x.parcels_total - x.parcels_delivered, 0);
  const delivered = trips.reduce((s, x) => s + x.parcels_delivered, 0);
  const driverOf = (id) => drivers.find((d) => d.id === id);
  const truckOf = (id) => trucks.find((x) => x.id === id);
  const planned = driverOf(planFor);
  const vehicle = (v) => { const k = `vt.${v}`, label = t(k); return label === k ? v : label; }; // unknown types show as stored
  const person = (d, id) => (d
    ? <span className="person"><span className="avatar sm">{initials(d.name)}</span><span><b>{d.name}</b><small>{d.id}</small></span></span>
    : id || dash);
  const est = (v, unit) => (v == null ? dash : t(unit, { n: v }));
  const parcels = (x) => <><small>{t("ofDelivered", { d: x.parcels_delivered, n: x.parcels_total })}</small><div className="bar"><i style={{ width: `${pct(x)}%` }} /></div></>;
  const q = query.trim().toLowerCase();
  const shown = (rows, search) => rows.filter((x) => (only === "all" || x.status === only) && matches(q, ...search(x)));
  const tools = (rows, placeholder) => (
    <TableTools {...{ query, setQuery, placeholder, value: only, setValue: setOnly }}
      filters={[["all", t("all"), rows.length], ...STATUSES[tab].map((k) => [k, t(`status.${k}`), rows.filter((x) => x.status === k).length])]} />
  );
  const noRows = (cols) => <tr><td colSpan={cols} className="empty-row">{t("noMatch")}</td></tr>;
  const driverRows = shown(drivers, (d) => [d.id, d.name, d.phone, d.licence_number, d.truck_id, d.route_name]);
  const truckRows = shown(trucks, (x) => [x.id, x.registration_number, x.vehicle_type, x.route_name, driverOf(x.driver_id)?.name]);
  const tripRows = shown(trips, (x) => [x.id, x.driver_id, x.truck_id, x.route_name, x.source, x.destination, driverOf(x.driver_id)?.name]);
  // Planning lives beside the fleet table, so "Plan" from any tab jumps to the overview and brings the panel into view.
  const plan = (id) => {
    setPlanFor(id);
    if (tab !== "overview") openTab("overview");
    requestAnimationFrame(() => panel.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }));
  };
  const planBtn = (id) => {
    const on = tab === "overview" && planFor === id;
    return <button className={`ghost-btn ${on ? "on" : ""}`} aria-pressed={on} onClick={() => plan(id)}><Route size={14} />{t("plan.btn")}</button>;
  };

  return (
    <main className="wrap">
      <nav className="tabs">{TABS.map((k) => <button key={k} className={tab === k ? "on" : ""} onClick={() => openTab(k)}>{t(`tab.${k}`)}</button>)}</nav>

      {tab === "overview" && (<>
        <section className="stats">
          <Stat icon={Users} accent="var(--indigo)" label={t("stat.drivers")} value={summary.drivers_total} sub={t("stat.onDuty", { n: summary.drivers_on_duty })} />
          <Stat icon={Truck} accent="var(--saffron)" label={t("stat.trucks")} value={summary.trucks_total} sub={t("stat.fleet")} />
          <Stat icon={Warehouse} accent="var(--mute)" label={t("stat.garage")} value={summary.trucks_in_garage} sub={t("stat.idle", { n: summary.trucks_total - summary.trucks_in_garage - summary.trucks_on_road })} />
          <Stat icon={Navigation} accent="var(--peacock)" label={t("stat.road")} value={summary.trucks_on_road} sub={t("stat.live")} />
          <Stat icon={PackageCheck} accent="var(--green)" label={t("stat.delivered")} value={delivered} sub={t("stat.onboard", { n: onboard })} />
          <Stat icon={ClipboardList} accent="var(--gold)" label={t("stat.trips")} value={running.length} sub={t("stat.tripsDone", { n: trips.filter((x) => x.status === "completed").length })} />
        </section>

        <div className="ov">
          <div className="card">
            <Title>{t("fleet.title")}</Title>
            <table>
              <thead><tr><th>{t("th.truck")}</th><th>{t("th.driver")}</th><th>{t("th.parcels")}</th><th>{t("th.route")}</th><th /></tr></thead>
              <tbody>
                {trucks.map((x) => {
                  const d = driverOf(x.driver_id), trip = running.find((y) => y.truck_id === x.id);
                  return (
                    <tr key={x.id} className={d && d.id === planFor ? "sel" : ""}>
                      <td><b>{x.id}</b><small>{x.registration_number}</small></td>
                      <td>{d ? d.name : <Status v={x.status} />}</td>
                      <td>{trip ? parcels(trip) : dash}</td>
                      <td>{x.route_name || dash}</td>
                      <td className="end">{d && planBtn(d.id)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="ov-side" ref={panel}>
            {planned && <PlannerPanel key={planFor} driver={planned} truck={truckOf(planned.truck_id)} trip={tripFor(trips, planFor)} plan={plans[planFor]} {...{ assignPlan, notes, sendNote }} />}
          </div>
        </div>
      </>)}

      {tab === "drivers" && (
        <div className="card scroll"><Title>{t("roster.title")}</Title>
          {tools(drivers, t("search.drivers"))}
          <table>
            <thead><tr><th>{t("th.name")}</th><th>{t("th.phone")}</th><th>{t("th.licence")}</th><th>{t("th.exp")}</th><th>{t("th.rating")}</th><th>{t("th.truck")}</th><th>{t("th.route")}</th><th>{t("th.status")}</th><th /></tr></thead>
            <tbody>{driverRows.length ? driverRows.map((d) => (
              <tr key={d.id}><td>{person(d)}</td><td>{d.phone}</td><td>{d.licence_number}</td><td>{t("yrs", { n: d.experience_years })}</td>
                <td><span className="rating"><Star size={13} className="star" fill="currentColor" />{d.rating}</span></td>
                <td>{d.truck_id ? [d.truck_id, truckOf(d.truck_id)?.registration_number].filter(Boolean).join(" · ") : dash}</td>
                <td>{d.route_name || dash}</td>
                <td><Status v={d.status} /></td>
                <td className="end">{d.status === "on_duty" && planBtn(d.id)}</td></tr>
            )) : noRows(9)}</tbody>
          </table>
        </div>
      )}

      {tab === "trucks" && (
        <div className="card scroll"><Title>{t("trucks.title")}</Title>
          {tools(trucks, t("search.trucks"))}
          <table>
            <thead><tr><th>{t("th.truck")}</th><th>{t("th.type")}</th><th>{t("th.capacity")}</th><th>{t("th.status")}</th><th>{t("th.driver")}</th><th>{t("th.route")}</th><th /></tr></thead>
            <tbody>{truckRows.length ? truckRows.map((x) => {
              const d = driverOf(x.driver_id);
              return (
                <tr key={x.id}><td><b>{x.id}</b><small>{x.registration_number}</small></td><td>{vehicle(x.vehicle_type)}</td>
                  <td>{t("kg", { n: x.Payload.toLocaleString("en-IN") })}</td>
                  <td><Status v={x.status} /></td>
                  <td>{person(d, x.driver_id)}</td>
                  <td>{x.route_name || dash}</td>
                  <td className="end">{d && planBtn(d.id)}</td></tr>
              );
            }) : noRows(7)}</tbody>
          </table>
        </div>
      )}

      {tab === "trips" && (
        <div className="card scroll"><Title>{t("trips.title")}</Title>
          {tools(trips, t("search.trips"))}
          <table>
            <thead><tr><th>{t("th.trip")}</th><th>{t("th.driver")}</th><th>{t("th.truck")}</th><th>{t("th.fromTo")}</th><th>{t("th.route")}</th><th>{t("th.status")}</th><th>{t("th.parcels")}</th><th>{t("th.estTime")}</th><th>{t("th.estFuel")}</th><th>{t("th.estCo2")}</th></tr></thead>
            <tbody>{tripRows.length ? tripRows.map((x) => (
              <tr key={x.id}><td><b>{x.id}</b></td>
                <td>{person(driverOf(x.driver_id), x.driver_id)}</td>
                <td><b>{x.truck_id}</b><small>{truckOf(x.truck_id)?.registration_number}</small></td>
                <td>{x.source}<small>→ {x.destination}</small></td>
                <td>{x.route_name}<small><Region v={regionOf(x)} /></small></td>
                <td><Status v={x.status} /></td>
                <td>{parcels(x)}</td>
                <td>{est(x.estimated_travel_time_minutes, "min")}</td>
                <td>{est(x.estimated_fuel_consumption_liters, "lit")}</td>
                <td>{est(x.estimated_co2_emissions_kg, "kg")}</td></tr>
            )) : noRows(10)}</tbody>
          </table>
          {trips.some((x) => x.is_mock_estimate) && <p className="api-note"><Info size={14} />{t("trips.mock")}</p>}
        </div>
      )}

    </main>
  );
}
