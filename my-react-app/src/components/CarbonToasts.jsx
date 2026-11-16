import { useEffect, useMemo, useState } from "react";
import { Leaf } from "lucide-react";
import { loadRoutes } from "../hooks";
import { useT } from "../i18n";

const SHOW_MS = 7000;
const FIRST_MS = 6000;
const gap = () => 20000 + Math.random() * 20000; // 20–40 s between pop-ups, so they don't feel mechanical

// Control-room pop-ups about the CO₂ saved by drivers who were given the balanced or greenest route.
// `items` is one { driver, trip, truck, pref } per such driver. Each saving is that trip's CO₂ on the fastest
// option minus its CO₂ on the assigned one, from the same road calculations the planner shows.
export default function CarbonToasts({ items }) {
  const t = useT();
  const [savings, setSavings] = useState(null);
  const [shown, setShown] = useState(null);

  const key = items.map((x) => `${x.driver.id}:${x.pref}:${x.trip?.id}`).join("|");
  useEffect(() => {
    let live = true;
    Promise.all(items.map(async ({ driver, trip, truck, pref }) => {
      const r = await loadRoutes(trip, truck).catch(() => null);
      if (!r) return null;
      const kg = +(r.options.fastest.co2 - r.options[pref].co2).toFixed(1);
      return kg > 0 ? { driver, trip, pref, kg } : null;
    })).then((all) => live && setSavings(all.filter(Boolean)));
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `key` captures what matters in `items`
  }, [key]);

  // What to say, in turn: each driver's saving, then the fleet total; a nudge when nothing has been saved yet.
  // Kept as data and worded at render time, so switching language rewords the pop-up without restarting the timer.
  const lines = useMemo(() => {
    if (!savings) return [];
    if (!savings.length) return [{ kind: "none" }];
    const kg = +savings.reduce((s, x) => s + x.kg, 0).toFixed(1);
    return [...savings.map((x) => ({ kind: "driver", ...x })), { kind: "total", kg, n: savings.length }];
  }, [savings]);
  const say = (x) => (x.kind === "none" ? t("co2.none")
    : x.kind === "total" ? t("co2.total", { kg: x.kg, n: x.n })
    : t("co2.driver", { name: t.d(x.driver.name), kg: x.kg, route: t.d(x.trip.route_name), pref: t(`pref.${x.pref}`).toLowerCase() }));

  useEffect(() => {
    if (!lines.length) return;
    let i = 0, hide, next;
    const pop = () => {
      setShown({ id: Date.now(), at: i % lines.length });
      i += 1;
      hide = setTimeout(() => setShown(null), SHOW_MS);
      next = setTimeout(pop, SHOW_MS + gap());
    };
    next = setTimeout(pop, FIRST_MS);
    return () => { clearTimeout(hide); clearTimeout(next); };
  }, [lines]);

  if (!shown || !lines[shown.at]) return null;
  return (
    <div className="toast eco" role="status" key={shown.id}>
      <span className="toast-ic"><Leaf size={18} /></span>
      <div><small>{t("co2.title")}</small><p>{say(lines[shown.at])}</p></div>
      <button className="toast-x" onClick={() => setShown(null)} aria-label={t("close")}>×</button>
      <i className="toast-timer" style={{ animationDuration: `${SHOW_MS}ms` }} />
    </div>
  );
}
