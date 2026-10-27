// cuentas-admin@v1 · r9 · direction B «Guirnalda»: a balloon garland strung across the venue ceiling is the stage and,
// on signed-in pages, the navigation; every screen is a placard that drops in on two ribbons and settles with an
// elastic pendulum swing. Real shadcn/Base UI + Animate UI components, restyled; Motion for the springs.
import * as React from "react";
import "@fontsource-variable/syne/index.css";
import "@fontsource-variable/manrope/index.css";
import "@fontsource-variable/jetbrains-mono/index.css";
import { motion } from "motion/react";
import { Check, Copy, Link2, Lock, LogOut, MoreHorizontal, Plus, RotateCcw, Search, ShieldAlert, UserPlus, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Field, FieldDescription, FieldError, FieldLabel } from "@/components/ui/field";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { CopyButton, CopyButtonIcon } from "@animate-ui/react/primitives/buttons/copy";
import { CountingNumber } from "@animate-ui/react/primitives/texts/counting-number";
import { mountMockup, useMockup } from "@kit/mockup";
import { useMotionProfile } from "@kit/motion";

/* ───────────────────────── mock data (illustrative; one source for every count) ───────────────────────── */

type Account = {
  id: string; name: string; email: string; company: string; role: string;
  status: "Activa" | "Invitada" | "Desactivada"; last: string; work: number; admin?: boolean;
};

const ACCOUNTS: Account[] = [
  { id: "a1", name: "David Torres", email: "davidt@sempertex.com", company: "Sempertex", role: "Administrador", status: "Activa", last: "Hoy, 09:12", work: 4, admin: true },
  { id: "a2", name: "Laura Gómez", email: "laura.gomez@sempertex.com", company: "Sempertex", role: "Empleado interno", status: "Activa", last: "Ayer, 17:40", work: 2 },
  { id: "a3", name: "Andrés Ocampo", email: "andres@globosyeventos.com", company: "Globos & Eventos", role: "Usuario · Plan 3", status: "Activa", last: "24 oct, 16:05", work: 3 },
  { id: "a4", name: "Camila Restrepo", email: "camila@fiestasbrillo.co", company: "Fiestas Brillo", role: "Usuario · Plan 2", status: "Invitada", last: "Aún no entra", work: 0 },
  { id: "a5", name: "Julián Pardo", email: "julian@eventosaurora.com", company: "", role: "Revisión de costos", status: "Activa", last: "25 oct, 10:48", work: 0 },
  { id: "a6", name: "Mariana Ríos", email: "mariana.rios@decoarte.co", company: "DecoArte", role: "Usuario · Plan 1", status: "Desactivada", last: "2 oct, 11:20", work: 0 },
];

const GROUPS: { tool: string; perms: { id: string; label: string }[] }[] = [
  { tool: "Chat asistido", perms: [{ id: "chat", label: "Usar el chat asistido" }] },
  { tool: "Contador de globos", perms: [{ id: "contador", label: "Usar el contador de globos" }] },
  { tool: "Catálogo", perms: [{ id: "catalogo", label: "Ver el catálogo" }, { id: "textos-en", label: "Corregir textos en inglés" }] },
  { tool: "Costos", perms: [{ id: "costos", label: "Usar la calculadora de costos" }] },
  { tool: "Decoraciones listas", perms: [{ id: "decoraciones", label: "Explorar decoraciones listas" }] },
  { tool: "Taller 3D", perms: [{ id: "taller", label: "Usar el Taller 3D: IA de escena, planos, hoja de montaje y exportar" }, { id: "propios", label: "Guardar proyectos y decoraciones propios" }] },
  { tool: "Equipo interno", perms: [{ id: "todos", label: "Ver los proyectos de todos" }, { id: "gasto", label: "Ver el consumo de IA" }, { id: "internas", label: "Usar herramientas internas" }] },
  { tool: "Administración", perms: [{ id: "cuentas", label: "Administrar cuentas" }, { id: "roles", label: "Administrar roles" }] },
];

const P1 = ["chat", "contador", "catalogo"];
const P2 = [...P1, "costos", "decoraciones"];
const P3 = [...P2, "taller", "propios"];
const EMP = [...P3, "todos", "gasto", "internas"];
type Role = { name: string; system: boolean; perms: string[] };
const ROLES: Role[] = [
  { name: "Usuario · Plan 1", system: true, perms: P1 },
  { name: "Usuario · Plan 2", system: true, perms: P2 },
  { name: "Usuario · Plan 3", system: true, perms: P3 },
  { name: "Empleado interno", system: true, perms: EMP },
  { name: "Administrador", system: true, perms: [...EMP, "cuentas", "roles", "textos-en"] },
  { name: "Revisión de costos", system: false, perms: ["costos", "gasto"] },
];
const usersOf = (role: string) => ACCOUNTS.filter((a) => a.role === role).length;
const TOOLS_OF: Record<string, string> = {
  "Usuario · Plan 1": "Chat asistido, contador de globos y catálogo.",
  "Usuario · Plan 2": "Plan 1 más calculadora de costos y decoraciones listas. Sin Taller 3D.",
  "Usuario · Plan 3": "Plan 2 más el Taller 3D y guardar proyectos y decoraciones propios.",
  "Empleado interno": "Plan 3 más proyectos de todos, consumo de IA y herramientas internas.",
  "Administrador": "Todo, incluidas cuentas, roles y corrección de textos en inglés.",
  "Revisión de costos": "Calculadora de costos y consumo de IA.",
};

const NOTICE = {
  es: {
    title: "Aviso de tratamiento de datos personales",
    parts: ["", "[RAZÓN SOCIAL DE SEMPERTEX]", " tratará tus datos personales —nombre, correo, empresa (si la indicas), el rol y el plan que te asignen, y las fechas de invitación, activación y último acceso— para darte acceso a Pictures durante el piloto, administrar tu cuenta y medir el uso de las herramientas, incluido el consumo de inteligencia artificial. Los proyectos y decoraciones que guardes quedan asociados a tu cuenta. Puedes conocer, actualizar, rectificar o pedir la supresión de tus datos, y revocar esta autorización, escribiendo a ", "[CORREO PARA DERECHOS]", ". La política de tratamiento de datos está en ", "[URL DE LA POLÍTICA]", ". Al activar tu cuenta declaras que leíste este aviso y autorizas el tratamiento descrito, conforme a la Ley 1581 de 2012."],
    accept: "Leí el aviso y autorizo el tratamiento de mis datos.",
  },
  en: {
    title: "Personal data notice",
    parts: ["", "[SEMPERTEX LEGAL NAME]", " will process your personal data —name, email, company (if you provide it), the role and plan assigned to you, and the dates of invitation, activation and last access— to give you access to Pictures during the pilot, manage your account and measure the use of the tools, including artificial-intelligence usage. The projects and decorations you save are linked to your account. You can access, update, correct or request deletion of your data, and withdraw this authorization, by writing to ", "[RIGHTS CONTACT EMAIL]", ". The data-processing policy is at ", "[POLICY URL]", ". By activating your account you confirm that you have read this notice and authorize the processing described, under Colombian Law 1581 of 2012."],
    accept: "I have read the notice and authorize the processing of my data.",
  },
} as const;

/* ───────────────────────── motion: one elastic grammar, scaled by profile ───────────────────────── */

const KIN = {
  expressive: { stiffness: 170, damping: 9, drop: 96, tilt: 5, wob: 3.2, stagger: 0.07 },
  natural: { stiffness: 260, damping: 18, drop: 44, tilt: 2, wob: 1.6, stagger: 0.045 },
  subtle: { stiffness: 420, damping: 38, drop: 14, tilt: 0.6, wob: 0.6, stagger: 0.02 },
} as const;

function useKin() {
  const mp = useMotionProfile();
  return { ...KIN[mp.profile], reduced: mp.reduced, profile: mp.profile };
}

/** A screen hangs from the garland: it drops on two ribbons, swings and settles; an error makes it wobble. */
function Placard({ wide, label, children }: { wide?: boolean; label: string; children: React.ReactNode }) {
  const k = useKin();
  const { state } = useMockup();
  const spring = { type: "spring" as const, stiffness: k.stiffness, damping: k.damping, mass: 1 };
  return (
    <motion.section
      aria-label={label}
      className={`placard ${wide ? "placard--wide" : ""}`}
      initial={k.reduced ? false : { y: -k.drop, rotate: -k.tilt }}
      animate={{ y: 0, rotate: 0 }}
      transition={spring}
    >
      <span className="ribbon ribbon--l" aria-hidden="true" />
      <span className="ribbon ribbon--r" aria-hidden="true" />
      <motion.div
        className="placard-body"
        initial={false}
        animate={state === "error" && !k.reduced ? { rotate: [0, -k.wob, k.wob * 0.66, -k.wob * 0.33, 0] } : { rotate: 0 }}
        transition={{ duration: 0.9, delay: 0.45, ease: [0.36, 0, 0.2, 1] }}
      >
        {children}
      </motion.div>
    </motion.section>
  );
}

/** Children rise into place one after the other, after the placard has swung in. */
function Rise({ i, children, className }: { i: number; children: React.ReactNode; className?: string }) {
  const k = useKin();
  return (
    <motion.div
      className={className}
      initial={k.reduced ? false : { y: 14 }}
      animate={{ y: 0 }}
      transition={{ type: "spring", stiffness: k.stiffness + 60, damping: k.damping + 4, delay: 0.18 + i * k.stagger }}
    >
      {children}
    </motion.div>
  );
}

/* ───────────────────────── stage: garland, balloons, navigation ───────────────────────── */

function Balloon({ tone, size = 56, className = "" }: { tone: "cobalt" | "tangerine" | "pearl"; size?: number; className?: string }) {
  return <span className={`balloon balloon--${tone} ${className}`} style={{ "--s": `${size}px` } as React.CSSProperties} aria-hidden="true" />;
}

const SIGNED_IN = ["mi-cuenta", "cuentas", "roles", "aviso"];

function AccountMenu() {
  const m = useMockup();
  const [open, setOpen] = React.useState(m.scene === "menu-cuenta");
  React.useEffect(() => setOpen(m.scene === "menu-cuenta"), [m.scene]);
  const denied = m.state === "sin-permiso";
  const person = denied ? { name: "Laura Gómez", role: "Empleado interno", ini: "LG" } : { name: "David Torres", role: "Administrador", ini: "DT" };
  return (
    <DropdownMenu open={open} onOpenChange={(o) => { setOpen(o); if (!o && m.scene === "menu-cuenta") m.set("scene", ""); }}>
      <DropdownMenuTrigger render={<button type="button" className="foil-trigger" aria-current={m.view === "mi-cuenta" ? "page" : undefined} />}>
        <span className="foil" aria-hidden="true">{person.ini}</span>
        <span className="foil-tether" aria-hidden="true" />
        <span className="foil-text"><span className="foil-name">{person.name}</span><span className="foil-role">{person.role}</span></span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={10} className="pl-menu">
        <DropdownMenuGroup>
          <DropdownMenuLabel className="pl-menu-head"><strong>{person.name}</strong><span>{person.role}</span></DropdownMenuLabel>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem className="pl-menu-item" onClick={() => { m.set("scene", ""); m.set("view", "mi-cuenta"); }}><UserRound />Mi cuenta</DropdownMenuItem>
        <DropdownMenuItem className="pl-menu-item" onClick={() => { m.set("scene", ""); m.set("view", "ingresar"); }}><LogOut />Cerrar sesión</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function Garland() {
  const m = useMockup();
  const k = useKin();
  const signed = SIGNED_IN.includes(m.view);
  const showNav = signed && m.view !== "aviso" && m.state !== "sin-permiso";
  const items = [{ id: "cuentas", label: "Cuentas", tone: "cobalt" as const }, { id: "roles", label: "Roles", tone: "tangerine" as const }];
  return (
    <header className={`garland-band ${signed ? "is-signed" : "is-access"}`}>
      <svg className="garland-svg" viewBox="0 0 1200 120" preserveAspectRatio="none" aria-hidden="true">
        <path className="garland-string" pathLength={1} d="M-10 22 C 300 118, 900 118, 1210 22" />
      </svg>
      <div className="cluster cluster--l" aria-hidden="true">
        <Balloon tone="cobalt" size={58} className="bob" /><Balloon tone="tangerine" size={44} className="bob bob--2" /><Balloon tone="pearl" size={34} className="bob bob--3" />
      </div>
      <div className="cluster cluster--r" aria-hidden="true">
        <Balloon tone="pearl" size={36} className="bob bob--2" /><Balloon tone="tangerine" size={52} className="bob" /><Balloon tone="cobalt" size={40} className="bob bob--3" />
      </div>
      {signed && (
        <div className="band-row">
          <span className="brand"><span className="brand-word">Pictures</span><span className="brand-sub">Administración · piloto</span></span>
          {showNav ? (
            <nav className="garland-nav" aria-label="Administración">
              {items.map((it, i) => (
                <motion.button
                  key={it.id}
                  type="button"
                  className="nav-balloon"
                  aria-current={m.view === it.id ? "page" : undefined}
                  onClick={() => m.set("view", it.id)}
                  initial={k.reduced ? false : { y: -60 }}
                  animate={{ y: 0 }}
                  transition={{ type: "spring", stiffness: k.stiffness, damping: k.damping, delay: 0.1 + i * k.stagger * 1.6 }}
                >
                  <Balloon tone={it.tone} size={48} />
                  <span className="nav-tether" aria-hidden="true" />
                  <span className="nav-label">{it.label}</span>
                </motion.button>
              ))}
            </nav>
          ) : <span className="band-gap" />}
          <AccountMenu />
        </div>
      )}
    </header>
  );
}

function Drift() {
  const ref = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    const on = () => document.documentElement.toggleAttribute("data-tab-hidden", document.hidden);
    document.addEventListener("visibilitychange", on);
    const io = new IntersectionObserver(([e]) => ref.current?.toggleAttribute("data-offscreen", !e.isIntersecting));
    if (ref.current) io.observe(ref.current);
    return () => { document.removeEventListener("visibilitychange", on); io.disconnect(); };
  }, []);
  return (
    <div className="drift-layer" ref={ref} aria-hidden="true">
      {["d1", "d2", "d3", "d4", "d5"].map((d, i) => <Balloon key={d} tone={i % 2 ? "tangerine" : "cobalt"} size={[26, 18, 30, 22, 16][i]} className={`drift ${d}`} />)}
    </div>
  );
}

/* ───────────────────────── small building blocks ───────────────────────── */

function TextField({ id, label, type = "text", value, hint, error, disabled, autoComplete, onChange, mono }: {
  id: string; label: string; type?: string; value?: string; hint?: string; error?: string; disabled?: boolean;
  autoComplete?: string; onChange?: (v: string) => void; mono?: boolean;
}) {
  return (
    <Field className="pl-field" data-invalid={error ? true : undefined}>
      <FieldLabel htmlFor={id} className="pl-label">{label}</FieldLabel>
      <Input
        id={id} type={type} className={`pl-input ${mono ? "mono" : ""}`} disabled={disabled} autoComplete={autoComplete}
        aria-invalid={error ? true : undefined} aria-describedby={hint || error ? `${id}-help` : undefined}
        {...(onChange ? { value: value ?? "", onChange: (e: React.ChangeEvent<HTMLInputElement>) => onChange(e.target.value) } : { defaultValue: value })}
      />
      {error ? <FieldError id={`${id}-help`} className="pl-error">{error}</FieldError>
        : hint ? <FieldDescription id={`${id}-help`} className="pl-hint">{hint}</FieldDescription> : null}
    </Field>
  );
}

function Busy({ label }: { label: string }) {
  return <><span className="inflate" aria-hidden="true" />{label}</>;
}

function Note({ kind, title, children }: { kind: "error" | "ok" | "warn" | "info"; title: string; children?: React.ReactNode }) {
  return (
    <div className={`note note--${kind}`} role={kind === "error" ? "alert" : "status"}>
      <strong>{title}</strong>
      {children && <span>{children}</span>}
    </div>
  );
}

function NotApplicable({ what }: { what: string }) {
  return <p className="na-note">Mockup: el estado elegido no aplica a {what}; se muestra la vista normal.</p>;
}

function Released() {
  return <Balloon tone="tangerine" size={40} className="release" />;
}

/* ───────────────────────── access screens ───────────────────────── */

function PlacardHead({ kicker, title }: { kicker: string; title: string }) {
  return (
    <div className="placard-head">
      <span className="kicker">{kicker}</span>
      <h1 className="pl-title">{title}</h1>
    </div>
  );
}

function Ingresar() {
  const { state, set } = useMockup();
  const applies = ["normal", "cargando", "error", "exito"].includes(state);
  const busy = state === "cargando";
  if (state === "exito") {
    return (
      <Placard label="Iniciar sesión">
        <Released />
        <PlacardHead kicker="Pictures · Sempertex" title="Adentro" />
        <Rise i={0}><Note kind="ok" title="Sesión iniciada como Andrés Ocampo.">Volvemos a la página que pediste: Calculadora de costos. Sin una página pedida, abrimos la primera herramienta de tu rol.</Note></Rise>
      </Placard>
    );
  }
  return (
    <Placard label="Iniciar sesión">
      <PlacardHead kicker="Pictures · Sempertex" title="Iniciar sesión" />
      {!applies && <NotApplicable what="Iniciar sesión" />}
      {state === "error" && (
        <Rise i={0}><Note kind="error" title="No pudimos iniciar tu sesión.">Revisa el correo y la contraseña. Después de varios intentos fallidos tendrás que esperar 15 minutos para volver a intentarlo.</Note></Rise>
      )}
      <form className="pl-form" onSubmit={(e) => { e.preventDefault(); set("state", "cargando"); }} aria-busy={busy}>
        <Rise i={1}><TextField id="login-email" label="Correo" type="email" autoComplete="email" value="andres@globosyeventos.com" disabled={busy} /></Rise>
        <Rise i={2}><TextField id="login-password" label="Contraseña" type="password" autoComplete="current-password" value="guirnalda-24" disabled={busy} /></Rise>
        <Rise i={3}>
          <Button type="submit" className="pl-btn pl-btn--primary pl-btn--block" disabled={busy}>{busy ? <Busy label="Entrando…" /> : "Entrar"}</Button>
        </Rise>
      </form>
      <Rise i={4} className="placard-foot">
        <p><strong>¿Olvidaste tu contraseña?</strong> Pide a tu administrador un enlace para restablecerla.</p>
        <p>Pictures es solo por invitación; no hay registro abierto.</p>
      </Rise>
    </Placard>
  );
}

function NoticeBlock({ version, error }: { version: number; error?: boolean }) {
  const [lang, setLang] = React.useState<"es" | "en">("es");
  const [accepted, setAccepted] = React.useState(false);
  const t = NOTICE[lang];
  return (
    <div className="notice">
      <div className="notice-top">
        <h2 className="notice-title">{t.title} <span className="notice-version">v{version}</span></h2>
        <label className="lang-pick" htmlFor="notice-lang">
          <span>Idioma del aviso</span>
          <select id="notice-lang" className="pl-select pl-select--sm" value={lang} onChange={(e) => setLang(e.target.value as "es" | "en")}>
            <option value="es">Español (de tu navegador)</option>
            <option value="en">English</option>
          </select>
        </label>
      </div>
      <div className="notice-text" tabIndex={0} role="region" aria-label={t.title}>
        <p>{t.parts.map((p, i) => (i % 2 ? <mark key={i} className="legal-ph" title="Pendiente de revisión legal">{p}</mark> : <React.Fragment key={i}>{p}</React.Fragment>))}</p>
      </div>
      <p className="legal-flag"><span className="legal-dot" aria-hidden="true" />Los textos entre corchetes siguen pendientes de revisión legal de Sempertex.</p>
      <div className={`accept-line ${error ? "is-invalid" : ""}`}>
        <Checkbox id="accept-notice" className="pl-check" checked={accepted} onCheckedChange={(v) => setAccepted(v === true)} aria-invalid={error ? true : undefined} />
        <label htmlFor="accept-notice">{t.accept}</label>
      </div>
      {error && <p className="pl-error" role="alert">Marca la casilla para aceptar el aviso; sin aceptarlo no se puede continuar.</p>}
      <NoticeSubmit accepted={accepted} />
    </div>
  );
}

const SubmitCtx = React.createContext<{ label: string; busy: boolean; onSubmit: () => void }>({ label: "", busy: false, onSubmit: () => undefined });
function NoticeSubmit({ accepted }: { accepted: boolean }) {
  const s = React.useContext(SubmitCtx);
  return (
    <div className="submit-row">
      <Button type="button" className="pl-btn pl-btn--primary pl-btn--block" disabled={!accepted || s.busy} onClick={s.onSubmit}>{s.busy ? <Busy label="Guardando…" /> : s.label}</Button>
      {!accepted && !s.busy && <p className="pl-hint">El botón se habilita al marcar la casilla.</p>}
    </div>
  );
}

function InvalidLink() {
  const { set } = useMockup();
  return (
    <>
      <Rise i={0}><Note kind="warn" title="Este enlace ya no sirve.">Pudo usarse antes o vencer. Pide a tu administrador un enlace nuevo.</Note></Rise>
      <Rise i={1}><Button type="button" className="pl-btn pl-btn--quiet" onClick={() => set("view", "ingresar")}>Ir a iniciar sesión</Button></Rise>
    </>
  );
}

function Activar() {
  const { state, set } = useMockup();
  const applies = ["normal", "cargando", "error", "exito", "enlace-invalido"].includes(state);
  if (state === "enlace-invalido") return <Placard label="Activar cuenta"><PlacardHead kicker="Invitación" title="Activa tu cuenta" /><InvalidLink /></Placard>;
  if (state === "exito") {
    return (
      <Placard label="Activar cuenta">
        <Released />
        <PlacardHead kicker="Invitación" title="Cuenta activa" />
        <Rise i={0}><Note kind="ok" title="Listo, Camila. Ya tienes sesión iniciada.">Te llevamos a Chat asistido, la primera herramienta de tu rol. Guardamos que aceptaste el aviso v1 el 27 oct 2026.</Note></Rise>
      </Placard>
    );
  }
  const checking = state === "cargando";
  const error = state === "error";
  return (
    <Placard wide label="Activar cuenta">
      <PlacardHead kicker="Invitación · válida 7 días" title="Activa tu cuenta" />
      {!applies && <NotApplicable what="Activar cuenta" />}
      <div className="split">
        <div className="split-col">
          {checking ? (
            <div className="who" aria-busy="true" aria-label="Comprobando la invitación"><Skeleton className="sk sk--lg" /><Skeleton className="sk" /><Skeleton className="sk sk--sm" /></div>
          ) : (
            <Rise i={0} className="who">
              <span className="who-name">Camila Restrepo</span>
              <span className="who-mail">camila@fiestasbrillo.co</span>
              <span className="who-role">Usuario · Plan 2 · Fiestas Brillo</span>
            </Rise>
          )}
          <Rise i={1}><TextField id="act-pass" label="Contraseña" type="password" autoComplete="new-password" value={error ? "globo12" : ""} hint="Al menos 8 caracteres." disabled={checking} error={error ? "Las contraseñas no coinciden." : undefined} /></Rise>
          <Rise i={2}><TextField id="act-pass2" label="Repite la contraseña" type="password" autoComplete="new-password" value={error ? "globo123" : ""} disabled={checking} /></Rise>
        </div>
        <Rise i={3} className="split-col">
          <SubmitCtx.Provider value={{ label: "Activar cuenta", busy: checking, onSubmit: () => set("state", "exito") }}>
            <NoticeBlock version={1} error={error} />
          </SubmitCtx.Provider>
        </Rise>
      </div>
    </Placard>
  );
}

function Restablecer() {
  const { state, set } = useMockup();
  const applies = ["normal", "cargando", "error", "exito", "enlace-invalido"].includes(state);
  if (state === "enlace-invalido") return <Placard label="Restablecer contraseña"><PlacardHead kicker="Enlace de restablecimiento" title="Nueva contraseña" /><InvalidLink /></Placard>;
  if (state === "exito") {
    return (
      <Placard label="Restablecer contraseña">
        <Released />
        <PlacardHead kicker="Enlace de restablecimiento" title="Contraseña nueva" />
        <Rise i={0}><Note kind="ok" title="Guardamos tu nueva contraseña.">Ahora inicia sesión con ella. Tus otras sesiones se cerraron.</Note></Rise>
        <Rise i={1}><Button type="button" className="pl-btn pl-btn--primary" onClick={() => set("view", "ingresar")}>Iniciar sesión</Button></Rise>
      </Placard>
    );
  }
  const busy = state === "cargando";
  const error = state === "error";
  return (
    <Placard label="Restablecer contraseña">
      <PlacardHead kicker="Enlace de restablecimiento · 24 horas" title="Nueva contraseña" />
      {!applies && <NotApplicable what="Restablecer contraseña" />}
      <Rise i={0}><p className="lede">Para <strong>laura.gomez@sempertex.com</strong>. El enlace sirve una sola vez.</p></Rise>
      <form className="pl-form" onSubmit={(e) => { e.preventDefault(); set("state", "exito"); }} aria-busy={busy}>
        <Rise i={1}><TextField id="rst-pass" label="Nueva contraseña" type="password" autoComplete="new-password" hint="Al menos 8 caracteres." disabled={busy} value={error ? "corta" : ""} error={error ? "Usa al menos 8 caracteres." : undefined} /></Rise>
        <Rise i={2}><TextField id="rst-pass2" label="Repite la nueva contraseña" type="password" autoComplete="new-password" disabled={busy} value={error ? "corta" : ""} /></Rise>
        <Rise i={3}><Button type="submit" className="pl-btn pl-btn--primary pl-btn--block" disabled={busy}>{busy ? <Busy label="Guardando…" /> : "Guardar contraseña"}</Button></Rise>
      </form>
    </Placard>
  );
}

function Aviso() {
  const { state, set } = useMockup();
  const applies = ["normal", "cargando", "error", "exito"].includes(state);
  if (state === "exito") {
    return (
      <Placard label="Aviso de datos">
        <Released />
        <PlacardHead kicker="Aviso de datos · versión 2" title="Gracias" />
        <Rise i={0}><Note kind="ok" title="Aceptaste la versión 2 el 27 oct 2026.">Seguimos a la página que abriste: Cuentas.</Note></Rise>
      </Placard>
    );
  }
  return (
    <Placard wide label="Aviso de datos">
      <PlacardHead kicker="Antes de seguir" title="Actualizamos el aviso" />
      {!applies && <NotApplicable what="Aviso de datos" />}
      <Rise i={0}><p className="lede">Para abrir cualquier página de Pictures necesitas aceptar la versión 2. Aceptaste la versión 1 el 26 oct 2026. El texto de la versión 2 es de muestra: hoy solo existe la v1.</p></Rise>
      {state === "error" && <Rise i={1}><Note kind="error" title="No pudimos guardar tu aceptación.">Revisa la conexión y vuelve a intentarlo; seguirás aquí hasta que se guarde.</Note></Rise>}
      <Rise i={2}>
        <SubmitCtx.Provider value={{ label: "Aceptar y continuar", busy: state === "cargando", onSubmit: () => set("state", "exito") }}>
          <NoticeBlock version={2} />
        </SubmitCtx.Provider>
      </Rise>
      <Rise i={3} className="placard-foot"><p>¿Prefieres no aceptar ahora? Usa <strong>Cerrar sesión</strong> en el menú de tu cuenta, arriba a la derecha.</p></Rise>
    </Placard>
  );
}

/* ───────────────────────── signed-in screens ───────────────────────── */

function Denied({ what }: { what: string }) {
  const { set } = useMockup();
  return (
    <Placard label={what}>
      <PlacardHead kicker="Sin permiso" title={what} />
      <Rise i={0}><Note kind="warn" title="Tu rol no incluye esta página.">Laura Gómez · Empleado interno. Administrar cuentas y roles es solo para quien tenga esos permisos; el servidor responde 403 y no se muestra ningún dato.</Note></Rise>
      <Rise i={1}><Button type="button" className="pl-btn pl-btn--quiet" onClick={() => set("view", "mi-cuenta")}>Ir a Mi cuenta</Button></Rise>
    </Placard>
  );
}

function MiCuenta() {
  const { state } = useMockup();
  const applies = ["normal", "cargando", "error", "exito"].includes(state);
  const busy = state === "cargando";
  return (
    <Placard wide label="Mi cuenta">
      <PlacardHead kicker="Tu cuenta" title="Mi cuenta" />
      {!applies && <NotApplicable what="Mi cuenta" />}
      <div className="split">
        <Rise i={0} className="split-col">
          <dl className="facts">
            <div><dt>Nombre</dt><dd>David Torres</dd></div>
            <div><dt>Correo</dt><dd>davidt@sempertex.com</dd></div>
            <div><dt>Empresa</dt><dd>Sempertex</dd></div>
            <div><dt>Rol</dt><dd>Administrador</dd></div>
            <div><dt>Aviso de datos</dt><dd>v1, aceptado el 26 oct 2026</dd></div>
          </dl>
          <p className="pl-hint">Tu nombre, correo y rol los cambia un administrador.</p>
        </Rise>
        <Rise i={1} className="split-col">
          <h2 className="pl-subtitle">Cambiar contraseña</h2>
          {state === "exito" && <Note kind="ok" title="Contraseña cambiada.">Cerramos tus sesiones en otros navegadores; este sigue dentro con una sesión nueva.</Note>}
          <form className="pl-form" onSubmit={(e) => e.preventDefault()} aria-busy={busy}>
            <TextField id="me-current" label="Contraseña actual" type="password" autoComplete="current-password" disabled={busy} value={state === "error" ? "globos-viejos" : ""} error={state === "error" ? "La contraseña actual no es correcta." : undefined} />
            <TextField id="me-new" label="Nueva contraseña" type="password" autoComplete="new-password" hint="Al menos 8 caracteres." disabled={busy} />
            <TextField id="me-new2" label="Repite la nueva contraseña" type="password" autoComplete="new-password" disabled={busy} />
            <Button type="submit" className="pl-btn pl-btn--primary" disabled={busy}>{busy ? <Busy label="Guardando…" /> : "Cambiar contraseña"}</Button>
          </form>
          <p className="pl-hint">Al cambiarla se cierran tus otras sesiones.</p>
        </Rise>
      </div>
    </Placard>
  );
}

const PICK = React.createContext<(scene: string, a?: Account) => void>(() => undefined);

function RowActions({ a }: { a: Account }) {
  const open = React.useContext(PICK);
  return (
    <DropdownMenu>
      <DropdownMenuTrigger render={<Button variant="ghost" className="pl-btn pl-btn--icon" aria-label={`Acciones para ${a.name}`} />}>
        <MoreHorizontal />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="pl-menu">
        <DropdownMenuItem className="pl-menu-item" onClick={() => open("cambiar-rol", a)}>Cambiar rol</DropdownMenuItem>
        <DropdownMenuItem className="pl-menu-item" onClick={() => open("enlace-restablecer", a)}>
          {a.status === "Invitada" ? "Generar nueva invitación" : "Generar enlace de restablecimiento"}
        </DropdownMenuItem>
        {a.status === "Desactivada"
          ? <DropdownMenuItem className="pl-menu-item" onClick={() => open("reactivar", a)}>Reactivar</DropdownMenuItem>
          : <DropdownMenuItem className="pl-menu-item" disabled={a.admin} onClick={() => open("desactivar", a)}>{a.admin ? "Desactivar (último administrador)" : "Desactivar"}</DropdownMenuItem>}
        <DropdownMenuSeparator />
        <DropdownMenuItem className="pl-menu-item pl-menu-item--danger" onClick={() => open(a.admin ? "eliminar-ultimo-admin" : a.work ? "eliminar-con-trabajo" : "eliminar", a)}>Eliminar…</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function StatusBadge({ s }: { s: Account["status"] }) {
  return <Badge className={`pl-badge pl-badge--${s === "Activa" ? "ok" : s === "Invitada" ? "invited" : "off"}`}>{s}</Badge>;
}

function Cuentas() {
  const { state, set } = useMockup();
  const open = React.useContext(PICK);
  const [q, setQ] = React.useState(state === "vacio" ? "pedro" : "");
  const [role, setRole] = React.useState("");
  const [status, setStatus] = React.useState("");
  if (state === "sin-permiso") return <Denied what="Cuentas" />;
  const applies = ["normal", "cargando", "error", "exito", "vacio"].includes(state);
  const rows = ACCOUNTS.filter((a) => (!q || `${a.name} ${a.email}`.toLowerCase().includes(q.toLowerCase())) && (!role || a.role === role) && (!status || a.status === status));
  return (
    <Placard wide label="Cuentas">
      <div className="admin-head">
        <div>
          <span className="kicker">Personas con acceso al piloto</span>
          <h1 className="pl-title pl-title--admin">Cuentas <span className="count"><CountingNumber number={ACCOUNTS.length} /></span></h1>
        </div>
        <Button type="button" className="pl-btn pl-btn--primary" onClick={() => open("invitar")}><UserPlus />Invitar persona</Button>
      </div>
      {!applies && <NotApplicable what="Cuentas" />}
      {state === "exito" && <Note kind="ok" title="Invitación creada para Camila Restrepo.">Copiaste el enlace; caduca en 7 días y sirve una sola vez.</Note>}
      <div className="toolbar" role="search">
        <label className="search" htmlFor="acc-q">
          <span className="sr-only">Buscar por nombre o correo</span>
          <Search aria-hidden="true" />
          <Input id="acc-q" className="pl-input pl-input--search" placeholder="Buscar por nombre o correo" value={q} onChange={(e) => setQ(e.target.value)} />
        </label>
        <label className="filter" htmlFor="acc-role"><span>Rol</span>
          <select id="acc-role" className="pl-select" value={role} onChange={(e) => setRole(e.target.value)}>
            <option value="">Todos</option>{ROLES.map((r) => <option key={r.name}>{r.name}</option>)}
          </select>
        </label>
        <label className="filter" htmlFor="acc-status"><span>Estado</span>
          <select id="acc-status" className="pl-select" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">Todos</option><option>Activa</option><option>Invitada</option><option>Desactivada</option>
          </select>
        </label>
      </div>
      {state === "error" ? (
        <div className="empty">
          <Note kind="error" title="No pudimos cargar las cuentas.">Revisa la conexión. Nada cambió en las cuentas.</Note>
          <Button type="button" className="pl-btn pl-btn--quiet" onClick={() => set("state", "normal")}><RotateCcw />Reintentar</Button>
        </div>
      ) : state === "cargando" ? (
        <div className="sk-list" aria-busy="true" aria-label="Cargando cuentas">
          {[0, 1, 2, 3].map((i) => <div className="sk-row" key={i}><Skeleton className="sk sk--lg" /><Skeleton className="sk" /><Skeleton className="sk sk--sm" /></div>)}
        </div>
      ) : rows.length === 0 ? (
        <div className="empty">
          <Balloon tone="pearl" size={44} className="empty-balloon" />
          <p className="empty-title">Ninguna cuenta coincide con «{q || "los filtros"}».</p>
          <p className="pl-hint">Busca por otro nombre o correo, o limpia los filtros. Si la persona aún no está, invítala.</p>
          <div className="row-gap">
            <Button type="button" className="pl-btn pl-btn--quiet" onClick={() => { setQ(""); setRole(""); setStatus(""); }}>Limpiar búsqueda</Button>
            <Button type="button" className="pl-btn pl-btn--primary" onClick={() => open("invitar")}>Invitar persona</Button>
          </div>
        </div>
      ) : (
        <Table className="acc-table">
          <TableHeader>
            <TableRow className="acc-head">
              <TableHead>Persona</TableHead><TableHead>Empresa</TableHead><TableHead>Rol</TableHead><TableHead>Estado</TableHead><TableHead>Último acceso</TableHead><TableHead><span className="sr-only">Acciones</span></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((a, i) => (
              <TableRow key={a.id} className="acc-row" style={{ "--i": i } as React.CSSProperties}>
                <TableCell className="c-person"><span className="p-name">{a.name}</span><span className="p-mail">{a.email}</span></TableCell>
                <TableCell className="c-company" data-label="Empresa">{a.company || "Sin empresa"}</TableCell>
                <TableCell className="c-role" data-label="Rol">{a.role}</TableCell>
                <TableCell className="c-status" data-label="Estado"><StatusBadge s={a.status} /></TableCell>
                <TableCell className="c-last" data-label="Último acceso">{a.last}</TableCell>
                <TableCell className="c-act"><RowActions a={a} /></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      <p className="table-foot">{state === "cargando" || state === "error" ? "Datos de muestra." : `${rows.length} de ${ACCOUNTS.length} cuentas · datos de muestra.`} Un enlace nuevo invalida los anteriores sin usar del mismo tipo.</p>
    </Placard>
  );
}

function Roles() {
  const { state } = useMockup();
  const open = React.useContext(PICK);
  const k = useKin();
  const list = state === "vacio" ? ROLES.filter((r) => r.system) : ROLES;
  const [sel, setSel] = React.useState(state === "vacio" ? 1 : 5);
  if (state === "sin-permiso") return <Denied what="Roles" />;
  const applies = ["normal", "cargando", "error", "exito", "vacio"].includes(state);
  const role = list[Math.min(sel, list.length - 1)];
  const inUse = usersOf(role.name);
  return (
    <Placard wide label="Roles">
      <div className="admin-head">
        <div>
          <span className="kicker">Un rol por persona · los planes son roles</span>
          <h1 className="pl-title pl-title--admin">Roles <span className="count"><CountingNumber number={list.length} /></span></h1>
        </div>
        <Button type="button" className="pl-btn pl-btn--primary" onClick={() => open("rol-editor")}><Plus />Crear rol</Button>
      </div>
      {!applies && <NotApplicable what="Roles" />}
      {state === "exito" && <Note kind="ok" title="Rol «Revisión de costos» guardado.">Sus 2 permisos se aplican a 1 cuenta en su próxima petición.</Note>}
      {state === "error" ? (
        <Note kind="error" title="No pudimos cargar los roles.">Revisa la conexión y vuelve a intentarlo. Ningún rol cambió.</Note>
      ) : state === "cargando" ? (
        <div className="sk-line" aria-busy="true" aria-label="Cargando roles">{[0, 1, 2, 3, 4].map((i) => <Skeleton key={i} className="sk sk--tag" />)}</div>
      ) : (
        <>
          <div className="line-wrap">
            <span className="clothesline" aria-hidden="true" />
            <div className="tags" role="tablist" aria-label="Roles">
              {list.map((r, i) => (
                <motion.button
                  key={r.name}
                  type="button"
                  role="tab"
                  id={`tab-${i}`}
                  aria-selected={i === sel}
                  aria-controls="role-panel"
                  tabIndex={i === sel ? 0 : -1}
                  className={`role-tag ${r.system ? "is-system" : "is-custom"}`}
                  onClick={() => setSel(i)}
                  onKeyDown={(e) => {
                    if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
                      const n = (i + (e.key === "ArrowRight" ? 1 : -1) + list.length) % list.length;
                      setSel(n);
                      (document.getElementById(`tab-${n}`) as HTMLElement | null)?.focus();
                    }
                  }}
                  initial={k.reduced ? false : { y: -40, rotate: -6 }}
                  animate={{ y: i === sel ? 10 : 0, rotate: 0 }}
                  transition={{ type: "spring", stiffness: k.stiffness, damping: k.damping, delay: 0.15 + i * k.stagger }}
                >
                  <span className="clip" aria-hidden="true" />
                  <span className="tag-name">{r.name}</span>
                  <span className="tag-meta">{r.system ? <><Lock aria-hidden="true" />Sistema</> : "Propio"} · {usersOf(r.name)} {usersOf(r.name) === 1 ? "cuenta" : "cuentas"}</span>
                </motion.button>
              ))}
            </div>
          </div>
          {state === "vacio" && <p className="pl-hint empty-inline">Aún no hay roles propios. Crea uno eligiendo permisos; los cinco roles del sistema no se editan.</p>}
          <div className="role-panel" id="role-panel" role="tabpanel" aria-labelledby={`tab-${sel}`}>
            <div className="role-panel-head">
              <div>
                <h2 className="pl-subtitle">{role.name}</h2>
                <p className="pl-hint">{TOOLS_OF[role.name]}</p>
              </div>
              {role.system ? (
                <span className="readonly"><Lock aria-hidden="true" />Rol del sistema: solo lectura</span>
              ) : (
                <div className="row-gap">
                  <Button type="button" className="pl-btn pl-btn--quiet" onClick={() => open("rol-editor")}>Editar</Button>
                  <Button type="button" className="pl-btn pl-btn--danger" onClick={() => open(inUse ? "rol-eliminar-en-uso" : "")}>Eliminar rol</Button>
                </div>
              )}
            </div>
            {!role.system && inUse > 0 && <p className="pl-hint">No se puede eliminar mientras {inUse} {inUse === 1 ? "cuenta lo use" : "cuentas lo usen"}: Julián Pardo.</p>}
            <div className="perm-grid">
              {GROUPS.map((g) => (
                <div className="perm-group" key={g.tool}>
                  <h3>{g.tool}</h3>
                  <ul>
                    {g.perms.map((p) => {
                      const on = role.perms.includes(p.id);
                      return <li key={p.id} className={on ? "is-on" : "is-off"}>{on ? <Check aria-hidden="true" /> : <span className="dash" aria-hidden="true" />}<span>{p.label}<span className="sr-only">{on ? ": incluido" : ": no incluido"}</span></span></li>;
                    })}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </Placard>
  );
}

/* ───────────────────────── dialogs (scene axis) ───────────────────────── */

const ACCOUNT_SCENES: Record<string, (a: Account) => boolean> = {
  "cambiar-rol": (a) => !a.admin,
  "enlace-restablecer": () => true,
  desactivar: (a) => a.status !== "Desactivada" && !a.admin,
  reactivar: (a) => a.status === "Desactivada",
  eliminar: (a) => !a.work && !a.admin,
  "eliminar-con-trabajo": (a) => a.work > 0 && !a.admin,
  "eliminar-ultimo-admin": (a) => !!a.admin,
};
const DEFAULT_TARGET: Record<string, string> = {
  "cambiar-rol": "a4", "enlace-restablecer": "a2", desactivar: "a3", reactivar: "a6", eliminar: "a4", "eliminar-con-trabajo": "a3", "eliminar-ultimo-admin": "a1",
};

function RoleSelect({ id, value, onChange, disabled }: { id: string; value: string; onChange: (v: string) => void; disabled?: boolean }) {
  return (
    <select id={id} className="pl-select pl-select--block" value={value} onChange={(e) => onChange(e.target.value)} disabled={disabled}>
      {ROLES.map((r) => <option key={r.name}>{r.name}</option>)}
    </select>
  );
}

function LinkBox({ kind, who }: { kind: "invitación" | "restablecimiento"; who: Account }) {
  const link = kind === "invitación" ? "demo-decoracion.vercel.app/activar/q7Fz-2kLm-9wRt" : "demo-decoracion.vercel.app/restablecer/Hc4x-8pVa-3nQe";
  return (
    <div className="linkbox">
      <span className="pl-label" id="link-label">Enlace de {kind} para {who.name}</span>
      <div className="link-row">
        <code className="link-code" aria-labelledby="link-label">{link}</code>
        <CopyButton content={link} aria-label="Copiar enlace" className="pl-btn pl-btn--primary copy-btn">
          <CopyButtonIcon icon={<Copy className="size-4" />} copiedIcon={<Check className="size-4" />} />
          Copiar
        </CopyButton>
      </div>
      <p className="pl-hint"><Link2 aria-hidden="true" className="inline-ico" />Se muestra una sola vez. {kind === "invitación" ? "Vale 7 días." : "Vale 24 horas."} Un solo uso. Al generarlo dejaron de servir los enlaces de {kind} anteriores sin usar de esta cuenta.</p>
    </div>
  );
}

function Dialogs({ chosen }: { chosen: Account | null }) {
  const { scene, set } = useMockup();
  const close = (o: boolean) => { if (!o) set("scene", ""); };
  const rule = ACCOUNT_SCENES[scene];
  const target = rule ? (chosen && rule(chosen) ? chosen : ACCOUNTS.find((a) => a.id === DEFAULT_TARGET[scene])!) : ACCOUNTS[3];
  const [newRole, setNewRole] = React.useState("Usuario · Plan 3");
  const [typed, setTyped] = React.useState("");
  const [roleName, setRoleName] = React.useState(scene === "rol-sin-permisos" ? "Solo consulta" : "Revisión de costos");
  const [perms, setPerms] = React.useState<string[]>(scene === "rol-sin-permisos" ? [] : ["costos", "gasto"]);
  React.useEffect(() => {
    setTyped("");
    setNewRole(target.role === "Usuario · Plan 3" ? "Usuario · Plan 2" : "Usuario · Plan 3");
    if (scene === "rol-sin-permisos") { setRoleName("Solo consulta"); setPerms([]); }
    if (scene === "rol-editor") { setRoleName("Revisión de costos"); setPerms(["costos", "gasto"]); }
  }, [scene, target.id, target.role]);

  const invite = scene === "invitar" || scene === "invitar-duplicado";
  const plainOpen = invite || scene === "invitar-enlace" || scene === "cambiar-rol" || scene === "enlace-restablecer" || scene === "rol-editor" || scene === "rol-sin-permisos";
  const alertOpen = ["desactivar", "reactivar", "eliminar", "eliminar-con-trabajo", "eliminar-ultimo-admin", "rol-eliminar-en-uso"].includes(scene);
  const dup = scene === "invitar-duplicado";

  return (
    <>
      <Dialog open={plainOpen} onOpenChange={close}>
        <DialogContent className={`pl-dialog ${scene.startsWith("rol-") ? "pl-dialog--wide" : ""}`} showCloseButton={false}>
          <span className="ribbon ribbon--l" aria-hidden="true" /><span className="ribbon ribbon--r" aria-hidden="true" />
          {invite && (
            <>
              <DialogTitle className="pl-dtitle">Invitar persona</DialogTitle>
              <DialogDescription className="pl-hint">Pictures no envía correos: al crear la invitación verás un enlace para copiar y compartir.</DialogDescription>
              <form className="pl-form" onSubmit={(e) => { e.preventDefault(); set("scene", "invitar-enlace"); }}>
                <TextField id="inv-name" label="Nombre" value={dup ? "Laura Gómez" : "Camila Restrepo"} />
                <TextField id="inv-mail" label="Correo" type="email" value={dup ? "laura.gomez@sempertex.com" : "camila@fiestasbrillo.co"} error={dup ? "Ese correo ya tiene una cuenta (Laura Gómez). Búscala en Cuentas para cambiar su rol o generarle un enlace." : undefined} />
                <TextField id="inv-company" label="Empresa (opcional)" value={dup ? "Sempertex" : "Fiestas Brillo"} />
                <div className="pl-field">
                  <label className="pl-label" htmlFor="inv-role">Rol o plan de acceso</label>
                  <RoleSelect id="inv-role" value={dup ? "Empleado interno" : "Usuario · Plan 2"} onChange={() => undefined} />
                  <p className="pl-hint">{TOOLS_OF[dup ? "Empleado interno" : "Usuario · Plan 2"]}</p>
                </div>
                <div className="pl-actions">
                  <Button type="button" className="pl-btn pl-btn--quiet" onClick={() => set("scene", "")}>Cancelar</Button>
                  <Button type="submit" className="pl-btn pl-btn--primary">Crear invitación</Button>
                </div>
              </form>
            </>
          )}
          {scene === "invitar-enlace" && (
            <>
              <DialogTitle className="pl-dtitle">Invitación lista</DialogTitle>
              <DialogDescription className="pl-hint">Camila Restrepo · camila@fiestasbrillo.co · Usuario · Plan 2</DialogDescription>
              <LinkBox kind="invitación" who={ACCOUNTS[3]} />
              <div className="pl-actions"><Button type="button" className="pl-btn pl-btn--quiet" onClick={() => set("scene", "")}>Listo, ya lo copié</Button></div>
            </>
          )}
          {scene === "enlace-restablecer" && (
            <>
              <DialogTitle className="pl-dtitle">{target.status === "Invitada" ? "Nueva invitación" : "Enlace de restablecimiento"}</DialogTitle>
              <DialogDescription className="pl-hint">{target.name} · {target.email}</DialogDescription>
              <LinkBox kind={target.status === "Invitada" ? "invitación" : "restablecimiento"} who={target} />
              <div className="pl-actions"><Button type="button" className="pl-btn pl-btn--quiet" onClick={() => set("scene", "")}>Listo, ya lo copié</Button></div>
            </>
          )}
          {scene === "cambiar-rol" && (
            <>
              <DialogTitle className="pl-dtitle">Cambiar rol de {target.name}</DialogTitle>
              <DialogDescription className="pl-hint">Ahora: {target.role}. El cambio se aplica en su próxima petición.</DialogDescription>
              <div className="pl-field">
                <label className="pl-label" htmlFor="new-role">Nuevo rol</label>
                <RoleSelect id="new-role" value={newRole} onChange={setNewRole} />
                <p className="pl-hint">{TOOLS_OF[newRole]}</p>
              </div>
              <div className="pl-actions">
                <Button type="button" className="pl-btn pl-btn--quiet" onClick={() => set("scene", "")}>Cancelar</Button>
                <Button type="button" className="pl-btn pl-btn--primary" disabled={newRole === target.role} onClick={() => set("scene", "")}>Guardar rol</Button>
              </div>
            </>
          )}
          {(scene === "rol-editor" || scene === "rol-sin-permisos") && (
            <>
              <DialogTitle className="pl-dtitle">{scene === "rol-editor" ? "Editar rol propio" : "Crear rol"}</DialogTitle>
              <DialogDescription className="pl-hint">Elige qué abre este rol. Los permisos se agrupan por herramienta.</DialogDescription>
              <TextField id="role-name" label="Nombre del rol" value={roleName} onChange={setRoleName} />
              <div className="perm-pick" role="group" aria-label="Permisos">
                {GROUPS.map((g) => (
                  <fieldset className="perm-set" key={g.tool}>
                    <legend>{g.tool}</legend>
                    {g.perms.map((p) => (
                      <div className="check-line" key={p.id}>
                        <Checkbox id={`perm-${p.id}`} className="pl-check" checked={perms.includes(p.id)} onCheckedChange={(v) => setPerms((old) => (v === true ? [...old, p.id] : old.filter((x) => x !== p.id)))} />
                        <label htmlFor={`perm-${p.id}`}>{p.label}</label>
                      </div>
                    ))}
                  </fieldset>
                ))}
              </div>
              {perms.length === 0 && <p className="pl-error" role="alert">Elige al menos un permiso: un rol sin permisos no abre ninguna herramienta (ROL_SIN_PERMISOS).</p>}
              <div className="pl-actions">
                <span className="pl-hint perm-count">{perms.length} {perms.length === 1 ? "permiso" : "permisos"}</span>
                <Button type="button" className="pl-btn pl-btn--quiet" onClick={() => set("scene", "")}>Cancelar</Button>
                <Button type="button" className="pl-btn pl-btn--primary" disabled={perms.length === 0 || !roleName.trim()} onClick={() => set("scene", "")}>Guardar rol</Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog open={alertOpen} onOpenChange={close}>
        <AlertDialogContent className="pl-dialog">
          <span className="ribbon ribbon--l" aria-hidden="true" /><span className="ribbon ribbon--r" aria-hidden="true" />
          {scene === "desactivar" && (
            <>
              <AlertDialogTitle className="pl-dtitle">Desactivar a {target.name}</AlertDialogTitle>
              <AlertDialogDescription className="pl-hint">Su acceso termina en su próxima petición. {target.work ? `Sus ${target.work} proyectos y decoraciones se conservan.` : "No tiene trabajo guardado."} Puedes reactivarla cuando quieras.</AlertDialogDescription>
              <div className="pl-actions"><AlertDialogCancel className="pl-btn pl-btn--quiet">Cancelar</AlertDialogCancel><AlertDialogAction className="pl-btn pl-btn--danger" onClick={() => set("scene", "")}>Desactivar cuenta</AlertDialogAction></div>
            </>
          )}
          {scene === "reactivar" && (
            <>
              <AlertDialogTitle className="pl-dtitle">Reactivar a {target.name}</AlertDialogTitle>
              <AlertDialogDescription className="pl-hint">Podrá volver a entrar con su contraseña de siempre, con el rol {target.role}.</AlertDialogDescription>
              <div className="pl-actions"><AlertDialogCancel className="pl-btn pl-btn--quiet">Cancelar</AlertDialogCancel><AlertDialogAction className="pl-btn pl-btn--primary" onClick={() => set("scene", "")}>Reactivar cuenta</AlertDialogAction></div>
            </>
          )}
          {scene === "eliminar" && (
            <>
              <AlertDialogTitle className="pl-dtitle">Eliminar a {target.name}</AlertDialogTitle>
              <AlertDialogDescription className="pl-hint">No tiene proyectos ni decoraciones guardados. Su consumo de IA se conserva sin datos personales, como «Cuenta eliminada». No se puede deshacer.</AlertDialogDescription>
              <TextField id="del-confirm" label={`Escribe ${target.email} para confirmar`} type="email" value={typed} onChange={setTyped} mono />
              <div className="pl-actions"><AlertDialogCancel className="pl-btn pl-btn--quiet">Cancelar</AlertDialogCancel><AlertDialogAction className="pl-btn pl-btn--danger" disabled={typed !== target.email} onClick={() => set("scene", "")}>Eliminar cuenta</AlertDialogAction></div>
            </>
          )}
          {scene === "eliminar-con-trabajo" && (
            <>
              <AlertDialogTitle className="pl-dtitle">{target.name} no se puede eliminar</AlertDialogTitle>
              <AlertDialogDescription className="pl-hint">Tiene {target.work} proyectos o decoraciones guardados y borrarla los dejaría sin dueño (CUENTA_CON_TRABAJO). No cambió nada. Si debe perder el acceso, desactívala: su trabajo se conserva.</AlertDialogDescription>
              <div className="pl-actions"><AlertDialogCancel className="pl-btn pl-btn--quiet">Cerrar</AlertDialogCancel><AlertDialogAction className="pl-btn pl-btn--primary" onClick={() => set("scene", "desactivar")}>Desactivar en su lugar</AlertDialogAction></div>
            </>
          )}
          {scene === "eliminar-ultimo-admin" && (
            <>
              <AlertDialogTitle className="pl-dtitle">{target.name} es el último administrador</AlertDialogTitle>
              <AlertDialogDescription className="pl-hint">Sin otro administrador nadie podría invitar personas ni cambiar roles. Da el rol Administrador a otra cuenta antes de eliminar, desactivar o cambiar de rol esta.</AlertDialogDescription>
              <div className="pl-actions"><AlertDialogCancel className="pl-btn pl-btn--quiet">Entendido</AlertDialogCancel></div>
            </>
          )}
          {scene === "rol-eliminar-en-uso" && (
            <>
              <AlertDialogTitle className="pl-dtitle">«Revisión de costos» tiene cuentas</AlertDialogTitle>
              <AlertDialogDescription className="pl-hint">1 cuenta usa este rol: Julián Pardo. Cámbiala a otro rol y vuelve a intentarlo. Los roles del sistema nunca se eliminan.</AlertDialogDescription>
              <div className="pl-actions"><AlertDialogCancel className="pl-btn pl-btn--quiet">Entendido</AlertDialogCancel></div>
            </>
          )}
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

/* ───────────────────────── the app ───────────────────────── */

function App() {
  const m = useMockup();
  const [chosen, setChosen] = React.useState<Account | null>(null);
  const pick = React.useCallback((scene: string, a?: Account) => { setChosen(a ?? null); if (scene) m.set("scene", scene); }, [m]);
  const View = { ingresar: Ingresar, activar: Activar, restablecer: Restablecer, aviso: Aviso, "mi-cuenta": MiCuenta, cuentas: Cuentas, roles: Roles }[m.view] ?? Ingresar;
  return (
    <PICK.Provider value={pick}>
      <style>{CSS}</style>
      <div className={`venue view-${m.view}`} data-view={m.view}>
        <Drift />
        <Garland />
        <main className="drop-zone"><View /></main>
      </div>
      <Dialogs chosen={chosen} />
    </PICK.Provider>
  );
}

/* ───────────────────────── direction tokens and styles ───────────────────────── */

const CSS = `
:root{
  --stage:#eaf0ff;--stage-2:#dfe7ff;--card:#ffffff;--ink:#0c1638;--ink-2:#434d78;--edge:#6b779f;--line:#c4cdec;
  --cobalt:#1f3fd6;--on-cobalt:#ffffff;--tangerine:#ff6b2c;--tangerine-ink:#a33900;--pearl:#f4efe6;--rope:#8a93b4;
  --ok:#0b6b44;--ok-bg:#e1f5ea;--bad:#b0142a;--bad-bg:#fde8eb;--warn:#7f4300;--warn-bg:#fff0dc;--field:#ffffff;--muted-fill:#eef1fa;
  --focus:#1f3fd6;--shadow:0 22px 44px -26px rgb(12 22 56 / .45);
  --display:"Syne Variable",ui-sans-serif,system-ui,sans-serif;--text:"Manrope Variable",ui-sans-serif,system-ui,sans-serif;--mono:"JetBrains Mono Variable",ui-monospace,monospace;
  --ease-elastic:linear(0,0.36 6%,0.86 14%,1.1 21%,1.15 27%,1.07 36%,0.98 46%,0.99 58%,1);--ease-lift:cubic-bezier(.2,.9,.25,1.25);
  --t-quick:180ms;--t-pull:620ms;
  --background:var(--stage);--foreground:var(--ink);--card-foreground:var(--ink);--popover:var(--card);--popover-foreground:var(--ink);
  --primary:var(--cobalt);--primary-foreground:var(--on-cobalt);--secondary:var(--muted-fill);--secondary-foreground:var(--ink);
  --muted:var(--muted-fill);--muted-foreground:var(--ink-2);--accent:var(--muted-fill);--accent-foreground:var(--ink);
  --destructive:var(--bad);--border:var(--line);--input:var(--edge);--ring:var(--focus);
}
:root.dark{
  --stage:#070b24;--stage-2:#0b1236;--card:#121a44;--ink:#eef1ff;--ink-2:#b0b9df;--edge:#8591c4;--line:#2b3672;
  --cobalt:#97a9ff;--on-cobalt:#07102f;--tangerine:#ff7a3d;--tangerine-ink:#ffb08a;--pearl:#d9d2c4;--rope:#5d6898;
  --ok:#6fe0ad;--ok-bg:#0f3327;--bad:#ff9aa8;--bad-bg:#3d1020;--warn:#ffc98a;--warn-bg:#3a2508;--field:#0d1438;--muted-fill:#1a2456;
  --focus:#ffb08a;--shadow:0 26px 50px -24px rgb(0 0 0 / .7);
}
:root[data-motion=natural]{--t-pull:420ms}
:root[data-motion=subtle]{--t-pull:200ms;--ease-elastic:cubic-bezier(.2,.8,.2,1)}
body{background:var(--stage)}
.venue{position:relative;min-height:calc(100svh - var(--mockup-bar-h,0px));background:linear-gradient(var(--stage) 0 62%,var(--stage-2));color:var(--ink);font-family:var(--text);font-size:15px;line-height:1.5;overflow:hidden;padding-bottom:56px}
.mono{font-family:var(--mono)}

/* garland band */
.garland-band{position:relative;height:150px;z-index:2;animation:band-parallax linear both;animation-timeline:scroll(root);animation-range:0 420px}
.garland-band.is-signed{height:172px}
.garland-svg{position:absolute;inset:0;width:100%;height:120px;overflow:visible}
.garland-string{fill:none;stroke:var(--rope);stroke-width:2.5;vector-effect:non-scaling-stroke;stroke-dasharray:1;stroke-dashoffset:1;animation:draw 1.3s cubic-bezier(.6,0,.2,1) .05s forwards}
.cluster{position:absolute;top:6px;display:flex;align-items:flex-start;gap:0}
.cluster--l{left:clamp(8px,4vw,56px)}.cluster--r{right:clamp(8px,4vw,56px)}
.cluster .balloon+.balloon{margin-left:-10px;margin-top:14px}
.balloon{position:relative;display:block;flex:none;width:var(--s);height:calc(var(--s)*1.16);border-radius:50% 50% 50% 50%/46% 46% 54% 54%;background-color:var(--c);
  background-image:radial-gradient(circle at 31% 27%,rgb(255 255 255/.62) 0 8%,rgb(255 255 255/0) 9%),radial-gradient(circle at 70% 82%,rgb(0 0 0/.22),rgb(0 0 0/0) 58%);
  box-shadow:inset -3px -5px 10px rgb(0 0 0/.12);transition:transform var(--t-quick) var(--ease-lift)}
.balloon::after{content:"";position:absolute;left:50%;bottom:-5px;width:8px;height:7px;translate:-50% 0;background:var(--c);clip-path:polygon(50% 0,100% 100%,0 100%)}
.balloon--cobalt{--c:var(--cobalt)}.balloon--tangerine{--c:var(--tangerine)}.balloon--pearl{--c:var(--pearl)}
.bob{animation:bob 4.6s ease-in-out infinite}.bob--2{animation-duration:5.4s;animation-delay:-1.2s}.bob--3{animation-duration:3.9s;animation-delay:-2.1s}

.band-row{position:relative;display:grid;grid-template-columns:1fr auto 1fr;align-items:start;gap:16px;max-width:1180px;margin:0 auto;padding:18px 24px 0}
.brand{display:flex;flex-direction:column;gap:2px;padding-top:14px;padding-left:clamp(0px,9vw,120px)}
.brand-word{font:800 24px/1 var(--display);letter-spacing:-.01em}
.brand-sub{font-size:13px;color:var(--ink-2)}
.band-gap{display:block}
.garland-nav{display:flex;flex-direction:row;gap:clamp(16px,4vw,48px);align-items:flex-start}
.nav-balloon{all:unset;box-sizing:border-box;position:relative;display:flex;flex-direction:column;align-items:center;gap:0;min-width:96px;padding:4px 8px 8px;cursor:pointer;border-radius:14px;
  outline:3px solid transparent;outline-offset:8px;transition:outline-offset var(--t-quick) var(--ease-elastic),outline-color var(--t-quick)}
.nav-balloon .balloon{transform:translateY(0);transition:transform var(--t-pull) var(--ease-elastic)}
.nav-tether{display:block;width:2px;height:12px;background:var(--rope);transition:height var(--t-pull) var(--ease-elastic)}
.nav-label{font:700 15px/1.2 var(--display);padding-top:6px;color:var(--ink);border-bottom:3px solid transparent;transition:border-color var(--t-quick),transform var(--t-pull) var(--ease-elastic)}
.nav-balloon:hover .balloon{transform:translateY(-4px) scale(1.07,.93)}
.nav-balloon:active .balloon{transform:translateY(2px) scale(.9,1.08);transition-duration:120ms}
.nav-balloon[aria-current=page] .balloon{transform:translateY(18px)}
.nav-balloon[aria-current=page] .nav-tether{height:4px}
.nav-balloon[aria-current=page] .nav-label{transform:translateY(16px);border-color:var(--tangerine)}
.nav-balloon[aria-current=page]:hover .balloon{transform:translateY(14px) scale(1.06,.94)}

.foil-trigger{all:unset;box-sizing:border-box;justify-self:end;display:grid;grid-template-columns:auto auto;grid-template-rows:auto auto;column-gap:10px;align-items:center;cursor:pointer;padding:6px 10px;border-radius:16px;
  outline:3px solid transparent;outline-offset:8px;transition:outline-offset var(--t-quick) var(--ease-elastic),outline-color var(--t-quick)}
.foil{grid-row:1;grid-column:1;display:grid;place-items:center;width:46px;height:46px;border-radius:50%;font:800 14px/1 var(--display);color:#0c1638;background-color:#e3e7ef;
  background-image:conic-gradient(from 210deg,#cfd5e1,#f8fafc,#a8b0c2,#eef1f6,#c2c9d7,#cfd5e1);box-shadow:inset 0 0 0 1.5px #8a93ab;transition:transform var(--t-pull) var(--ease-elastic)}
.foil-tether{grid-row:2;grid-column:1;justify-self:center;width:2px;height:16px;background:var(--rope)}
.foil-text{grid-row:1;grid-column:2;display:flex;flex-direction:column;line-height:1.2}
.foil-name{font-weight:700;font-size:14px}.foil-role{font-size:13px;color:var(--ink-2)}
.foil-trigger:hover .foil{transform:rotate(-8deg) scale(1.05)}
.foil-trigger[aria-current=page] .foil,.foil-trigger[data-popup-open] .foil{transform:translateY(8px)}

/* placard */
.drop-zone{position:relative;z-index:1;display:flex;justify-content:center;padding:0 24px}
.placard{position:relative;width:min(460px,100%);margin-top:28px;transform-origin:50% -150px}
.placard--wide{width:min(1120px,100%)}
.view-activar .placard--wide,.view-aviso .placard--wide{width:min(940px,100%)}
.placard-body{position:relative;background:var(--card);border:1.5px solid var(--line);border-radius:26px;padding:32px;box-shadow:var(--shadow);transform-origin:50% -60px}
.placard-body::before,.placard-body::after{content:"";position:absolute;top:14px;width:12px;height:12px;border-radius:50%;background:var(--stage);box-shadow:inset 0 0 0 2px var(--tangerine)}
.placard-body::before{left:22%}.placard-body::after{right:22%}
.ribbon{position:absolute;bottom:calc(100% - 22px);width:2px;height:240px;background:var(--tangerine);z-index:0}
.ribbon--l{left:calc(22% + 5px)}.ribbon--r{right:calc(22% + 5px)}
.placard-head{display:flex;flex-direction:column;gap:6px;margin:10px 0 22px}
.kicker{font-size:13px;font-weight:600;color:var(--tangerine-ink)}
.pl-title{margin:0;font:800 40px/1.02 var(--display);letter-spacing:-.025em;color:var(--ink)}
.pl-title--admin{font-size:52px;display:flex;align-items:baseline;gap:14px}
.count{font:700 22px/1 var(--display);color:var(--tangerine-ink);font-variant-numeric:tabular-nums}
.pl-subtitle{margin:0 0 6px;font:700 22px/1.15 var(--display);letter-spacing:-.01em}
.lede{margin:0 0 18px;color:var(--ink-2);max-width:62ch}
.lede strong{color:var(--ink)}
.placard-foot{margin-top:22px;padding-top:18px;border-top:1.5px dashed var(--line);display:grid;gap:6px;color:var(--ink-2);font-size:14px}
.placard-foot p{margin:0}.placard-foot strong{color:var(--ink)}
.na-note{margin:-8px 0 16px;font-size:13px;color:var(--ink-2)}

/* forms */
.pl-form{display:grid;gap:18px}
.pl-field{display:grid;gap:6px}
.pl-label{font-size:14px;font-weight:700;color:var(--ink)}
.pl-input{height:46px;border-radius:14px;border:1.5px solid var(--edge);background:var(--field);color:var(--ink);font:500 15px var(--text);padding:0 14px;
  transition:border-color var(--t-quick),box-shadow var(--t-pull) var(--ease-elastic)}
.pl-input.mono{font-family:var(--mono);font-size:14px}
.pl-input::placeholder{color:var(--ink-2);opacity:1}
.pl-input:focus-visible{border-color:var(--focus);box-shadow:0 0 0 4px color-mix(in oklab,var(--focus) 30%,transparent);outline:2px solid var(--focus);outline-offset:2px}
.pl-input[aria-invalid=true]{border-color:var(--bad)}
.pl-input:disabled{background:var(--muted-fill);opacity:1;color:var(--ink-2)}
.pl-hint{margin:0;font-size:13.5px;color:var(--ink-2)}
.pl-error{margin:0;font-size:13.5px;font-weight:600;color:var(--bad)}
.pl-select{height:44px;border-radius:12px;border:1.5px solid var(--edge);background:var(--field);color:var(--ink);font:600 14px var(--text);padding:0 12px;color-scheme:light}
:root.dark .pl-select{color-scheme:dark}
.pl-select--sm{height:38px}.pl-select--block{width:100%}
.pl-select:focus-visible{outline:3px solid var(--focus);outline-offset:2px}

.pl-btn{height:46px;padding:0 18px;border-radius:999px;font:700 15px var(--text);gap:8px;border:1.5px solid transparent;
  transition:transform var(--t-quick) var(--ease-lift),background-color var(--t-quick),box-shadow var(--t-quick);outline:3px solid transparent;outline-offset:8px}
.pl-btn:focus-visible{outline:3px solid var(--focus);outline-offset:3px;transition:outline-offset var(--t-quick) var(--ease-elastic),transform var(--t-quick)}
.pl-btn:hover:not(:disabled){transform:scale(1.035,.965)}
.pl-btn:active:not(:disabled){transform:scale(.95,1.04);transition-duration:110ms}
.pl-btn--primary{background:var(--cobalt);color:var(--on-cobalt);box-shadow:inset 0 -3px 0 rgb(0 0 0/.18)}
.pl-btn--primary:hover:not(:disabled){background:var(--cobalt)}
.pl-btn--quiet{background:transparent;color:var(--ink);border-color:var(--edge)}
.pl-btn--quiet:hover:not(:disabled){background:var(--muted-fill)}
.pl-btn--danger{background:var(--bad-bg);color:var(--bad);border-color:var(--bad)}
.pl-btn--danger:hover:not(:disabled){background:var(--bad-bg)}
.pl-btn--block{width:100%}
.pl-btn--icon{width:44px;height:44px;padding:0;border-radius:50%;color:var(--ink);border-color:transparent}
.pl-btn--icon:hover{background:var(--muted-fill)}
.pl-btn:disabled{opacity:1;background:var(--muted-fill);color:var(--ink-2);border:1.5px dashed var(--edge);box-shadow:none}
.inflate{display:inline-block;width:14px;height:16px;border-radius:50% 50% 50% 50%/46% 46% 54% 54%;background:currentColor;animation:inflate .9s var(--ease-lift) infinite alternate}

.pl-check{width:22px;height:22px;border-radius:7px;border:2px solid var(--edge);background:var(--field)}
.pl-check[data-checked]{background:var(--cobalt);border-color:var(--cobalt);color:var(--on-cobalt)}
.pl-check:focus-visible{outline:3px solid var(--focus);outline-offset:3px}

.note{display:grid;gap:4px;padding:14px 16px;border-radius:16px;border:1.5px solid;margin-bottom:18px;font-size:14px}
.note strong{font-weight:700}
.note--error{background:var(--bad-bg);border-color:var(--bad);color:var(--ink)}.note--error strong{color:var(--bad)}
.note--ok{background:var(--ok-bg);border-color:var(--ok);color:var(--ink)}.note--ok strong{color:var(--ok)}
.note--warn{background:var(--warn-bg);border-color:var(--warn);color:var(--ink)}.note--warn strong{color:var(--warn)}
.note--info{background:var(--muted-fill);border-color:var(--edge)}

.release{position:absolute;right:28px;top:-10px;z-index:3;animation:release 2.2s cubic-bezier(.3,.1,.5,1) .5s both}

/* activation and notice */
.split{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.25fr);gap:32px;align-items:start}
.split-col{display:grid;gap:18px;align-content:start}
.who{display:grid;gap:4px;padding:16px 18px;border-radius:18px;background:var(--muted-fill);border:1.5px solid var(--line)}
.who-name{font:800 22px/1.1 var(--display)}.who-mail{font-family:var(--mono);font-size:14px}.who-role{font-size:13.5px;color:var(--ink-2)}
.sk{height:14px;width:70%;border-radius:8px;background:var(--line)}.sk--lg{height:22px;width:55%}.sk--sm{width:40%}.sk--tag{height:64px;width:150px;border-radius:14px}
.notice{display:grid;gap:12px}
.notice-top{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:end;gap:10px}
.notice-title{margin:0;font:700 18px/1.2 var(--display)}
.notice-version{font:700 13px var(--mono);color:var(--tangerine-ink)}
.lang-pick{display:grid;gap:4px;font-size:13px;font-weight:600}
.notice-text{max-height:210px;overflow:auto;padding:14px 16px;border-radius:16px;border:1.5px solid var(--edge);background:var(--field);font-size:14px;line-height:1.6}
.notice-text p{margin:0}
.notice-text:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.legal-ph{background:color-mix(in oklab,var(--tangerine) 22%,var(--field));color:var(--ink);padding:0 3px;border-radius:4px;font-weight:700}
.legal-flag{margin:0;display:flex;gap:8px;align-items:center;font-size:13px;color:var(--ink-2)}
.legal-dot{width:8px;height:8px;border-radius:50%;background:var(--tangerine);flex:none}
.accept-line{display:flex;gap:12px;align-items:flex-start;padding:14px 16px;border-radius:16px;border:1.5px solid var(--edge);font-weight:600;font-size:14.5px}
.accept-line.is-invalid{border-color:var(--bad)}
.accept-line label{cursor:pointer}
.submit-row{display:grid;gap:8px}

/* admin */
.admin-head{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:end;gap:16px;margin:8px 0 22px}
.toolbar{display:flex;flex-wrap:wrap;gap:12px;align-items:end;margin-bottom:12px}
.search{position:relative;flex:1 1 280px;display:block}
.search svg{position:absolute;left:14px;top:50%;translate:0 -50%;width:18px;height:18px;color:var(--ink-2);pointer-events:none}
.pl-input--search{padding-left:42px}
.filter{display:grid;gap:4px;font-size:13px;font-weight:700}
.acc-table{border-collapse:separate;border-spacing:0}
.acc-table th{height:40px;font:600 13px var(--text);color:var(--ink-2);text-align:left;padding:0 12px;border-bottom:1.5px solid var(--line)}
.acc-table td{padding:14px 12px;border-bottom:1px solid var(--line);vertical-align:middle;font-size:14.5px}
.acc-row{transform-origin:50% 0;transition:transform var(--t-quick) var(--ease-lift),background-color var(--t-quick)}
.acc-row:hover{background:var(--muted-fill);transform:rotate(-.25deg)}
.p-name{display:block;font-weight:700}.p-mail{display:block;font-size:13.5px;color:var(--ink-2)}
.c-act{width:56px;text-align:right}
.c-last{font-variant-numeric:tabular-nums;white-space:nowrap}
.pl-badge{height:26px;padding:0 10px;border-radius:999px;font:700 12.5px var(--text);border:1.5px solid}
.pl-badge--ok{background:var(--ok-bg);color:var(--ok);border-color:var(--ok)}
.pl-badge--invited{background:var(--warn-bg);color:var(--warn);border-color:var(--warn)}
.pl-badge--off{background:var(--muted-fill);color:var(--ink-2);border-color:var(--edge)}
.table-foot{margin:16px 0 0;font-size:13px;color:var(--ink-2)}
.sk-list{display:grid;gap:16px;padding:12px 0}.sk-row{display:grid;grid-template-columns:2fr 1fr 1fr;gap:16px}
.empty{display:grid;gap:12px;justify-items:start;padding:28px 0}
.empty-title{margin:0;font:700 20px/1.2 var(--display)}
.empty-balloon{animation:bob 4.6s ease-in-out infinite}
.row-gap{display:flex;flex-wrap:wrap;gap:10px}

/* roles: tags on a clothesline */
.line-wrap{position:relative;padding-top:14px;margin-bottom:26px}
.clothesline{position:absolute;left:-32px;right:-32px;top:16px;height:2px;background:var(--rope)}
.tags{position:relative;display:flex;flex-wrap:wrap;gap:14px}
.role-tag{all:unset;box-sizing:border-box;position:relative;display:grid;gap:4px;min-width:150px;padding:20px 16px 14px;border-radius:6px 6px 18px 18px;background:var(--card);border:1.5px solid var(--edge);cursor:pointer;
  transform-origin:50% 0;outline:3px solid transparent;outline-offset:8px;transition:outline-offset var(--t-quick) var(--ease-elastic),outline-color var(--t-quick),background-color var(--t-quick),border-color var(--t-quick)}
.role-tag:hover{background:var(--muted-fill)}
.role-tag[aria-selected=true]{border-color:var(--cobalt);box-shadow:inset 0 0 0 1.5px var(--cobalt)}
.role-tag.is-custom{border-style:dashed}
.clip{position:absolute;top:-10px;left:50%;translate:-50% 0;width:14px;height:20px;border-radius:4px;background:var(--tangerine)}
.tag-name{font:700 15px/1.2 var(--display)}
.tag-meta{display:flex;align-items:center;gap:4px;font-size:12.5px;color:var(--ink-2)}
.tag-meta svg{width:13px;height:13px}
.empty-inline{margin:-10px 0 18px}
.sk-line{display:flex;flex-wrap:wrap;gap:14px;margin-bottom:26px}
.role-panel{border-top:1.5px solid var(--line);padding-top:22px}
.role-panel-head{display:flex;flex-wrap:wrap;justify-content:space-between;gap:16px;align-items:start;margin-bottom:12px}
.readonly{display:inline-flex;gap:6px;align-items:center;font-size:13.5px;font-weight:700;color:var(--ink-2)}
.readonly svg{width:15px;height:15px}
.perm-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:20px 24px;margin-top:16px}
.perm-group h3{margin:0 0 8px;font:700 14px var(--display);color:var(--ink)}
.perm-group ul{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.perm-group li{display:flex;gap:8px;align-items:flex-start;font-size:14px}
.perm-group li svg{width:16px;height:16px;flex:none;margin-top:2px;color:var(--ok)}
.perm-group li.is-off{color:var(--ink-2)}
.dash{width:10px;height:2px;margin:10px 3px 0;background:var(--ink-2);flex:none}

/* mi cuenta */
.facts{margin:0;display:grid;gap:0}
.facts div{display:grid;grid-template-columns:140px 1fr;gap:12px;padding:12px 0;border-bottom:1px solid var(--line)}
.facts dt{font-size:13.5px;color:var(--ink-2)}.facts dd{margin:0;font-weight:600}

/* dialogs and menus (portaled outside .venue) */
[data-slot=dialog-overlay],[data-slot=alert-dialog-overlay]{background:rgb(7 11 36/.5);backdrop-filter:none}
.pl-dialog{width:min(560px,calc(100vw - 32px));max-width:min(560px,calc(100vw - 32px));padding:30px;gap:16px;border-radius:26px;background:var(--card);color:var(--ink);border:1.5px solid var(--line);box-shadow:var(--shadow);font-family:var(--text);font-size:15px;overflow:visible}
.pl-dialog--wide{width:min(780px,calc(100vw - 32px));max-width:min(780px,calc(100vw - 32px));max-height:calc(100svh - 48px);overflow:auto}
.pl-dialog .ribbon{height:100vh;bottom:100%}
.pl-dialog--wide .ribbon{display:none}
.pl-dtitle{margin:0;font:800 26px/1.1 var(--display);letter-spacing:-.015em;color:var(--ink)}
.pl-actions{display:flex;flex-wrap:wrap;justify-content:flex-end;align-items:center;gap:10px;margin-top:6px}
.perm-count{margin-right:auto}
.linkbox{display:grid;gap:8px}
.link-row{display:flex;gap:10px;align-items:center}
.link-code{flex:1;min-width:0;overflow-wrap:anywhere;padding:12px 14px;border-radius:14px;border:1.5px dashed var(--edge);background:var(--muted-fill);font:500 13.5px/1.4 var(--mono);color:var(--ink)}
.copy-btn{display:inline-flex;align-items:center;justify-content:center;flex:none}
.inline-ico{display:inline;width:14px;height:14px;vertical-align:-2px;margin-right:4px}
.perm-pick{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px 22px}
.perm-set{margin:0;padding:12px 14px;border:1.5px solid var(--line);border-radius:16px;display:grid;gap:8px}
.perm-set legend{padding:0 6px;font:700 14px var(--display)}
.check-line{display:flex;gap:10px;align-items:flex-start;font-size:14px}
.check-line label{cursor:pointer}
.pl-menu{min-width:220px;padding:8px;border-radius:18px;background:var(--card);color:var(--ink);border:1.5px solid var(--line);box-shadow:var(--shadow);font-family:var(--text)}
.pl-menu-head{display:grid;gap:2px;padding:8px 10px}
.pl-menu-head strong{font:700 15px var(--display);color:var(--ink)}.pl-menu-head span{font-size:13px;color:var(--ink-2)}
.pl-menu-item{min-height:40px;padding:8px 10px;border-radius:12px;font-size:14px;font-weight:600;color:var(--ink)}
.pl-menu-item[data-highlighted]{background:var(--muted-fill)}
.pl-menu-item--danger{color:var(--bad)}
.pl-menu-item[data-disabled]{opacity:1;color:var(--ink-2)}

.foil-trigger:focus-visible,.nav-balloon:focus-visible,.role-tag:focus-visible{outline-color:var(--focus);outline-offset:3px}

/* ambient drift */
.drift-layer{position:absolute;inset:0;pointer-events:none;z-index:0}
.drift{position:absolute;bottom:-60px;opacity:.55;animation:drift 26s linear infinite}
.d1{left:4%;animation-duration:28s}.d2{left:12%;animation-duration:34s;animation-delay:-9s}.d3{right:6%;animation-duration:31s;animation-delay:-4s}
.d4{right:14%;animation-duration:24s;animation-delay:-14s}.d5{left:48%;animation-duration:38s;animation-delay:-20s}
:root[data-tab-hidden] .drift,:root[data-tab-hidden] .bob,.drift-layer[data-offscreen] .drift{animation-play-state:paused}

@keyframes draw{to{stroke-dashoffset:0}}
@keyframes bob{0%,100%{transform:translateY(0) rotate(-2deg)}50%{transform:translateY(-7px) rotate(2deg)}}
@keyframes drift{0%{transform:translate(0,0)}25%{transform:translate(14px,-25vh)}50%{transform:translate(-10px,-50vh)}75%{transform:translate(12px,-75vh)}100%{transform:translate(0,-110vh)}}
@keyframes inflate{from{transform:scale(.55,.6)}to{transform:scale(1,1)}}
@keyframes release{0%{transform:translate(0,0) rotate(0)}30%{transform:translate(-6px,-60px) rotate(-6deg)}100%{transform:translate(18px,-420px) rotate(8deg)}}
@keyframes band-parallax{to{transform:translateY(48px)}}

/* tablet */
@media (max-width:1023px){
  .perm-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  .acc-table thead{display:none}
  .acc-table,.acc-table tbody{display:block}
  .acc-table tbody{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
  .acc-row{position:relative;display:grid;grid-template-columns:1fr auto;gap:6px 12px;padding:16px;border:1.5px solid var(--line);border-radius:6px 6px 18px 18px;background:var(--card)}
  .acc-table td{display:block;padding:0;border:0}
  .acc-table td[data-label]{grid-column:1/-1;font-size:14px}
  .acc-table td[data-label]::before{content:attr(data-label) ": ";color:var(--ink-2);font-size:13px}
  .c-person{grid-column:1;grid-row:1}.c-act{grid-column:2;grid-row:1;width:auto}
  .brand{padding-left:0}
}
/* phone */
@media (max-width:639px){
  .venue{font-size:15px}
  .garland-band{height:118px}.garland-band.is-signed{height:156px}
  .cluster .balloon{--s:30px!important}
  .band-row{grid-template-columns:1fr auto;padding:12px 20px 0;gap:8px}
  .brand{display:none}
  .garland-nav{gap:8px}
  .nav-balloon{min-width:72px;padding:4px 4px 8px}
  .nav-balloon .balloon{--s:38px!important}
  .foil-text{display:none}
  .drop-zone{padding:0 12px}
  .placard{margin-top:16px}
  .placard-body{padding:24px 20px;border-radius:22px}
  .pl-title{font-size:32px}.pl-title--admin{font-size:38px}
  .split{grid-template-columns:1fr;gap:22px}
  .acc-table tbody{grid-template-columns:1fr}
  .perm-grid,.perm-pick{grid-template-columns:1fr}
  .facts div{grid-template-columns:1fr;gap:2px}
  .pl-dialog{padding:24px 20px}
  .admin-head .pl-btn{width:100%}
  .role-tag{min-width:0;flex:1 1 140px}
  .link-row{flex-direction:column;align-items:stretch}
  .ribbon--l{left:calc(22% + 5px)}.ribbon--r{right:calc(22% + 5px)}
}
/* reduced motion and ?still=1: everything at rest, nothing travels */
@media (prefers-reduced-motion:reduce){
  .garland-string{animation:none;stroke-dashoffset:0}
  .bob,.drift,.inflate,.release,.empty-balloon,.garland-band{animation:none!important}
  .release{display:none}
}
:root[data-reduced-motion] .garland-string{animation:none;stroke-dashoffset:0}
:root[data-reduced-motion] :is(.bob,.drift,.inflate,.release,.empty-balloon,.garland-band){animation:none!important}
:root[data-reduced-motion] .release{display:none}
:root[data-reduced-motion] *{transition-duration:0s!important}
`;

mountMockup(App, {
  title: "Cuentas y acceso · dirección B «Guirnalda»",
  views: [
    { id: "ingresar", label: "Iniciar sesión" },
    { id: "activar", label: "Activar invitación" },
    { id: "restablecer", label: "Restablecer contraseña" },
    { id: "aviso", label: "Aviso nuevo (re-aceptación)" },
    { id: "mi-cuenta", label: "Mi cuenta" },
    { id: "cuentas", label: "Administración · Cuentas" },
    { id: "roles", label: "Administración · Roles" },
  ],
  states: [
    { id: "normal", label: "Normal" },
    { id: "cargando", label: "Cargando" },
    { id: "error", label: "Error" },
    { id: "exito", label: "Éxito" },
    { id: "vacio", label: "Vacío / sin resultados" },
    { id: "enlace-invalido", label: "Enlace usado o vencido" },
    { id: "sin-permiso", label: "Sin permiso (403)" },
  ],
  scenes: [
    { id: "", label: "Ninguno" },
    { id: "menu-cuenta", label: "Menú de cuenta" },
    { id: "invitar", label: "Invitar persona" },
    { id: "invitar-duplicado", label: "Invitar: correo ya registrado" },
    { id: "invitar-enlace", label: "Invitar: enlace de un solo uso" },
    { id: "cambiar-rol", label: "Cambiar rol" },
    { id: "enlace-restablecer", label: "Generar enlace de restablecimiento" },
    { id: "desactivar", label: "Desactivar cuenta" },
    { id: "reactivar", label: "Reactivar cuenta" },
    { id: "eliminar", label: "Eliminar cuenta sin trabajo" },
    { id: "eliminar-con-trabajo", label: "Eliminar: cuenta con trabajo" },
    { id: "eliminar-ultimo-admin", label: "Eliminar: último administrador" },
    { id: "rol-editor", label: "Editar rol propio" },
    { id: "rol-sin-permisos", label: "Crear rol sin permisos" },
    { id: "rol-eliminar-en-uso", label: "Eliminar rol con cuentas" },
  ],
});
