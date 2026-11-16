import { useEffect, useState } from "react";
import { Bell, BellRing, Inbox, MessageSquare, X } from "lucide-react";
import { useT, noteText } from "../i18n";

const TOAST_MS = 2000;

export default function Notifications({ notes, onRead, onToasted }) {
  const t = useT();
  const [open, setOpen] = useState(false);
  const [fresh, setFresh] = useState([]); // ids that were unread when the panel was opened
  const [toast, setToast] = useState(null);
  const unread = notes.filter((n) => !n.read).length;

  // Pop the newest note that hasn't been shown yet, then mark the batch as toasted.
  useEffect(() => {
    const next = notes.find((n) => !n.toasted);
    if (!next) return;
    const h = setTimeout(() => { setToast(next); onToasted(); }, 250);
    return () => clearTimeout(h);
  }, [notes, onToasted]);

  useEffect(() => {
    if (!toast) return;
    const h = setTimeout(() => setToast(null), TOAST_MS);
    return () => clearTimeout(h);
  }, [toast]);

  const toggle = () => {
    if (!open) { setFresh(notes.filter((n) => !n.read).map((n) => n.id)); onRead(); setToast(null); }
    setOpen(!open);
  };

  return (
    <div className="bell-wrap">
      <button className={`icon-btn bell ${unread ? "has" : ""}`} aria-label={t("notif.open")} aria-expanded={open} onClick={toggle}>
        <Bell size={19} />
        {unread > 0 && <span className="badge">{unread}</span>}
      </button>

      {open && (<>
        <div className="scrim clear" onClick={() => setOpen(false)} />
        <div className="pop" role="dialog" aria-label={t("notif.title")}>
          <div className="pop-head"><b>{t("notif.title")}</b>
            <button className="icon-btn sm" onClick={() => setOpen(false)} aria-label={t("close")}><X size={16} /></button></div>
          {notes.length ? (
            <ul className="pop-list">{notes.map((n) => (
              <li key={n.id} className={fresh.includes(n.id) ? "new" : ""}>
                <span className="pop-ic"><MessageSquare size={15} /></span>
                <div><small>{t("notif.from")} · {n.t}</small><p>{noteText(n, t)}</p></div>
              </li>
            ))}</ul>
          ) : <div className="pop-empty"><Inbox size={22} /><p>{t("notif.empty")}</p></div>}
        </div>
      </>)}

      {toast && (
        <div className="toast" role="status" key={toast.id}>
          <span className="toast-ic"><BellRing size={18} /></span>
          <div><small>{t("notif.new")} · {toast.t}</small><p>{noteText(toast, t)}</p></div>
          <i className="toast-timer" style={{ animationDuration: `${TOAST_MS}ms` }} />
        </div>
      )}
    </div>
  );
}
