import { useState } from "react";
import { Clock, Fuel, Info, Leaf, MessageSquare, Package, Route, Ruler, Send, Star } from "lucide-react";
import { PREFS, option, useCompare } from "../hooks";
import RouteMap from "./RouteMap";
import { Status, Region } from "./ui";
import { regionOf } from "../data/places";
import { useT, noteText } from "../i18n";

const STOPS = [0, 50, 100];
const TABS = [["route", Route], ["message", MessageSquare], ["deliveries", Package]];

// Route planning for one driver, shown beside the fleet table on the overview.
// `trip` and `truck` come from the backend and may be missing (an off-duty driver has neither).
export default function PlannerPanel({ driver: wd, truck: wt, trip, plan, assignPlan, notes, sendNote }) {
  const t = useT();
  const name = t.d(wd.name), first = name.split(" ")[0];
  const [tab, setTab] = useState("route");
  const [bal, setBal] = useState(STOPS[Math.max(PREFS.indexOf(plan), 0)]);
  const [msg, setMsg] = useState("");
  const { data, error } = useCompare(trip, wt);

  const pref = PREFS[bal < 34 ? 0 : bal < 67 ? 1 : 2];
  const pick = data && option(data, pref), base = data && option(data, PREFS[0]);
  const dMin = pick && pick.min - base.min, dCo = pick && Math.round(((base.co2 - pick.co2) / base.co2) * 100);
  const dFuel = pick && +(base.fuel - pick.fuel).toFixed(1), dKm = pick && +(pick.km - base.km).toFixed(1);
  const mine = notes.filter((n) => n.to === wd.id);
  const assign = () => { assignPlan(wd.id, pref); sendNote({ key: "note.plan", vars: { pref } }, wd.id); };
  const send = () => { sendNote({ text: msg.trim() }, wd.id); setMsg(""); };
  const progress = trip && trip.parcels_total ? trip.parcels_delivered / trip.parcels_total : 0;

  return (
    <aside className="card planner" aria-labelledby="plan-h">
      <header className="planner-head">
        <div className="planner-who">
          <span className="avatar">{name.split(" ").map((w) => w[0]).join("")}</span>
          <div>
            <small>{t("plan.title")}</small>
            <h2 id="plan-h">{name}</h2>
            <span className="meta">{wt ? `${wt.id} · ${wt.registration_number} · ` : ""}<Star size={12} className="star" fill="currentColor" />{wd.rating}</span>
          </div>
        </div>
        {trip && <Status v={trip.status} />}
      </header>

      <nav className="seg">{TABS.map(([k, Icon]) => (
        <button key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>
          <Icon size={15} />{t(`ptab.${k}`)}{k === "message" && mine.length > 0 && <span className="count">{mine.length}</span>}
        </button>
      ))}</nav>

      <div className="planner-body">
        {tab === "route" && (!trip || !wt ? <p className="empty">{t("noTrip", { name })}</p> : (<>
          <p className="current"><small>{t("who.current")}</small><b>{t.d(trip.route_name)}</b><Region v={regionOf(trip)} /><span>{t.d(trip.source)} → {t.d(trip.destination)}</span></p>
          <div className="ends"><span>{t("ends.fast")}</span><span>{t("ends.green")}</span></div>
          <input type="range" min="0" max="100" value={bal} onChange={(e) => setBal(+e.target.value)} aria-label={`${t("ends.fast")} – ${t("ends.green")}`} />
          <div className="chips">{PREFS.map((p, i) => <button key={p} className={pref === p ? "on" : ""} onClick={() => setBal(STOPS[i])}>{t(`pref.${p}`)}</button>)}</div>
          {pick && <h3 className="ask">{pick.pref === base.pref ? t("ask.base") : t("ask.save", { p: dCo, m: dMin })}</h3>}
          <RouteMap trip={trip} progress={progress} />
          {error && <p className="empty">{t("cmp.failed")} ({error.message})</p>}
          {!data && !error && <p className="empty">{t("loading")}</p>}
          {pick && (<>
            <div className="metrics four">
              <div><small><Clock size={13} />{t("m.time")}</small><b>{t("min", { n: pick.min })}</b><span>{dMin ? t("plusMin", { n: dMin }) : t("baseline")}</span></div>
              <div><small><Leaf size={13} />{t("m.co2")}</small><b>{t("kg", { n: pick.co2 })}</b><span>{dCo ? `−${dCo}%` : t("baseline")}</span></div>
              <div><small><Fuel size={13} />{t("why.fuel")}</small><b>{t("lit", { n: pick.fuel })}</b><span>{dFuel ? `−${t("lit", { n: dFuel })}` : t("baseline")}</span></div>
              <div><small><Ruler size={13} />{t("why.dist")}</small><b>{t("km", { n: pick.km })}</b><span>{dKm ? t("moreKm", { n: dKm }) : t("baseline")}</span></div>
            </div>
            {data.is_mock && <p className="api-note"><Info size={14} />{t("cmp.mock")}</p>}
          </>)}
        </>))}

        {tab === "message" && (<>
          <label className="lbl" htmlFor="instr">{t("instr", { name })}</label>
          <textarea id="instr" rows="3" value={msg} onChange={(e) => setMsg(e.target.value)} placeholder={t("msg.ph")} />
          <button className="btn" disabled={!msg.trim()} onClick={send}><Send size={15} />{t("send")}</button>
          <h4 className="sub-h">{t("sent")}</h4>
          {mine.length
            ? <ul className="log">{mine.map((n) => <li key={n.id}><small>{n.t}</small>{noteText(n, t)}</li>)}</ul>
            : <p className="empty">{t("noMsgs")}</p>}
        </>)}

        {tab === "deliveries" && (trip ? (<>
          <h4 className="sub-h first">{t.d(trip.source)} → {t.d(trip.destination)}</h4>
          <p>{t("ofDelivered", { d: trip.parcels_delivered, n: trip.parcels_total })}</p>
          <div className="bar big"><i style={{ width: `${progress * 100}%` }} /></div>
        </>) : <p className="empty">{t("noTrip", { name })}</p>)}
      </div>

      {tab === "route" && pick && (
        <footer className="planner-foot">
          <button className="btn block" disabled={plan === pref} onClick={assign}>
            {plan === pref ? t("assigned", { name: first }) : t("assign", { name })}
          </button>
        </footer>
      )}
    </aside>
  );
}
