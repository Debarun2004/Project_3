import { useCallback, useEffect, useMemo, useState } from "react";
import { LoaderCircle, LogOut, RefreshCw } from "lucide-react";
import { getFleet } from "./api";
import { tripFor } from "./data/places";
import { Motif, LangSwitch } from "./components/ui";
import Notifications from "./components/Notifications";
import AdminDashboard from "./pages/AdminDashboard";
import DriverDashboard from "./pages/DriverDashboard";
import Login from "./pages/Login";
import { LangCtx, makeT } from "./i18n";

const now = () => new Date().toTimeString().slice(0, 5);

// The session survives a refresh but not a closed tab; storage may be blocked, so never rely on it.
const SESSION_KEY = "prithvi.session";
const loadSession = () => { try { return JSON.parse(sessionStorage.getItem(SESSION_KEY)); } catch { return null; } };
const saveSession = (s) => { try { s ? sessionStorage.setItem(SESSION_KEY, JSON.stringify(s)) : sessionStorage.removeItem(SESSION_KEY); } catch { /* ignore */ } };

export default function App() {
  const [session, setSession] = useState(loadSession);
  const [lang, setLang] = useState("en");
  // Drivers, trucks, trips and the summary are read from the backend each time someone signs in.
  const [fleet, setFleet] = useState(null);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);
  // The backend has no update endpoints yet, so these three live only in this page until it is reloaded:
  // parcels handed over since loading (per trip), the route option assigned to each driver, and control-room messages.
  const [handed, setHanded] = useState({});
  const [plans, setPlans] = useState({});
  const [notes, setNotes] = useState([]);

  const signedIn = !!session;
  useEffect(() => {
    if (!signedIn) return;
    let live = true;
    getFleet().then((f) => { if (live) { setFleet(f); setError(null); } }, (e) => live && setError(e));
    return () => { live = false; };
  }, [signedIn, attempt]);

  const trips = useMemo(() => (fleet?.trips ?? []).map((x) => {
    const parcels_delivered = Math.min(x.parcels_total, x.parcels_delivered + (handed[x.id] ?? 0));
    if (parcels_delivered === x.parcels_delivered) return x;
    return { ...x, parcels_delivered, status: x.status === "in_progress" && parcels_delivered === x.parcels_total ? "completed" : x.status };
  }), [fleet, handed]);

  const sendNote = (note, to) => setNotes((n) => [{ id: n.length + 1, t: now(), to, read: false, toasted: false, ...note }, ...n]);
  const patchNotes = useCallback((to, patch) => setNotes((n) => n.map((x) => (x.to === to ? { ...x, ...patch } : x))), []);
  const deliver = (trip_id) => setHanded((h) => ({ ...h, [trip_id]: (h[trip_id] ?? 0) + 1 }));
  const assignPlan = (driver_id, pref) => setPlans((p) => ({ ...p, [driver_id]: pref }));
  const me = session?.id;
  const onToasted = useCallback(() => patchNotes(me, { toasted: true }), [patchNotes, me]);
  const t = makeT(lang);
  const signIn = (s) => { saveSession(s); setSession(s); };
  const signOut = () => { saveSession(null); setSession(null); };
  const role = session?.role;

  if (!session) return <LangCtx.Provider value={lang}><div lang={lang}><Login onLogin={signIn} {...{ lang, setLang }} /></div></LangCtx.Provider>;

  const driver = role === "driver" ? fleet?.drivers.find((d) => d.id === me) : null;
  let page;
  if (!fleet) {
    page = (
      <main className="wrap"><div className="card state">
        {error ? (<>
          <h2>{t("load.fail")}</h2>
          <p>{t("load.hint")} <code>python -m uvicorn app.main:app --reload</code></p>
          <p className="api-note">{error.message === "offline" ? t("load.offline") : error.message}</p>
          <button className="btn" onClick={() => { setError(null); setAttempt((a) => a + 1); }}><RefreshCw size={15} />{t("retry")}</button>
        </>) : <p><LoaderCircle size={16} className="spin" /> {t("loading")}</p>}
      </div></main>
    );
  } else if (role === "admin") {
    page = <AdminDashboard drivers={fleet.drivers} trucks={fleet.trucks} summary={fleet.summary} {...{ trips, plans, assignPlan, notes, sendNote }} />;
  } else if (driver) {
    // An off-duty driver has no truck of their own, so fall back to the one their last trip used.
    const trip = tripFor(trips, driver.id);
    page = <DriverDashboard me={driver} truck={fleet.trucks.find((x) => x.id === (driver.truck_id ?? trip?.truck_id))} trip={trip} plan={plans[driver.id]} deliver={deliver} />;
  } else {
    page = <main className="wrap"><div className="card state"><h2>{t("load.noRecord")}</h2></div></main>;
  }

  return (
    <LangCtx.Provider value={lang}>
      <div lang={lang}>
        <header className="top">
          <div className="top-in">
            <div className="brand"><Motif size={38} color="var(--saffron)" sw={2} />
              <div><h1>Prithvi Route</h1><small>{t("brandSub")}</small></div></div>
            <div className="top-actions">
              <LangSwitch {...{ lang, setLang }} />
              {role === "driver" && (
                <Notifications notes={notes.filter((n) => n.to === me)} onRead={() => patchNotes(me, { read: true, toasted: true })} onToasted={onToasted} />
              )}
              <div className="who-chip"><small>{t(`role.${role}`)}</small><b>{session.name}</b></div>
              <button className="ghost-btn signout" onClick={signOut}><LogOut size={14} />{t("auth.logout")}</button>
            </div>
          </div>
        </header>
        {page}
        <footer className="foot">Prithvi Route · {t("brandSub")}{fleet && ` · ${t("foot.data", { mode: fleet.health.dataset_status })}`}</footer>
      </div>
    </LangCtx.Provider>
  );
}
