import * as React from 'react';
import { Check, ChevronDown, CircleAlert, LogOut, Moon, Sun, WifiOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Spinner } from '@/components/ui/spinner';
import { Separator } from '@/components/ui/separator';
import { mountMockup, useMockup } from '@kit/mockup';
import { useMotionProfile } from '@kit/motion';
import bodyFont from '/home/david/dev/pictures-wt/t12/.next/static/media/caa3a2e1cccd8315-s.p.0wgildi0cnwt9.woff2';
import monoFont from '/home/david/dev/pictures-wt/t12/.next/static/media/797e433ab948586e-s.p.0r6juujl39pe6.woff2';

// Direction A · «Ficha dividida»: operational account sheet. One divided paper — identity ledger | password form —
// inside the existing Pictures/Sempertex shell. Precise quick cuts: clip reveals, short registers, instant closes.
const css = `
@font-face{font-family:Geist;src:url(${bodyFont}) format('woff2');font-weight:100 900;font-display:block}
@font-face{font-family:'Geist Mono';src:url(${monoFont}) format('woff2');font-weight:100 900;font-display:block}
:root,[data-theme="light"]{--fondo:#faf9fc;--superficie:#ffffff;--superficie-suave:#faf8fd;--superficie-2:#efe9f8;--borde:#e3daef;--borde-suave:#efe9f8;--texto:#1c1425;--texto-suave:#6b6178;--texto-tenue:#766c85;--acento:#6d3fe0;--acento-hover:#5530b8;--acento-suave:#ece3fb;--sobre-acento:#ffffff;--exito:#1f7a55;--exito-suave:#dcf5e9;--error:#b23a45;--error-suave:#ffeaec;--aviso:#8f5f12;--aviso-suave:#fff3d8;--sombra:rgb(28 20 37 / 0.08);--overlay:rgb(28 20 37 / 0.4);--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--card-foreground:var(--texto);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);--secondary:var(--superficie-2);--secondary-foreground:var(--texto);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--superficie-2);--accent-foreground:var(--texto);--destructive:var(--error);--border:var(--borde);--input:var(--texto-tenue);--ring:var(--acento);color-scheme:light}
.dark,[data-theme="dark"]{--fondo:#0b0c10;--superficie:#16181f;--superficie-suave:#1c1e26;--superficie-2:#242733;--borde:#383c48;--borde-suave:#2a2d38;--texto:#f4f5f7;--texto-suave:#9aa1ad;--texto-tenue:#8a91a0;--acento:#9479ff;--acento-hover:#a58dff;--acento-suave:#241f3d;--sobre-acento:#120b24;--exito:#78d6a8;--exito-suave:#173b31;--error:#ff979f;--error-suave:#43252a;--aviso:#f7c46b;--aviso-suave:#3f311c;--sombra:rgb(0 0 0 / 0.4);--overlay:rgb(0 0 0 / 0.6);--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--card-foreground:var(--texto);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);--secondary:var(--superficie-2);--secondary-foreground:var(--texto);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--superficie-2);--accent-foreground:var(--texto);--destructive:var(--error);--border:var(--borde);--input:var(--texto-tenue);--ring:var(--acento);color-scheme:dark}
body{font-family:Geist,ui-sans-serif,system-ui,sans-serif;font-size:15px;line-height:1.5;background:var(--fondo);color:var(--texto);margin:0}
*{box-sizing:border-box}button,input,select{font:inherit}h1,h2,h3,p,dl,dd{margin:0}svg{flex-shrink:0;width:18px;height:18px}
.app{--cut:cubic-bezier(.32,.72,0,1);--t-menu:200ms;--t-row:260ms;--t-quick:150ms;--step:28ms;min-height:calc(100svh - var(--mockup-bar-h,0px));padding:0 40px 28px;max-width:1520px;margin:auto;display:flex;flex-direction:column}
.app[data-profile="natural"]{--t-menu:160ms;--t-row:200ms;--t-quick:130ms;--step:20ms}.app[data-profile="subtle"]{--t-menu:110ms;--t-row:140ms;--t-quick:100ms;--step:12ms}
.app[data-reduced="true"] *, .app[data-reduced="true"] *::before{animation:none!important;transition:none!important}
:root[data-hidden] .app *{animation-play-state:paused!important}
:focus-visible{outline:3px solid var(--acento);outline-offset:4px}
.mono{font-family:'Geist Mono',ui-monospace,monospace;font-variant-numeric:tabular-nums}
/* shell — reproduced from sibling contracts (herramientas-chat@v1, planes@v1) */
.masthead{min-height:76px;display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 0;border-bottom:1px solid var(--borde-suave)}
.brand{display:flex;align-items:center;gap:12px;font-size:16px;font-weight:600;white-space:nowrap}.brandmark{width:28px;height:28px;display:grid;place-items:center;background:var(--acento);color:var(--sobre-acento);border-radius:8px}.brandmark svg{width:16px;height:16px}
.company{font:12px 'Geist Mono',monospace;border-left:1px solid var(--texto);margin-left:12px;padding-left:16px}
.header-tools{display:flex;gap:16px;align-items:center}.language{display:flex;align-items:center;gap:10px;font-size:13px;color:var(--texto-suave)}
select.native{min-height:44px;border:1px solid var(--texto-tenue);border-radius:18px;background:var(--superficie);color:var(--texto);padding:0 14px}
/* account trigger + popup */
.acct{position:relative}
.acct-trigger{min-height:44px;display:flex;align-items:center;gap:8px;padding:0 12px 0 6px;border:1px solid var(--texto-tenue);border-radius:999px;background:var(--superficie);color:var(--texto);font-size:14px;font-weight:500;cursor:pointer;transition:border-color var(--t-quick) var(--cut),background-color var(--t-quick) var(--cut)}
.acct-trigger:hover{border-color:var(--acento)}.acct-trigger[aria-expanded="true"]{background:var(--superficie-2)}
.acct-trigger .chev{width:16px;height:16px;color:var(--texto-suave);transition:transform var(--t-quick) var(--cut)}.acct-trigger[aria-expanded="true"] .chev{transform:rotate(180deg)}
.initial{width:32px;height:32px;border-radius:50%;display:grid;place-items:center;background:var(--acento-suave);color:var(--acento);font-size:13px;font-weight:600}
.acct-name{max-width:176px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.acct-menu{position:absolute;right:0;top:calc(100% + 8px);z-index:40;width:320px;max-width:calc(100vw - 24px);background:var(--superficie);border:1px solid var(--borde);border-radius:20px;box-shadow:0 18px 40px var(--sombra);padding:8px;transform-origin:top right;animation:menu-cut var(--t-menu) var(--cut) both}
@keyframes menu-cut{from{clip-path:inset(0 0 100% 35% round 20px);opacity:.4}to{clip-path:inset(0 0 0 0 round 20px);opacity:1}}
.who{display:grid;grid-template-columns:40px 1fr;gap:12px;padding:10px 10px 12px}.who .initial{width:40px;height:40px;font-size:15px}
.who-name{font-size:16px;font-weight:600;line-height:1.3;overflow-wrap:anywhere}.who-mail{font-size:12px;color:var(--texto-suave);overflow-wrap:anywhere;margin-top:2px}
.who-access{display:inline-flex;gap:6px;align-items:baseline;margin-top:8px;font-size:12px;padding:3px 10px;border-radius:999px;background:var(--superficie-2);color:var(--texto)}.who-access b{font-weight:600}
.menu-group{display:grid;padding:4px 0}.menu-group>*{animation:item-in var(--t-row) var(--cut) both;animation-delay:calc(var(--i,0) * var(--step))}
@keyframes item-in{from{transform:translateY(-4px);opacity:0}to{transform:none;opacity:1}}
.mi{min-height:44px;display:flex;align-items:center;gap:10px;padding:0 12px;border-radius:12px;color:var(--texto);text-decoration:none;font-size:14px;background:none;border:0;width:100%;text-align:left;cursor:pointer;transition:background-color var(--t-quick) var(--cut)}
.mi:hover{background:var(--superficie-2)}.mi[aria-current="page"]{font-weight:600}.mi .tick{margin-left:auto;width:16px;height:16px;color:var(--texto-suave)}
.mi-err{font-size:12px;color:var(--error);padding:2px 12px 6px}
[data-slot="separator"].menu-sep{background:var(--borde-suave);margin:4px 8px}
/* page */
.page{flex:1;width:100%;max-width:1040px;margin:0 auto;padding-top:24px}
.page-head{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;flex-wrap:wrap;position:relative;padding-bottom:12px}
.page-head h1{font-size:24px;line-height:1.25;font-weight:600;letter-spacing:-.01em}.page-head p{font-size:13px;color:var(--texto-suave);margin-top:4px}
.head-rule{position:absolute;left:0;right:0;bottom:0;height:1px;background:var(--borde);transform-origin:left;animation:rule-draw calc(var(--t-row) * 1.6) var(--cut) both}
@keyframes rule-draw{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.route-nav{display:flex;gap:4px;flex-wrap:wrap}.route-nav a{min-height:44px;display:inline-flex;align-items:center;padding:0 12px;border-radius:12px;font-size:14px;color:var(--texto-suave);text-decoration:none;transition:color var(--t-quick) var(--cut),background-color var(--t-quick) var(--cut)}
.route-nav a:hover{color:var(--texto);background:var(--superficie-2)}.route-nav a[aria-current="page"]{color:var(--texto);font-weight:600;background:var(--superficie-2)}
.mock-context{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:16px 0 0;font-size:12px;color:var(--texto-suave)}.mock-context select{min-height:44px;font-size:13px}
.paper{margin-top:16px;background:var(--superficie);border:1px solid var(--borde);border-radius:32px;display:grid;grid-template-columns:340px minmax(0,1fr);overflow:clip}
.ficha{padding:28px;border-right:1px solid var(--borde-suave);min-width:0}
.pw{padding:28px;min-width:0}
.sec-title{font-size:17px;font-weight:600;line-height:1.3}.sec-note{font-size:13px;color:var(--texto-suave);margin-top:4px}
.ledger{margin-top:18px;display:grid}
.ficha-row{display:grid;grid-template-columns:88px minmax(0,1fr);gap:12px;align-items:baseline;padding:12px 0;border-top:1px solid var(--borde-suave);animation:reg-in var(--t-row) var(--cut) both;animation-delay:calc(var(--i,0) * var(--step) + 60ms)}
.ficha-row:last-child{border-bottom:1px solid var(--borde-suave)}
@keyframes reg-in{from{transform:translateX(-6px);opacity:0}to{transform:none;opacity:1}}
.ficha-row dt{font-size:12px;color:var(--texto-suave)}
.ficha-row dd{min-width:0;overflow-wrap:anywhere}
.v-name{font-size:20px;font-weight:600;line-height:1.3}.v-name.fallback{font-size:15px;font-weight:500}
.v-mail{font-size:13px}
.v-access{font-size:15px;font-weight:600}.v-access small{display:block;font-size:12px;font-weight:400;color:var(--texto-suave);margin-top:2px}
.v-plain{font-size:14px}
/* password form */
.pw-form{display:grid;gap:16px;margin-top:20px}
.pw-pair{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.field{display:grid;gap:6px;min-width:0;align-content:start}.field label{font-size:14px;font-weight:500}
.app .field input[data-slot="input"]{height:44px;border-radius:18px;padding:0 14px;font-size:15px;background:var(--superficie);border-color:var(--texto-tenue);color:var(--texto);transition:border-color var(--t-quick) var(--cut),box-shadow var(--t-quick) var(--cut)}
.app .field input[aria-invalid="true"]{border-color:var(--error)}.app .field input[readonly]{background:var(--superficie-suave);color:var(--texto-suave)}
.hint{font-size:12px;color:var(--texto-suave)}
.pw-msg{display:grid;grid-template-rows:0fr;transition:grid-template-rows var(--t-row) var(--cut)}.pw-msg[data-on="true"]{grid-template-rows:1fr}.pw-msg>div{overflow:hidden}
.pw-msg p{font-size:13px;font-weight:500;color:var(--error);padding-top:2px}
.form-status{display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-radius:18px;font-size:14px;animation:status-in var(--t-row) var(--cut) both}
.form-status.err{background:var(--error-suave);color:var(--error)}.form-status.ok{background:var(--exito-suave);color:var(--exito)}
@keyframes status-in{from{transform:translateY(4px);opacity:0}to{transform:none;opacity:1}}
.form-status .draw path{stroke-dasharray:24;stroke-dashoffset:0;animation:draw calc(var(--t-row) * 1.4) var(--cut) 80ms both}
@keyframes draw{from{stroke-dashoffset:24}to{stroke-dashoffset:0}}
.form-actions{display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.app .btn[data-slot="button"]{min-height:44px;height:auto;padding:0 20px;border-radius:18px;font-size:14px;font-weight:600;min-width:196px;gap:8px;transition:background-color var(--t-quick) var(--cut),transform var(--t-quick) var(--cut)}
.app .btn[data-slot="button"]:hover{background:var(--acento-hover)}.app .btn[data-slot="button"]:active{transform:translateY(1px)}
.app .btn[data-slot="button"]:disabled{opacity:1;background:var(--acento-hover)}
.btn-link{min-height:44px;background:none;border:0;color:var(--acento);font-size:14px;font-weight:500;cursor:pointer;text-decoration:underline;text-underline-offset:4px;padding:0 4px}
/* other signed-in page */
.other{margin-top:16px;padding:28px;border:1px dashed var(--borde);border-radius:32px;color:var(--texto-suave);font-size:14px}
/* loading */
.app [data-slot="skeleton"]{background:var(--superficie-2)}.trigger-skel{height:44px;width:180px;border-radius:999px!important}
.footer{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;border-top:1px solid var(--borde-suave);margin-top:32px;padding-top:16px;font-size:12px;color:var(--texto-suave)}
/* view swap */
.swap{animation:swap-in var(--t-row) var(--cut) both}@keyframes swap-in{from{opacity:.2}to{opacity:1}}
@media (max-width:1099px){.paper{grid-template-columns:300px minmax(0,1fr)}.pw-pair{grid-template-columns:1fr}}
@media (max-width:839px){.paper{grid-template-columns:1fr}.ficha{border-right:0;border-bottom:1px solid var(--borde-suave)}.page-head{align-items:flex-start}}
@media (max-width:639px){.app{padding:0 20px 24px}.masthead{gap:12px}.company{margin-left:2px;padding-left:12px}.header-tools{gap:10px}.ficha,.pw{padding:20px}.paper{border-radius:24px}.page-head{flex-direction:column;gap:8px}.route-nav{margin-left:-12px}.form-actions .btn[data-slot="button"]{width:100%}}
@media (max-width:479px){.masthead{position:relative;flex-wrap:wrap;row-gap:12px}.header-tools{width:100%;justify-content:space-between}.acct{position:static;min-width:0}.acct-trigger{max-width:100%}.acct-name{max-width:150px}.trigger-skel{width:180px}.ficha-row{grid-template-columns:1fr;gap:2px}.acct-menu{left:0;right:0;width:auto;max-width:none;top:calc(100% + 4px)}}
@media (max-width:399px){.acct-name{display:none}.acct-trigger{padding:0 10px 0 8px}.language{gap:8px}}
`;

type Lang = 'es' | 'en';
type Access = { kind: 'plan'; plan: 'entusiasta' | 'designer' | 'designer_plus' | 'master_designer' } | { kind: 'role'; role: 'admin' | 'employee' | 'custom' };
type Fixture = { id: string; label: string; name: string | null; email: string; company?: string; access: Access; adminAccounts: boolean; adminRoles: boolean };

// plan-catalogue@1 names (src/lib/planes/catalogo.ts); this mockup only reads them, it does not own them.
const PLAN_NAMES: Record<string, [string, string]> = { entusiasta: ['Entusiasta', 'Enthusiast'], designer: ['Designer', 'Designer'], designer_plus: ['Designer Plus', 'Designer Plus'], master_designer: ['Master Designer', 'Master Designer'] };
const ROLE_NAMES: Record<string, [string, string]> = { admin: ['Administrador', 'Administrator'], employee: ['Empleado interno', 'Internal employee'], custom: ['Rol de prueba', 'Rol de prueba'] };

const FIXTURES: Fixture[] = [
  { id: 'admin', label: 'Administrador · con nombre', name: 'Cuenta administradora', email: 'admin@prueba.local', access: { kind: 'role', role: 'admin' }, adminAccounts: true, adminRoles: true },
  { id: 'employee', label: 'Empleado interno · sin administración', name: 'Cuenta de empleado interno', email: 'empleado@prueba.local', access: { kind: 'role', role: 'employee' }, adminAccounts: false, adminRoles: false },
  { id: 'custom', label: 'Rol personalizado · solo roles', name: 'Cuenta con rol personalizado', email: 'rol@prueba.local', access: { kind: 'role', role: 'custom' }, adminAccounts: false, adminRoles: true },
  { id: 'entusiasta', label: 'Entusiasta · sin nombre', name: '   ', email: 'entusiasta@prueba.local', access: { kind: 'plan', plan: 'entusiasta' }, adminAccounts: false, adminRoles: false },
  { id: 'designer', label: 'Designer · nombre largo', name: 'Cuenta Designer de ejemplo con un nombre muy largo para comprobar el ajuste de línea', email: 'designer@prueba.local', access: { kind: 'plan', plan: 'designer' }, adminAccounts: false, adminRoles: false },
  { id: 'plus', label: 'Designer Plus · correo largo y empresa', name: 'Cuenta Designer Plus', email: 'cuenta.designer.plus.con.un.correo.largo@subdominio-de-prueba.prueba.local', company: 'Empresa de ejemplo', access: { kind: 'plan', plan: 'designer_plus' }, adminAccounts: false, adminRoles: false },
  { id: 'master', label: 'Master Designer · con nombre', name: 'Cuenta Master Designer', email: 'master@prueba.local', access: { kind: 'plan', plan: 'master_designer' }, adminAccounts: false, adminRoles: false },
];

const TXT = {
  es: { language: 'Idioma', account: 'Cuenta', title: 'Mi cuenta', active: 'Tu cuenta está activa.', identity: 'Tu identidad', name: 'Nombre', email: 'Correo', plan: 'Plan', role: 'Rol', company: 'Empresa', myAccount: 'Mi cuenta', plans: 'Planes', administration: 'Administración', roles: 'Roles y permisos', accounts: 'Cuentas', theme: 'Cambiar tema', signOut: 'Cerrar sesión', changePassword: 'Cambiar contraseña', pwNote: 'Al cambiarla, esta sesión se renueva y tus otras sesiones terminan.', current: 'Contraseña actual', next: 'Contraseña nueva', repeat: 'Repite la contraseña nueva', hint: 'Entre 8 y 200 caracteres.', submit: 'Cambiar contraseña', loading: 'Guardando…', required: 'Completa los tres campos de contraseña.', tooShort: 'La contraseña nueva debe tener al menos 8 caracteres.', tooLong: 'La contraseña nueva debe tener como máximo 200 caracteres.', mismatch: 'Las contraseñas nuevas no coinciden.', currentInvalid: 'La contraseña actual no es correcta. Inténtalo de nuevo.', changeError: 'No se pudo cambiar la contraseña. Inténtalo de nuevo.', network: 'No hubo conexión con el servidor. Tus datos siguen escritos; inténtalo de nuevo.', changed: 'Contraseña cambiada. Esta sesión se renovó; tus otras sesiones terminaron.', retry: 'Intentar de nuevo', staff: 'Acceso del personal de Sempertex', custom: 'Rol personalizado', tools: 'Herramientas', otherPage: 'Mockup · Página existente con sesión iniciada. Su contenido no cambia en SP-2; solo se muestra el menú de cuenta compartido.', mock: 'Mockup · Cuenta de ejemplo', footer: 'Mockup · Datos y operaciones simulados', rev: 'cuentas-admin@v2 · dirección A «Ficha dividida», borrador r1', loadingPage: 'Cargando tu cuenta…' },
  en: { language: 'Language', account: 'Account', title: 'My account', active: 'Your account is active.', identity: 'Your identity', name: 'Name', email: 'Email', plan: 'Plan', role: 'Role', company: 'Company', myAccount: 'My account', plans: 'Plans', administration: 'Administration', roles: 'Roles and permissions', accounts: 'Accounts', theme: 'Change theme', signOut: 'Sign out', changePassword: 'Change password', pwNote: 'Changing it renews this session and ends your other sessions.', current: 'Current password', next: 'New password', repeat: 'Repeat new password', hint: 'Between 8 and 200 characters.', submit: 'Change password', loading: 'Saving…', required: 'Complete all three password fields.', tooShort: 'The new password must be at least 8 characters.', tooLong: 'The new password must be at most 200 characters.', mismatch: 'The new passwords do not match.', currentInvalid: 'The current password is incorrect. Try again.', changeError: 'Could not change the password. Please try again.', network: 'Could not reach the server. Your entries are kept; try again.', changed: 'Password changed. This session was renewed; your other sessions ended.', retry: 'Try again', staff: 'Sempertex staff access', custom: 'Custom role', tools: 'Tools', otherPage: 'Mockup · Existing signed-in page. Its content does not change in SP-2; only the shared account menu is shown.', mock: 'Mockup · Example account', footer: 'Mockup · Simulated data and operations', rev: 'cuentas-admin@v2 · direction A “Ficha dividida”, draft r1', loadingPage: 'Loading your account…' },
} as const;

type PwState = 'idle' | 'required' | 'short' | 'long' | 'mismatch' | 'wrong-current' | 'pending' | 'service-error' | 'network-error' | 'success';
const LONG = 'x'.repeat(201);
// Field values per declared state (masked inputs; values are fixture placeholders, never real secrets).
const PRESET: Record<PwState, [string, string, string]> = {
  idle: ['', '', ''], required: ['ejemplo-actual', '', ''], short: ['ejemplo-actual', 'corta', 'corta'], long: ['ejemplo-actual', LONG, LONG], mismatch: ['ejemplo-actual', 'ejemplo-nueva-1', 'ejemplo-nueva-2'], 'wrong-current': ['ejemplo-erronea', 'ejemplo-nueva-1', 'ejemplo-nueva-1'], pending: ['ejemplo-actual', 'ejemplo-nueva-1', 'ejemplo-nueva-1'], 'service-error': ['ejemplo-actual', 'ejemplo-nueva-1', 'ejemplo-nueva-1'], 'network-error': ['ejemplo-actual', 'ejemplo-nueva-1', 'ejemplo-nueva-1'], success: ['', '', ''],
};

function accessLine(f: Fixture, L: Lang) {
  const i = L === 'es' ? 0 : 1;
  if (f.access.kind === 'plan') return { label: TXT[L].plan, value: PLAN_NAMES[f.access.plan][i], sub: '' };
  const r = f.access.role;
  return { label: TXT[L].role, value: ROLE_NAMES[r][i], sub: r === 'custom' ? TXT[L].custom : '' };
}
const displayName = (f: Fixture) => (f.name && f.name.trim()) || f.email;

function AccountMenu({ f, L, open, setOpen, current }: { f: Fixture; L: Lang; open: boolean; setOpen: (v: boolean) => void; current: string }) {
  const m = useMockup();
  const T = TXT[L];
  const wrap = React.useRef<HTMLDivElement>(null);
  const trigger = React.useRef<HTMLButtonElement>(null);
  const [signOutError, setSignOutError] = React.useState(false);
  const name = displayName(f);
  const a = accessLine(f, L);
  React.useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') { e.preventDefault(); setOpen(false); trigger.current?.focus(); } };
    // Outside pointer closes without moving focus: the clicked focusable target keeps it.
    const onDown = (e: PointerEvent) => { if (wrap.current && !wrap.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('keydown', onKey);
    document.addEventListener('pointerdown', onDown, true);
    return () => { document.removeEventListener('keydown', onKey); document.removeEventListener('pointerdown', onDown, true); };
  }, [open, setOpen]);
  const toggleTheme = () => { const el = document.getElementById('theme') as HTMLSelectElement | null; if (!el) return; el.value = m.theme === 'dark' ? 'light' : 'dark'; el.dispatchEvent(new Event('change', { bubbles: true })); };
  const links: { id: string; label: string; show: boolean }[] = [
    { id: '/cuenta', label: T.myAccount, show: true },
    { id: '/planes', label: T.plans, show: true },
    { id: '/admin/cuentas', label: T.administration, show: f.adminAccounts },
    { id: '/admin/roles', label: T.roles, show: f.adminRoles },
  ];
  let i = 0;
  return (
    <div className="acct" ref={wrap} onBlur={(e) => { if (open && !e.currentTarget.contains(e.relatedTarget as Node | null) && e.relatedTarget) setOpen(false); }}>
      <button ref={trigger} type="button" className="acct-trigger" aria-expanded={open} aria-controls="account-popup" aria-label={`${T.account}: ${name}`} onClick={() => setOpen(!open)}>
        <span className="initial" aria-hidden="true">{name.slice(0, 1).toLocaleUpperCase()}</span>
        <span className="acct-name">{name}</span>
        <ChevronDown className="chev" aria-hidden="true" />
      </button>
      {open && (
        <div id="account-popup" className="acct-menu" role="group" aria-label={T.account}>
          <div className="who">
            <span className="initial" aria-hidden="true">{name.slice(0, 1).toLocaleUpperCase()}</span>
            <div style={{ minWidth: 0 }}>
              <p className="who-name">{name}</p>
              <p className="who-mail mono">{f.email}</p>
              <p className="who-access"><span>{a.label}</span><b>{a.value}</b></p>
            </div>
          </div>
          <Separator className="menu-sep" />
          <nav className="menu-group" aria-label={T.account}>
            {links.filter((l) => l.show).map((l) => (
              <a key={l.id} href={l.id} className="mi" style={{ '--i': i++ } as React.CSSProperties} aria-current={l.id === current ? 'page' : undefined} onClick={(e) => { e.preventDefault(); setOpen(false); if (l.id === '/cuenta') m.set('view', 'cuenta'); }}>
                {l.label}{l.id === current && <Check className="tick" aria-hidden="true" />}
              </a>
            ))}
          </nav>
          <Separator className="menu-sep" />
          <div className="menu-group">
            <button type="button" className="mi" style={{ '--i': i++ } as React.CSSProperties} onClick={toggleTheme}>{m.theme === 'dark' ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}{T.theme}</button>
          </div>
          <Separator className="menu-sep" />
          <div className="menu-group">
            <button type="button" className="mi" style={{ '--i': i++ } as React.CSSProperties} onClick={() => setSignOutError(true)}><LogOut aria-hidden="true" />{T.signOut}</button>
            {signOutError && <p role="alert" className="mi-err">{L === 'es' ? 'Mockup · En el producto, cerrar sesión lleva a /login.' : 'Mockup · In the product, signing out goes to /login.'}</p>}
          </div>
        </div>
      )}
    </div>
  );
}

function FieldRow({ id, label, value, onChange, error, hint, readOnly, autoComplete, inputRef }: { id: string; label: string; value: string; onChange: (v: string) => void; error?: string; hint?: string; readOnly?: boolean; autoComplete: string; inputRef?: React.Ref<HTMLInputElement> }) {
  const desc = [hint ? `${id}-hint` : '', error ? `${id}-err` : ''].filter(Boolean).join(' ') || undefined;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <Input ref={inputRef} id={id} type="password" autoComplete={autoComplete} maxLength={260} value={value} readOnly={readOnly} aria-invalid={error ? true : undefined} aria-describedby={desc} onChange={(e) => onChange(e.target.value)} />
      {hint && <p id={`${id}-hint`} className="hint">{hint}</p>}
      <div className="pw-msg" data-on={Boolean(error)}><div>{error && <p id={`${id}-err`}>{error}</p>}</div></div>
    </div>
  );
}

function PasswordForm({ L, state }: { L: Lang; state: PwState }) {
  const T = TXT[L];
  const [vals, setVals] = React.useState<[string, string, string]>(PRESET[state]);
  const [st, setSt] = React.useState<PwState>(state);
  const statusRef = React.useRef<HTMLDivElement>(null);
  const firstRef = React.useRef<HTMLInputElement>(null);
  React.useEffect(() => { setVals(PRESET[state]); setSt(state); }, [state]);
  const set = (k: 0 | 1 | 2) => (v: string) => { const n = [...vals] as [string, string, string]; n[k] = v; setVals(n); if (st !== 'pending') setSt('idle'); };
  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const [c, n, r] = vals;
    let next: PwState;
    if (!c || !n || !r) next = 'required';
    else if (n.length < 8) next = 'short';
    else if (n.length > 200) next = 'long';
    else if (n !== r) next = 'mismatch';
    else next = 'pending';
    setSt(next);
    if (next === 'pending') {
      // Mockup: the service result is chosen with the «Estado» selector; a free submit shows the server-confirmed path.
      window.setTimeout(() => { setVals(['', '', '']); setSt('success'); requestAnimationFrame(() => statusRef.current?.focus()); }, 900);
    }
  };
  const pending = st === 'pending';
  const fieldErr = (k: 0 | 1 | 2): string | undefined => {
    if (st === 'required' && !vals[k]) return T.required;
    if (k === 0 && st === 'wrong-current') return T.currentInvalid;
    if (k === 1 && st === 'short') return T.tooShort;
    if (k === 1 && st === 'long') return T.tooLong;
    if (k === 2 && st === 'mismatch') return T.mismatch;
    return undefined;
  };
  return (
    <form className="pw-form" onSubmit={submit} aria-busy={pending} noValidate>
      {st === 'success' && (
        <div ref={statusRef} tabIndex={-1} role="status" className="form-status ok">
          <svg className="draw" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5" /></svg>
          <span>{T.changed}</span>
        </div>
      )}
      {(st === 'service-error' || st === 'network-error') && (
        <div role="alert" className="form-status err">
          {st === 'network-error' ? <WifiOff aria-hidden="true" /> : <CircleAlert aria-hidden="true" />}
          <span>{st === 'network-error' ? T.network : T.changeError}</span>
        </div>
      )}
      <FieldRow id="pw-current" inputRef={firstRef} label={T.current} autoComplete="current-password" value={vals[0]} onChange={set(0)} error={fieldErr(0)} readOnly={pending} />
      <div className="pw-pair">
        <FieldRow id="pw-next" label={T.next} autoComplete="new-password" value={vals[1]} onChange={set(1)} error={fieldErr(1)} hint={T.hint} readOnly={pending} />
        <FieldRow id="pw-repeat" label={T.repeat} autoComplete="new-password" value={vals[2]} onChange={set(2)} error={fieldErr(2)} readOnly={pending} />
      </div>
      <div className="form-actions">
        <Button type="submit" className="btn" disabled={pending}>
          {pending ? <><Spinner aria-hidden="true" aria-label={undefined} />{T.loading}</> : T.submit}
        </Button>
      </div>
    </form>
  );
}

function Ficha({ f, L }: { f: Fixture; L: Lang }) {
  const T = TXT[L];
  const a = accessLine(f, L);
  const named = Boolean(f.name && f.name.trim());
  const rows: [string, React.ReactNode][] = [
    [T.name, <span className={'v-name' + (named ? '' : ' fallback mono')}>{displayName(f)}</span>],
    [T.email, <span className="v-mail mono">{f.email}</span>],
    [a.label, <span className="v-access">{a.value}{a.sub && <small>{a.sub}</small>}</span>],
  ];
  if (f.company) rows.push([T.company, <span className="v-plain">{f.company}</span>]);
  return (
    <section className="ficha" aria-labelledby="identity-title">
      <h2 id="identity-title" className="sec-title">{T.identity}</h2>
      <dl className="ledger">
        {rows.map(([k, v], i) => (
          <div key={k} className="ficha-row" style={{ '--i': i } as React.CSSProperties}><dt>{k}</dt><dd>{v}</dd></div>
        ))}
      </dl>
    </section>
  );
}

function LoadingPaper({ L }: { L: Lang }) {
  return (
    <div className="paper" aria-busy="true" aria-label={TXT[L].loadingPage}>
      <div className="ficha"><Skeleton style={{ height: 20, width: 140 }} />{[0, 1, 2].map((i) => <div key={i} className="ficha-row" style={{ '--i': i } as React.CSSProperties}><Skeleton style={{ height: 12, width: 56 }} /><Skeleton style={{ height: 18, width: '80%' }} /></div>)}</div>
      <div className="pw"><Skeleton style={{ height: 20, width: 180 }} /><div className="pw-form">{[0, 1, 2].map((i) => <div key={i} className="field"><Skeleton style={{ height: 14, width: 160 }} /><Skeleton style={{ height: 44, borderRadius: 18 }} /></div>)}<Skeleton style={{ height: 44, width: 196, borderRadius: 18 }} /></div></div>
    </div>
  );
}

function App() {
  const m = useMockup();
  const profile = useMotionProfile();
  const [L, setL] = React.useState<Lang>('es');
  const [fx, setFx] = React.useState('admin');
  const [open, setOpen] = React.useState(m.view !== 'cuenta');
  const f = FIXTURES.find((x) => x.id === fx) || FIXTURES[0];
  const T = TXT[L];
  React.useEffect(() => { setOpen(m.view !== 'cuenta'); }, [m.view]);
  React.useEffect(() => { document.documentElement.lang = L; }, [L]);
  React.useEffect(() => { const on = () => document.documentElement.toggleAttribute('data-hidden', document.hidden); document.addEventListener('visibilitychange', on); return () => document.removeEventListener('visibilitychange', on); }, []);
  const loading = m.state === 'loading';
  const pw = (loading ? 'idle' : m.state) as PwState;
  const onTools = m.view === 'herramientas';
  const routes = [
    ...(f.adminAccounts ? [{ href: '/admin/cuentas', label: T.accounts }] : []),
    ...(f.adminRoles ? [{ href: '/admin/roles', label: T.roles }] : []),
    { href: '/cuenta', label: T.myAccount },
  ];
  return (
    <>
      <style>{css}</style>
      <div className="app" lang={L} data-profile={profile.profile} data-reduced={String(profile.reduced)}>
        <header className="masthead">
          <div className="brand"><span className="brandmark" aria-hidden="true"><svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeOpacity=".65" strokeWidth="1.2" /><circle cx="8" cy="8" r="1.8" fill="currentColor" /></svg></span>Pictures<span className="company">Sempertex</span></div>
          <div className="header-tools">
            <label className="language" htmlFor="language"><span>{T.language}</span><select id="language" className="native" aria-label={T.language} value={L} onChange={(e) => setL(e.target.value as Lang)}><option value="es">ES</option><option value="en">EN</option></select></label>
            {loading ? <Skeleton className="trigger-skel" /> : <AccountMenu f={f} L={L} open={open} setOpen={setOpen} current={onTools ? '/' : '/cuenta'} />}
          </div>
        </header>
        <main className="page" key={m.view}>
          <div className="mock-context"><label htmlFor="fixture">{T.mock}</label><select id="fixture" className="native" value={fx} onChange={(e) => setFx(e.target.value)}>{FIXTURES.map((x) => <option key={x.id} value={x.id}>{x.label}</option>)}</select></div>
          {onTools ? (
            <div className="swap">
              <div className="page-head" style={{ marginTop: 16 }}><div><h1>{T.tools}</h1></div><span className="head-rule" aria-hidden="true" /></div>
              <p className="other">{T.otherPage}</p>
            </div>
          ) : (
            <div className="swap">
              <div className="page-head" style={{ marginTop: 16 }}>
                <div><h1>{T.title}</h1><p>{T.active}</p></div>
                <nav className="route-nav" aria-label={L === 'es' ? 'Navegación de cuentas' : 'Account navigation'}>
                  {routes.map((r) => <a key={r.href} href={r.href} aria-current={r.href === '/cuenta' ? 'page' : undefined} onClick={(e) => e.preventDefault()}>{r.label}</a>)}
                </nav>
                <span className="head-rule" aria-hidden="true" />
              </div>
              {loading ? <LoadingPaper L={L} /> : (
                <div className="paper" key={fx}>
                  <Ficha f={f} L={L} />
                  <section className="pw" aria-labelledby="pw-title">
                    <h2 id="pw-title" className="sec-title">{T.changePassword}</h2>
                    <p className="sec-note">{T.pwNote}</p>
                    <PasswordForm L={L} state={pw} />
                  </section>
                </div>
              )}
            </div>
          )}
        </main>
        <footer className="footer"><span>{T.footer}</span><span>{T.rev}</span></footer>
      </div>
    </>
  );
}

mountMockup(App, {
  title: 'cuentas-admin@v2 · A «Ficha dividida» · r1',
  motion: 'expressive',
  views: [
    { id: 'cuenta', label: 'Mi cuenta · menú cerrado' },
    { id: 'menu', label: 'Mi cuenta · menú abierto' },
    { id: 'herramientas', label: 'Otra página · menú abierto' },
  ],
  states: [
    { id: 'idle', label: 'Contraseña en reposo' },
    { id: 'loading', label: 'Cargando cuenta' },
    { id: 'required', label: 'Campos requeridos' },
    { id: 'short', label: 'Nueva muy corta' },
    { id: 'long', label: 'Nueva muy larga' },
    { id: 'mismatch', label: 'No coinciden' },
    { id: 'wrong-current', label: 'Actual incorrecta' },
    { id: 'pending', label: 'Guardando' },
    { id: 'service-error', label: 'Error del servicio' },
    { id: 'network-error', label: 'Error de red' },
    { id: 'success', label: 'Contraseña cambiada' },
  ],
});
