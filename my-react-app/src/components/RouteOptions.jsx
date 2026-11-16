import { ArrowDown, ArrowUp, Clock, Fuel, Info, Leaf, Ruler, Sparkles } from "lucide-react";
import { PREFS, PREF_COLOR, option, useCompare } from "../hooks";
import { useT } from "../i18n";

// The backend's fastest / balanced / greenest comparison for a trip. `chosen` is the option the control room assigned, if any.
export default function RouteOptions({ trip, truck, chosen }) {
  const t = useT();
  const { data, error } = useCompare(trip, truck);
  if (error) return <p className="empty">{t("cmp.failed")} ({error.message})</p>;
  if (!data) return <p className="empty">{t("loading")}</p>;

  const all = PREFS.map((p) => option(data, p)), base = all[0], r = all.find((x) => x.pref === chosen);
  const isBase = r === base;
  const tiles = r && [
    { Icon: Leaf, label: t("why.co2"), value: t("kg", { n: r.co2 }), note: isBase ? t("baseline") : t("lessPct", { p: Math.round((1 - r.co2 / base.co2) * 100) }), good: !isBase },
    { Icon: Clock, label: t("why.time"), value: t("min", { n: r.min }), note: isBase ? t("fastest") : t("moreMin", { n: r.min - base.min }), up: !isBase },
    { Icon: Fuel, label: t("why.fuel"), value: t("lit", { n: r.fuel }), note: isBase ? t("baseline") : t("lessPct", { p: Math.round((1 - r.fuel / base.fuel) * 100) }), good: !isBase },
    { Icon: Ruler, label: t("why.dist"), value: t("km", { n: r.km }), note: isBase ? t("baseline") : t("moreKm", { n: +(r.km - base.km).toFixed(1) }), up: !isBase },
  ];

  const compare = (title, field) => {
    const max = Math.max(...all.map((x) => x[field]));
    return (
      <div className="cmp">
        <small>{title}</small>
        {all.map((x) => (
          <div key={x.pref} className={`cmp-row ${x === r ? "on" : ""}`} title={`${t(`pref.${x.pref}`)}: ${x[field]}`}>
            <span className="cmp-name">{t(`pref.${x.pref}`)}</span>
            <span className="cmp-track"><i style={{ width: `${(x[field] / max) * 100}%`, background: x === r ? PREF_COLOR[x.pref] : undefined }} /></span>
            <span className="cmp-val">{x[field]}</span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="whyv">
      <p className={`verdict ${r && !isBase ? "" : "warn"}`}><Sparkles size={17} />{t(`verdict.${chosen ?? "none"}`)}</p>
      {tiles && (
        <div className="why-tiles">
          {tiles.map(({ Icon, label, value, note, good, up }) => (
            <div key={label} className="why-tile">
              <small><Icon size={14} />{label}</small>
              <b>{value}</b>
              <span className={`delta ${good ? "good" : ""}`}>{good && <ArrowDown size={13} />}{up && <ArrowUp size={13} />}{note}</span>
            </div>
          ))}
        </div>
      )}
      <div className="cmp-grid">
        {compare(t("cmp.co2"), "co2")}
        {compare(t("cmp.time"), "min")}
      </div>
      {data.is_mock && <p className="api-note"><Info size={14} />{data.notice}</p>}
    </div>
  );
}
