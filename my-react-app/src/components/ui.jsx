import { Languages } from "lucide-react";
import { useT, LANGS } from "../i18n";

export function Motif({ size = 40, color = "currentColor", sw = 1.4 }) {
  return (
    <svg width={size} height={size} viewBox="-50 -50 100 100" fill="none" stroke={color} strokeWidth={sw} aria-hidden="true">
      {[...Array(8)].map((_, i) => <ellipse key={i} cy="-24" rx="9" ry="22" transform={`rotate(${i * 45})`} />)}
      {[...Array(8)].map((_, i) => <circle key={"d" + i} cy="-47" r="1.8" fill={color} stroke="none" transform={`rotate(${i * 45 + 22.5})`} />)}
      <circle r="9" /><circle r="3" fill={color} />
    </svg>
  );
}
export const LangSwitch = ({ lang, setLang }) => (
  <div className="lang" role="group" aria-label={useT()("lang")}>
    <Languages size={15} aria-hidden="true" />
    {LANGS.map(([k, l]) => <button key={k} lang={k} className={lang === k ? "on" : ""} aria-pressed={lang === k} onClick={() => setLang(k)}>{l}</button>)}
  </div>
);
export const Title = ({ children, right }) => (
  <div className="title"><span className="mark" /><h2>{children}</h2>{right}</div>
);
export const Stat = ({ label, value, sub, accent, icon: Icon }) => (
  <div className="stat" style={{ "--a": accent }}>
    <div className="stat-top"><span>{label}</span>{Icon && <i className="stat-ic"><Icon size={16} /></i>}</div>
    <b>{value}</b>{sub && <small>{sub}</small>}
  </div>
);
export const Tag = ({ tone = "", children }) => <span className={`tag ${tone}`}>{children}</span>;
const REGION_TONE = { urban: "", industrial: "gold", rural: "green", hilly: "maroon" };
export const Region = ({ v }) => {
  const t = useT();
  return v ? <Tag tone={REGION_TONE[v]}>{t(`region.${v}`)}</Tag> : null;
};
const STATUS_TONE = { on_duty: "green", on_road: "green", in_progress: "gold", completed: "green", cancelled: "red" };
export const Status = ({ v }) => <Tag tone={STATUS_TONE[v] || ""}>{useT()(`status.${v}`)}</Tag>;
