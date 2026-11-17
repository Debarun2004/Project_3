import { useCallback, useEffect, useMemo, useState } from "react";
import { LoaderCircle, LogOut, RefreshCw } from "lucide-react";
import { deliverParcel, getDispatch, getFleet, getTrips, markRead, sendMessage, setPlan } from "./api";
import { tripFor } from "./data/places";
import { LangSwitch } from "./components/ui";
import Notifications from "./components/Notifications";
import AdminDashboard from "./pages/AdminDashboard";
import DriverDashboard from "./pages/DriverDashboard";
import Login from "./pages/Login";
import { LangCtx, makeT } from "./i18n";

// The session survives a refresh but not a closed tab; storage may be blocked, so never rely on it.
const SESSION_KEY = "prithvi.session";
const loadSession = () => { try { return JSON.parse(sessionStorage.getItem(SESSION_KEY)); } catch { return null; } };
const saveSession = (s) => { try { s ? sessionStorage.setItem(SESSION_KEY, JSON.stringify(s)) : sessionStorage.removeItem(SESSION_KEY); } catch { /* ignore */ } };

// How often the page asks the backend for new messages and route options.
const POLL_MS = 4000;
const EMPTY_DISPATCH = { messages: [], plans: {}, deliveries: null };

export default function App() {
  const [session, setSession] = useState(loadSession);
  const [lang, setLang] = useState("en");
  // Drivers, trucks, trips and the summary are read from the backend each time someone signs in.
  const [fleet, setFleet] = useState(null);
  const [error, setError] = useState(null);
  const [attempt, setAttempt] = useState(0);
  // Control-room messages, each driver's route option and the delivery log live in the backend, so every
  // signed-in screen sees them. `deliveries` stays null until the first answer, so old ones don't pop up as new.
  const [dispatch, setDispatch] = useState(EMPTY_DISPATCH);
  const [toasted, setToasted] = useState(() => new Set()); // message ids already popped up on this screen

  const signedIn = !!session;
  useEffect(() => {
    if (!signedIn) return;
    let live = true;
    getFleet().then((f) => { if (live) { setFleet(f); setError(null); } }, (e) => live && setError(e));
    return () => { live = false; };
  }, [signedIn, attempt]);

  const trips = useMemo(() => fleet?.trips ?? [], [fleet]);

  const me = session?.id;
  const role = session?.role;
  // A driver only fetches their own messages; the control room fetches everyone's. Trips are re-read too, so
  // parcels a driver hands over show up on the control room's screen.
  const refresh = useCallback(() => Promise.all([getDispatch(role === "driver" ? me : undefined), getTrips()]).then(([d, latest]) => {
    setDispatch(d);
    setFleet((f) => f && { ...f, trips: latest });
  }, () => {}), [role, me]);
  const loaded = !!fleet;
  useEffect(() => {
    if (!loaded) return;
    refresh();
    const h = setInterval(refresh, POLL_MS);
    window.addEventListener("focus", refresh);
    return () => { clearInterval(h); window.removeEventListener("focus", refresh); };
  }, [loaded, refresh]);

  const sendNote = (driver_id, text) => sendMessage(driver_id, text).then(refresh);
  const assignPlan = (driver_id, pref) => setPlan(driver_id, pref).then(refresh);
  const deliver = (trip_id, pref, co2_saved_kg) => deliverParcel(trip_id, pref, co2_saved_kg).then((trip) => {
    setFleet((f) => f && { ...f, trips: f.trips.map((x) => (x.id === trip.id ? trip : x)) });
    refresh();
  });
  const onRead = () => {
    setDispatch((d) => ({ ...d, messages: d.messages.map((m) => ({ ...m, read: true })) }));
    markRead(me).then(refresh, () => {});
  };
  const onToasted = useCallback((id) => setToasted((s) => new Set(s).add(id)), []);
  const { messages: notes, plans, deliveries } = dispatch;
  const t = makeT(lang);
  const signIn = (s) => { saveSession(s); setSession(s); };
  const signOut = () => { saveSession(null); setSession(null); setFleet(null); setDispatch(EMPTY_DISPATCH); };

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
    page = <AdminDashboard drivers={fleet.drivers} trucks={fleet.trucks} summary={fleet.summary} {...{ trips, plans, assignPlan, notes, sendNote, deliveries }} />;
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
            <div className="brand"><img className="logo" src="/logo.png" alt="" width="44" height="44" />
              <div><h1>{t("brand")}</h1><small>{t("brandSub")}</small></div></div>
            <div className="top-actions">
              <LangSwitch {...{ lang, setLang }} />
              {role === "driver" && (
                <Notifications notes={notes} toasted={toasted} onRead={onRead} onToasted={onToasted} />
              )}
              <div className="who-chip"><small>{t(`role.${role}`)}</small><b>{t.d(session.name)}</b></div>
              <button className="ghost-btn signout" onClick={signOut}><LogOut size={14} />{t("auth.logout")}</button>
            </div>
          </div>
        </header>
        {page}
        <footer className="foot">{t("brand")} · {t("brandSub")}</footer>
      </div>
    </LangCtx.Provider>
  );
}
