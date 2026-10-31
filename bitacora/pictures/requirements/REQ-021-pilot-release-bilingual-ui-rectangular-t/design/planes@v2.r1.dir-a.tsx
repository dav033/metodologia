// planes@v2 · r1 · direction A — «Fichas en fila»: operational reading of the four access plans.
// A CHANGE to the published /planes surface (commit 0715a331): same masthead, heading row, back link, tokens and
// Geist font; the comparison tabs, plan index rail, highlighted plan and selection summary are removed and the
// divided sheet becomes four peer subscription cards in one row whose headers align through CSS subgrid.
// Signed-in composition reuses the shared account bar/menu of cuentas-admin@v2 (chosen, draft) unchanged.
import * as React from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { Check, ChevronDown, ChevronLeft, CircleAlert, CircleDashed, Moon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { mountMockup, useMockup } from '@kit/mockup';
import { useMotionProfile } from '@kit/motion';
import bodyFont from '/home/david/dev/pictures-wt/t12/.next/static/media/caa3a2e1cccd8315-s.p.0wgildi0cnwt9.woff2';

type Lang = 'es' | 'en';

// Fixture copied from src/lib/planes/catalogo.ts (plan-catalogue@1) at 0715a331 — not an alternative catalogue.
// The chat line renders the tool `descripcion`, exactly as the published page does.
type Tool = { id: string; label: Record<Lang, string>; available: boolean };
const T = (id: string, es: string, en: string, available = true): Tool => ({ id, label: { es, en }, available });
const chat = T('chat', 'Chat asistido con límites.', 'Assisted chat with limits.');
const chatHigher = T('chat', 'Chat asistido con límites más altos.', 'Assisted chat with higher limits.');
const counter = T('contador_globos', 'Contador de globos', 'Balloon counter');
const catalog = T('catalogo', 'Catálogo', 'Catalog');
const costs = T('calculadora_costos', 'Calculadora de costos', 'Cost calculator');
const extended = T('chat_extendido', 'Chat extendido', 'Extended chat', false);
const structure = T('deteccion_estructura', 'Detección de estructura', 'Structure detection', false);
const advanced = T('deteccion_globos_avanzada', 'Detección avanzada de globos', 'Advanced balloon detection', false);
const workshop = T('taller_3d', 'Taller 3D', '3D workshop');

const PLANES = [
  { id: 'entusiasta', name: { es: 'Entusiasta', en: 'Enthusiast' }, cop: 0, usd: 0, tools: [chat, counter, catalog] },
  { id: 'designer', name: { es: 'Designer', en: 'Designer' }, cop: 20000, usd: 7, tools: [chatHigher, counter, catalog] },
  { id: 'designer_plus', name: { es: 'Designer Plus', en: 'Designer Plus' }, cop: 45000, usd: 14, tools: [chatHigher, counter, catalog, costs, extended, structure, advanced] },
  { id: 'master_designer', name: { es: 'Master Designer', en: 'Master Designer' }, cop: 70000, usd: 25, tools: [chatHigher, counter, catalog, costs, extended, structure, advanced, workshop] },
] as const;

// Copy: textos-planes.ts (kept keys only), textos-acceso.ts, textos-cuenta.ts, approved planes@v1 state copy.
const COPY = {
  es: {
    language: 'Idioma', title: 'Planes', backSignedOut: 'Volver al acceso', backSignedIn: 'Volver',
    includedTools: 'Herramientas incluidas', administrator: 'Un administrador asigna el plan.', free: 'Gratis',
    monthly: 'COP / mes', unavailable: 'aún no disponible', loading: 'Cargando planes…',
    errorTitle: 'No se pudieron cargar los planes', errorBody: 'Vuelve a intentarlo para consultar los planes.', retry: 'Reintentar',
    account: 'Cuenta', plan: 'Plan', myAccount: 'Mi cuenta', plans: 'Planes', signOut: 'Cerrar sesión',
    loginTitle: 'Iniciar sesión', invitationOnly: 'El acceso a Pictures es solo por invitación de un administrador.',
    recoveryGuidance: 'Para restablecer tu contraseña, pídele al administrador que genere un enlace de recuperación.',
    email: 'Correo electrónico', password: 'Contraseña', enter: 'Entrar',
    resetGuidance: '¿Olvidaste tu contraseña? Pide al administrador un enlace de restablecimiento. Es de un solo uso y dura 24 horas.',
    theme: 'Cambiar tema', mock: 'Mockup · Datos de ejemplo', url: 'URL simulada',
  },
  en: {
    language: 'Language', title: 'Plans', backSignedOut: 'Back to sign in', backSignedIn: 'Back',
    includedTools: 'Included tools', administrator: 'An administrator assigns the plan.', free: 'Free',
    monthly: 'USD / month', unavailable: 'not available yet', loading: 'Loading plans…',
    errorTitle: 'Could not load plans', errorBody: 'Try again to view the plans.', retry: 'Retry',
    account: 'Account', plan: 'Plan', myAccount: 'My account', plans: 'Plans', signOut: 'Sign out',
    loginTitle: 'Sign in', invitationOnly: 'Pictures access is by administrator invitation only.',
    recoveryGuidance: 'To reset your password, ask your administrator to generate a recovery link.',
    email: 'Email address', password: 'Password', enter: 'Sign in',
    resetGuidance: 'Forgot your password? Ask your administrator for a reset link. It is single use and valid for 24 hours.',
    theme: 'Change theme', mock: 'Mockup · Sample data', url: 'Simulated URL',
  },
} as const;

// Sample signed-in account, same fixture as cuentas-admin@v2 (clearly mock).
const ACCOUNT = { name: 'Cuenta Designer Plus', email: 'designerplus@prueba.local', planName: { es: 'Designer Plus', en: 'Designer Plus' } };

const formatAmount = (n: number, lang: Lang) => new Intl.NumberFormat(lang === 'es' ? 'es-CO' : 'en-US', { maximumFractionDigits: 0 }).format(n);

const css = `
@font-face{font-family:Geist;src:url(${bodyFont}) format('woff2');font-weight:100 900;font-display:swap}
:root{--fondo:#faf9fc;--superficie:#ffffff;--superficie-suave:#faf8fd;--superficie-2:#efe9f8;--borde:#e3daef;--borde-suave:#efe9f8;--texto:#1c1425;--texto-suave:#6b6178;--texto-tenue:#766c85;--acento:#6d3fe0;--acento-hover:#5530b8;--acento-suave:#ece3fb;--sobre-acento:#ffffff;--error:#b23a45;--error-suave:#ffeaec;--aviso:#8f5f12;--aviso-suave:#fff3d8;--sombra:rgb(28 20 37 / .08);--ease-out:cubic-bezier(.23,1,.32,1);color-scheme:light}
:root.dark,:root[data-theme=dark]{--fondo:#0b0c10;--superficie:#16181f;--superficie-suave:#1c1e26;--superficie-2:#242733;--borde:#383c48;--borde-suave:#2a2d38;--texto:#f4f5f7;--texto-suave:#9aa1ad;--texto-tenue:#8a91a0;--acento:#9479ff;--acento-hover:#a58dff;--acento-suave:#241f3d;--sobre-acento:#120b24;--error:#ff979f;--error-suave:#43252a;--aviso:#f7c46b;--aviso-suave:#3f311c;--sombra:rgb(0 0 0 / .4);color-scheme:dark}
:root{--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--card-foreground:var(--texto);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);--secondary:var(--superficie-2);--secondary-foreground:var(--texto);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--acento-suave);--accent-foreground:var(--acento);--destructive:var(--error);--border:var(--texto-tenue);--input:var(--texto-tenue);--ring:var(--acento);--radius:.8rem;--shadow-float:0 12px 32px var(--sombra)}
*{box-sizing:border-box}
body{margin:0;background:var(--fondo);color:var(--texto);font:15px/1.5 Geist,ui-sans-serif,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
h1,h2,h3,p,ul{margin:0}ul{padding:0;list-style:none}button,input,select{font:inherit}
.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}

/* Motion grammar — precise quick cuts on the product's own --ease-out; no overshoot. */
.shell{--cut:220ms;--stagger:40ms;--row:16ms;--swap:.16}
.shell[data-profile=natural]{--cut:170ms;--stagger:28ms;--row:10ms;--swap:.13}
.shell[data-profile=subtle]{--cut:120ms;--stagger:14ms;--row:6ms;--swap:.1}
.shell[data-reduced=true] *,.shell[data-reduced=true] *::before{animation:none!important;transition:none!important}
.shell[data-hidden=true] *{animation-play-state:paused!important}

/* Shared signed-in bar and account menu — cuentas-admin@v2 composition, unchanged. */
.account-bar{position:relative;z-index:30;min-height:64px;display:flex;align-items:center;justify-content:flex-end;border-bottom:1px solid var(--borde-suave);padding:0 32px}
.account-menu{position:relative}
.menu-trigger{display:flex;align-items:center;gap:8px;min-height:44px;max-width:min(260px,calc(100vw - 32px));padding:0 14px 0 8px;border-radius:999px;border:1px solid var(--texto-tenue);background:var(--superficie);color:var(--texto);font-size:14px;font-weight:500;cursor:pointer;transition:transform 90ms cubic-bezier(.4,0,.7,1),border-color 140ms ease,box-shadow 140ms ease}
.menu-trigger:hover{border-color:var(--acento)}.menu-trigger:active{transform:scale(.95)}
.menu-trigger[aria-expanded=true]{border-color:var(--acento);box-shadow:0 0 0 3px var(--acento-suave)}
.menu-trigger .name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.menu-trigger .chev{color:var(--texto-suave);transition:transform 300ms cubic-bezier(.34,1.42,.64,1)}
.menu-trigger[aria-expanded=true] .chev{transform:rotate(180deg)}
.initial{display:grid;place-items:center;flex-shrink:0;border-radius:999px;background:var(--acento-suave);color:var(--acento);font-weight:650;width:28px;height:28px;font-size:12px}
.menu-panel{position:absolute;right:0;top:calc(100% + 8px);width:304px;max-width:calc(100vw - 32px);background:var(--popover);border:1px solid var(--borde);border-radius:24px;padding:16px;box-shadow:var(--shadow-float);transform-origin:top right;font-size:14px}
.menu-who{display:grid;grid-template-columns:40px minmax(0,1fr);gap:12px;align-items:start}.menu-who .initial{width:40px;height:40px;font-size:16px}
.menu-name{font-weight:600;overflow-wrap:anywhere;line-height:1.35}.menu-email{font-size:13px;color:var(--texto-suave);overflow-wrap:anywhere;margin-top:2px}
.access-chip{display:inline-flex;gap:6px;align-items:baseline;margin-top:10px;padding:3px 12px;border-radius:999px;background:var(--superficie-2);font-size:13px;max-width:100%}
.access-chip span{color:var(--texto-suave)}.access-chip b{font-weight:600}
.menu-lang{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:14px;padding-top:12px;border-top:1px solid var(--borde-suave);font-size:13px;color:var(--texto-suave)}
.lang-pair{display:flex;gap:4px}
.lang-btn{min-height:36px;min-width:44px;border-radius:10px;border:1px solid var(--texto-tenue);background:var(--superficie);color:var(--texto);font-size:12px;font-weight:650;cursor:pointer;transition:transform 90ms cubic-bezier(.4,0,.7,1)}
.lang-btn:active{transform:scale(.92)}.lang-btn[aria-pressed=true]{background:var(--acento);color:var(--sobre-acento);border-color:var(--acento)}
.menu-links{display:grid;gap:2px;margin-top:12px;padding-top:8px;border-top:1px solid var(--borde-suave)}
.menu-link,.signout{display:flex;align-items:center;min-height:44px;padding:0 12px;border-radius:12px;color:var(--acento);font-weight:550;text-decoration:none;border:0;background:none;text-align:left;cursor:pointer;font-size:14px}
.menu-link:hover{background:var(--acento-suave)}.menu-link[aria-current=page]{color:var(--texto);background:var(--superficie-2)}
.signout{color:var(--texto);margin-top:6px;border-top:1px solid var(--borde-suave);border-radius:0 0 12px 12px}.signout:hover{background:var(--superficie-suave)}
.menu-trigger:focus-visible,.menu-link:focus-visible,.lang-btn:focus-visible,.signout:focus-visible{outline:2px solid var(--acento);outline-offset:2px}

/* /planes page — published masthead and heading row, kept. */
.page{width:min(100% - 48px,1440px);margin:0 auto;padding:28px 0 24px}
.masthead{display:flex;justify-content:space-between;align-items:center;gap:20px;padding-bottom:28px}
.brand{display:inline-flex;align-items:center;gap:10px;font-size:15px;font-weight:650;letter-spacing:-.02em}
.brand-mark{display:grid;width:30px;height:30px;place-items:center;border:1px solid var(--borde);border-radius:50%;color:var(--acento)}
.brand-mark span{width:7px;height:7px;border-radius:50%;background:currentColor;box-shadow:0 0 0 5px color-mix(in srgb,currentColor 15%,transparent)}
.company{margin-left:-6px;color:var(--texto-suave);font-weight:400}
.language{display:flex;align-items:center;gap:10px;color:var(--texto-suave);font-size:13px}
.native{min-width:64px;min-height:44px;padding:0 12px;border:1px solid var(--texto-tenue);border-radius:14px;background:var(--superficie);color:var(--texto)}
.heading-row{display:flex;align-items:center;justify-content:space-between;gap:20px}
.heading-row h1{font-size:24px;line-height:1.25;font-weight:600;letter-spacing:-.03em}
.back{display:inline-flex;min-height:44px;align-items:center;gap:7px;color:var(--texto-suave);text-decoration:none;font-size:14px;border-radius:10px}
.back svg{transition:transform 120ms var(--ease-out)}.back:hover{color:var(--acento)}.back:hover svg{transform:translateX(-3px)}.back:active svg{transform:translateX(-5px)}
.context{margin:4px 0 24px;color:var(--texto-suave);font-size:14px;line-height:1.55}
.page a:focus-visible,.page select:focus-visible,.page button:focus-visible,.page input:focus-visible{outline:3px solid var(--acento);outline-offset:3px}

/* Changed area — four peer cards; header rows aligned across a row of cards with subgrid. */
.plan-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;align-items:stretch}
.plan-card{display:grid;grid-row:span 5;grid-template-rows:subgrid;row-gap:0;min-width:0;padding:20px;border:1px solid var(--borde);border-radius:24px;background:var(--superficie);
  animation:card-cut var(--cut) var(--ease-out) both;animation-delay:calc(var(--i) * var(--stagger))}
.plan-name{font-size:16px;line-height:1.35;font-weight:600;overflow-wrap:anywhere}
.price-box{position:relative;overflow:hidden;height:44px;margin-top:6px}
.price-value{position:absolute;inset:0 auto auto 0;display:flex;align-items:baseline;gap:6px;white-space:nowrap;font-size:28px;line-height:44px;font-weight:650;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.price-value small{font-size:12px;font-weight:400;letter-spacing:0;color:var(--texto-suave)}
.plan-rule{height:1px;margin:14px 0 12px;background:var(--borde-suave);transform-origin:left;animation:rule-draw calc(var(--cut) * 1.4) var(--ease-out) both;animation-delay:calc(var(--i) * var(--stagger) + var(--cut) * .5)}
.tools-head{display:flex;align-items:baseline;justify-content:space-between;gap:8px;margin-bottom:4px}
.tools-head h3{font-size:12px;font-weight:550;color:var(--texto-suave)}
.tool-count{font-size:12px;color:var(--texto-tenue);font-variant-numeric:tabular-nums}
.tool-list{align-self:start}
.tool-list li{display:flex;align-items:flex-start;gap:8px;min-width:0;padding:8px 0;border-top:1px solid var(--borde-suave);font-size:14px;line-height:1.45;
  animation:row-in var(--cut) var(--ease-out) both;animation-delay:calc(var(--i) * var(--stagger) + var(--j) * var(--row) + 60ms)}
.tool-list li:first-child{border-top:0}
.tool-list svg{flex:none;width:16px;height:16px;margin-top:2px;color:var(--acento)}
.tool-list li.is-unavailable svg{color:var(--aviso)}
.tool-label{min-width:0;overflow-wrap:anywhere}
.tool-status{display:block;margin-top:1px;font-size:12px;color:var(--aviso)}
@keyframes card-cut{from{transform:translateY(8px);opacity:.6}to{transform:none;opacity:1}}
@keyframes rule-draw{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes row-in{from{transform:translateX(-6px);opacity:.55}to{transform:none;opacity:1}}

/* Loading and catalogue-unavailable states. */
.loading-card{display:grid;gap:12px;padding:20px;border:1px solid var(--borde);border-radius:24px;background:var(--superficie)}
.loading-card [data-slot=skeleton]{background:var(--superficie-2)}
.shell[data-reduced=true] [data-slot=skeleton]{animation:none}
.message{display:grid;justify-items:start;gap:10px;max-width:560px;padding:24px;border:1px solid var(--borde);border-radius:24px;background:var(--superficie);animation:card-cut var(--cut) var(--ease-out) both}
.message h2{display:flex;align-items:center;gap:8px;font-size:18px;font-weight:600;color:var(--error)}
.message h2 svg{width:20px;height:20px}
.message p{color:var(--texto-suave);font-size:14px}
.retry{min-height:44px;padding:0 18px;border-radius:999px;border-color:var(--texto-tenue);transition:transform 90ms cubic-bezier(.4,0,.7,1)}
.retry:active{transform:scale(.97)}

.footer{display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px;margin-top:24px;padding-top:18px;border-top:1px solid var(--borde-suave);color:var(--texto-suave);font-size:12px}

/* Sign-in entry (unchanged surface, shown for flow 1). */
.login{position:relative;display:flex;min-height:calc(100svh - var(--mockup-bar-h,0px));flex-direction:column;align-items:center;justify-content:center;padding:24px 16px}
.theme-btn{position:absolute;top:12px;right:12px;display:grid;place-items:center;width:44px;height:44px;border-radius:12px;border:1px solid var(--texto-tenue);background:var(--superficie);color:var(--texto);cursor:pointer}
.theme-btn svg{width:18px;height:18px}
.acc-head{display:flex;width:100%;max-width:676px;align-items:center;justify-content:space-between;gap:16px;padding:16px 0}
.acc-brand{display:flex;align-items:center;gap:12px;font-size:14px;font-weight:600;letter-spacing:.02em}
.acc-mark{display:grid;place-items:center;width:32px;height:32px;border:2px solid var(--acento);border-radius:50%}.acc-mark span{width:8px;height:8px;border-radius:50%;background:var(--acento)}
.acc-brand small{font-size:14px;font-weight:400;color:var(--texto-suave)}
.acc-lang{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--texto-suave)}.acc-lang .native{min-height:40px;border-radius:.7rem}
.login-card{display:grid;gap:20px;width:100%;max-width:672px;padding:32px;border:1px solid var(--borde-suave);border-radius:1.25rem;background:var(--superficie);box-shadow:0 1px 2px var(--sombra)}
.login-card h1{font-size:24px;font-weight:600}.login-card p{font-size:14px;color:var(--texto-suave)}
.login-card label{display:grid;gap:8px;font-size:14px;font-weight:500}
.login-card [data-slot=input]{height:44px;border-radius:.7rem;border-color:var(--texto-tenue);background:var(--superficie);color:var(--texto)}
.enter{width:100%;min-height:44px;border-radius:.8rem;font-size:14px}
.login-card .center{text-align:center}
.plans-link{display:flex;min-height:44px;align-items:center;justify-content:center;border:1px solid var(--texto-tenue);border-radius:.5rem;color:var(--acento);font-size:14px;font-weight:500;text-decoration:none}
.plans-link:hover{background:var(--superficie-suave)}
.login a:focus-visible,.login button:focus-visible,.login select:focus-visible,.login input:focus-visible{outline:3px solid var(--acento);outline-offset:3px}
.login .footer{width:100%;max-width:672px;flex-direction:column;gap:4px}

@media (max-width:1099px){.plan-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.account-bar{padding:0 24px}}
@media (max-width:639px){
  .page{width:calc(100% - 40px);padding-top:20px}
  .masthead{flex-wrap:wrap;align-items:flex-start;padding-bottom:22px}.language{margin-left:auto}
  .heading-row{flex-direction:column;align-items:flex-start;gap:4px}
  .plan-grid{grid-template-columns:minmax(0,1fr);gap:12px}
  .plan-card{padding:20px}.price-value{font-size:26px}
  .account-bar{padding:0 16px}
  .menu-panel{position:fixed;left:16px;right:16px;top:calc(var(--mockup-bar-h,0px) + 72px);width:auto;max-width:none}
  .login-card{padding:24px 20px}.acc-head{flex-wrap:wrap}
}
`;

function useHidden() {
  const [hidden, setHidden] = React.useState(false);
  React.useEffect(() => {
    const on = () => setHidden(document.hidden);
    document.addEventListener('visibilitychange', on);
    return () => document.removeEventListener('visibilitychange', on);
  }, []);
  return hidden;
}

function AccountMenu({ lang, setLang }: { lang: Lang; setLang: (l: Lang) => void }) {
  const m = useMockup();
  const c = COPY[lang];
  const { reduced, spring } = useMotionProfile();
  const [open, setOpen] = React.useState(m.scene === 'menu');
  const wrap = React.useRef<HTMLDivElement>(null);
  const trigger = React.useRef<HTMLButtonElement>(null);
  React.useEffect(() => setOpen(m.scene === 'menu'), [m.scene]);
  const show = (next: boolean) => { setOpen(next); m.set('scene', next ? 'menu' : ''); };
  React.useEffect(() => {
    if (!open) return;
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape') { show(false); trigger.current?.focus(); } };
    const down = (e: PointerEvent) => { if (wrap.current && !wrap.current.contains(e.target as Node)) show(false); };
    document.addEventListener('keydown', key);
    document.addEventListener('pointerdown', down);
    return () => { document.removeEventListener('keydown', key); document.removeEventListener('pointerdown', down); };
  });
  const onBlur = (e: React.FocusEvent<HTMLDivElement>) => {
    const next = e.relatedTarget as Node | null;
    if (next && wrap.current && !wrap.current.contains(next)) show(false);
  };
  return (
    <div className="account-menu" ref={wrap} onBlur={onBlur}>
      <button ref={trigger} type="button" className="menu-trigger" aria-expanded={open} aria-controls="account-menu-panel"
        aria-label={`${c.account}: ${ACCOUNT.name}`} onClick={() => show(!open)}>
        <span className="initial" aria-hidden="true">{ACCOUNT.name.slice(0, 1)}</span>
        <span className="name">{ACCOUNT.name}</span>
        <ChevronDown className="chev" aria-hidden="true" size={16} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div id="account-menu-panel" className="menu-panel" lang={lang}
            initial={reduced ? false : { opacity: 0, y: -10, scale: 0.94 }} animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduced ? { opacity: 0, transition: { duration: 0 } } : { opacity: 0, y: -6, scale: 0.97, transition: { duration: 0.12 } }}
            transition={reduced ? { duration: 0 } : spring}>
            <div className="menu-who">
              <span className="initial" aria-hidden="true">{ACCOUNT.name.slice(0, 1)}</span>
              <div style={{ minWidth: 0 }}>
                <p className="menu-name">{ACCOUNT.name}</p>
                <p className="menu-email">{ACCOUNT.email}</p>
                <p className="access-chip"><span>{c.plan}</span><b>{ACCOUNT.planName[lang]}</b></p>
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
              <a className="menu-link" href="#cuenta" onClick={(e) => e.preventDefault()}>{c.myAccount}</a>
              <a className="menu-link" href="#planes" aria-current="page" onClick={(e) => { e.preventDefault(); show(false); trigger.current?.focus(); }}>{c.plans}</a>
              <button type="button" className="signout">{c.signOut}</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Price({ plan, lang, index }: { plan: (typeof PLANES)[number]; lang: Lang; index: number }) {
  const c = COPY[lang];
  const { reduced, profile } = useMotionProfile();
  const swap = profile === 'expressive' ? 0.16 : profile === 'natural' ? 0.13 : 0.1;
  const amount = lang === 'es' ? plan.cop : plan.usd;
  return (
    <div className="price-box">
      <AnimatePresence initial={false} mode="popLayout">
        <motion.p key={lang} className="price-value" data-price={plan.id}
          initial={reduced ? false : { y: '70%', opacity: 0.3 }} animate={{ y: '0%', opacity: 1 }}
          exit={reduced ? { opacity: 0, transition: { duration: 0 } } : { y: '-70%', opacity: 0, transition: { duration: swap * 0.75, ease: [0.23, 1, 0.32, 1] } }}
          transition={reduced ? { duration: 0 } : { duration: swap, delay: index * 0.025, ease: [0.23, 1, 0.32, 1] }}>
          {amount === 0 ? c.free : <>{formatAmount(amount, lang)}<small>{c.monthly}</small></>}
        </motion.p>
      </AnimatePresence>
    </div>
  );
}

function PlanGrid({ lang }: { lang: Lang }) {
  const c = COPY[lang];
  return (
    <section className="plan-grid" aria-label={c.title}>
      {PLANES.map((plan, i) => {
        const name = plan.name[lang];
        return (
          <article key={plan.id} className="plan-card" id={`plan-${plan.id}`} aria-labelledby={`plan-title-${plan.id}`} style={{ '--i': i } as React.CSSProperties}>
            <h2 className="plan-name" id={`plan-title-${plan.id}`}>{name}</h2>
            <Price plan={plan} lang={lang} index={i} />
            <div className="plan-rule" aria-hidden="true" />
            <div className="tools-head"><h3>{c.includedTools}</h3><span className="tool-count" aria-hidden="true">{plan.tools.length}</span></div>
            <ul className="tool-list" aria-label={`${c.includedTools}: ${name}`}>
              {plan.tools.map((tool, j) => (
                <li key={tool.id} className={tool.available ? '' : 'is-unavailable'} style={{ '--j': j } as React.CSSProperties}>
                  {tool.available ? <Check aria-hidden="true" /> : <CircleDashed aria-hidden="true" />}
                  <span className="tool-label">{tool.label[lang]}{!tool.available && <small className="tool-status">{c.unavailable}</small>}</span>
                </li>
              ))}
            </ul>
          </article>
        );
      })}
    </section>
  );
}

function Loading({ lang }: { lang: Lang }) {
  return (
    <div className="plan-grid" aria-busy="true">
      <p className="sr-only" role="status">{COPY[lang].loading}</p>
      {PLANES.map((p) => (
        <div key={p.id} className="loading-card" aria-hidden="true">
          <Skeleton style={{ width: '55%', height: 20 }} />
          <Skeleton style={{ width: '70%', height: 32 }} />
          <Skeleton style={{ width: '100%', height: 1 }} />
          {[0, 1, 2].map((k) => <Skeleton key={k} style={{ width: `${88 - k * 14}%`, height: 16 }} />)}
        </div>
      ))}
    </div>
  );
}

function Unavailable({ lang }: { lang: Lang }) {
  const m = useMockup();
  const c = COPY[lang];
  return (
    <section className="message" role="alert">
      <h2><CircleAlert aria-hidden="true" />{c.errorTitle}</h2>
      <p>{c.errorBody}</p>
      <Button variant="outline" className="retry" onClick={() => m.set('state', 'listo')}>{c.retry}</Button>
    </section>
  );
}

function PlansPage({ lang, setLang, signed }: { lang: Lang; setLang: (l: Lang) => void; signed: boolean }) {
  const m = useMockup();
  const c = COPY[lang];
  const url = m.view === 'legado' ? '/planes?vista=seleccionar' : '/planes';
  return (
    <>
      {signed && <header className="account-bar" lang={lang}><AccountMenu lang={lang} setLang={setLang} /></header>}
      <main className="page" lang={lang}>
        <header className="masthead">
          <div className="brand"><span className="brand-mark" aria-hidden="true"><span /></span><span>Pictures</span><span className="company">Sempertex</span></div>
          <label className="language" htmlFor="planes-language">
            <span>{c.language}</span>
            <select id="planes-language" className="native" value={lang} onChange={(e) => setLang(e.currentTarget.value === 'en' ? 'en' : 'es')}>
              <option value="es">ES</option><option value="en">EN</option>
            </select>
          </label>
        </header>
        <div className="heading-row">
          <h1>{c.title}</h1>
          <a className="back" href={signed ? '#volver' : '/login'} onClick={(e) => { e.preventDefault(); if (!signed) m.set('view', 'acceso'); }}>
            <ChevronLeft aria-hidden="true" size={18} />{signed ? c.backSignedIn : c.backSignedOut}
          </a>
        </div>
        <p className="context">{c.administrator}</p>
        {m.state === 'cargando' ? <Loading lang={lang} /> : m.state === 'error' ? <Unavailable lang={lang} /> : <PlanGrid lang={lang} />}
        <footer className="footer"><span>Pictures · Sempertex</span><span>{c.mock} · {c.url}: {url}</span></footer>
      </main>
    </>
  );
}

function Login({ lang, setLang }: { lang: Lang; setLang: (l: Lang) => void }) {
  const m = useMockup();
  const c = COPY[lang];
  return (
    <main className="login" lang={lang}>
      <button type="button" className="theme-btn" aria-label={c.theme}><Moon aria-hidden="true" /></button>
      <header className="acc-head">
        <div className="acc-brand" aria-label="Pictures Sempertex"><span className="acc-mark" aria-hidden="true"><span /></span><span>Pictures <small>· Sempertex</small></span></div>
        <label className="acc-lang" htmlFor="login-language"><span>{c.language}</span>
          <select id="login-language" className="native" value={lang} onChange={(e) => setLang(e.currentTarget.value === 'en' ? 'en' : 'es')}>
            <option value="es">ES</option><option value="en">EN</option>
          </select>
        </label>
      </header>
      <form className="login-card" onSubmit={(e) => e.preventDefault()}>
        <h1>{c.loginTitle}</h1>
        <p>{c.invitationOnly}</p>
        <p>{c.recoveryGuidance}</p>
        <label>{c.email}<Input type="email" autoComplete="username" /></label>
        <label>{c.password}<Input type="password" autoComplete="current-password" /></label>
        <Button type="submit" className="enter">{c.enter}</Button>
        <p className="center">{c.resetGuidance}</p>
        <a className="plans-link" href="/planes" onClick={(e) => { e.preventDefault(); m.set('view', 'planes'); }}>{c.plans}</a>
      </form>
      <footer className="footer"><span>Pictures · Sempertex</span><span>{c.mock} · {c.url}: /login</span></footer>
    </main>
  );
}

function App() {
  const m = useMockup();
  const motionProfile = useMotionProfile();
  const hidden = useHidden();
  const [lang, setLangState] = React.useState<Lang>(m.view === 'planes-en' ? 'en' : 'es');
  const setLang = (l: Lang) => setLangState(l);
  React.useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  return (
    <div className="shell" data-profile={motionProfile.profile} data-reduced={motionProfile.reduced} data-hidden={hidden}>
      <style>{css}</style>
      {m.view === 'acceso'
        ? <Login lang={lang} setLang={setLang} />
        : <PlansPage lang={lang} setLang={setLang} signed={m.view === 'planes-sesion'} />}
    </div>
  );
}

mountMockup(App, {
  title: 'Planes · SP-14 · planes@v2 · r1 · A · Fichas en fila · Borrador',
  views: [
    { id: 'planes', label: 'Planes · sin sesión (ES)' },
    { id: 'planes-en', label: 'Plans · sin sesión (EN, USD)' },
    { id: 'planes-sesion', label: 'Planes · con sesión' },
    { id: 'legado', label: '/planes?vista=seleccionar · legado' },
    { id: 'acceso', label: 'Iniciar sesión · enlace a Planes' },
  ],
  states: [
    { id: 'listo', label: 'Listo' },
    { id: 'cargando', label: 'Cargando' },
    { id: 'error', label: 'Catálogo no disponible' },
  ],
  scenes: [{ id: '', label: 'Ninguno' }, { id: 'menu', label: 'Menú de cuenta (con sesión)' }],
  motion: 'expressive',
});
