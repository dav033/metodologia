// planes@v2 · r1 · direction B — «Estantería» (spatial).
// Planning mockup of a CHANGE to the existing public /planes page of Pictures (published commit 0715a331).
// Shell reproduced from production (ComparadorPlanes masthead: ring-and-dot brand, «Idioma» select, H1 + «Volver al
// acceso», administrator sentence, footer) and, when signed in, the shared account bar/menu as composed by the
// chosen cuentas-admin@v2. Only the plans area changes: the comparison tabs, side index, highlight and selection
// summary are removed and the four catalogue plans become four peer subscription cards on one shelf whose
// tool rows line up across cards. Mock data only; no account, plan or network operation.
import * as React from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { AlertCircle, Check, ChevronDown, ChevronLeft, Inbox, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { mountMockup, useMockup } from '@kit/mockup';
import { useMotionProfile } from '@kit/motion';
import bodyFont from '/home/david/dev/pictures-wt/t12/.next/static/media/caa3a2e1cccd8315-s.p.0wgildi0cnwt9.woff2';
import monoFont from '/home/david/dev/pictures-wt/t12/.next/static/media/797e433ab948586e-s.p.0r6juujl39pe6.woff2';

type Lang = 'es' | 'en';

// Strings from src/components/planes/textos-planes.ts (production), minus the superseded comparison/selection copy,
// plus the catalogue-state copy of the approved planes@v1 contract §8 and the account-menu copy of textos-cuenta.ts.
const COPY = {
  es: {
    language: 'Idioma', title: 'Planes', back: 'Volver al acceso', includedTools: 'Herramientas incluidas',
    administrator: 'Un administrador asigna el plan.', free: 'Gratis', monthly: 'COP / mes', unavailable: 'aún no disponible',
    plansList: 'Planes de acceso', loading: 'Cargando planes…',
    emptyTitle: 'No hay planes disponibles', errorTitle: 'No se pudieron cargar los planes', offlineTitle: 'Sin conexión',
    retryHint: 'Vuelve a intentarlo para consultar los planes.', offlineHint: 'Conéctate y vuelve a cargar los planes.', retry: 'Reintentar',
    account: 'Cuenta', plan: 'Plan', myAccount: 'Mi cuenta', plans: 'Planes', signOut: 'Cerrar sesión',
    signOutPending: 'Cerrando sesión…', signOutError: 'No se pudo cerrar la sesión. Inténtalo de nuevo.',
  },
  en: {
    language: 'Language', title: 'Plans', back: 'Back to sign in', includedTools: 'Included tools',
    administrator: 'An administrator assigns the plan.', free: 'Free', monthly: 'USD / month', unavailable: 'not available yet',
    plansList: 'Access plans', loading: 'Loading plans…',
    emptyTitle: 'No plans available', errorTitle: 'Could not load plans', offlineTitle: 'Offline',
    retryHint: 'Try again to view the plans.', offlineHint: 'Connect and reload the plans.', retry: 'Retry',
    account: 'Account', plan: 'Plan', myAccount: 'My account', plans: 'Plans', signOut: 'Sign out',
    signOutPending: 'Signing out…', signOutError: 'Could not sign out. Try again.',
  },
} as const;

// Requirements-derived fixture mirroring src/lib/planes/catalogo.ts (names, prices, tools in cumulative catalogue
// order, availability). The chat row shows the catalogue description, as production does.
type Tool = { id: string; label: Record<Lang, string>; available: boolean };
const T = {
  chat: { id: 'chat', label: { es: 'Chat asistido con límites.', en: 'Assisted chat with limits.' }, available: true },
  chatHigher: { id: 'chat', label: { es: 'Chat asistido con límites más altos.', en: 'Assisted chat with higher limits.' }, available: true },
  counter: { id: 'contador_globos', label: { es: 'Contador de globos', en: 'Balloon counter' }, available: true },
  catalogue: { id: 'catalogo', label: { es: 'Catálogo', en: 'Catalog' }, available: true },
  costs: { id: 'calculadora_costos', label: { es: 'Calculadora de costos', en: 'Cost calculator' }, available: true },
  extended: { id: 'chat_extendido', label: { es: 'Chat extendido', en: 'Extended chat' }, available: false },
  structure: { id: 'deteccion_estructura', label: { es: 'Detección de estructura', en: 'Structure detection' }, available: false },
  advanced: { id: 'deteccion_globos_avanzada', label: { es: 'Detección avanzada de globos', en: 'Advanced balloon detection' }, available: false },
  workshop: { id: 'taller_3d', label: { es: 'Taller 3D', en: '3D workshop' }, available: true },
} satisfies Record<string, Tool>;
type Plan = { id: string; name: Record<Lang, string>; cop: number; usd: number; tools: Tool[] };
const PLANES: Plan[] = [
  { id: 'entusiasta', name: { es: 'Entusiasta', en: 'Enthusiast' }, cop: 0, usd: 0, tools: [T.chat, T.counter, T.catalogue] },
  { id: 'designer', name: { es: 'Designer', en: 'Designer' }, cop: 20000, usd: 7, tools: [T.chatHigher, T.counter, T.catalogue] },
  { id: 'designer_plus', name: { es: 'Designer Plus', en: 'Designer Plus' }, cop: 45000, usd: 14, tools: [T.chatHigher, T.counter, T.catalogue, T.costs, T.extended, T.structure, T.advanced] },
  { id: 'master_designer', name: { es: 'Master Designer', en: 'Master Designer' }, cop: 70000, usd: 25, tools: [T.chatHigher, T.counter, T.catalogue, T.costs, T.extended, T.structure, T.advanced, T.workshop] },
];
const MAX_TOOLS = Math.max(...PLANES.map((p) => p.tools.length));

// Signed-in fixture borrowed from the chosen cuentas-admin@v2 mockup (clearly mock). Its plan is NOT marked on any card.
const ACCOUNT = { name: 'Cuenta Designer Plus', email: 'designerplus@prueba.local', plan: { es: 'Designer Plus', en: 'Designer Plus' } };

const fmt = (n: number, lang: Lang) => new Intl.NumberFormat(lang === 'es' ? 'es-CO' : 'en-US', { maximumFractionDigits: 0 }).format(n);

// The language survives view/state switches (the mockup remounts the product on each switch).
let savedLang: Lang | null = null;
function useLang(force?: Lang): [Lang, (l: Lang) => void] {
  const [lang, set] = React.useState<Lang>(() => (savedLang = force ?? savedLang ?? 'es'));
  React.useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  return [lang, (l: Lang) => { savedLang = l; set(l); }];
}

const css = `
@font-face{font-family:Geist;src:url(${bodyFont}) format('woff2');font-weight:100 900;font-display:block}
@font-face{font-family:'Geist Mono';src:url(${monoFont}) format('woff2');font-weight:100 900;font-display:block}
:root,[data-theme="light"]{--fondo:#faf9fc;--superficie:#ffffff;--superficie-suave:#faf8fd;--superficie-2:#efe9f8;--borde:#e3daef;--borde-suave:#efe9f8;--texto:#1c1425;--texto-suave:#6b6178;--texto-tenue:#766c85;--acento:#6d3fe0;--acento-hover:#5530b8;--acento-suave:#ece3fb;--sobre-acento:#ffffff;--error:#b23a45;--error-suave:#ffeaec;--aviso:#8f5f12;--aviso-suave:#fff3d8;--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--acento-suave);--border:var(--borde);--input:var(--texto-tenue);--ring:var(--acento);--destructive:var(--error);--shadow-float:0 18px 40px -12px rgb(28 20 37 / .28);color-scheme:light}
.dark,[data-theme="dark"]{--fondo:#0b0c10;--superficie:#16181f;--superficie-suave:#1c1e26;--superficie-2:#242733;--borde:#383c48;--borde-suave:#2a2d38;--texto:#f4f5f7;--texto-suave:#9aa1ad;--texto-tenue:#8a91a0;--acento:#9479ff;--acento-hover:#a58dff;--acento-suave:#241f3d;--sobre-acento:#120b24;--error:#ff979f;--error-suave:#43252a;--aviso:#f7c46b;--aviso-suave:#3f311c;--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--acento-suave);--border:var(--borde);--input:var(--texto-tenue);--ring:var(--acento);--destructive:var(--error);--shadow-float:0 18px 40px -12px rgb(0 0 0 / .7);color-scheme:dark}
body{margin:0;font-family:Geist,ui-sans-serif,system-ui,sans-serif;font-size:15px;line-height:1.5;background:var(--fondo);color:var(--texto)}
*{box-sizing:border-box}h1,h2,h3,p,ul{margin:0}button,select{font:inherit}svg{flex-shrink:0}
/* Spatial glide grammar: long expo-out glides for space, short cuts for repeated controls. */
.app{--glide:620ms;--quick:180ms;--stagger:70ms;--row-stagger:28ms;--ease-glide:cubic-bezier(.16,1,.3,1);--ease-cut:cubic-bezier(.2,.8,.2,1);min-height:calc(100svh - var(--mockup-bar-h));display:flex;flex-direction:column}
.app[data-profile="natural"]{--glide:380ms;--quick:150ms;--stagger:45ms;--row-stagger:18ms}
.app[data-profile="subtle"]{--glide:180ms;--quick:110ms;--stagger:15ms;--row-stagger:6ms}
[data-reduced-motion] .app,[data-reduced-motion] .app *{animation:none!important;transition:none!important}
[data-tab-hidden] .app *{animation-play-state:paused!important}
/* ---- shared signed-in account bar (MenuCuenta as composed by cuentas-admin@v2) ---- */
.account-bar{position:relative;z-index:50;min-height:64px;display:flex;align-items:center;justify-content:flex-end;border-bottom:1px solid var(--borde-suave);padding:0 32px}
.account-menu{position:relative}
.menu-trigger{display:flex;align-items:center;gap:8px;min-height:44px;max-width:min(260px,calc(100vw - 32px));padding:0 14px 0 8px;border-radius:999px;border:1px solid var(--borde);background:var(--superficie);color:var(--texto);font-size:14px;font-weight:500;cursor:pointer;transition:transform 90ms cubic-bezier(.4,0,.7,1),border-color var(--quick) ease,box-shadow var(--quick) ease}
.menu-trigger:hover{border-color:var(--acento)}.menu-trigger:active{transform:scale(.95)}
.menu-trigger[aria-expanded="true"]{border-color:var(--acento);box-shadow:0 0 0 3px var(--acento-suave)}
.menu-trigger .name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}
.menu-trigger .chev{color:var(--texto-suave);transition:transform var(--glide) var(--ease-glide)}
.menu-trigger[aria-expanded="true"] .chev{transform:rotate(180deg)}
.initial{display:grid;place-items:center;flex-shrink:0;border-radius:999px;background:var(--acento-suave);color:var(--acento);font-weight:650;width:28px;height:28px;font-size:12px}
.menu-panel{position:absolute;right:0;top:calc(100% + 8px);width:304px;max-width:calc(100vw - 32px);background:var(--popover);border:1px solid var(--borde);border-radius:24px;padding:16px;box-shadow:var(--shadow-float);transform-origin:top right;font-size:14px}
.menu-who{display:grid;grid-template-columns:40px minmax(0,1fr);gap:12px;align-items:start}.menu-who .initial{width:40px;height:40px;font-size:16px}
.menu-name{font-weight:600;overflow-wrap:anywhere;line-height:1.35}.menu-email{font-size:13px;color:var(--texto-suave);overflow-wrap:anywhere;margin-top:2px}
.access-chip{display:inline-flex;gap:6px;align-items:baseline;margin-top:10px;padding:3px 12px;border-radius:999px;background:var(--superficie-2);font-size:13px;max-width:100%}.access-chip span{color:var(--texto-suave)}.access-chip b{font-weight:600}
.menu-lang{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:14px;padding-top:12px;border-top:1px solid var(--borde-suave);font-size:13px;color:var(--texto-suave)}
.lang-pair{display:flex;gap:4px}
.lang-btn{min-height:36px;min-width:44px;border-radius:10px;border:1px solid var(--borde);background:var(--superficie);color:var(--texto);font-size:12px;font-weight:650;cursor:pointer;transition:transform 90ms cubic-bezier(.4,0,.7,1)}
.lang-btn:active{transform:scale(.92)}.lang-btn[aria-pressed="true"]{background:var(--acento);color:var(--sobre-acento);border-color:var(--acento)}
.menu-links{display:grid;gap:2px;margin-top:12px;padding-top:8px;border-top:1px solid var(--borde-suave)}
.menu-link,.signout{display:flex;align-items:center;min-height:44px;padding:0 12px;border-radius:12px;color:var(--acento);font-weight:550;text-decoration:none;border:0;background:none;text-align:left;cursor:pointer;font-size:14px}
.menu-link:hover{background:var(--acento-suave)}.menu-link[aria-current="page"]{color:var(--texto);background:var(--superficie-2)}
.signout{color:var(--texto);margin-top:6px;border-top:1px solid var(--borde-suave);border-radius:0 0 12px 12px}.signout:hover{background:var(--superficie-suave)}.signout:disabled{opacity:.65;cursor:progress}
.menu-alert{font-size:12px;color:var(--error);padding:4px 12px 0}
/* ---- /planes page (ComparadorPlanes shell, unchanged) ---- */
.page{width:min(100% - 48px,1440px);margin:0 auto;padding:28px 0 24px;flex:1;display:flex;flex-direction:column}
.masthead{display:flex;justify-content:space-between;align-items:center;gap:20px;padding-bottom:28px}
.brand{display:inline-flex;align-items:center;gap:10px;font-size:15px;font-weight:650;letter-spacing:-.02em}
.brand-mark{display:grid;width:30px;height:30px;place-items:center;border:1px solid var(--borde);border-radius:50%;color:var(--acento)}
.brand-mark i{width:7px;height:7px;border-radius:50%;background:currentColor;box-shadow:0 0 0 5px color-mix(in srgb,currentColor 15%,transparent)}
.company{margin-left:-6px;color:var(--texto-suave);font-weight:400}
.language{display:flex;align-items:center;gap:10px;color:var(--texto-suave);font-size:13px}
.language select{min-width:64px;min-height:44px;padding:0 12px;border:1px solid var(--texto-tenue);border-radius:14px;background:var(--superficie);color:var(--texto)}
.heading-row{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-bottom:8px}
.page-title{font-size:24px;line-height:1.25;font-weight:600;letter-spacing:-.03em}
.back-link{display:inline-flex;min-height:44px;align-items:center;gap:7px;color:var(--texto-suave);text-decoration:none;font-size:14px;transition:color var(--quick) var(--ease-cut)}
.back-link svg{transition:transform var(--quick) var(--ease-cut)}.back-link:hover{color:var(--acento)}.back-link:hover svg{transform:translateX(-3px)}
.context{margin:0 0 24px;color:var(--texto-suave);font-size:14px;line-height:1.55}
:where(.app) :where(a,button,select):focus-visible{outline:3px solid var(--acento);outline-offset:3px}
/* ---- the shelf: four peer cards; tool rows share tracks across cards (subgrid) ---- */
.shelf{display:grid;gap:16px;align-items:stretch;position:relative}
.shelf[data-cols="4"]{grid-template-columns:repeat(4,minmax(0,1fr))}
.shelf[data-cols="2"]{grid-template-columns:repeat(2,minmax(0,1fr))}
.shelf[data-cols="1"]{grid-template-columns:minmax(0,1fr)}
.plan-card{position:relative;min-width:0;display:grid;background:var(--superficie);border:1px solid var(--borde);border-radius:24px;padding:24px 22px 22px;transform-origin:50% 0}
.shelf:not([data-cols="1"]) .plan-card{grid-row:span ${MAX_TOOLS + 3};grid-template-rows:subgrid;row-gap:0}
.shelf[data-cols="1"] .plan-card{align-content:start}
.card-head{display:grid;gap:4px;padding-bottom:18px;border-bottom:1px solid var(--borde-suave);margin-bottom:14px;background:var(--superficie)}
.shelf:not([data-cols="1"]) .card-head{grid-row:span 2;grid-template-rows:subgrid}
.shelf[data-cols="1"] .card-head{position:sticky;top:var(--mockup-bar-h,0px);z-index:2;margin:-24px -22px 14px;padding:20px 22px 16px;border-radius:24px 24px 0 0}
.plan-name{font-size:18px;line-height:1.3;font-weight:600;overflow-wrap:anywhere}
.price{display:flex;align-items:baseline;gap:6px;min-height:40px;overflow:hidden;font-variant-numeric:tabular-nums}
.price-roll{display:inline-flex;align-items:baseline;gap:6px;white-space:nowrap}
.price-amount{font-size:30px;line-height:1.25;font-weight:650;letter-spacing:-.02em}
.price-unit{color:var(--texto-suave);font-size:13px;font-weight:400}
.tools-heading{color:var(--texto-suave);font-size:12px;font-weight:550;margin-bottom:6px}
.tools{list-style:none;padding:0;display:grid}
.shelf:not([data-cols="1"]) .tools{grid-row:span ${MAX_TOOLS};grid-template-rows:subgrid}
.tool-row{display:grid;grid-template-columns:16px minmax(0,1fr);column-gap:8px;align-items:start;padding:6px 0;font-size:14px;line-height:1.45;animation:slot-in var(--glide) var(--ease-glide) both;animation-delay:calc(var(--card) * var(--stagger) + var(--row) * var(--row-stagger) + 120ms)}
.tool-row>svg{margin-top:2px;color:var(--acento)}
.tool-row[data-available="false"]>svg{color:var(--aviso)}
.tool-row span{min-width:0;overflow-wrap:anywhere}
.tool-row small{grid-column:2;color:var(--aviso);font-size:12px;line-height:1.4}
@keyframes slot-in{from{transform:translateX(-10px);opacity:.5}to{transform:none;opacity:1}}
/* ---- catalogue states ---- */
.state-panel{display:grid;justify-items:start;gap:10px;padding:28px;border:1px solid var(--borde);border-radius:24px;background:var(--superficie);max-width:560px;animation:slot-in var(--glide) var(--ease-glide) both}
.state-panel h2{font-size:18px;font-weight:600;display:flex;gap:10px;align-items:center}
.state-panel p{color:var(--texto-suave);font-size:14px}
.state-panel[data-kind="error"] h2 svg{color:var(--error)}.state-panel h2 svg{color:var(--texto-suave)}
.retry{min-height:44px!important;padding:0 18px!important;border-radius:999px!important;margin-top:6px;background:var(--acento)!important;color:var(--sobre-acento)!important;font-weight:600!important}
.retry:hover{background:var(--acento-hover)!important}
.skel{display:grid;gap:10px}.skel [data-slot=skeleton]{background:var(--superficie-2);border-radius:10px;animation:none}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.footer{display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-top:auto;padding-top:18px;border-top:1px solid var(--borde-suave);color:var(--texto-suave);font-size:12px}
.footer-wrap{margin-top:24px}
.mock-note{font:12px/1.5 'Geist Mono',monospace;color:var(--texto-suave)}
@media (max-width:1023px){.account-bar{padding:0 24px}}
@media (max-width:639px){
 .account-bar{padding:0 16px}
 .page{width:calc(100% - 40px);padding-top:20px}
 .masthead{align-items:flex-start;flex-wrap:wrap;padding-bottom:22px}.language{margin-left:auto}
 .heading-row{align-items:flex-start;flex-direction:column;gap:4px}
 .plan-card{padding:24px 20px 20px}
 .shelf[data-cols="1"] .card-head{margin:-24px -20px 14px;padding:18px 20px 14px}
 .price-amount{font-size:26px}
 .state-panel{padding:22px 20px}
 .menu-panel{position:fixed;left:16px;right:16px;top:calc(var(--mockup-bar-h) + 72px);width:auto;max-width:none}
}
`;

function AccountMenu({ lang, setLang, initialOpen }: { lang: Lang; setLang: (l: Lang) => void; initialOpen: boolean }) {
  const c = COPY[lang];
  const { reduced, spring } = useMotionProfile();
  const [open, setOpen] = React.useState(initialOpen);
  const [signOut, setSignOut] = React.useState<'idle' | 'pending' | 'error'>('idle');
  const wrap = React.useRef<HTMLDivElement>(null);
  const trigger = React.useRef<HTMLButtonElement>(null);
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
      <button ref={trigger} type="button" className="menu-trigger" aria-expanded={open} aria-controls="account-menu-panel"
        aria-label={`${c.account}: ${ACCOUNT.name}`} onClick={() => setOpen((o) => !o)}>
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
                <p className="access-chip"><span>{c.plan}</span><b>{ACCOUNT.plan[lang]}</b></p>
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
              <a className="menu-link" href="#planes" aria-current="page" onClick={(e) => e.preventDefault()}>{c.plans}</a>
              <button type="button" className="signout" disabled={signOut === 'pending'}
                onClick={() => { setSignOut('pending'); window.setTimeout(() => setSignOut('error'), 900); }}>
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

// Column count follows the shelf's own width. Just before the count changes, the cards' current boxes are recorded so
// they can glide from their old cell to the new one (manual FLIP; Motion's layout projection skips window resizes).
function useColumns(ref: React.RefObject<HTMLElement | null>, beforeChange?: () => void): 1 | 2 | 4 {
  const pick = (w: number): 1 | 2 | 4 => (w >= 1040 ? 4 : w >= 600 ? 2 : 1);
  const [cols, setCols] = React.useState<1 | 2 | 4>(() => pick(Math.min(innerWidth, 1440) - 48));
  const current = React.useRef(cols);
  React.useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => {
      const next = pick(e.contentRect.width);
      if (next === current.current) return;
      beforeChange?.();
      current.current = next;
      setCols(next);
    });
    ro.observe(el);
    return () => ro.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ref]);
  return cols;
}

function Price({ plan, lang, c }: { plan: Plan; lang: Lang; c: (typeof COPY)[Lang] }) {
  const { reduced } = useMotionProfile();
  const amount = lang === 'es' ? plan.cop : plan.usd;
  // Language switch: the old currency rolls up out of the price slot while the new one rolls in from below.
  return (
    <p className="price">
      <AnimatePresence mode="popLayout" initial={false}>
        <motion.span key={lang} className="price-roll"
          initial={reduced ? false : { y: '110%', opacity: 0 }} animate={{ y: '0%', opacity: 1 }}
          exit={reduced ? { opacity: 0, transition: { duration: 0 } } : { y: '-110%', opacity: 0 }}
          transition={reduced ? { duration: 0 } : { type: 'spring', stiffness: 260, damping: 26 }}>
          {amount === 0 ? <span className="price-amount">{c.free}</span>
            : <><span className="price-amount">{fmt(amount, lang)}</span><span className="price-unit">{c.monthly}</span></>}
        </motion.span>
      </AnimatePresence>
    </p>
  );
}

function Shelf({ lang }: { lang: Lang }) {
  const c = COPY[lang];
  const ref = React.useRef<HTMLDivElement>(null);
  const { reduced, profile } = useMotionProfile();
  const before = React.useRef<DOMRect[]>([]);
  const cards = () => [...(ref.current?.querySelectorAll<HTMLElement>('.plan-card') ?? [])];
  const cols = useColumns(ref, () => { before.current = cards().map((el) => el.getBoundingClientRect()); });
  const glide = profile === 'expressive' ? 620 : profile === 'natural' ? 380 : 180;
  // Reflow across a breakpoint: every card glides from its previous cell to its new one.
  const firstCols = React.useRef(true);
  React.useLayoutEffect(() => {
    if (firstCols.current) { firstCols.current = false; return; }
    if (reduced || !before.current.length) return;
    cards().forEach((el, i) => {
      const a = before.current[i], b = el.getBoundingClientRect();
      if (!a) return;
      el.animate([{ transform: `translate(${a.left - b.left}px, ${a.top - b.top}px)` }, { transform: 'none' }],
        { duration: glide + i * 30, easing: 'cubic-bezier(.16,1,.3,1)' });
    });
    before.current = [];
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cols]);
  // Load choreography: the cards are dealt from behind the first card to their own cell, whatever the layout.
  React.useLayoutEffect(() => {
    if (reduced || !ref.current) return;
    const cards = [...ref.current.querySelectorAll<HTMLElement>('.plan-card')];
    const r0 = cards[0]?.getBoundingClientRect();
    if (!r0) return;
    const dur = glide;
    const anims = cards.map((el, i) => {
      const r = el.getBoundingClientRect();
      const dx = r0.left - r.left, dy = r0.top - r.top;
      return el.animate([{ transform: `translate(${dx}px, ${dy}px) scale(.96)` }, { transform: 'none' }],
        { duration: dur + i * 40, delay: i * (profile === 'subtle' ? 15 : 70), easing: 'cubic-bezier(.16,1,.3,1)', fill: 'backwards' });
    });
    return () => anims.forEach((a) => a.cancel());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <section aria-label={c.plansList}>
      <div ref={ref} className="shelf" data-cols={cols}>
        {PLANES.map((plan, i) => (
          <article key={plan.id}
            className="plan-card" id={`plan-${plan.id}`} aria-labelledby={`plan-title-${plan.id}`}
            style={{ zIndex: PLANES.length - i, ['--card' as string]: i }}>
            <header className="card-head">
              <h2 className="plan-name" id={`plan-title-${plan.id}`}>{plan.name[lang]}</h2>
              <Price plan={plan} lang={lang} c={c} />
            </header>
            <h3 className="tools-heading">{c.includedTools}</h3>
            <ul className="tools" aria-label={`${c.includedTools}: ${plan.name[lang]}`}>
              {plan.tools.map((tool, j) => (
                <li key={tool.id} className="tool-row" data-available={tool.available} style={{ ['--row' as string]: j }}>
                  <Check aria-hidden="true" size={16} />
                  <span>{tool.label[lang]}</span>
                  {!tool.available && <small>{c.unavailable}</small>}
                </li>
              ))}
            </ul>
          </article>
        ))}
      </div>
    </section>
  );
}

function LoadingShelf({ lang }: { lang: Lang }) {
  const c = COPY[lang];
  const ref = React.useRef<HTMLDivElement>(null);
  const cols = useColumns(ref);
  return (
    <section aria-label={c.plansList} aria-busy="true">
      <p className="sr" role="status">{c.loading}</p>
      <div ref={ref} className="shelf" data-cols={cols} aria-hidden="true">
        {PLANES.map((p) => (
          <div key={p.id} className="plan-card skel">
            <Skeleton className="h-5 w-2/5" /><Skeleton className="h-8 w-3/5" />
            <div style={{ height: 8 }} />
            {[0, 1, 2, 3, 4].map((k) => <Skeleton key={k} className="h-4 w-4/5" />)}
          </div>
        ))}
      </div>
    </section>
  );
}

function StatePanel({ kind, lang }: { kind: 'vacio' | 'error' | 'sin-conexion'; lang: Lang }) {
  const c = COPY[lang];
  const { set } = useMockup();
  const title = kind === 'vacio' ? c.emptyTitle : kind === 'error' ? c.errorTitle : c.offlineTitle;
  const hint = kind === 'sin-conexion' ? c.offlineHint : c.retryHint;
  const Icon = kind === 'vacio' ? Inbox : kind === 'error' ? AlertCircle : WifiOff;
  // Mock retry: shows loading, then the complete local fixture. Never a partial catalogue.
  const retry = () => { set('state', 'cargando'); window.setTimeout(() => set('state', 'listo'), 900); };
  return (
    <section aria-label={c.plansList}>
      <div className="state-panel" data-kind={kind === 'error' ? 'error' : 'info'} role={kind === 'error' ? 'alert' : 'status'}>
        <h2><Icon aria-hidden="true" size={20} />{title}</h2>
        <p>{hint}</p>
        <Button className="retry" onClick={retry}>{c.retry}</Button>
      </div>
    </section>
  );
}

function App() {
  const { view, state, motion: profile } = useMockup();
  const [lang, setLang] = useLang(view === 'ingles' ? 'en' : undefined);
  const c = COPY[lang];
  const signedIn = view === 'con-sesion' || view === 'con-sesion-menu';
  React.useEffect(() => {
    const on = () => document.documentElement.toggleAttribute('data-tab-hidden', document.hidden);
    document.addEventListener('visibilitychange', on);
    return () => document.removeEventListener('visibilitychange', on);
  }, []);
  const url = view === 'legado' ? '/planes?vista=seleccionar' : '/planes';
  return (
    <div className="app" data-profile={profile}>
      <style>{css}</style>
      {signedIn && (
        <header className="account-bar" lang={lang}>
          <AccountMenu lang={lang} setLang={setLang} initialOpen={view === 'con-sesion-menu'} />
        </header>
      )}
      <main className="page" lang={lang}>
        <header className="masthead">
          <div className="brand"><span className="brand-mark" aria-hidden="true"><i /></span><span>Pictures</span><span className="company">Sempertex</span></div>
          <label className="language" htmlFor="planes-language">
            <span>{c.language}</span>
            <select id="planes-language" value={lang} onChange={(e) => setLang(e.currentTarget.value === 'en' ? 'en' : 'es')}>
              <option value="es">ES</option><option value="en">EN</option>
            </select>
          </label>
        </header>
        <div className="heading-row">
          <h1 className="page-title">{c.title}</h1>
          <a className="back-link" href="#login" onClick={(e) => e.preventDefault()}><ChevronLeft aria-hidden="true" size={18} />{c.back}</a>
        </div>
        <p className="context">{c.administrator}</p>
        {state === 'cargando' ? <LoadingShelf lang={lang} />
          : state === 'vacio' || state === 'error' || state === 'sin-conexion' ? <StatePanel kind={state} lang={lang} />
          : <Shelf lang={lang} />}
        <div className="footer-wrap" />
        <footer className="footer">
          <span>Pictures · Sempertex</span>
          <span className="mock-note">Mockup · datos simulados · URL {url}</span>
        </footer>
      </main>
    </div>
  );
}

mountMockup(App, {
  title: 'Planes (/planes) · planes@v2 r1 · dirección B «Estantería»',
  views: [
    { id: 'sin-sesion', label: 'Sin sesión · desde Acceso' },
    { id: 'con-sesion', label: 'Con sesión · barra de cuenta' },
    { id: 'con-sesion-menu', label: 'Con sesión · menú abierto' },
    { id: 'ingles', label: 'Visitante en inglés (USD)' },
    { id: 'legado', label: 'Enlace antiguo ?vista=seleccionar' },
  ],
  states: [
    { id: 'listo', label: 'Listo' },
    { id: 'cargando', label: 'Cargando' },
    { id: 'vacio', label: 'Catálogo vacío' },
    { id: 'error', label: 'Error' },
    { id: 'sin-conexion', label: 'Sin conexión' },
  ],
});
