import { useEffect, useState } from "react";
import { Eye, EyeOff, KeyRound, LoaderCircle, LogIn, ShieldCheck, Truck, TriangleAlert } from "lucide-react";
import { getDrivers } from "../api";
import { ADMIN, DRIVER_PASSWORD, authenticate } from "../auth";
import { Motif, LangSwitch } from "../components/ui";
import { useT } from "../i18n";

// Placeholder: drop the real clip into public/ under this name (or change the path).
const BG_VIDEO = "/login-bg.mp4";
const ROLES = [["admin", ShieldCheck], ["driver", Truck]];
const still = typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

export default function Login({ onLogin, lang, setLang }) {
  const t = useT();
  const [role, setRole] = useState("admin");
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [show, setShow] = useState(false);
  const [error, setError] = useState("");
  const [caps, setCaps] = useState(false);
  const [busy, setBusy] = useState(false);
  const isAdmin = role === "admin";
  // The driver hint is the phone of the first on-duty driver in the backend, so it is missing while the backend is down.
  const [phone, setPhone] = useState("");
  useEffect(() => {
    let live = true;
    getDrivers().then((ds) => live && setPhone((ds.find((d) => d.status === "on_duty") ?? ds[0])?.phone ?? ""), () => {});
    return () => { live = false; };
  }, []);
  const demo = isAdmin ? ADMIN : phone ? { login: phone, password: DRIVER_PASSWORD } : null;

  const pickRole = (r) => { setRole(r); setLogin(""); setPassword(""); setError(""); };
  const fillDemo = () => { setLogin(demo.login); setPassword(demo.password); setError(""); };
  const submit = (e) => {
    e.preventDefault();
    if (busy) return;
    if (!login.trim() || !password) return setError(t("auth.empty"));
    setBusy(true);
    authenticate(role, login, password).then(
      (acc) => { setBusy(false); acc ? onLogin(acc) : setError(t("auth.error")); },
      () => { setBusy(false); setError(t("auth.offline")); },
    );
  };

  return (
    <div className="auth">
      <video className="auth-video" src={BG_VIDEO} autoPlay={!still} muted loop playsInline preload="auto" aria-hidden="true" />
      <div className="auth-shade" />
      <div className="auth-lang"><LangSwitch {...{ lang, setLang }} /></div>

      <form className="auth-card" onSubmit={submit} noValidate>
        <div className="auth-brand">
          <Motif size={44} color="var(--saffron)" sw={2} />
          <div><h1>{t("brand")}</h1><small>{t("brandSub")}</small></div>
        </div>

        <h2>{t("auth.title")}</h2>
        <p className="auth-sub">{t("auth.sub")}</p>

        <div className="switch auth-roles" role="group" aria-label={t("auth.role")}>
          {ROLES.map(([k, Icon]) => (
            <button key={k} type="button" className={role === k ? "on" : ""} aria-pressed={role === k} onClick={() => pickRole(k)}>
              <Icon size={15} />{t(`role.${k}`)}
            </button>
          ))}
        </div>

        <label className="field">
          <span>{isAdmin ? t("auth.email") : t("auth.phone")}</span>
          <input type={isAdmin ? "text" : "tel"} autoComplete="username" value={login} placeholder={isAdmin ? t("auth.namePh") : t("auth.phonePh")}
            onChange={(e) => { setLogin(e.target.value); setError(""); }} autoFocus />
        </label>

        <label className="field">
          <span>{t("auth.password")}</span>
          <span className="pw">
            <input type={show ? "text" : "password"} autoComplete="current-password" value={password}
              onChange={(e) => { setPassword(e.target.value); setError(""); }}
              onKeyUp={(e) => setCaps(e.getModifierState?.("CapsLock"))} onBlur={() => setCaps(false)} />
            <button type="button" className="icon-btn sm" onClick={() => setShow(!show)} aria-label={show ? t("auth.hide") : t("auth.show")}>
              {show ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </span>
          {caps && <small className="caps"><TriangleAlert size={13} />{t("auth.capsLock")}</small>}
        </label>

        {error && <p className="auth-error" role="alert">{error}</p>}

        <button className="btn block" type="submit" disabled={busy}>
          {busy ? <><LoaderCircle size={16} className="spin" />{t("auth.signing")}</> : <><LogIn size={16} />{t("auth.submit")}</>}
        </button>

        {demo && (
          <div className="auth-demo">
            <span>{t("auth.demo")} <code>{demo.login}</code> · <code>{demo.password}</code></span>
            <button type="button" className="link-btn" onClick={fillDemo}><KeyRound size={13} />{t("auth.fillDemo")}</button>
          </div>
        )}
      </form>
    </div>
  );
}
