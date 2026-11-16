import { useState } from "react";
import { Check, ChevronDown, CircleCheck, Clock, MapPin, Navigation, Ruler } from "lucide-react";
import RouteMap from "../components/RouteMap";
import RouteOptions from "../components/RouteOptions";
import { Title, Status, Region } from "../components/ui";
import { regionOf } from "../data/places";
import { useRoad } from "../hooks";
import { useT } from "../i18n";

const CHECKS = 5; // handover steps, worded in i18n as check.0 … check.4

// The backend counts a trip's parcels but doesn't itemise them, so the list below is numbered from those counts.
export default function DriverDashboard({ me, truck, trip, plan, deliver }) {
  const t = useT();
  const [checks, setChecks] = useState([]); // steps ticked for the parcel being handed over
  const [open, setOpen] = useState(true);
  const road = useRoad(trip);
  const first = me.name.split(" ")[0];

  if (!trip) return <main className="wrap driver"><div className="greet"><h1>{t("greet", { name: first })}</h1><p>{t("noTrip", { name: me.name })}</p></div></main>;

  const n = trip.parcels_total, done = trip.parcels_delivered, live = trip.status === "in_progress";
  // Driving time still ahead: the trip's estimate (else the map route's own time), scaled by the parcels left.
  const total = trip.estimated_travel_time_minutes ?? road?.min;
  const left = total != null && n ? Math.round(total * (1 - done / n)) : null;
  const toggle = (i) => setChecks((c) => (c.includes(i) ? c.filter((x) => x !== i) : [...c, i]));
  const handOver = () => { deliver(trip.id); setChecks([]); };

  const banner = done < n ? (
    <div className="next-stop">
      <span className="next-ic"><Navigation size={17} /></span>
      <div><small>{t("nextStop", { i: done + 1, n })}</small><b>{trip.destination}</b><span>{left != null && live && <><Clock size={12} /> <strong>{t("minAway", { n: left })}</strong> · </>}{trip.source} → {trip.destination}</span></div>
    </div>
  ) : (
    <div className="next-stop done"><span className="next-ic"><CircleCheck size={17} /></span><div><b>{t("allDone")}</b></div></div>
  );

  const row = (i) => {
    const gone = i < done, next = i === done && live, isOpen = next && open;
    return (
      <li key={i} className={`job ${gone ? "gone" : ""} ${isOpen ? "open" : ""}`}>
        <button className="head" onClick={() => setOpen(!open)} aria-expanded={isOpen} disabled={!next}>
          <span className="no">{gone ? <Check size={15} /> : i + 1}</span>
          <span className="who"><b>{t("parcel", { i: i + 1 })}</b><small>{gone ? t("deliveredLbl") : trip.destination}</small></span>
          {next && <ChevronDown size={16} className="chev" />}
        </button>
        {isOpen && (
          <div className="check">
            {[...Array(CHECKS)].map((_, c) => (
              <label key={c}><input type="checkbox" checked={checks.includes(c)} onChange={() => toggle(c)} />{t(`check.${c}`)}</label>
            ))}
            <button className="btn" disabled={checks.length < CHECKS} onClick={handOver}>{t("markDelivered")}</button>
          </div>
        )}
      </li>
    );
  };

  return (
    <main className="wrap driver">
      <div className="greet">
        <h1>{t("greet", { name: first })}</h1>
        <p>{t("truckLine", { plate: truck?.registration_number ?? trip.truck_id, route: trip.route_name, d: done, n })} <Status v={trip.status} /></p>
        <div className="bar big"><i style={{ width: `${n ? (done / n) * 100 : 0}%` }} /></div>
      </div>

      <div className="cols">
        <div className="card map-card"><Title>{t("yourRoute")}</Title><RouteMap trip={trip} progress={n ? done / n : 0} big banner={banner} />
          <div className="conds">
            <span><MapPin size={15} />{trip.route_name}</span>
            <Region v={regionOf(trip)} />
            {road?.km != null && <span><Ruler size={15} />{t("km", { n: road.km.toFixed(1) })}</span>}
            {total != null && <span><Clock size={15} />{t("min", { n: Math.round(total) })}</span>}
          </div>
        </div>
        <div className="card"><Title>{t("why")}</Title>{truck ? <RouteOptions trip={trip} truck={truck} chosen={plan} /> : <p className="empty">{t("noTrip", { name: me.name })}</p>}</div>
      </div>

      <div className="cols">
        <div className="card"><Title>{t("allDel")}</Title>
          <ul className="jobs">{[...Array(n)].map((_, i) => row(i))}</ul>
          <p className="api-note">{t("localOnly")}</p>
        </div>
      </div>
    </main>
  );
}
