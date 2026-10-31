import * as React from 'react';
import { motion } from 'motion/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Spinner } from '@/components/ui/spinner';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Check, ChevronDown, CircleAlert, IdCard, KeyRound, LogOut, Moon, Sun } from 'lucide-react';
import { mountMockup, useMockup } from '@kit/mockup';
import { useMotionProfile } from '@kit/motion';
import bodyFont from '/home/david/dev/pictures-wt/t12/.next/static/media/caa3a2e1cccd8315-s.p.0wgildi0cnwt9.woff2';
import monoFont from '/home/david/dev/pictures-wt/t12/.next/static/media/797e433ab948586e-s.p.0r6juujl39pe6.woff2';

// Pictures tokens copied from the product globals.css (light + dark), mapped once onto the kit's shadcn roles.
const css = `
@font-face{font-family:Geist;src:url(${bodyFont}) format('woff2');font-weight:100 900;font-display:block}
@font-face{font-family:Geist Mono;src:url(${monoFont}) format('woff2');font-weight:100 900;font-display:block}
:root,[data-theme="light"]{--fondo:#faf9fc;--superficie:#ffffff;--superficie-suave:#faf8fd;--superficie-2:#efe9f8;--borde:#e3daef;--borde-suave:#efe9f8;--texto:#1c1425;--texto-suave:#6b6178;--texto-tenue:#766c85;--acento:#6d3fe0;--acento-hover:#5530b8;--acento-suave:#ece3fb;--sobre-acento:#ffffff;--exito:#1f7a55;--exito-suave:#dcf5e9;--error:#b23a45;--error-suave:#ffeaec;--overlay:rgb(28 20 37 / 0.18);--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--card-foreground:var(--texto);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);--secondary:var(--superficie-2);--secondary-foreground:var(--texto);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--acento-suave);--accent-foreground:var(--acento);--destructive:var(--error);--border:var(--borde);--input:var(--texto-tenue);--ring:var(--acento);color-scheme:light}
.dark,[data-theme="dark"]{--fondo:#0b0c10;--superficie:#16181f;--superficie-suave:#1c1e26;--superficie-2:#242733;--borde:#383c48;--borde-suave:#2a2d38;--texto:#f4f5f7;--texto-suave:#9aa1ad;--texto-tenue:#8a91a0;--acento:#9479ff;--acento-hover:#a58dff;--acento-suave:#241f3d;--sobre-acento:#120b24;--exito:#78d6a8;--exito-suave:#173b31;--error:#ff979f;--error-suave:#43252a;--overlay:rgb(0 0 0 / 0.5);--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--card-foreground:var(--texto);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);--secondary:var(--superficie-2);--secondary-foreground:var(--texto);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--acento-suave);--accent-foreground:var(--acento);--destructive:var(--error);--border:var(--borde);--input:var(--texto-tenue);--ring:var(--acento);color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--fondo);color:var(--texto);font:15px/1.5 Geist,system-ui,sans-serif}
h1,h2,h3,p,dl,dd{margin:0}button,input,select{font:inherit;max-width:100%}svg{flex-shrink:0;width:18px;height:18px}
.app{--seat:560ms;--glide:cubic-bezier(.3,1.18,.4,1);--quick:180ms;--ease:cubic-bezier(.22,1,.36,1);--step:60ms;max-width:1520px;margin:auto;padding:0 40px 40px;min-height:calc(100svh - var(--mockup-bar-h))}
.app[data-profile="natural"]{--seat:380ms;--quick:150ms;--step:40ms;--glide:cubic-bezier(.25,1.05,.45,1)}
.app[data-profile="subtle"]{--seat:200ms;--quick:110ms;--step:20ms;--glide:cubic-bezier(.2,.8,.2,1)}
.app[data-reduced="true"] *,.app[data-reduced="true"] *::before,.app[data-reduced="true"] *::after{animation:none!important;transition:none!important}
.app[data-hidden="true"] *{animation-play-state:paused!important}
/* Shared shell, unchanged from sibling contracts */
.masthead{min-height:76px;display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 0;border-bottom:1px solid var(--borde-suave)}
.brand{display:flex;align-items:center;gap:12px;font-size:16px;font-weight:600;white-space:nowrap}
.brandmark{width:28px;height:28px;display:grid;place-items:center;background:var(--acento);color:var(--sobre-acento);border-radius:8px}.brandmark svg{width:16px;height:16px}
.company{font:12px 'Geist Mono',monospace;border-left:1px solid var(--texto);margin-left:12px;padding-left:16px}
.header-tools{display:flex;gap:16px;align-items:center;flex-wrap:wrap}
.language{display:flex;gap:8px;align-items:center;font-size:13px}
.native{min-height:44px;border:1px solid var(--texto-tenue);border-radius:999px;padding:10px 16px;background:var(--superficie);color:var(--texto)}
:where(a,button,input,select,summary,[tabindex]):focus-visible{outline:3px solid var(--acento)!important;outline-offset:4px!important;box-shadow:none!important}
.btn{min-height:44px!important;height:auto!important;line-height:1.35!important;border-radius:999px!important;padding:11px 18px!important;white-space:normal!important;font-weight:600!important;gap:8px!important;transition:transform var(--quick) var(--ease),background-color var(--quick)!important}
.btn[data-variant=default]{background:var(--acento)!important;color:var(--sobre-acento)!important}
.btn[data-variant=outline]{background:var(--superficie)!important;color:var(--texto)!important;border:1px solid var(--texto-tenue)!important}
.btn:hover:not(:disabled){transform:translateY(-1px)}.btn:active:not(:disabled){transform:translateY(1px) scale(.98)}
.btn:disabled{opacity:1!important;color:var(--texto-suave)!important;background:var(--superficie-2)!important;cursor:not-allowed}
[data-slot=input]{min-height:46px!important;height:auto!important;border:1px solid var(--texto-tenue)!important;border-radius:18px!important;padding:11px 16px!important;background:var(--superficie)!important;color:var(--texto)!important;box-shadow:none!important;transition:border-color var(--quick)}
[data-slot=input][aria-invalid=true]{border-color:var(--error)!important}
.heading{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;padding:24px 0 18px}
.heading h1{font-size:24px;line-height:1.25;font-weight:600;letter-spacing:-.4px}.heading h1:focus{outline:none}
.heading p{font-size:13px;color:var(--texto-suave);margin-top:6px}
.route-nav{display:flex;gap:32px;flex-wrap:wrap;min-height:58px;align-items:stretch;margin-bottom:24px;border-block:1px solid var(--borde-suave)}
.route-nav a{display:flex;align-items:center;min-height:52px;padding:12px 0;color:var(--texto-suave);text-decoration:none;border-bottom:3px solid transparent;font-size:14px}
.route-nav a[aria-current=page]{color:var(--texto);border-bottom-color:var(--texto)}.route-nav a:hover{color:var(--texto)}
.mock-context{padding:8px 16px;background:var(--superficie-suave);border:1px solid var(--borde);border-radius:18px;margin-bottom:20px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;font-size:12px}
.mock-context label{display:flex;gap:8px;align-items:center}.mock-context .native{min-height:36px;padding:6px 12px}
.fixture-hint{color:var(--texto-suave)}
.scope-feedback{margin:-8px 0 16px;font-size:13px;color:var(--texto-suave)}
/* Account disclosure: native details/summary, unfolds from the trigger corner */
.user-menu{position:relative}
.user-menu summary{list-style:none;display:flex;gap:10px;align-items:center;min-height:44px;padding:8px 14px 8px 8px;border:1px solid var(--texto-tenue);border-radius:999px;cursor:pointer;font-size:13px;font-weight:500;max-width:260px;transition:border-color var(--quick),background-color var(--quick)}
.user-menu summary::-webkit-details-marker{display:none}
.user-menu summary:hover{background:var(--superficie-2)}
.trigger-name{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.chev{transition:transform var(--quick) var(--ease)}.user-menu[open] .chev{transform:rotate(180deg)}
.monogram.monogram{width:28px;height:28px;border-radius:999px;font-size:13px;flex-shrink:0}.monogram [data-slot=avatar-fallback]::before{content:attr(data-initial)}.monogram [data-slot=avatar-fallback]{background:var(--acento-suave);color:var(--acento);font-size:inherit;font-weight:600}
.menu-sheet{position:absolute;right:0;top:calc(100% + 10px);z-index:30;width:320px;max-width:calc(100vw - 40px);background:var(--superficie);border:1px solid var(--texto-tenue);border-radius:24px;box-shadow:0 18px 40px var(--overlay);padding:8px;transform-origin:top right;animation:menu-unfold var(--seat) var(--glide) both}
.menu-id{display:grid;grid-template-columns:auto minmax(0,1fr);gap:12px;padding:14px 12px 16px;border-bottom:1px solid var(--borde-suave)}
.menu-id .monogram.monogram{width:40px;height:40px;font-size:16px}
.menu-name{font-weight:600;overflow-wrap:anywhere}.menu-email{font-size:13px;color:var(--texto-suave);overflow-wrap:anywhere}
.menu-access{display:inline-flex;gap:6px;margin-top:8px;padding:3px 10px;border-radius:999px;background:var(--acento-suave);color:var(--acento);font-size:12px;font-weight:600;max-width:100%;overflow-wrap:anywhere}
.menu-group{display:grid;gap:2px;padding:8px 0}.menu-group+.menu-group{border-top:1px solid var(--borde-suave)}
.menu-item{display:flex;align-items:center;gap:10px;min-height:44px;padding:10px 12px;border-radius:14px;color:var(--texto);text-decoration:none;background:none;border:0;text-align:left;width:100%;font-size:14px;font-weight:500;animation:item-glide var(--seat) var(--glide) both;animation-delay:calc(var(--n,0) * var(--step));transition:background-color var(--quick)}
.menu-item:hover{background:var(--superficie-2)}.menu-item[aria-current=page]{background:var(--superficie-2);font-weight:600}
.menu-item svg{color:var(--texto-suave)}
.menu-error{margin:4px 12px 8px;color:var(--error);font-size:13px}
@keyframes menu-unfold{from{transform:translate(10px,-10px) scale(.96)}to{transform:none}}
@keyframes item-glide{from{transform:translateX(10px)}to{transform:none}}
/* Local in-page navigation: segmented, a gliding indicator marks the panel in focus */
.local-nav{display:inline-flex;gap:4px;padding:4px;border-radius:999px;background:var(--superficie-2);border:1px solid var(--borde)}
.local-tab{position:relative;display:inline-flex;align-items:center;gap:8px;min-height:40px;padding:8px 16px;border:0;border-radius:999px;background:none;color:var(--texto-suave);font-size:14px;font-weight:500;cursor:pointer;transition:color var(--quick)}
.local-tab[aria-pressed=true]{color:var(--texto);font-weight:600}.local-tab:hover{color:var(--texto)}
.local-tab .tab-label,.local-tab>svg{position:relative;z-index:1}
.local-tab .local-nav-indicator{position:absolute;inset:0;z-index:0;border-radius:999px;background:var(--superficie);box-shadow:0 1px 3px var(--overlay);transition:background-color var(--quick)}
/* Spatial workspace: pass beside the security panel; a sliding track below 840px */
.account-viewport{min-width:0}
.account-track{display:grid;grid-template-columns:340px minmax(0,1fr);gap:28px;align-items:start}
.paper{background:var(--superficie);border:1px solid var(--borde);border-radius:32px;min-width:0;transition:border-color var(--quick),scale var(--seat) var(--glide)}
.paper[data-spot=true]{border-color:var(--texto-tenue)}
.paper[data-spot=false]{scale:.985}
.identity-pass{position:sticky;top:16px;padding:28px;animation:seat-left var(--seat) var(--glide) both}
.security-panel{padding:28px;animation:seat-right var(--seat) var(--glide) both;animation-delay:var(--step)}
.panel-head{display:flex;align-items:center;gap:12px;margin-bottom:22px}
.panel-head>svg{color:var(--texto-suave)}
.panel-title{font-size:20px;line-height:1.3;font-weight:600;letter-spacing:-.2px}.panel-title:focus{outline:none}
.pass-top{display:flex;align-items:center;gap:16px;margin-bottom:22px}
.monogram.monogram-lg{width:64px;height:64px;font-size:26px}
.pass-rows{display:grid;gap:16px}
.pass-row{display:grid;gap:2px;min-width:0;animation:row-glide var(--seat) var(--glide) both;animation-delay:calc(var(--n,0) * var(--step) + var(--step))}
.pass-row dt{font-size:13px;color:var(--texto-suave)}
.pass-row dd{font-weight:500;overflow-wrap:anywhere}
.pass-row.name dd{font-size:18px;font-weight:600;line-height:1.35}
.pass-access{margin-top:22px;padding-top:18px;border-top:1px solid var(--borde-suave)}
.access-value{font-size:20px;font-weight:600;letter-spacing:-.2px;line-height:1.3;overflow-wrap:anywhere}
@keyframes seat-left{from{transform:translateX(-18px)}to{transform:none}}
@keyframes seat-right{from{transform:translateX(18px)}to{transform:none}}
@keyframes row-glide{from{transform:translateX(-10px)}to{transform:none}}
.pw-form{display:grid;gap:20px}
.pw-group{display:grid;gap:20px}.pw-group+.pw-group{padding-top:20px;border-top:1px solid var(--borde-suave)}
.pw-pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.field{display:grid;gap:6px;min-width:0;align-content:start}
.field label{font-size:14px;font-weight:600}
.field-hint{font-size:13px;color:var(--texto-suave)}
.field-error{position:relative;padding-left:22px;font-size:13px;color:var(--error);animation:err-in var(--quick) var(--ease) both}.field-error svg{position:absolute;left:0;top:2px;width:16px;height:16px}
@keyframes err-in{from{transform:translateY(-4px)}to{transform:none}}
.note{display:flex;gap:12px;align-items:flex-start;padding:14px 16px;border-radius:18px;border:1px solid var(--borde);font-size:14px}
.note[data-tone=error]{background:var(--error-suave);border-color:var(--error);color:var(--texto)}.note[data-tone=error]>svg{color:var(--error)}
.receipt{display:flex;gap:12px;align-items:flex-start;padding:16px;margin-bottom:20px;border-radius:18px;background:var(--exito-suave);border:1px solid var(--exito);animation:receipt-drop var(--seat) var(--glide) both}
.receipt>svg{color:var(--exito)}.receipt p{font-size:14px}
@keyframes receipt-drop{from{transform:translateY(-12px)}to{transform:none}}
.form-actions{display:flex;flex-wrap:wrap;gap:12px;align-items:center}
.pending-text{font-size:13px;color:var(--texto-suave)}
.skel{display:grid;gap:14px}.skel [data-slot=skeleton]{background:var(--superficie-2);border-radius:12px;height:18px}
.skel .tall{height:46px;border-radius:18px}.skel .round{width:64px;height:64px;border-radius:999px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
@media(max-width:1099px){.app{padding-inline:24px}.route-nav{gap:20px}.account-track{grid-template-columns:300px minmax(0,1fr);gap:20px}.pw-pair{grid-template-columns:minmax(0,1fr)}.identity-pass,.security-panel{padding:24px}}
@media(max-width:839px){
 .account-viewport{overflow:clip;margin:-8px;padding:8px}
 .account-track{grid-template-columns:100% 100%;column-gap:16px;transform:translateX(calc(var(--i,0) * (-100% - 16px)));transition:transform var(--seat) var(--glide)}
 .identity-pass{position:static}
 .paper[data-spot=false]{scale:1}
 .paper[data-spot]{border-color:var(--borde)}
}
@media(max-width:639px){
 .app{padding-inline:20px}
 .masthead{min-height:70px;gap:12px;flex-wrap:wrap}.company{margin-left:2px;padding-left:12px}
 .header-tools{gap:10px;width:100%;justify-content:space-between;flex-wrap:nowrap;position:relative}
 .user-menu{position:static;min-width:0}.user-menu summary{max-width:100%}.language{flex-shrink:0}
 .heading{flex-wrap:wrap;align-items:flex-start;padding:20px 0 16px}.heading>div{flex:1 0 100%}
 .local-nav{width:100%}.local-tab{flex:1;justify-content:center;padding:8px 10px}
 .route-nav{gap:0 20px;min-height:0;margin-bottom:16px}.route-nav a{min-height:44px;padding:10px 0;font-size:13px}
 .identity-pass,.security-panel{padding:20px;border-radius:24px}
 .pass-top{margin-bottom:18px}.monogram.monogram-lg{width:56px;height:56px;font-size:22px}
 .form-actions .btn{width:100%}
 .mock-context{gap:8px}.mock-context label{width:100%;justify-content:space-between}.mock-context .native{flex:1}
 .menu-sheet{width:min(320px,calc(100vw - 40px))}
}
`;

// Mock snapshot of plan-catalogue@1 names. Production reads the catalogue; nothing here is real data.
const planNames: Record<string, [string, string]> = { entusiasta: ['Entusiasta', 'Enthusiast'], designer: ['Designer', 'Designer'], 'designer-plus': ['Designer Plus', 'Designer Plus'], 'master-designer': ['Master Designer', 'Master Designer'] };
const staffRoles: Record<string, [string, string]> = { administrador: ['Administrador', 'Administrator'], empleado: ['Empleado interno', 'Internal employee'], personalizado: ['Rol de prueba', 'Rol de prueba'] };
const people: Record<string, { name: string | null; email: string; company?: string }> = {
  'con-nombre': { name: 'Cuenta de ejemplo', email: 'cuenta@prueba.local', company: 'Empresa de ejemplo' },
  'sin-nombre': { name: '   ', email: 'sin-nombre@prueba.local' },
  'nombre-largo': { name: 'Cuenta de ejemplo con un nombre registrado largo para comprobar el ajuste de línea', email: 'nombre-largo@prueba.local' },
  'correo-largo': { name: 'Cuenta de ejemplo', email: 'cuenta.de.ejemplo.con.un.correo.electronico.largo@subdominio.prueba.local' },
};
// Persist mock-only choices across the mockup's view/state remounts.
const fixture = { access: 'designer-plus', person: 'con-nombre', lang: 'es' };

const PASSWORD_STATES = ['requerido', 'corta', 'larga', 'no-coinciden', 'actual-incorrecta', 'pendiente', 'error-servicio', 'error-red', 'exito'];

function Mono({ text, className = '' }: { text: string; className?: string }) {
  return <Avatar aria-hidden="true" className={`monogram ${className}`}><AvatarFallback data-initial={text.slice(0, 1).toLocaleUpperCase()} /></Avatar>;
}

type Errors = Partial<Record<'current' | 'next' | 'repeat', string>>;

function App() {
  const m = useMockup(), profile = useMotionProfile();
  const [lang, setLang] = React.useState(fixture.lang);
  const [access, setAccess] = React.useState(fixture.access);
  const [personKey, setPersonKey] = React.useState(fixture.person);
  const t = (es: string, en: string) => (lang === 'en' ? en : es);
  const li = lang === 'en' ? 1 : 0;
  const person = people[personKey];
  const displayName = person.name?.trim() || person.email;
  const isPlan = access in planNames;
  const accessLabel = isPlan ? t('Plan', 'Plan') : t('Rol', 'Role');
  const accessValue = isPlan ? planNames[access][li] : staffRoles[access][li];
  const canUsers = access === 'administrador' || access === 'personalizado';
  const canRoles = access === 'administrador';
  const state = m.state;
  const loading = state === 'cargando';

  // Shared account disclosure
  const startOpen = m.view === 'menu' || state === 'cerrando-sesion' || state === 'error-cierre';
  const [menu, setMenu] = React.useState(startOpen);
  const [signingOut, setSigningOut] = React.useState(state === 'cerrando-sesion');
  const [signOutError, setSignOutError] = React.useState(state === 'error-cierre');
  const [feedback, setFeedback] = React.useState('');
  const menuRef = React.useRef<HTMLDetailsElement>(null);
  const summaryRef = React.useRef<HTMLElement>(null);
  const [hidden, setHidden] = React.useState(document.hidden);

  React.useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  React.useEffect(() => {
    const vis = () => setHidden(document.hidden);
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape' && menuRef.current?.open) { setMenu(false); summaryRef.current?.focus(); } };
    // Outside pointer closes without moving focus: the clicked focusable keeps it.
    const outside = (e: PointerEvent) => { if (menuRef.current?.open && !menuRef.current.contains(e.target as Node)) setMenu(false); };
    document.addEventListener('visibilitychange', vis);
    document.addEventListener('keydown', key);
    document.addEventListener('pointerdown', outside);
    return () => { document.removeEventListener('visibilitychange', vis); document.removeEventListener('keydown', key); document.removeEventListener('pointerdown', outside); };
  }, []);
  const onMenuBlur = (e: React.FocusEvent) => { const next = e.relatedTarget as Node | null; if (next && !menuRef.current?.contains(next)) setMenu(false); };
  const go = (msg: string) => { setMenu(false); setFeedback(msg); summaryRef.current?.focus(); };
  const signOut = () => { setSigningOut(true); setSignOutError(false); setTimeout(() => { setSigningOut(false); setFeedback(t('Mockup · Al cerrar sesión, el producto lleva a /login.', 'Mockup · Signing out takes the product to /login.')); setMenu(false); }, 700); };
  const toggleTheme = () => { const el = document.getElementById('theme') as HTMLSelectElement | null; if (!el) return; el.value = m.theme === 'dark' ? 'light' : 'dark'; el.dispatchEvent(new Event('change', { bubbles: true })); };

  // Spatial panels: side by side from 840px, a sliding track below
  const [narrow, setNarrow] = React.useState(() => matchMedia('(max-width: 839px)').matches);
  React.useEffect(() => { const q = matchMedia('(max-width: 839px)'); const on = () => setNarrow(q.matches); q.addEventListener('change', on); return () => q.removeEventListener('change', on); }, []);
  const [panel, setPanel] = React.useState<'identity' | 'password'>(PASSWORD_STATES.includes(state) ? 'password' : 'identity');
  const identityRef = React.useRef<HTMLElement>(null), securityRef = React.useRef<HTMLElement>(null);
  React.useEffect(() => {
    const set = (el: HTMLElement | null, off: boolean) => { if (!el) return; if (off) { el.setAttribute('inert', ''); el.setAttribute('aria-hidden', 'true'); } else { el.removeAttribute('inert'); el.removeAttribute('aria-hidden'); } };
    set(identityRef.current, narrow && panel !== 'identity');
    set(securityRef.current, narrow && panel !== 'password');
  }, [narrow, panel]);
  const jump = (to: 'identity' | 'password') => {
    setPanel(to);
    const target = document.getElementById(to === 'identity' ? 'identity-title' : 'password-title');
    setTimeout(() => target?.focus({ preventScroll: narrow }), narrow ? 40 : 0);
  };

  // Password form (simulated)
  const preset: Record<string, [string, string, string]> = { corta: ['actual-ejemplo', 'corta1', 'corta1'], larga: ['actual-ejemplo', 'x'.repeat(200), 'x'.repeat(200)], 'no-coinciden': ['actual-ejemplo', 'nueva-ejemplo-1', 'nueva-ejemplo-2'], 'actual-incorrecta': ['incorrecta', 'nueva-ejemplo-1', 'nueva-ejemplo-1'], pendiente: ['actual-ejemplo', 'nueva-ejemplo-1', 'nueva-ejemplo-1'], 'error-servicio': ['actual-ejemplo', 'nueva-ejemplo-1', 'nueva-ejemplo-1'], 'error-red': ['actual-ejemplo', 'nueva-ejemplo-1', 'nueva-ejemplo-1'], requerido: ['', '', ''] };
  const [pw, setPw] = React.useState(() => { const p = preset[state] || ['', '', '']; return { current: p[0], next: p[1], repeat: p[2] }; });
  const tooLong = t('La contraseña nueva no puede tener más de 200 caracteres.', 'The new password cannot be longer than 200 characters.');
  const initialErrors: Errors = state === 'requerido' ? { current: t('Completa los tres campos de contraseña.', 'Complete all three password fields.'), next: ' ', repeat: ' ' }
    : state === 'corta' ? { next: t('La contraseña nueva debe tener al menos 8 caracteres.', 'The new password must be at least 8 characters.') }
    : state === 'larga' ? { next: tooLong }
    : state === 'no-coinciden' ? { repeat: t('Las contraseñas nuevas no coinciden.', 'The new passwords do not match.') }
    : state === 'actual-incorrecta' ? { current: t('La contraseña actual no es correcta. Inténtalo de nuevo.', 'The current password is incorrect. Try again.') } : {};
  const [errors, setErrors] = React.useState<Errors>(initialErrors);
  const [pending, setPending] = React.useState(state === 'pendiente');
  const [serviceError, setServiceError] = React.useState(state === 'error-servicio' || state === 'error-red');
  const [success, setSuccess] = React.useState(state === 'exito');
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess(false); setServiceError(false);
    let next: Errors = {};
    if (!pw.current || !pw.next || !pw.repeat) next = { current: !pw.current ? t('Completa los tres campos de contraseña.', 'Complete all three password fields.') : undefined, next: !pw.next ? ' ' : undefined, repeat: !pw.repeat ? ' ' : undefined };
    else if (pw.next.length < 8) next = { next: t('La contraseña nueva debe tener al menos 8 caracteres.', 'The new password must be at least 8 characters.') };
    else if (pw.next.length > 200) next = { next: tooLong };
    else if (pw.next !== pw.repeat) next = { repeat: t('Las contraseñas nuevas no coinciden.', 'The new passwords do not match.') };
    const clean = Object.fromEntries(Object.entries(next).filter(([, v]) => v)) as Errors;
    setErrors(clean);
    const first = (['current', 'next', 'repeat'] as const).find((k) => clean[k]);
    if (first) { document.getElementById(`pw-${first}`)?.focus(); return; }
    setPending(true);
    setTimeout(() => { setPending(false); setPw({ current: '', next: '', repeat: '' }); setSuccess(true); }, 900);
  };
  const requiredMsg = errors.current && errors.next === ' ' ? errors.current : '';
  const field = (key: 'current' | 'next' | 'repeat', label: string, auto: string, hint?: string) => {
    const err = errors[key]; const show = err && err.trim() && !(key === 'current' && requiredMsg);
    const describedBy = [hint ? `pw-${key}-hint` : '', show ? `pw-${key}-err` : '', requiredMsg && err ? 'pw-required' : ''].filter(Boolean).join(' ') || undefined;
    return <div className="field">
      <label htmlFor={`pw-${key}`}>{label}</label>
      <Input id={`pw-${key}`} name={key} type="password" autoComplete={auto} required minLength={key === 'current' ? 1 : 8} maxLength={key === 'current' ? undefined : 200} value={pw[key]} onChange={(e) => { const v = e.target.value; setPw((p) => ({ ...p, [key]: v })); }} aria-invalid={err ? true : undefined} aria-describedby={describedBy} />
      {hint && <p className="field-hint" id={`pw-${key}-hint`}>{hint}</p>}
      {show && <p className="field-error" id={`pw-${key}-err`}><CircleAlert aria-hidden="true" />{err}</p>}
    </div>;
  };

  const tabs: { id: 'identity' | 'password'; icon: typeof IdCard; label: string }[] = [
    { id: 'identity', icon: IdCard, label: t('Identidad', 'Identity') },
    { id: 'password', icon: KeyRound, label: t('Contraseña', 'Password') },
  ];
  const indicatorTransition = profile.reduced ? { duration: 0 } : profile.profile === 'expressive' ? { type: 'spring' as const, stiffness: 300, damping: 24 } : profile.profile === 'natural' ? { type: 'spring' as const, stiffness: 420, damping: 34 } : { duration: 0.12 };

  const menuItems: { key: string; label: string; current?: boolean; onClick: () => void; icon?: React.ReactNode }[] = [
    { key: 'cuenta', label: t('Mi cuenta', 'My account'), current: true, onClick: () => { setMenu(false); document.getElementById('page-title')?.focus(); } },
    { key: 'planes', label: t('Planes', 'Plans'), onClick: () => go(t('Mockup · Planes: destino sin cambios definido en planes@v1.', 'Mockup · Plans: unchanged destination defined in planes@v1.')) },
    ...(canUsers ? [{ key: 'admin', label: t('Administración', 'Administration'), onClick: () => go(t('Mockup · Administración: pantalla sin cambios de cuentas-admin@v1.', 'Mockup · Administration: unchanged cuentas-admin@v1 screen.')) }] : []),
    ...(canRoles ? [{ key: 'roles', label: t('Roles y permisos', 'Roles and permissions'), onClick: () => go(t('Mockup · Roles y permisos: pantalla sin cambios de cuentas-admin@v1.', 'Mockup · Roles and permissions: unchanged cuentas-admin@v1 screen.')) }] : []),
  ];

  return <><style>{css}</style><div className="app" data-profile={profile.profile} data-reduced={profile.reduced} data-hidden={hidden}>
    <header className="masthead">
      <div className="brand"><span className="brandmark" aria-hidden="true"><svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeOpacity=".65" strokeWidth="1.2" /><circle cx="8" cy="8" r="1.8" fill="currentColor" /></svg></span>Pictures<span className="company">Sempertex</span></div>
      <div className="header-tools">
        <label className="language" htmlFor="language">{t('Idioma', 'Language')}<select id="language" className="native" value={lang} onChange={(e) => { fixture.lang = e.target.value; setLang(e.target.value); }}><option value="es">ES</option><option value="en">EN</option></select></label>
        <details className="user-menu" ref={menuRef} open={menu} onBlur={onMenuBlur}>
          <summary ref={summaryRef} aria-label={`${t('Cuenta', 'Account')}: ${displayName}`} onClick={(e) => { e.preventDefault(); setMenu((v) => !v); }}>
            <Mono text={displayName} />
            <span className="trigger-name" aria-hidden="true">{displayName}</span>
            <ChevronDown className="chev" aria-hidden="true" />
          </summary>
          {menu && <div className="menu-sheet">
            <div className="menu-id">
              <Mono text={displayName} />
              <div style={{ minWidth: 0 }}>
                <p className="menu-name">{displayName}</p>
                {displayName !== person.email && <p className="menu-email">{person.email}</p>}
                <p className="menu-access">{accessLabel} · {accessValue}</p>
              </div>
            </div>
            <nav className="menu-group" aria-label={t('Cuenta', 'Account')}>
              {menuItems.map((item, n) => <a key={item.key} className="menu-item" style={{ '--n': n } as React.CSSProperties} href={item.key === 'cuenta' ? '/cuenta' : item.key === 'planes' ? '/planes' : item.key === 'admin' ? '/admin/cuentas' : '/admin/roles'} aria-current={item.current ? 'page' : undefined} onClick={(e) => { e.preventDefault(); item.onClick(); }}>{item.label}</a>)}
            </nav>
            <div className="menu-group">
              <button type="button" className="menu-item" style={{ '--n': menuItems.length } as React.CSSProperties} onClick={toggleTheme}>{m.theme === 'dark' ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}{t('Cambiar tema', 'Change theme')}</button>
              <button type="button" className="menu-item" style={{ '--n': menuItems.length + 1 } as React.CSSProperties} onClick={signOut} disabled={signingOut} aria-busy={signingOut || undefined}>{signingOut ? <Spinner aria-hidden="true" /> : <LogOut aria-hidden="true" />}{signingOut ? t('Cerrando sesión…', 'Signing out…') : t('Cerrar sesión', 'Sign out')}</button>
              {signOutError && !signingOut && <p className="menu-error" role="alert">{t('No se pudo cerrar la sesión. Inténtalo de nuevo.', 'Could not sign out. Please try again.')}</p>}
            </div>
          </div>}
        </details>
      </div>
    </header>

    <div className="heading">
      <div><h1 id="page-title" tabIndex={-1}>{t('Mi cuenta', 'My account')}</h1><p>{t('Tu cuenta está activa.', 'Your account is active.')}</p></div>
      <nav className="local-nav" aria-label={t('Secciones de Mi cuenta', 'My account sections')}>
        {tabs.map((tab) => { const on = panel === tab.id; return <button key={tab.id} type="button" className="local-tab" aria-pressed={on} aria-controls={tab.id === 'identity' ? 'identity-pass' : 'security-panel'} onClick={() => jump(tab.id)}>
          {on && <motion.span layoutId="local-indicator" className="local-nav-indicator" aria-hidden="true" transition={indicatorTransition} />}
          <tab.icon aria-hidden="true" /><span className="tab-label">{tab.label}</span></button>; })}
      </nav>
    </div>
    <nav className="route-nav" aria-label={t('Navegación de cuentas', 'Account navigation')}>
      {canUsers && <a href="/admin/cuentas" onClick={(e) => { e.preventDefault(); setFeedback(t('Mockup · Cuentas: pantalla sin cambios de cuentas-admin@v1.', 'Mockup · Accounts: unchanged cuentas-admin@v1 screen.')); }}>{t('Cuentas', 'Accounts')}</a>}
      {canRoles && <a href="/admin/roles" onClick={(e) => { e.preventDefault(); setFeedback(t('Mockup · Roles y permisos: pantalla sin cambios de cuentas-admin@v1.', 'Mockup · Roles and permissions: unchanged cuentas-admin@v1 screen.')); }}>{t('Roles y permisos', 'Roles and permissions')}</a>}
      <a href="/cuenta" aria-current="page" onClick={(e) => e.preventDefault()}>{t('Mi cuenta', 'My account')}</a>
    </nav>
    <aside className="mock-context" aria-label="Mockup · datos de ejemplo">
      <label htmlFor="fixture-access">Mockup · {t('Acceso', 'Access')}<select id="fixture-access" className="native" value={access} onChange={(e) => { fixture.access = e.target.value; setAccess(e.target.value); }}>
        <option value="entusiasta">Plan Entusiasta</option><option value="designer">Plan Designer</option><option value="designer-plus">Plan Designer Plus</option><option value="master-designer">Plan Master Designer</option>
        <option value="administrador">Administrador</option><option value="empleado">Empleado interno</option><option value="personalizado">Rol personalizado (solo cuentas)</option></select></label>
      <label htmlFor="fixture-person">Mockup · {t('Persona', 'Person')}<select id="fixture-person" className="native" value={personKey} onChange={(e) => { fixture.person = e.target.value; setPersonKey(e.target.value); }}>
        <option value="con-nombre">Con nombre y empresa</option><option value="sin-nombre">Sin nombre</option><option value="nombre-largo">Nombre largo</option><option value="correo-largo">Correo largo</option></select></label>
      <span className="fixture-hint">{t('Datos y operaciones simulados', 'Simulated data and operations')}</span>
    </aside>
    {feedback && <p className="scope-feedback" role="status">{feedback}</p>}

    <div className="account-viewport">
      <div className="account-track" style={{ '--i': panel === 'password' ? 1 : 0 } as React.CSSProperties} aria-busy={loading || undefined}>
        <section ref={identityRef} id="identity-pass" className="paper identity-pass" data-spot={narrow ? undefined : panel === 'identity'} aria-labelledby="identity-title" onFocus={() => !narrow && setPanel('identity')}>
          {loading ? <div className="skel"><span className="sr" role="status">{t('Cargando tu cuenta…', 'Loading your account…')}</span><Skeleton className="round" /><Skeleton style={{ width: '60%' }} /><Skeleton /><Skeleton style={{ width: '80%' }} /><Skeleton style={{ width: '40%' }} /></div> : <>
            <div className="pass-top">
              <Mono text={displayName} className="monogram-lg" />
              <h2 id="identity-title" className="panel-title" tabIndex={-1}>{t('Tu identidad', 'Your identity')}</h2>
            </div>
            <dl className="pass-rows">
              <div className="pass-row name" style={{ '--n': 0 } as React.CSSProperties}><dt>{t('Nombre', 'Name')}</dt><dd>{displayName}</dd></div>
              <div className="pass-row" style={{ '--n': 1 } as React.CSSProperties}><dt>{t('Correo', 'Email')}</dt><dd>{person.email}</dd></div>
              {person.company && <div className="pass-row" style={{ '--n': 2 } as React.CSSProperties}><dt>{t('Empresa', 'Company')}</dt><dd>{person.company}</dd></div>}
            </dl>
            <dl className="pass-access"><div className="pass-row" style={{ '--n': 3 } as React.CSSProperties}><dt>{accessLabel}</dt><dd className="access-value">{accessValue}</dd></div></dl>
          </>}
        </section>

        <section ref={securityRef} id="security-panel" className="paper security-panel" data-spot={narrow ? undefined : panel === 'password'} aria-labelledby="password-title" onFocus={() => !narrow && setPanel('password')}>
          {loading ? <div className="skel"><Skeleton style={{ width: '45%' }} /><Skeleton className="tall" /><Skeleton className="tall" /><Skeleton className="tall" /><Skeleton style={{ width: '30%', height: 44 }} /></div> : <>
            <div className="panel-head"><KeyRound aria-hidden="true" /><h2 id="password-title" className="panel-title" tabIndex={-1}>{t('Cambiar contraseña', 'Change password')}</h2></div>
            {success && <div className="receipt" role="status"><Check aria-hidden="true" /><p>{t('Contraseña cambiada. Esta sesión se renovó; tus otras sesiones terminaron.', 'Password changed. This session was renewed; your other sessions ended.')}</p></div>}
            <form className="pw-form" noValidate onSubmit={submit} aria-busy={pending || undefined}>
              {requiredMsg && <p className="field-error" id="pw-required" role="alert"><CircleAlert aria-hidden="true" />{requiredMsg}</p>}
              <div className="pw-group">{field('current', t('Contraseña actual', 'Current password'), 'current-password')}</div>
              <div className="pw-group"><div className="pw-pair">
                {field('next', t('Contraseña nueva', 'New password'), 'new-password', t('Entre 8 y 200 caracteres.', 'Between 8 and 200 characters.'))}
                {field('repeat', t('Repite la contraseña nueva', 'Repeat new password'), 'new-password')}
              </div></div>
              {serviceError && <div className="note" data-tone="error" role="alert"><CircleAlert aria-hidden="true" /><p>{t('No se pudo cambiar la contraseña. Inténtalo de nuevo.', 'Could not change the password. Please try again.')}</p></div>}
              <div className="form-actions">
                <Button type="submit" className="btn" data-variant="default" disabled={pending}>{pending ? <Spinner aria-hidden="true" /> : null}{pending ? t('Guardando…', 'Saving…') : t('Cambiar contraseña', 'Change password')}</Button>
                {pending && <span className="pending-text" role="status">{t('Verificando tu contraseña actual…', 'Checking your current password…')}</span>}
              </div>
            </form>
          </>}
        </section>
      </div>
    </div>
  </div></>;
}

mountMockup(App, {
  title: 'cuentas-admin@v2 · Dirección B · Pase y panel',
  views: [{ id: 'cuenta', label: 'Mi cuenta' }, { id: 'menu', label: 'Menú de cuenta abierto' }],
  states: [
    { id: 'normal', label: 'Normal' }, { id: 'cargando', label: 'Cargando' },
    { id: 'requerido', label: 'Contraseña: campos vacíos' }, { id: 'corta', label: 'Contraseña: corta' }, { id: 'larga', label: 'Contraseña: más de 200' },
    { id: 'no-coinciden', label: 'Contraseña: no coinciden' }, { id: 'actual-incorrecta', label: 'Contraseña actual incorrecta' }, { id: 'pendiente', label: 'Guardando' },
    { id: 'error-servicio', label: 'Error del servicio' }, { id: 'error-red', label: 'Error de red' }, { id: 'exito', label: 'Contraseña cambiada' },
    { id: 'cerrando-sesion', label: 'Menú: cerrando sesión' }, { id: 'error-cierre', label: 'Menú: error al cerrar sesión' },
  ],
  motion: 'expressive',
});
