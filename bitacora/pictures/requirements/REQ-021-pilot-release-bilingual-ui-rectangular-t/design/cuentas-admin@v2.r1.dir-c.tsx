// cuentas-admin@v2 · r1 · direction C — «Ficha en su sitio» (direct manipulation).
// Planning mockup of a CHANGE to the existing /cuenta page and the shared signed-in account menu of Pictures.
// Shell reproduced from production (MenuCuenta bar, CabeceraCuentas, NavegacionCuentas, 676px column); only the
// identity/password area and the menu presentation/dismissal change. Mock data only; no real account operation.
import * as React from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Check, ChevronDown, CircleAlert, LoaderCircle } from 'lucide-react';
import { mountMockup, useMockup } from '@kit/mockup';
import { useMotionProfile } from '@kit/motion';
import { accountStyles as css } from './cuentas-admin@v2.r1.dir-c.styles';
// Shared presentation styles live in the adjacent styles module.

type Lang = 'es' | 'en';

// Strings from src/components/cuentas/textos-cuenta.ts (production) plus the few v2 labels the brief names
// (Nombre/Name, Correo/Email, Plan, Empresa) and the proposed too-long / hint / cancel copy (open questions).
const COPY = {
  es: {
    account: 'Cuenta', role: 'Rol', plan: 'Plan', myAccount: 'Mi cuenta', administration: 'Administración',
    rolesAdministration: 'Roles y permisos', plans: 'Planes', language: 'Idioma', signOut: 'Cerrar sesión',
    signOutPending: 'Cerrando sesión…', signOutError: 'No se pudo cerrar la sesión. Inténtalo de nuevo.',
    title: 'Mi cuenta', active: 'Tu cuenta está activa.', identity: 'Tu identidad', name: 'Nombre', email: 'Correo',
    company: 'Empresa', password: 'Contraseña', changePassword: 'Cambiar contraseña', cancel: 'Cancelar',
    currentPassword: 'Contraseña actual', newPassword: 'Contraseña nueva', repeatPassword: 'Repite la contraseña nueva',
    submit: 'Cambiar contraseña', required: 'Completa los tres campos de contraseña.',
    fieldRequired: 'Este campo es obligatorio.',
    mismatch: 'Las contraseñas nuevas no coinciden.', tooShort: 'La contraseña nueva debe tener al menos 8 caracteres.',
    tooLong: 'La contraseña nueva debe tener como máximo 200 caracteres.', hint: 'Entre 8 y 200 caracteres.',
    currentInvalid: 'La contraseña actual no es correcta. Inténtalo de nuevo.',
    changeError: 'No se pudo cambiar la contraseña. Inténtalo de nuevo.',
    changed: 'Contraseña cambiada. Esta sesión se renovó; tus otras sesiones terminaron.', loading: 'Guardando…',
    accountsNav: 'Cuentas', navLabel: 'Navegación de cuentas', accountsTitle: 'Cuentas',
    unchanged: 'Contenido de esta página según cuentas-admin@v1, sin cambios. Solo el menú de cuenta compartido cambia en v2.',
    mock: 'Mockup · Datos de ejemplo y operaciones simuladas', masked: 'Contraseña guardada',
  },
  en: {
    account: 'Account', role: 'Role', plan: 'Plan', myAccount: 'My account', administration: 'Administration',
    rolesAdministration: 'Roles and permissions', plans: 'Plans', language: 'Language', signOut: 'Sign out',
    signOutPending: 'Signing out…', signOutError: 'Could not sign out. Please try again.',
    title: 'My account', active: 'Your account is active.', identity: 'Your identity', name: 'Name', email: 'Email',
    company: 'Company', password: 'Password', changePassword: 'Change password', cancel: 'Cancel',
    currentPassword: 'Current password', newPassword: 'New password', repeatPassword: 'Repeat new password',
    submit: 'Change password', required: 'Complete all three password fields.', fieldRequired: 'This field is required.',
    mismatch: 'The new passwords do not match.', tooShort: 'The new password must be at least 8 characters.',
    tooLong: 'The new password must be at most 200 characters.', hint: 'Between 8 and 200 characters.',
    currentInvalid: 'The current password is incorrect. Try again.',
    changeError: 'Could not change the password. Please try again.',
    changed: 'Password changed. This session was renewed; your other sessions ended.', loading: 'Saving…',
    accountsNav: 'Accounts', navLabel: 'Account navigation', accountsTitle: 'Accounts',
    unchanged: 'This page keeps its cuentas-admin@v1 content unchanged. Only the shared account menu changes in v2.',
    mock: 'Mockup · Sample data and simulated operations', masked: 'Saved password',
  },
} as const;

// Catalogue names from src/lib/planes/catalogo.ts (plan-catalogue@1).
const PLANS = {
  entusiasta: { es: 'Entusiasta', en: 'Enthusiast' },
  designer: { es: 'Designer', en: 'Designer' },
  designer_plus: { es: 'Designer Plus', en: 'Designer Plus' },
  master_designer: { es: 'Master Designer', en: 'Master Designer' },
} as const;
type PlanId = keyof typeof PLANS;

type Access = { kind: 'plan'; plan: PlanId } | { kind: 'role'; name: { es: string; en: string } };
type Fixture = { name: string | null; email: string; access: Access; company?: string; perms: ('cuentas' | 'roles')[] };

const FIX: Record<string, Fixture> = {
  designerPlus: { name: 'Cuenta Designer Plus', email: 'designerplus@prueba.local', access: { kind: 'plan', plan: 'designer_plus' }, company: 'Empresa de ejemplo', perms: [] },
  entusiasta: { name: 'Cuenta Entusiasta', email: 'entusiasta@prueba.local', access: { kind: 'plan', plan: 'entusiasta' }, perms: [] },
  designer: { name: 'Cuenta Designer', email: 'designer@prueba.local', access: { kind: 'plan', plan: 'designer' }, perms: [] },
  master: { name: 'Cuenta Master Designer', email: 'master@prueba.local', access: { kind: 'plan', plan: 'master_designer' }, perms: [] },
  admin: { name: 'Cuenta administradora', email: 'admin@prueba.local', access: { kind: 'role', name: { es: 'Administrador', en: 'Administrator' } }, perms: ['cuentas', 'roles'] },
  empleado: { name: 'Cuenta de empleado interno', email: 'empleado@prueba.local', access: { kind: 'role', name: { es: 'Empleado interno', en: 'Internal employee' } }, perms: [] },
  custom: { name: 'Cuenta con rol personalizado', email: 'rolpropio@prueba.local', access: { kind: 'role', name: { es: 'Rol personalizado de ejemplo', en: 'Rol personalizado de ejemplo' } }, perms: [] },
  sinNombre: { name: '   ', email: 'sinnombre@prueba.local', access: { kind: 'plan', plan: 'designer' }, perms: [] },
  largo: { name: 'Cuenta de ejemplo con un nombre deliberadamente largo para probar el ajuste de línea', email: 'cuenta.de.ejemplo.con.un.correo.deliberadamente.largo@subdominio.prueba.local', access: { kind: 'plan', plan: 'master_designer' }, company: 'Empresa de ejemplo con una razón social larga para comprobar el ajuste', perms: [] },
};

const STATE_FIXTURE: Record<string, keyof typeof FIX> = {
  'fx-entusiasta': 'entusiasta', 'fx-designer': 'designer', 'fx-master': 'master', 'fx-admin': 'admin',
  'fx-empleado': 'empleado', 'fx-rol': 'custom', 'fx-sin-nombre': 'sinNombre', 'fx-largo': 'largo',
};

const short = (s: string) => (s.length > 26 ? `${s.slice(0, 25).trimEnd()}…` : s);
const displayName = (f: Fixture) => (f.name && f.name.trim() ? f.name.trim() : f.email);
const accessLabel = (f: Fixture, lang: Lang) => (f.access.kind === 'plan' ? COPY[lang].plan : COPY[lang].role);
const accessValue = (f: Fixture, lang: Lang) => (f.access.kind === 'plan' ? PLANS[f.access.plan][lang] : f.access.name[lang]);

let savedLang: Lang = 'es';
function useLang(): [Lang, (l: Lang) => void] {
  const [lang, set] = React.useState<Lang>(savedLang);
  return [lang, (l: Lang) => { savedLang = l; set(l); }];
}



function AccountMenu({ fx, lang, setLang, initialOpen, signOutState, current }: { fx: Fixture; lang: Lang; setLang: (l: Lang) => void; initialOpen: boolean; signOutState: 'idle' | 'pending' | 'error'; current: 'cuenta' | 'cuentas' }) {
  const c = COPY[lang];
  const { reduced, spring } = useMotionProfile();
  const [open, setOpen] = React.useState(initialOpen);
  const [signOut, setSignOut] = React.useState(signOutState);
  const wrap = React.useRef<HTMLDivElement>(null);
  const trigger = React.useRef<HTMLButtonElement>(null);
  const name = displayName(fx);

  React.useEffect(() => {
    if (!open) return;
    // Outside pointer closes without stealing focus: the clicked focusable target keeps it.
    const onDown = (e: PointerEvent) => { if (wrap.current && !wrap.current.contains(e.target as Node)) setOpen(false); };
    // Escape closes and returns focus to the trigger.
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { e.stopPropagation(); setOpen(false); trigger.current?.focus(); } };
    document.addEventListener('pointerdown', onDown, true);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('pointerdown', onDown, true); document.removeEventListener('keydown', onKey); };
  }, [open]);

  // Tab / Shift+Tab may leave freely; the panel closes once focus is outside it (no trap).
  const onBlur = (e: React.FocusEvent<HTMLDivElement>) => {
    const next = e.relatedTarget as Node | null;
    if (next && wrap.current && !wrap.current.contains(next)) setOpen(false);
  };

  const doSignOut = () => {
    setSignOut('pending');
    window.setTimeout(() => setSignOut('error'), 900); // mockup: sign-out never leaves the preview
  };

  return (
    <div className="account-menu" ref={wrap} onBlur={onBlur}>
      <button
        ref={trigger}
        type="button"
        className="menu-trigger"
        aria-expanded={open}
        aria-controls="account-menu-panel"
        aria-label={`${c.account}: ${name}`}
        onClick={() => setOpen((o) => !o)}
      >
        <span className="initial" aria-hidden="true">{name.slice(0, 1).toLocaleUpperCase()}</span>
        <span className="name">{short(name)}</span>
        <ChevronDown className="chev" aria-hidden="true" size={16} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            id="account-menu-panel"
            className="menu-panel"
            lang={lang}
            initial={reduced ? false : { opacity: 0, y: -10, scale: 0.94 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduced ? { opacity: 0, transition: { duration: 0 } } : { opacity: 0, y: -6, scale: 0.97, transition: { duration: 0.12 } }}
            transition={reduced ? { duration: 0 } : spring}
          >
            <div className="menu-who">
              <span className="initial" aria-hidden="true">{name.slice(0, 1).toLocaleUpperCase()}</span>
              <div style={{ minWidth: 0 }}>
                <p className="menu-name">{name}</p>
                <p className="menu-email">{fx.email}</p>
                <p className="access-chip"><span>{accessLabel(fx, lang)}</span><b>{accessValue(fx, lang)}</b></p>
              </div>
            </div>
            <div className="menu-lang" role="group" aria-label={c.language}>
              <span>{c.language}</span>
              <span className="lang-pair">
                {(['es', 'en'] as const).map((l) => (
                  <button key={l} type="button" className="lang-btn" aria-pressed={lang === l} onClick={() => setLang(l)}>{l.toUpperCase()}</button>
                ))}
              </span>
            </div>
            <div className="menu-links">
              <a className="menu-link" href="#cuenta" aria-current={current === 'cuenta' ? 'page' : undefined} onClick={(e) => e.preventDefault()}>{c.myAccount}</a>
              {fx.perms.includes('cuentas') && <a className="menu-link" href="#admin-cuentas" aria-current={current === 'cuentas' ? 'page' : undefined} onClick={(e) => e.preventDefault()}>{c.administration}</a>}
              {fx.perms.includes('roles') && <a className="menu-link" href="#admin-roles" onClick={(e) => e.preventDefault()}>{c.rolesAdministration}</a>}
              <a className="menu-link" href="#planes" onClick={(e) => e.preventDefault()}>{c.plans}</a>
              <button type="button" className="signout" onClick={doSignOut} disabled={signOut === 'pending'}>
                {signOut === 'pending' ? c.signOutPending : c.signOut}
              </button>
              {signOut === 'error' && <p role="alert" className="menu-alert">{c.signOutError}</p>}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Shell({ fx, lang, setLang, current, menuOpen, signOutState, children }: { fx: Fixture; lang: Lang; setLang: (l: Lang) => void; current: 'cuenta' | 'cuentas'; menuOpen: boolean; signOutState: 'idle' | 'pending' | 'error'; children: React.ReactNode }) {
  const c = COPY[lang];
  const routes = [
    ...(fx.perms.includes('cuentas') ? [{ id: 'cuentas', label: c.accountsNav }] : []),
    ...(fx.perms.includes('roles') ? [{ id: 'roles', label: c.rolesAdministration }] : []),
    { id: 'cuenta', label: c.myAccount },
  ];
  return (
    <>
      <header className="account-bar" lang={lang}>
        <AccountMenu fx={fx} lang={lang} setLang={setLang} initialOpen={menuOpen} signOutState={signOutState} current={current} />
      </header>
      <main className="column" lang={lang}>
        <header className="cabecera">
          <div className="brand" aria-label="Pictures Sempertex">
            <span className="brand-ring" aria-hidden="true"><i /></span>
            <span>Pictures <span className="co">· Sempertex</span></span>
          </div>
          <label className="idioma">
            <span>{c.language}</span>
            <select aria-label={c.language} value={lang} onChange={(e) => setLang(e.target.value as Lang)}>
              <option value="es">ES</option>
              <option value="en">EN</option>
            </select>
          </label>
        </header>
        <h1 className="page-title">{current === 'cuenta' ? c.title : c.accountsTitle}</h1>
        {current === 'cuenta' && <p className="page-sub">{c.active}</p>}
        <nav className="route-nav" aria-label={c.navLabel}>
          {routes.map((r) => (
            <a key={r.id} href={`#${r.id}`} aria-current={r.id === current ? 'page' : undefined} onClick={(e) => e.preventDefault()}>{r.label}</a>
          ))}
        </nav>
        {children}
        <p className="foot">{c.mock}</p>
      </main>
    </>
  );
}

type PwState = 'closed' | 'open' | 'required' | 'short' | 'long' | 'mismatch' | 'current' | 'pending' | 'error' | 'success';
type Pw = { current: string; next: string; repeat: string };

const PRESET: Partial<Record<PwState, Pw>> = {
  required: { current: '', next: 'ejemplo-clave-2', repeat: '' },
  short: { current: 'actual-de-ejemplo', next: 'corta7', repeat: 'corta7' },
  long: { current: 'actual-de-ejemplo', next: 'x'.repeat(200), repeat: 'x'.repeat(200) },
  mismatch: { current: 'actual-de-ejemplo', next: 'ejemplo-clave-2', repeat: 'ejemplo-clave-3' },
  current: { current: 'incorrecta', next: 'ejemplo-clave-2', repeat: 'ejemplo-clave-2' },
  pending: { current: 'actual-de-ejemplo', next: 'ejemplo-clave-2', repeat: 'ejemplo-clave-2' },
  error: { current: 'actual-de-ejemplo', next: 'ejemplo-clave-2', repeat: 'ejemplo-clave-2' },
};

function PasswordRow({ lang, initial, index }: { lang: Lang; initial: PwState; index: number }) {
  const c = COPY[lang];
  const { reduced, spring } = useMotionProfile();
  const [state, setState] = React.useState<PwState>(initial);
  const [pw, setPw] = React.useState<Pw>(PRESET[initial] ?? { current: '', next: '', repeat: '' });
  const editing = state !== 'closed' && state !== 'success';
  const pending = state === 'pending';

  const openEditor = () => { setPw({ current: '', next: '', repeat: '' }); setState('open'); window.setTimeout(() => document.getElementById('pw-current')?.focus(), 30); };
  const close = () => { setPw({ current: '', next: '', repeat: '' }); setState('closed'); window.setTimeout(() => document.getElementById('pw-toggle')?.focus(), 30); };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!pw.current || !pw.next || !pw.repeat) return setState('required');
    if (pw.next.length < 8) return setState('short');
    if (pw.next.length > 200) return setState('long');
    if (pw.next !== pw.repeat) return setState('mismatch');
    setState('pending');
    // Mockup service: «incorrecta» simulates a wrong current password; anything else succeeds.
    window.setTimeout(() => {
      if (pw.current === 'incorrecta') { setState('current'); return; }
      setPw({ current: '', next: '', repeat: '' });
      setState('success');
      window.setTimeout(() => document.getElementById('pw-toggle')?.focus(), 30);
    }, 900);
  };

  const errFor = (field: keyof Pw): string | null => {
    if (state === 'required' && !pw[field]) return c.fieldRequired;
    if (field === 'next' && state === 'short') return c.tooShort;
    if (field === 'next' && state === 'long') return c.tooLong;
    if (field === 'repeat' && state === 'mismatch') return c.mismatch;
    if (field === 'current' && state === 'current') return c.currentInvalid;
    return null;
  };
  const summary = state === 'required' ? c.required : state === 'error' ? c.changeError : null;
  const lenOk = pw.next.length >= 8 && pw.next.length <= 200;
  const matchOk = pw.repeat.length > 0 && pw.repeat === pw.next;

  const fields: { key: keyof Pw; label: string; auto: string }[] = [
    { key: 'current', label: c.currentPassword, auto: 'current-password' },
    { key: 'next', label: c.newPassword, auto: 'new-password' },
    { key: 'repeat', label: c.repeatPassword, auto: 'new-password' },
  ];

  return (
    <>
      <div className="fila fila-pass" data-editing={editing} style={{ ['--i' as string]: index }}>
        <span className="k" id="pw-label">{c.password}</span>
        <span className="v"><span className="masked" role="img" aria-label={c.masked}>••••••••</span></span>
        {!editing && (
          <Button id="pw-toggle" type="button" className="act" data-variant="outline" aria-expanded={false} onClick={openEditor}>
            {c.changePassword}
          </Button>
        )}
        {state === 'success' && (
          <p className="sealed" role="status">
            <svg className="seal-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
            <span>{c.changed}</span>
          </p>
        )}
      </div>
      <AnimatePresence initial={!reduced}>
        {editing && (
          <motion.div
            id="pw-drawer"
            className="drawer"
            role="region"
            aria-labelledby="pw-label"
            initial={reduced ? false : { height: 0, opacity: 0.4 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={reduced ? { height: 0, transition: { duration: 0 } } : { height: 0, opacity: 0, transition: { duration: 0.18 } }}
            transition={reduced ? { duration: 0 } : spring}
          >
            <form className="editor" onSubmit={submit} noValidate aria-busy={pending} onKeyDown={(e) => { if (e.key === 'Escape' && !pending) { e.stopPropagation(); close(); } }}>
              {summary && (
                <p className="summary" role="alert"><CircleAlert aria-hidden="true" /><span>{summary}</span></p>
              )}
              {fields.map((f, i) => {
                const err = errFor(f.key);
                const helpId = `pw-${f.key}-help`;
                return (
                  <div className="field" key={f.key} style={{ ['--i' as string]: i + 1 }}>
                    <label htmlFor={`pw-${f.key}`}>{f.label}</label>
                    <Input
                      id={`pw-${f.key}`}
                      className="pw"
                      type="password"
                      name={f.key}
                      autoComplete={f.auto}
                      required
                      maxLength={f.key === 'current' ? undefined : 200}
                      value={pw[f.key]}
                      disabled={pending}
                      aria-invalid={err ? true : undefined}
                      aria-describedby={err || f.key !== 'current' ? helpId : undefined}
                      onChange={(e) => { const v = e.target.value; setPw((p) => ({ ...p, [f.key]: v })); if (state !== 'open' && state !== 'pending') setState('open'); }}
                    />
                    {f.key === 'next' && !err && (
                      <>
                        <div className="meter" data-ok={lenOk} aria-hidden="true"><i style={{ transform: `scaleX(${Math.min(pw.next.length / 8, 1)})` }} /></div>
                        <p className="field-help" id={helpId} data-ok={lenOk}>{lenOk ? <Check aria-hidden="true" /> : null}{c.hint}</p>
                      </>
                    )}
                    {f.key === 'repeat' && !err && matchOk && (
                      <p className="field-help" id={helpId} data-ok="true"><Check aria-hidden="true" />{lang === 'es' ? 'Coinciden.' : 'They match.'}</p>
                    )}
                    {err && <p className="field-error" id={helpId}><CircleAlert aria-hidden="true" />{err}</p>}
                  </div>
                );
              })}
              <div className="editor-actions" style={{ ['--i' as string]: 4 }}>
                <Button type="submit" className="act" data-variant="primary" disabled={pending}>
                  {pending ? <><LoaderCircle className="spin" aria-hidden="true" size={16} />{c.loading}</> : c.submit}
                </Button>
                <Button type="button" className="act" data-variant="outline" onClick={close} disabled={pending}>{c.cancel}</Button>
              </div>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

function IdentitySheet({ fx, lang, pw }: { fx: Fixture; lang: Lang; pw: PwState }) {
  const c = COPY[lang];
  const name = displayName(fx);
  let i = 0;
  return (
    <section className="ficha" aria-labelledby="identidad">
      <h2 id="identidad">{c.identity}</h2>
      <div className="plate">
        <span className="initial" aria-hidden="true">{name.slice(0, 1).toLocaleUpperCase()}</span>
        <dl className="id-pair">
          <div><dt>{c.name}</dt><dd className="id-name">{name}</dd></div>
          <div><dt>{c.email}</dt><dd className="id-email">{fx.email}</dd></div>
        </dl>
      </div>
      <dl className="rows">
        <div className="fila" style={{ ['--i' as string]: ++i }}>
          <dt className="k">{accessLabel(fx, lang)}</dt>
          <dd className="v">{accessValue(fx, lang)}</dd>
        </div>
        {fx.company && (
          <div className="fila" style={{ ['--i' as string]: ++i }}>
            <dt className="k">{c.company}</dt>
            <dd className="v">{fx.company}</dd>
          </div>
        )}
      </dl>
      <PasswordRow lang={lang} initial={pw} index={++i} />
    </section>
  );
}

function LoadingSheet({ lang }: { lang: Lang }) {
  return (
    <section className="ficha" aria-busy="true" aria-label={COPY[lang].identity}>
      <div className="skeleton-rows">
        <div style={{ display: 'flex', gap: 20, alignItems: 'center' }}>
          <Skeleton style={{ width: 64, height: 64, borderRadius: 999 }} />
          <div style={{ display: 'grid', gap: 10, flex: 1 }}><Skeleton style={{ height: 22, width: '60%' }} /><Skeleton style={{ height: 16, width: '75%' }} /></div>
        </div>
        <Skeleton style={{ height: 44 }} />
        <Skeleton style={{ height: 44 }} />
      </div>
    </section>
  );
}

const PW_STATES: Record<string, PwState> = {
  'pw-abierto': 'open', 'pw-requerido': 'required', 'pw-corta': 'short', 'pw-larga': 'long', 'pw-distintas': 'mismatch',
  'pw-actual': 'current', 'pw-guardando': 'pending', 'pw-error': 'error', 'pw-exito': 'success',
};

function App() {
  const { view, state, motion: profile, reduced } = useMockup();
  const [lang, setLang] = useLang();
  React.useEffect(() => {
    const on = () => document.documentElement.toggleAttribute('data-tab-hidden', document.hidden);
    document.addEventListener('visibilitychange', on);
    return () => document.removeEventListener('visibilitychange', on);
  }, []);
  const fxKey = STATE_FIXTURE[state] ?? (view === 'otra' ? 'admin' : 'designerPlus');
  const fx = FIX[fxKey];
  const pw = PW_STATES[state] ?? 'closed';
  const signOutState = state === 'salida-pendiente' ? 'pending' : state === 'salida-error' ? 'error' : 'idle';
  const menuOpen = view === 'menu' || signOutState !== 'idle';
  return (
    <div className="app" data-profile={reduced ? 'still' : profile}>
      <style>{css}</style>
      {view === 'otra' ? (
        <Shell fx={fx} lang={lang} setLang={setLang} current="cuentas" menuOpen={state !== 'menu-cerrado'} signOutState={signOutState}>
          <p className="unchanged">{COPY[lang].unchanged}</p>
        </Shell>
      ) : (
        <Shell fx={fx} lang={lang} setLang={setLang} current="cuenta" menuOpen={menuOpen && state !== 'menu-cerrado'} signOutState={signOutState}>
          {state === 'cargando' ? <LoadingSheet lang={lang} /> : <IdentitySheet fx={fx} lang={lang} pw={view === 'menu' ? 'closed' : pw} />}
        </Shell>
      )}
    </div>
  );
}

mountMockup(App, {
  title: 'cuentas-admin@v2 · Mi cuenta y menú de cuenta · dirección C «Ficha en su sitio»',
  views: [
    { id: 'cuenta', label: 'Mi cuenta (/cuenta)' },
    { id: 'menu', label: 'Menú abierto' },
    { id: 'otra', label: 'Menú en Cuentas (v1)' },
  ],
  states: [
    { id: 'normal', label: 'Designer Plus + empresa' },
    { id: 'fx-entusiasta', label: 'Plan Entusiasta' },
    { id: 'fx-designer', label: 'Plan Designer' },
    { id: 'fx-master', label: 'Plan Master Designer' },
    { id: 'fx-admin', label: 'Administrador' },
    { id: 'fx-empleado', label: 'Empleado interno' },
    { id: 'fx-rol', label: 'Rol personalizado' },
    { id: 'fx-sin-nombre', label: 'Sin nombre' },
    { id: 'fx-largo', label: 'Datos largos' },
    { id: 'menu-cerrado', label: 'Menú cerrado' },
    { id: 'cargando', label: 'Cargando' },
    { id: 'pw-abierto', label: 'Clave · editor abierto' },
    { id: 'pw-requerido', label: 'Clave · obligatorios' },
    { id: 'pw-corta', label: 'Clave · corta' },
    { id: 'pw-larga', label: 'Clave · larga' },
    { id: 'pw-distintas', label: 'Clave · no coinciden' },
    { id: 'pw-actual', label: 'Clave · actual incorrecta' },
    { id: 'pw-guardando', label: 'Clave · guardando' },
    { id: 'pw-error', label: 'Clave · error servicio/red' },
    { id: 'pw-exito', label: 'Clave · cambiada' },
    { id: 'salida-pendiente', label: 'Salida · pendiente' },
    { id: 'salida-error', label: 'Salida · error' },
  ],
});
