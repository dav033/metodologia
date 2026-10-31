// planes@v2 · r3 · direction C — «Cartas al pie» (direct manipulation inside the existing /planes page).
// Planning mockup of a CHANGE to the published /planes page of Pictures (commit 0715a331, ComparadorPlanes):
// same masthead (ring-and-dot mark, «Idioma» select), heading row with back link, administrator line and footer.
// Removed per P-211: «Comparar planes / Seleccionar para comparar» route tabs, «Ir a un plan» rail, highlighted
// plan, selection summary. Added: four peer subscription cards at natural height on a shared price line; the
// language select edits the page in place (names, tools and COP⇄USD prices roll and settle). Mock data only.
// r3 (owner, 2026-10-31): «Escoger» / «Choose» is purely visual — a focusable button with the plan in its accessible
// name and the press motion; pressing it does absolutely nothing (no message, navigation, request or account change).
import * as React from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { Button } from '@/components/ui/button';
import { Check, ChevronDown, ChevronLeft, Moon } from 'lucide-react';
import { mountMockup, useMockup } from '@kit/mockup';
import { useMotionProfile } from '@kit/motion';
import bodyFont from '/home/david/dev/pictures-wt/t12/.next/static/media/caa3a2e1cccd8315-s.p.0wgildi0cnwt9.woff2';
import monoFont from '/home/david/dev/pictures-wt/t12/.next/static/media/797e433ab948586e-s.p.0r6juujl39pe6.woff2';

type Lang = 'es' | 'en';

// src/components/planes/textos-planes.ts (published) minus the comparison/selection strings P-211 removes.
const COPY = {
  es: {
    language: 'Idioma', title: 'Planes', back: 'Volver al acceso', backSigned: 'Volver al acceso', choose: 'Escoger', includedTools: 'Herramientas incluidas',
    administrator: 'Un administrador asigna el plan.', free: 'Gratis', monthly: 'COP / mes', unavailable: 'aún no disponible',
    // MenuCuenta (cuentas-admin@v2) and LoginForm (textos-acceso.ts), unchanged.
    account: 'Cuenta', plan: 'Plan', myAccount: 'Mi cuenta', plans: 'Planes', signOut: 'Cerrar sesión',
    loginTitle: 'Iniciar sesión', invitationOnly: 'El acceso a Pictures es solo por invitación de un administrador.',
    recoveryGuidance: 'Para restablecer tu contraseña, pídele al administrador que genere un enlace de recuperación.',
    email: 'Correo electrónico', password: 'Contraseña', enter: 'Entrar',
    resetGuidance: '¿Olvidaste tu contraseña? Pide al administrador un enlace de restablecimiento. Es de un solo uso y dura 24 horas.',
    theme: 'Cambiar tema', mock: 'Mockup · datos del catálogo; ninguna tarjeta compra, solicita ni cambia el acceso',
  },
  en: {
    language: 'Language', title: 'Plans', back: 'Back to sign in', backSigned: 'Back to sign in', choose: 'Choose', includedTools: 'Included tools',
    administrator: 'An administrator assigns the plan.', free: 'Free', monthly: 'USD / month', unavailable: 'not available yet',
    account: 'Account', plan: 'Plan', myAccount: 'My account', plans: 'Plans', signOut: 'Sign out',
    loginTitle: 'Sign in', invitationOnly: 'Pictures access is by administrator invitation only.',
    recoveryGuidance: 'To reset your password, ask your administrator to generate a recovery link.',
    email: 'Email address', password: 'Password', enter: 'Sign in',
    resetGuidance: 'Forgot your password? Ask your administrator for a reset link. It is single use and valid for 24 hours.',
    theme: 'Change theme', mock: 'Mockup · catalogue data; no card buys, requests or changes access',
  },
} as const;

// Exact copy of src/lib/planes/catalogo.ts (plan-catalogue@1): names, monthly prices, cumulative tools in catalogue
// order, availability. The chat line shows the catalogue description (limits named without numbers), as today.
type Tool = { id: string; es: string; en: string; available: boolean };
const T = {
  chat: { id: 'chat', es: 'Chat asistido con límites.', en: 'Assisted chat with limits.', available: true },
  chatHigh: { id: 'chat', es: 'Chat asistido con límites más altos.', en: 'Assisted chat with higher limits.', available: true },
  counter: { id: 'contador_globos', es: 'Contador de globos', en: 'Balloon counter', available: true },
  catalog: { id: 'catalogo', es: 'Catálogo', en: 'Catalog', available: true },
  costs: { id: 'calculadora_costos', es: 'Calculadora de costos', en: 'Cost calculator', available: true },
  extended: { id: 'chat_extendido', es: 'Chat extendido', en: 'Extended chat', available: false },
  structure: { id: 'deteccion_estructura', es: 'Detección de estructura', en: 'Structure detection', available: false },
  advanced: { id: 'deteccion_globos_avanzada', es: 'Detección avanzada de globos', en: 'Advanced balloon detection', available: false },
  workshop: { id: 'taller_3d', es: 'Taller 3D', en: '3D workshop', available: true },
} satisfies Record<string, Tool>;
const PLANS: { id: string; name: { es: string; en: string }; cop: number; usd: number; tools: Tool[] }[] = [
  { id: 'entusiasta', name: { es: 'Entusiasta', en: 'Enthusiast' }, cop: 0, usd: 0, tools: [T.chat, T.counter, T.catalog] },
  { id: 'designer', name: { es: 'Designer', en: 'Designer' }, cop: 20000, usd: 7, tools: [T.chatHigh, T.counter, T.catalog] },
  { id: 'designer_plus', name: { es: 'Designer Plus', en: 'Designer Plus' }, cop: 45000, usd: 14, tools: [T.chatHigh, T.counter, T.catalog, T.costs, T.extended, T.structure, T.advanced] },
  { id: 'master_designer', name: { es: 'Master Designer', en: 'Master Designer' }, cop: 70000, usd: 25, tools: [T.chatHigh, T.counter, T.catalog, T.costs, T.extended, T.structure, T.advanced, T.workshop] },
];
const fmt = (n: number, l: Lang) => new Intl.NumberFormat(l === 'es' ? 'es-CO' : 'en-US', { maximumFractionDigits: 0 }).format(n);

const CSS = `
@font-face{font-family:Geist;src:url(${bodyFont}) format('woff2');font-weight:100 900;font-display:block}
@font-face{font-family:'Geist Mono';src:url(${monoFont}) format('woff2');font-weight:100 900;font-display:block}
:root,[data-theme="light"]{--fondo:#faf9fc;--superficie:#ffffff;--superficie-suave:#faf8fd;--superficie-2:#efe9f8;--borde:#e3daef;--borde-suave:#efe9f8;--texto:#1c1425;--texto-suave:#6b6178;--texto-tenue:#766c85;--acento:#6d3fe0;--acento-hover:#5530b8;--acento-suave:#ece3fb;--sobre-acento:#ffffff;--error:#b23a45;--error-suave:#ffeaec;--aviso:#8f5f12;--aviso-suave:#fff3d8;--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--acento-suave);--border:var(--borde);--input:var(--texto-tenue);--ring:var(--acento);--destructive:var(--error);--shadow-float:0 18px 40px -12px rgb(28 20 37 / .28);color-scheme:light}
.dark,[data-theme="dark"]{--fondo:#0b0c10;--superficie:#16181f;--superficie-suave:#1c1e26;--superficie-2:#242733;--borde:#383c48;--borde-suave:#2a2d38;--texto:#f4f5f7;--texto-suave:#9aa1ad;--texto-tenue:#8a91a0;--acento:#9479ff;--acento-hover:#a58dff;--acento-suave:#241f3d;--sobre-acento:#120b24;--error:#ff979f;--error-suave:#43252a;--aviso:#f7c46b;--aviso-suave:#3f311c;--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--acento-suave);--border:var(--borde);--input:var(--texto-tenue);--ring:var(--acento);--destructive:var(--error);--shadow-float:0 18px 40px -12px rgb(0 0 0 / .7);color-scheme:dark}
body{margin:0;font-family:Geist,ui-sans-serif,system-ui,sans-serif;font-size:15px;line-height:1.5;background:var(--fondo);color:var(--texto)}
*{box-sizing:border-box}h1,h2,h3,p,ul{margin:0}button,input,select{font:inherit}svg{flex-shrink:0}
/* Tactile press/settle grammar shared with cuentas-admin@v2 (chosen dir C). */
.app{--press:90ms;--settle:460ms;--quick:180ms;--ease-press:cubic-bezier(.4,0,.7,1);--ease-settle:cubic-bezier(.34,1.42,.64,1);--card-stagger:70ms;--row-stagger:35ms;min-height:calc(100svh - var(--mockup-bar-h,0px));display:flex;flex-direction:column;background:var(--fondo)}
.app[data-profile="natural"]{--settle:300ms;--quick:150ms;--card-stagger:45ms;--row-stagger:22ms;--ease-settle:cubic-bezier(.3,1.18,.6,1)}
.app[data-profile="subtle"]{--settle:170ms;--quick:110ms;--card-stagger:15ms;--row-stagger:8ms;--ease-settle:cubic-bezier(.2,.8,.2,1)}
[data-reduced-motion] .app,[data-reduced-motion] .app *,.app[data-profile="still"],.app[data-profile="still"] *{animation:none!important;transition:none!important}
[data-tab-hidden] .app *{animation-play-state:paused!important}
.route{display:flex;align-items:center;gap:8px;padding:6px 24px;font:12px/1.4 'Geist Mono',monospace;color:var(--texto-suave);border-bottom:1px dashed var(--borde)}
.route b{font-weight:500;color:var(--texto)}
.route[data-login="true"]{width:min(100% - 32px,672px);margin:0 auto;padding-inline:0}
/* ---- shared signed-in account bar (MenuCuenta, cuentas-admin@v2) ---- */
.account-bar{min-height:64px;display:flex;align-items:center;justify-content:flex-end;border-bottom:1px solid var(--borde-suave);padding:0 32px}
.account-menu{position:relative;z-index:50}
.menu-trigger{display:flex;align-items:center;gap:8px;min-height:44px;max-width:min(260px,calc(100vw - 32px));padding:0 14px 0 8px;border-radius:999px;border:1px solid var(--borde);background:var(--superficie);color:var(--texto);font-size:14px;font-weight:500;cursor:pointer;transition:transform var(--press) var(--ease-press),border-color var(--quick) ease,box-shadow var(--quick) ease}
.menu-trigger:hover{border-color:var(--acento)}.menu-trigger:active{transform:scale(.95)}
.menu-trigger[aria-expanded="true"]{border-color:var(--acento);box-shadow:0 0 0 3px var(--acento-suave)}
.menu-trigger .name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.menu-trigger .chev{color:var(--texto-suave);transition:transform var(--settle) var(--ease-settle)}
.menu-trigger[aria-expanded="true"] .chev{transform:rotate(180deg)}
.initial{display:grid;place-items:center;flex-shrink:0;border-radius:999px;background:var(--acento-suave);color:var(--acento);font-weight:650;width:28px;height:28px;font-size:12px}
.menu-panel{position:absolute;right:0;top:calc(100% + 8px);width:304px;max-width:calc(100vw - 32px);background:var(--popover);border:1px solid var(--borde);border-radius:24px;padding:16px;box-shadow:var(--shadow-float);transform-origin:top right;font-size:14px}
.menu-who{display:grid;grid-template-columns:40px minmax(0,1fr);gap:12px;align-items:start}
.menu-who .initial{width:40px;height:40px;font-size:16px}
.menu-name{font-weight:600;overflow-wrap:anywhere;line-height:1.35}.menu-email{font-size:13px;color:var(--texto-suave);overflow-wrap:anywhere;margin-top:2px}
.access-chip{display:inline-flex;gap:6px;align-items:baseline;margin-top:10px;padding:3px 12px;border-radius:999px;background:var(--superficie-2);font-size:13px;max-width:100%}
.access-chip span{color:var(--texto-suave)}.access-chip b{font-weight:600}
.menu-lang{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:14px;padding-top:12px;border-top:1px solid var(--borde-suave);font-size:13px;color:var(--texto-suave)}
.lang-pair{display:flex;gap:4px}
.lang-btn{min-height:36px;min-width:44px;border-radius:10px;border:1px solid var(--borde);background:var(--superficie);color:var(--texto);font-size:12px;font-weight:650;cursor:pointer;transition:transform var(--press) var(--ease-press)}
.lang-btn:active{transform:scale(.92)}.lang-btn[aria-pressed="true"]{background:var(--acento);color:var(--sobre-acento);border-color:var(--acento)}
.menu-links{display:grid;gap:2px;margin-top:12px;padding-top:8px;border-top:1px solid var(--borde-suave)}
.menu-link,.signout{display:flex;align-items:center;min-height:44px;padding:0 12px;border-radius:12px;color:var(--acento);font-weight:550;text-decoration:none;border:0;background:none;text-align:left;cursor:pointer;transition:transform var(--press) var(--ease-press),background-color var(--quick) ease}
.menu-link:hover{background:var(--acento-suave)}.menu-link:active,.signout:active{transform:scale(.97)}
.menu-link[aria-current="page"]{color:var(--texto);background:var(--superficie-2)}
.signout{color:var(--texto);margin-top:6px;border-top:1px solid var(--borde-suave);border-radius:0 0 12px 12px}
/* ---- /planes page (ComparadorPlanes shell, published) ---- */
.page{width:min(100% - 48px,1440px);margin:0 auto;padding:28px 0 24px;flex:1;display:flex;flex-direction:column}
.masthead{display:flex;justify-content:space-between;align-items:center;gap:20px;padding-bottom:28px}
.brand{display:inline-flex;align-items:center;gap:10px;font-size:15px;font-weight:650;letter-spacing:-.02em}
.brand-mark{display:grid;width:30px;height:30px;place-items:center;border:1px solid var(--borde);border-radius:50%;color:var(--acento)}
.brand-mark i{width:7px;height:7px;border-radius:50%;background:currentColor;box-shadow:0 0 0 5px color-mix(in srgb,currentColor 15%,transparent)}
.brand .co{color:var(--texto-suave);font-weight:400}
.idioma{display:flex;align-items:center;gap:10px;color:var(--texto-suave);font-size:13px}
.idioma select{min-width:64px;min-height:44px;padding:0 12px;border:1px solid var(--texto-tenue);border-radius:14px;background:var(--superficie);color:var(--texto);cursor:pointer;transition:transform var(--press) var(--ease-press),border-color var(--quick) ease}
.idioma select:hover{border-color:var(--acento)}.idioma select:active{transform:scale(.95)}
.idioma[data-settle="true"] select{animation:lang-settle var(--settle) var(--ease-settle)}
@keyframes lang-settle{0%{transform:scale(.92)}60%{transform:scale(1.04)}100%{transform:none}}
.heading-row{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:8px}
.heading-row h1{font-size:24px;line-height:1.25;font-weight:600;letter-spacing:-.03em}
.back{display:inline-flex;min-height:44px;align-items:center;gap:7px;padding:0 12px 0 6px;margin-right:-12px;border-radius:14px;color:var(--texto-suave);text-decoration:none;font-size:14px;transition:transform var(--press) var(--ease-press),color var(--quick) ease,background-color var(--quick) ease}
.back svg{transition:transform var(--settle) var(--ease-settle)}
.back:hover{color:var(--acento);background:var(--acento-suave)}.back:hover svg{transform:translateX(-3px)}
.back:active{transform:scale(.96)}
.context{margin:0 0 24px;color:var(--texto-suave);font-size:14px;line-height:1.55}
/* Four peer cards at natural height; identity blocks share one height so every price sits on one line. */
.deck{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;align-items:start;list-style:none;padding:0}
.plan-card{min-width:0;background:var(--superficie);border:1px solid var(--borde-suave);border-radius:24px;padding:24px;animation:card-drop var(--settle) var(--ease-settle) both;animation-delay:calc(var(--c,0) * var(--card-stagger))}
@keyframes card-drop{0%{opacity:.4;transform:translateY(18px) scale(.97)}100%{opacity:1;transform:none}}
.plan-id{display:grid;gap:6px;min-height:96px;align-content:start;padding-bottom:18px;border-bottom:1px solid var(--borde-suave)}
.plan-id h2{font-size:18px;line-height:1.3;font-weight:600;overflow-wrap:anywhere}
.price{display:flex;align-items:baseline;flex-wrap:wrap;gap:4px 8px;min-height:40px}
.roll{display:inline-grid;overflow:clip;overflow-clip-margin:6px;padding:2px 0}
.roll>*{grid-area:1/1}
.amount{font-size:30px;line-height:1.2;font-weight:600;letter-spacing:-.02em;font-variant-numeric:tabular-nums;white-space:nowrap}
.unit{color:var(--texto-suave);font-size:13px;white-space:nowrap}
.choose{width:100%;min-height:44px;margin-top:16px;border:1px solid var(--acento)!important;border-radius:999px!important;background:var(--superficie)!important;color:var(--acento)!important;font-weight:600!important;cursor:pointer;transition:transform var(--press) var(--ease-press),background-color var(--quick) ease!important}.choose:hover{background:var(--acento-suave)!important}.choose:active{transform:scale(.97)}
.tools-heading{margin:18px 0 6px;color:var(--texto-suave);font-size:12px;font-weight:550}
.tools{display:grid;margin:0;padding:0;list-style:none}
.tools li{display:grid;grid-template-columns:16px minmax(0,1fr);gap:8px;padding:6px 0;font-size:14px;line-height:1.45;animation:row-in var(--settle) var(--ease-settle) both;animation-delay:calc(var(--base,160ms) + var(--c,0) * var(--card-stagger) + var(--i,0) * var(--row-stagger))}
@keyframes row-in{0%{opacity:.4;transform:translateY(-6px)}100%{opacity:1;transform:none}}
.tools li svg{margin-top:2px;color:var(--acento)}
.tools li[data-available="false"] svg{color:var(--aviso)}
.tools li span{min-width:0;overflow-wrap:anywhere}
.tools small{display:block;color:var(--aviso);font-size:12px}
.footer{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:24px;padding-top:18px;border-top:1px solid var(--borde-suave);color:var(--texto-suave);font-size:12px}
.footer .mock{font-family:'Geist Mono',monospace}
/* ---- /login (unchanged; only its Planes link is in scope) ---- */
.login{position:relative;flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px 16px}
.theme-btn{position:absolute;right:12px;top:12px;display:grid;place-items:center;width:44px;height:44px;border-radius:12px;border:1px solid var(--borde);background:var(--superficie);color:var(--texto);cursor:pointer}
.cabecera{width:100%;max-width:676px;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:16px 0}
.cab-brand{display:flex;align-items:center;gap:12px;font-size:14px;font-weight:600;letter-spacing:.02em}
.cab-ring{display:grid;place-items:center;width:32px;height:32px;border-radius:999px;border:2px solid var(--acento)}.cab-ring i{width:8px;height:8px;border-radius:999px;background:var(--acento)}
.cab-brand .co{font-weight:400;color:var(--texto-suave)}
.cab-lang{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--texto-suave)}
.cab-lang select{min-height:40px;border-radius:14px;border:1px solid var(--texto-tenue);background:var(--superficie);color:var(--texto);padding:4px 10px}
.login-card{width:100%;max-width:672px;display:grid;gap:20px;background:var(--superficie);border:1px solid var(--borde-suave);border-radius:32px;padding:32px}
.login-card h1{font-size:24px;font-weight:600}.login-card p{font-size:14px;color:var(--texto-suave)}
.login-card label{display:grid;gap:8px;font-size:14px;font-weight:500}
.login-card input{min-height:48px;border-radius:18px;border:1px solid var(--texto-tenue);background:var(--superficie);color:var(--texto);padding:0 16px}
.enter{min-height:48px;border-radius:999px;border:0;background:var(--acento);color:var(--sobre-acento);font-weight:600;cursor:pointer}
.login-card .reset{text-align:center}
.plans-link{display:flex;min-height:44px;align-items:center;justify-content:center;border-radius:12px;border:1px solid var(--borde);padding:0 12px;font-weight:550;color:var(--acento);text-decoration:none;transition:transform var(--press) var(--ease-press),background-color var(--quick) ease}
.plans-link:hover{background:var(--superficie-suave)}.plans-link:active{transform:scale(.97)}
.app a:focus-visible,.app button:focus-visible,.app select:focus-visible,.app input:focus-visible{outline:3px solid var(--acento);outline-offset:3px}
@media (min-width:640px) and (max-width:1099px){.deck{grid-template-columns:repeat(2,minmax(0,1fr))}.account-bar{padding:0 24px}}
@media (max-width:639px){
 .page{width:calc(100% - 40px);padding-top:20px}
 .masthead{flex-wrap:wrap;padding-bottom:22px}.idioma{margin-left:auto}
 .heading-row{flex-direction:column;align-items:flex-start;gap:4px}.back{margin:0 0 0 -6px}
 .deck{grid-template-columns:minmax(0,1fr);gap:12px}
 .plan-card{padding:20px;border-radius:24px}.plan-id{min-height:0}.amount{font-size:26px}
 .account-bar{padding:0 16px}
 .menu-panel{position:fixed;left:16px;right:16px;top:calc(var(--mockup-bar-h,0px) + 72px);width:auto;max-width:none}
 .login{justify-content:flex-start;padding-top:64px}.login-card{padding:24px 20px;border-radius:24px}.route{padding:6px 20px}
}
`;

let savedLang: Lang | null = null;

function AccountMenu({ lang, setLang, initialOpen, onPlans, staff }: { lang: Lang; setLang: (l: Lang) => void; initialOpen: boolean; onPlans: () => void; staff: boolean }) {
  const c = COPY[lang];
  const { reduced, spring } = useMotionProfile();
  const [open, setOpen] = React.useState(initialOpen);
  React.useEffect(() => setOpen(initialOpen), [initialOpen]);
  const wrap = React.useRef<HTMLDivElement>(null);
  const trigger = React.useRef<HTMLButtonElement>(null);
  const name = staff ? 'Cuenta de empleado interno' : 'Cuenta Designer Plus';
  const email = staff ? 'empleado@prueba.local' : 'designerplus@prueba.local';
  React.useEffect(() => {
    if (!open) return;
    const onDown = (e: PointerEvent) => { if (wrap.current && !wrap.current.contains(e.target as Node)) setOpen(false); };
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { setOpen(false); trigger.current?.focus(); } };
    document.addEventListener('pointerdown', onDown, true);
    document.addEventListener('keydown', onKey);
    return () => { document.removeEventListener('pointerdown', onDown, true); document.removeEventListener('keydown', onKey); };
  }, [open]);
  const onBlur = (e: React.FocusEvent<HTMLDivElement>) => {
    const next = e.relatedTarget as Node | null;
    if (next && wrap.current && !wrap.current.contains(next)) setOpen(false);
  };
  return (
    <div className="account-menu" ref={wrap} onBlur={onBlur}>
      <button ref={trigger} type="button" className="menu-trigger" aria-expanded={open} aria-controls="account-menu-panel" aria-label={`${c.account}: ${name}`} onClick={() => setOpen((o) => !o)}>
        <span className="initial" aria-hidden="true">C</span>
        <span className="name">{name}</span>
        <ChevronDown className="chev" aria-hidden="true" size={16} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div id="account-menu-panel" className="menu-panel" lang={lang}
            initial={reduced ? false : { opacity: 0, y: -10, scale: 0.94 }} animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduced ? { opacity: 0, transition: { duration: 0 } } : { opacity: 0, y: -6, scale: 0.97, transition: { duration: 0.12 } }}
            transition={reduced ? { duration: 0 } : spring}>
            <div className="menu-who">
              <span className="initial" aria-hidden="true">C</span>
              <div style={{ minWidth: 0 }}>
                <p className="menu-name">{name}</p>
                <p className="menu-email">{email}</p>
                <p className="access-chip">{staff ? <><span>{lang === 'es' ? 'Rol' : 'Role'}</span><b>{lang === 'es' ? 'Empleado interno' : 'Internal employee'}</b></> : <><span>{c.plan}</span><b>Designer Plus</b></>}</p>
              </div>
            </div>
            <div className="menu-lang" role="group" aria-label={c.language}>
              <span>{c.language}</span>
              <span className="lang-pair">
                {(['es', 'en'] as const).map((l) => <button key={l} type="button" className="lang-btn" aria-pressed={lang === l} onClick={() => setLang(l)}>{l.toUpperCase()}</button>)}
              </span>
            </div>
            <div className="menu-links">
              <a className="menu-link" href="#cuenta" onClick={(e) => e.preventDefault()}>{c.myAccount}</a>
              <a className="menu-link" href="#planes" aria-current="page" onClick={(e) => { e.preventDefault(); setOpen(false); onPlans(); }}>{c.plans}</a>
              <button type="button" className="signout">{c.signOut}</button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function Price({ plan, lang }: { plan: (typeof PLANS)[number]; lang: Lang }) {
  const c = COPY[lang];
  const { reduced, spring } = useMotionProfile();
  const amount = lang === 'es' ? plan.cop : plan.usd;
  // In-place edit: the old figure rolls up and out, the new one rises from below and settles (key = currency).
  return (
    <p className="price">
      <span className="roll">
        <AnimatePresence initial={false} mode="popLayout">
          <motion.span key={`${lang}-${amount}`} className="amount"
            initial={reduced ? false : { y: '70%', opacity: 0.4 }} animate={{ y: 0, opacity: 1 }}
            exit={reduced ? { opacity: 0, transition: { duration: 0 } } : { y: '-70%', opacity: 0, transition: { duration: 0.14 } }}
            transition={reduced ? { duration: 0 } : spring}>
            {amount === 0 ? c.free : fmt(amount, lang)}
          </motion.span>
        </AnimatePresence>
      </span>
      {amount !== 0 && <span className="unit">{c.monthly}</span>}
    </p>
  );
}

function PlansPage({ lang, setLang, onBack, settle }: { lang: Lang; setLang: (l: Lang) => void; onBack: () => void; settle: boolean }) {
  const c = COPY[lang];
  const first = React.useRef(true);
  React.useEffect(() => { first.current = false; }, []);
  return (
    <main className="page" lang={lang}>
      <header className="masthead">
        <div className="brand" aria-label="Pictures Sempertex">
          <span className="brand-mark" aria-hidden="true"><i /></span>
          <span>Pictures</span><span className="co">Sempertex</span>
        </div>
        <label className="idioma" htmlFor="planes-language" data-settle={settle}>
          <span>{c.language}</span>
          <select id="planes-language" value={lang} onChange={(e) => setLang(e.currentTarget.value === 'en' ? 'en' : 'es')}>
            <option value="es">ES</option>
            <option value="en">EN</option>
          </select>
        </label>
      </header>
      <div className="heading-row">
        <h1>{c.title}</h1>
        <a className="back" href="/login" onClick={(e) => { e.preventDefault(); onBack(); }}>
          <ChevronLeft aria-hidden="true" size={18} />{c.back}
        </a>
      </div>
      <p className="context">{c.administrator}</p>
      <div className="deck">
          {PLANS.map((plan, ci) => (
            <article className="plan-card" key={plan.id} id={`plan-${plan.id}`} aria-labelledby={`plan-title-${plan.id}`} style={{ ['--c' as string]: ci }}>
              <div className="plan-id">
                <h2 id={`plan-title-${plan.id}`}>{plan.name[lang]}</h2>
                <Price plan={plan} lang={lang} />
              </div>
              <Button type="button" className="choose" aria-label={`${c.choose}: ${plan.name[lang]}`}>{c.choose}</Button>
              <h3 className="tools-heading">{c.includedTools}</h3>
              <ul key={lang} className="tools" aria-label={`${c.includedTools}: ${plan.name[lang]}`} style={{ ['--base' as string]: first.current ? '160ms' : '0ms', ['--c' as string]: first.current ? ci : 0 }}>
                {plan.tools.map((tool, ti) => (
                  <li key={`${tool.id}-${ti}`} data-available={tool.available} style={{ ['--i' as string]: ti }}>
                    <Check aria-hidden="true" size={16} />
                    <span>{tool[lang]}{!tool.available && <small>{c.unavailable}</small>}</span>
                  </li>
                ))}
              </ul>
            </article>
          ))}
      </div>
      <footer className="footer"><span>Pictures · Sempertex</span><span className="mock">{c.mock}</span></footer>
    </main>
  );
}

function LoginScreen({ lang, setLang, onPlans }: { lang: Lang; setLang: (l: Lang) => void; onPlans: () => void }) {
  const c = COPY[lang];
  return (
    <main className="login" lang={lang}>
      <button type="button" className="theme-btn" aria-label={c.theme}><Moon aria-hidden="true" size={18} /></button>
      <header className="cabecera">
        <div className="cab-brand" aria-label="Pictures Sempertex"><span className="cab-ring" aria-hidden="true"><i /></span><span>Pictures <span className="co">· Sempertex</span></span></div>
        <label className="cab-lang"><span>{c.language}</span>
          <select aria-label={c.language} value={lang} onChange={(e) => setLang(e.currentTarget.value === 'en' ? 'en' : 'es')}><option value="es">ES</option><option value="en">EN</option></select>
        </label>
      </header>
      <form className="login-card" onSubmit={(e) => e.preventDefault()} noValidate>
        <h1>{c.loginTitle}</h1>
        <p>{c.invitationOnly}</p>
        <p>{c.recoveryGuidance}</p>
        <label>{c.email}<input type="email" autoComplete="username" defaultValue="persona@prueba.local" /></label>
        <label>{c.password}<input type="password" autoComplete="current-password" /></label>
        <button type="submit" className="enter">{c.enter}</button>
        <p className="reset">{c.resetGuidance}</p>
        <a className="plans-link" href="#planes" onClick={(e) => { e.preventDefault(); onPlans(); }}>{c.plans}</a>
      </form>
    </main>
  );
}

const ROUTES: Record<string, string> = {
  publica: '/planes', sesion: '/planes', legado: '/planes?vista=seleccionar', acceso: '/login', menu: '/planes',
};

function App() {
  const { view, state, motion: profile, reduced, set } = useMockup();
  const initial: Lang = state === 'en' ? 'en' : 'es';
  const [lang, setLangRaw] = React.useState<Lang>(savedLang ?? initial);
  const [settle, setSettle] = React.useState(false);
  React.useEffect(() => { savedLang = null; setLangRaw(state === 'en' ? 'en' : 'es'); }, [state]);
  React.useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  React.useEffect(() => {
    const on = () => document.documentElement.toggleAttribute('data-tab-hidden', document.hidden);
    document.addEventListener('visibilitychange', on);
    return () => document.removeEventListener('visibilitychange', on);
  }, []);
  const setLang = (l: Lang) => {
    savedLang = l; setLangRaw(l);
    setSettle(false); requestAnimationFrame(() => setSettle(true));
    window.setTimeout(() => setSettle(false), 600);
  };
  const signed = view === 'sesion' || view === 'menu';
  const staff = state === 'empleado';
  return (
    <div className="app" data-profile={reduced ? 'still' : profile}>
      <style>{CSS}</style>
      <div className="route" data-mockup-chrome="" data-login={view === 'acceso'}>{`${lang === 'es' ? 'Ruta' : 'Route'} ${ROUTES[view] ?? '/planes'}`}{signed ? (lang === 'es' ? ' · con sesión' : ' · signed in') : view === 'acceso' ? '' : (lang === 'es' ? ' · sin sesión' : ' · signed out')}</div>
      {view === 'acceso' ? (
        <LoginScreen lang={lang} setLang={setLang} onPlans={() => set('view', 'publica')} />
      ) : (
        <>
          {signed && (
            <header className="account-bar" lang={lang}>
              <AccountMenu lang={lang} setLang={setLang} initialOpen={view === 'menu'} staff={staff} onPlans={() => set('view', 'sesion')} />
            </header>
          )}
          <PlansPage lang={lang} setLang={setLang} settle={settle}
            onBack={() => set('view', 'acceso')} />
        </>
      )}
    </div>
  );
}

mountMockup(App, {
  title: 'planes@v2 · r3 · Planes · dirección C «Cartas al pie»',
  views: [
    { id: 'publica', label: 'Planes · sin sesión' },
    { id: 'sesion', label: 'Planes · con sesión' },
    { id: 'legado', label: 'Consulta antigua (?vista=seleccionar)' },
    { id: 'acceso', label: 'Acceso · enlace a Planes' },
    { id: 'menu', label: 'Menú de cuenta · enlace a Planes' },
  ],
  states: [
    { id: 'normal', label: 'Catálogo · español (COP)' },
    { id: 'en', label: 'Navegador en inglés (USD)' },
    { id: 'empleado', label: 'Con sesión · Empleado interno' },
  ],
  motion: 'expressive',
});
