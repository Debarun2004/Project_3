import { Search, X } from "lucide-react";
import { useT } from "../i18n";

// Search box plus status chips (each with its count) that sit above a register table.
export default function TableTools({ query, setQuery, filters, value, setValue, placeholder }) {
  const t = useT();
  return (
    <div className="tools">
      <label className="search">
        <Search size={15} aria-hidden="true" />
        <input type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder={placeholder} aria-label={placeholder} />
        {query && <button type="button" className="icon-btn sm" onClick={() => setQuery("")} aria-label={t("clear")}><X size={14} /></button>}
      </label>
      <div className="chips filter" role="group" aria-label={t("th.status")}>
        {filters.map(([k, label, n]) => (
          <button key={k} type="button" className={value === k ? "on" : ""} aria-pressed={value === k} onClick={() => setValue(k)}>
            {label}<span className="n">{n}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
