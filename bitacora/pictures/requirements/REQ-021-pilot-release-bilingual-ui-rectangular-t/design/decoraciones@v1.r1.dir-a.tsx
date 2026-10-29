import * as React from 'react';
import { motion } from 'motion/react';
import { ArrowLeft, BookmarkPlus, Box, Camera, Check, ChevronDown, CircleAlert, CloudOff, Eye, HardDrive, LayoutGrid, Loader2, Lock, Pencil, Plus, Redo2, Replace, Search, Settings2, ShoppingCart, Trash2, Undo2, UserRound, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogFooter, AlertDialogCancel } from '@/components/ui/alert-dialog';
import { mountMockup, useMockup } from '@kit/mockup';
import { useMotionProfile } from '@kit/motion';
import bodyFont from '/home/david/dev/pictures-wt/t12/.next/static/media/caa3a2e1cccd8315-s.p.0wgildi0cnwt9.woff2';
import monoFont from '/home/david/dev/pictures-wt/t12/.next/static/media/797e433ab948586e-s.p.0r6juujl39pe6.woff2';

// Explicit fixture: neutral mock names, no requests, credentials, customer data or browser-storage writes.
type Tipo = 'escena' | 'estructura' | 'decoracion' | 'utileria';
type Item = { id: string; name: string; tipo: Tipo; ocasion: string; globos: number; local?: boolean; pending?: boolean };
const MINE: Item[] = [
  { id: 'e1', name: 'Escena de ejemplo', tipo: 'escena', ocasion: 'Cumpleaños', globos: 214 },
  { id: 's1', name: 'Arco de ejemplo', tipo: 'estructura', ocasion: 'Cumpleaños', globos: 96 },
  { id: 's2', name: 'Columna de ejemplo', tipo: 'estructura', ocasion: 'General', globos: 38 },
  { id: 'd1', name: 'Decoración de ejemplo', tipo: 'decoracion', ocasion: 'Boda', globos: 12 },
  { id: 'd2', name: 'Flor de ejemplo', tipo: 'decoracion', ocasion: 'General', globos: 7 },
];
const OTHER: Item[] = [
  { id: 'o1', name: 'Arco de ejemplo · 2', tipo: 'estructura', ocasion: 'Boda', globos: 120 },
  { id: 'o2', name: 'Decoración de ejemplo · 2', tipo: 'decoracion', ocasion: 'General', globos: 9 },
  { id: 'o3', name: 'Escena de ejemplo · 2', tipo: 'escena', ocasion: 'Baby shower', globos: 180 },
];
const LOCAL: Item[] = [
  { id: 'l1', name: 'Guirnalda de ejemplo', tipo: 'decoracion', ocasion: 'General', globos: 24, local: true },
  { id: 'l2', name: 'Escena de ejemplo · navegador', tipo: 'escena', ocasion: 'Cumpleaños', globos: 150, local: true },
];
const GROUPS: { tipo: Tipo; es: string; en: string }[] = [
  { tipo: 'escena', es: 'Escenas', en: 'Scenes' },
  { tipo: 'estructura', es: 'Estructuras', en: 'Structures' },
  { tipo: 'decoracion', es: 'Decoraciones', en: 'Decorations' },
  { tipo: 'utileria', es: 'Utilería', en: 'Party props' },
];
const TIPO_ES: Record<Tipo, string> = { escena: 'Escena', estructura: 'Estructura', decoracion: 'Decoración', utileria: 'Utilería' };
const TIPO_EN: Record<Tipo, string> = { escena: 'Scene', estructura: 'Structure', decoracion: 'Decoration', utileria: 'Party prop' };
const OCASIONES = ['General', 'Cumpleaños', 'Boda', 'Baby shower'];
const TABS = [
  { id: 'estructuras', es: 'Estructuras', en: 'Structures' },
  { id: 'decoraciones', es: 'Decoraciones', en: 'Decorations' },
  { id: 'utileria', es: 'Utilería', en: 'Props' },
  { id: 'ideas', es: 'Ideas', en: 'Ideas' },
  { id: 'mia', es: 'Mi biblioteca', en: 'My library' },
];

const css = `
@font-face{font-family:Geist;src:url(${bodyFont}) format('woff2');font-weight:100 900;font-display:block}
@font-face{font-family:'Geist Mono';src:url(${monoFont}) format('woff2');font-weight:100 900;font-display:block}
:root,[data-theme=light]{--fondo:#faf9fc;--superficie:#ffffff;--superficie-suave:#faf8fd;--superficie-2:#efe9f8;--borde:#e3daef;--borde-suave:#efe9f8;--texto:#1c1425;--texto-suave:#6b6178;--texto-tenue:#766c85;--acento:#6d3fe0;--acento-hover:#5530b8;--sobre-acento:#ffffff;--exito:#1f7a55;--exito-suave:#dcf5e9;--aviso:#8f5f12;--aviso-suave:#fff3d8;--error:#b23a45;--error-suave:#ffeaec;--taller-barra:#ffffff;--taller-panel:#faf9fc;--taller-visor:#ebe7f1;--taller-tarjeta:#ffffff;--taller-boton:#ffffff;--taller-linea:#ebe5f3;--taller-texto:#1c1425;--taller-texto-2:#3a3146;--taller-suave:#675e74;--taller-medio:#5a5168;--taller-encima:#f3eefb;--taller-elegido:#ece3fb;--taller-borde:#ddd3ea;--taller-acento:#5530b8;--taller-primario:#6d3fe0;--taller-sobre-primario:#ffffff;--taller-resalte:#6d3fe0;--taller-peligro:#a8323d;--taller-valido:#1a6a4a;--overlay:rgb(28 20 37 / 0.4);color-scheme:light}
:root.dark,[data-theme=dark]{--fondo:#0b0c10;--superficie:#16181f;--superficie-suave:#1c1e26;--superficie-2:#242733;--borde:#383c48;--borde-suave:#2a2d38;--texto:#f4f5f7;--texto-suave:#9aa1ad;--texto-tenue:#8a91a0;--acento:#9479ff;--acento-hover:#a58dff;--sobre-acento:#120b24;--exito:#78d6a8;--exito-suave:#173b31;--aviso:#f7c46b;--aviso-suave:#3f311c;--error:#ff979f;--error-suave:#43252a;--taller-barra:#121018;--taller-panel:#16131d;--taller-visor:#1a1722;--taller-tarjeta:#1d1926;--taller-boton:#1b1724;--taller-linea:#221e2b;--taller-texto:#f2eff7;--taller-texto-2:#ddd8e6;--taller-suave:#8d85a0;--taller-medio:#a59db5;--taller-encima:#231e2e;--taller-elegido:#2a2140;--taller-borde:#2d2838;--taller-acento:#b9a4ff;--taller-primario:#7a55ec;--taller-sobre-primario:#ffffff;--taller-resalte:#8f6ef5;--taller-peligro:#f08a94;--taller-valido:#5fd3a0;--overlay:rgb(0 0 0 / 0.6);color-scheme:dark}
:root{--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--card-foreground:var(--texto);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);--secondary:var(--superficie-2);--secondary-foreground:var(--texto);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--superficie-2);--accent-foreground:var(--texto);--destructive:var(--error);--destructive-foreground:#ffffff;--input:var(--texto-tenue);--border:var(--borde);--ring:var(--acento);--radius:18px;--font-sans:Geist,system-ui,sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--fondo);color:var(--texto);font:15px/1.5 Geist,system-ui,sans-serif}h1,h2,h3,h4,p{margin:0}details:not([open])>:not(summary){display:none}button,input,select{font:inherit;max-width:100%}button{cursor:pointer}svg{width:18px;height:18px;flex-shrink:0}h1,h2,h3,p,button,summary{overflow-wrap:anywhere}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.app{--cut:150ms;--step:16ms;--sweep:260ms;--ease:cubic-bezier(.2,0,0,1);max-width:1520px;margin:auto;padding:0 40px 32px;min-height:calc(100svh - var(--mockup-bar-h))}.app[data-profile=natural]{--cut:120ms;--step:10ms;--sweep:200ms}.app[data-profile=subtle]{--cut:90ms;--step:5ms;--sweep:140ms}
.masthead{min-height:76px;display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 0;border-bottom:1px solid var(--borde-suave)}.brand{display:flex;align-items:center;gap:12px;font-size:16px;font-weight:600;white-space:nowrap}.brandmark{width:28px;height:28px;display:grid;place-items:center;background:var(--acento);color:var(--sobre-acento);border-radius:8px}.brandmark svg{width:16px;height:16px}.company{font:12px 'Geist Mono',monospace;border-left:1px solid var(--texto);margin-left:12px;padding-left:16px}.header-tools{display:flex;gap:16px;align-items:center;flex-wrap:wrap}.language{display:flex;gap:8px;align-items:center;font-size:13px}.native{min-height:44px;border:1px solid var(--texto-tenue);border-radius:999px;padding:10px 16px;background:var(--superficie);color:var(--texto)}.user-menu{position:relative}.user-menu summary{list-style:none;display:flex;gap:10px;align-items:center;min-height:44px;padding:10px 16px;border:1px solid var(--texto-tenue);border-radius:999px;cursor:pointer;font-size:13px}.user-menu summary::-webkit-details-marker{display:none}.menu-options{position:absolute;right:0;top:calc(100% + 8px);z-index:30;display:grid;gap:12px;width:260px;max-width:calc(100vw - 40px);padding:20px;background:var(--superficie);border:1px solid var(--texto-tenue);border-radius:24px;box-shadow:0 12px 24px var(--overlay)}.menu-options p{font-size:13px;color:var(--texto-suave)}
.heading{display:flex;align-items:center;justify-content:space-between;gap:24px;padding:24px 0}.heading h1{font-size:24px;line-height:1.25;font-weight:600;letter-spacing:-.4px}.route-nav{display:flex;gap:32px;flex-wrap:wrap;min-height:58px;align-items:stretch;margin-bottom:24px;border-block:1px solid var(--borde-suave)}.route-nav a{display:flex;align-items:center;min-height:52px;padding:12px 0;color:var(--texto-suave);text-decoration:none;border-bottom:3px solid transparent}.route-nav a[aria-current=page]{color:var(--texto);border-bottom-color:var(--texto)}
.btn{min-height:44px!important;height:auto!important;line-height:1.35!important;border-radius:999px!important;padding:11px 18px!important;white-space:normal!important;font-weight:600!important;gap:8px!important;transition:transform var(--cut) var(--ease),background-color var(--cut)!important}.btn[data-variant=default]{background:var(--acento)!important;color:var(--sobre-acento)!important}.btn[data-variant=outline]{background:var(--superficie)!important;color:var(--texto)!important;border:1px solid var(--texto-tenue)!important}.btn:active:not(:disabled){transform:translateY(1px)}.btn:disabled{opacity:1!important;color:var(--texto-suave)!important;background:var(--superficie-2)!important;border-color:var(--texto-tenue)!important;cursor:not-allowed}
:where(a,button,input,select,summary,[tabindex]):focus-visible{outline:3px solid var(--acento)!important;outline-offset:3px!important;box-shadow:none!important}
[data-slot=input]{min-height:40px!important;height:auto!important;border:1px solid var(--texto-tenue)!important;border-radius:10px!important;padding:8px 12px!important;background:var(--taller-tarjeta)!important;color:var(--taller-texto)!important;box-shadow:none!important;font-size:14px!important}[data-slot=input]::placeholder{color:var(--taller-suave)!important;opacity:1}
.tbtn{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:40px;padding:10px 14px;border-radius:10px;border:1px solid var(--texto-tenue);background:var(--taller-boton);color:var(--taller-texto);font-size:13px;font-weight:500;line-height:1.3;text-align:left;transition:background-color var(--cut) var(--ease),transform var(--cut) var(--ease)}.tbtn:hover:not(:disabled){background:var(--taller-encima)}.tbtn:active:not(:disabled){transform:translateY(1px)}.tbtn svg{width:16px;height:16px}.tbtn.pri{background:var(--taller-primario);border-color:var(--taller-primario);color:var(--taller-sobre-primario)}.tbtn.pri:hover:not(:disabled){background:var(--acento-hover)}.tbtn.danger{color:var(--error);border-color:var(--error)}.tbtn:disabled{cursor:not-allowed;background:var(--taller-encima);color:var(--taller-medio);border-color:var(--texto-tenue)}.tbtn.ico{padding:0;width:40px;min-width:40px}.tbtn.wide{width:100%;justify-content:flex-start}
.workshop{border:1px solid var(--borde);border-radius:24px;overflow:hidden;background:var(--taller-panel);color:var(--taller-texto)}.save-header{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;padding:12px 20px;background:var(--taller-barra);border-bottom:1px solid var(--taller-linea)}.scene-identity{display:flex;gap:12px;align-items:center;flex-wrap:wrap;font-size:14px}.scene-identity .project-status{font-size:13px;color:var(--taller-medio);display:flex;gap:6px;align-items:center}.scene-identity .project-status svg{width:16px;height:16px;color:var(--taller-valido)}.group-actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.studio-body{display:grid;grid-template-columns:60px 330px minmax(0,1fr) 300px;min-height:560px}.tool-rail{display:flex;flex-direction:column;gap:8px;align-items:center;background:var(--taller-barra);padding:12px 8px;border-right:1px solid var(--taller-linea)}.rail-btn{width:44px;height:44px;display:grid;place-items:center;border-radius:12px;border:0;background:transparent;color:var(--taller-medio)}.rail-btn[aria-pressed=true]{background:var(--taller-elegido);color:var(--taller-acento)}.rail-btn:hover{background:var(--taller-encima)}
.library-panel{min-width:0;border-right:1px solid var(--taller-linea);display:flex;flex-direction:column;background:var(--taller-panel)}.panel-top{padding:16px 16px 12px;display:grid;gap:10px;border-bottom:1px solid var(--taller-linea)}.panel-top h2{font-size:15px;font-weight:600}.searchbox{position:relative}.searchbox svg{position:absolute;left:12px;top:12px;width:16px;height:16px;color:var(--taller-suave)}.searchbox [data-slot=input]{padding-left:36px!important;width:100%}
.seg-tabs{display:flex;flex-wrap:wrap;gap:3px;padding:3px;border-radius:10px;background:var(--taller-encima)}.seg{position:relative;flex:1 1 auto;white-space:nowrap;overflow-wrap:normal;min-height:34px;padding:6px 8px;border:0;border-radius:8px;background:transparent;color:var(--taller-medio);font-size:12px;font-weight:500;z-index:0}.seg[aria-selected=true]{color:var(--taller-texto)}.seg-indicator{position:absolute;inset:0;border-radius:8px;background:var(--taller-tarjeta);box-shadow:0 0 0 1px var(--taller-borde);z-index:-1;transition:transform var(--cut) var(--ease)}
.filters{display:flex;gap:8px;flex-wrap:wrap}.chip-select{min-height:36px;flex:1 1 120px;min-width:0;border:1px solid var(--texto-tenue);border-radius:9px;background:var(--taller-tarjeta);color:var(--taller-texto);padding:4px 8px;font-size:13px}.owner-field{display:grid;gap:4px;font-size:12px;font-weight:600;color:var(--taller-texto-2)}.owner-field select{flex:none;width:100%}
.lib-summary{display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:12px;color:var(--taller-medio);min-height:20px}.lib-summary .sync{display:flex;align-items:center;gap:6px;overflow:hidden}.lib-summary .sync svg{width:14px;height:14px}.sync-text{display:inline-block;animation:tick var(--cut) var(--ease) both}
.lib-scroll{flex:1;overflow:auto;padding:4px 8px 16px}.lib-group{padding-top:12px}.lib-group-title{font-size:11px;font-weight:600;line-height:1;letter-spacing:.08em;text-transform:uppercase;color:var(--taller-medio);padding:0 8px 6px;display:flex;justify-content:space-between}
.lib-row{position:relative;display:grid;grid-template-columns:44px minmax(0,1fr) 20px 40px;align-items:center;gap:8px;padding:4px 4px 4px 6px;border-radius:10px;min-height:52px;overflow:hidden;animation:row-cut var(--cut) var(--ease) backwards;animation-delay:calc(var(--i) * var(--step))}.lib-row[data-selected=true]{background:var(--taller-elegido)}.lib-row:hover{background:var(--taller-encima)}.lib-row[data-selected=true]:hover{background:var(--taller-elegido)}.lib-row[data-fresh=true]::after{content:'';position:absolute;left:0;right:0;bottom:0;height:2px;background:var(--taller-valido);transform-origin:left;animation:sweep var(--sweep) var(--ease) both}
.row-mini{width:44px;height:36px;border-radius:7px;background:var(--taller-visor);display:grid;place-items:center;color:var(--taller-medio)}.row-mini svg{width:40px;height:32px}.row-open{all:unset;cursor:pointer;min-width:0;display:grid;gap:1px;padding:4px 2px;border-radius:6px}.row-name{font-size:14px;font-weight:600;line-height:1.3;color:var(--taller-texto);overflow-wrap:anywhere}.row-meta{font-size:12px;color:var(--taller-medio);line-height:1.3}.row-state{display:grid;place-items:center;color:var(--taller-valido)}.row-state svg{width:16px;height:16px}.row-state[data-kind=local]{color:var(--taller-medio)}.row-state[data-kind=pending]{color:var(--taller-medio)}.row-state[data-kind=locked]{color:var(--taller-medio)}
.local-group{margin-top:12px;border-top:1px dashed var(--taller-borde);padding-top:8px}.local-group summary{list-style:none;display:flex;justify-content:space-between;align-items:center;min-height:40px;padding:4px 8px;border-radius:8px;font-size:13px;font-weight:600;color:var(--taller-texto-2);cursor:pointer}.local-group summary::-webkit-details-marker{display:none}.local-group summary svg{width:16px;height:16px;transition:transform var(--cut) var(--ease)}.local-group[open] summary svg{transform:rotate(180deg)}.local-group .why{font-size:12px;color:var(--taller-medio);padding:0 8px 8px}
.panel-msg{margin:12px 8px;padding:16px;border:1px solid var(--taller-borde);border-radius:14px;background:var(--taller-tarjeta);display:grid;gap:8px;animation:tick var(--cut) var(--ease) both}.panel-msg h3{font-size:14px;font-weight:600;display:flex;gap:8px;align-items:center}.panel-msg h3 svg{width:16px;height:16px}.panel-msg p{font-size:13px;color:var(--taller-medio)}.panel-msg[data-tone=error]{border-color:var(--error)}.panel-msg[data-tone=error] h3 svg{color:var(--error)}.panel-msg[data-tone=warning] h3 svg{color:var(--aviso)}.skel-row{display:grid;grid-template-columns:44px 1fr;gap:8px;align-items:center;padding:6px}[data-slot=skeleton]{background:var(--taller-encima);animation:none;border-radius:8px;height:14px}
.other-tab{padding:12px 8px;display:grid;gap:10px}.other-tab p{font-size:12px;color:var(--taller-medio)}.cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.card{border:1px solid var(--taller-borde);border-radius:12px;background:var(--taller-tarjeta);padding:8px;display:grid;gap:6px;font-size:12px;font-weight:500}.card span{height:56px;border-radius:8px;background:var(--taller-encima)}.card small{font-size:11px;color:var(--taller-medio);font-weight:400}
.studio-canvas{position:relative;min-width:0;background:var(--taller-visor);display:grid;place-items:center;padding:24px}.scene-art{width:100%;max-width:560px;height:300px;display:block}.scene-note{position:absolute;bottom:16px;left:16px;font-size:12px;padding:6px 12px;border-radius:999px;background:var(--taller-tarjeta);color:var(--taller-medio)}.placed{position:absolute;top:16px;left:16px;right:16px;display:flex;gap:8px;align-items:center;padding:8px 12px;border-radius:10px;background:var(--taller-tarjeta);border:1px solid var(--taller-borde);font-size:13px;animation:tick var(--cut) var(--ease) both}.placed svg{width:16px;height:16px;color:var(--taller-valido)}
.inspector{min-width:0;border-left:1px solid var(--taller-linea);background:var(--taller-panel);display:flex;flex-direction:column}.inspector-tabs{display:flex;gap:20px;padding:14px 20px;border-bottom:1px solid var(--taller-linea);font-size:13px;color:var(--taller-medio)}.inspector-tabs span:first-child{color:var(--taller-texto);font-weight:600}
.item-sheet{display:flex;flex-direction:column;min-width:0}.sheet-head{display:flex;justify-content:space-between;align-items:center;gap:8px;padding:10px 12px 10px 20px;border-bottom:1px solid var(--taller-linea)}.sheet-head .lbl{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--taller-medio)}
.item-sheet-body{padding:16px 20px 20px;display:grid;gap:14px;animation:sheet-cut var(--cut) var(--ease) both}.sheet-mini{height:150px;border-radius:12px;background:var(--taller-visor);display:grid;place-items:center;position:relative;overflow:hidden}.sheet-mini svg{width:100%;height:140px}.sheet-mini .scene-note{bottom:8px;left:8px;padding:4px 10px}
.item-sheet h2{font-size:18px;font-weight:600;line-height:1.3;letter-spacing:-.2px}.name-line{display:flex;align-items:start;justify-content:space-between;gap:8px}.facts{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:12px}.etq{border-radius:999px;padding:2px 10px;background:var(--taller-tarjeta);border:1px solid var(--taller-borde);color:var(--taller-texto-2)}.mono{font-family:'Geist Mono',monospace;font-size:12px;color:var(--taller-texto-2)}.dots{display:flex;gap:4px}.dots i{width:14px;height:14px;border-radius:50%;border:1px solid var(--texto-tenue);display:block}
.owner-line{display:flex;gap:8px;align-items:start;font-size:13px;color:var(--taller-texto-2);padding:10px 12px;border-radius:10px;background:var(--taller-tarjeta);border:1px solid var(--taller-borde)}.owner-line svg{width:16px;height:16px;margin-top:2px;color:var(--taller-valido)}.owner-line[data-kind=readonly] svg,.owner-line[data-kind=local] svg{color:var(--taller-medio)}
.sheet-actions{display:grid;gap:8px}.hint{font-size:12px;color:var(--taller-medio)}.status-line{font-size:13px;color:var(--taller-texto-2);display:flex;gap:6px;align-items:start}.status-line svg{width:16px;height:16px;margin-top:2px}.status-line[data-tone=error]{color:var(--error)}.status-line[data-tone=ok] svg{color:var(--taller-valido)}.rename-form{display:grid;gap:8px;transform-origin:left center;animation:sheet-cut var(--cut) var(--ease) both}.rename-form label{font-size:12px;font-weight:600}.inline-error{color:var(--error);font-size:13px}
.pieces{padding:16px 20px;display:grid;gap:4px;border-bottom:1px solid var(--taller-linea)}.pieces h3,.save-block h3{font-size:14px;font-weight:600;margin-bottom:6px}.piece{display:flex;justify-content:space-between;align-items:center;min-height:36px;padding:4px 10px;border-radius:8px;font-size:13px;color:var(--taller-texto-2)}.piece[data-on=true]{background:var(--taller-elegido);color:var(--taller-texto);font-weight:600}.piece small{font-size:12px;color:var(--taller-medio);font-weight:400}
.save-block{padding:16px 20px 20px;display:grid;gap:10px}.save-block .two{display:grid;grid-template-columns:1fr 1fr;gap:6px}.save-link{all:unset;cursor:pointer;min-height:36px;display:flex;align-items:center;font-size:13px;color:var(--taller-acento);text-decoration:underline;text-underline-offset:3px;justify-self:start}.save-form{display:grid;gap:10px;padding:12px;border-radius:12px;background:var(--taller-tarjeta);border:1px solid var(--taller-borde);animation:sheet-cut var(--cut) var(--ease) both}.save-form .what{font-size:12px;color:var(--taller-medio)}.save-form label{display:grid;gap:4px;font-size:12px;font-weight:600;color:var(--taller-texto)}.save-form select{min-height:40px;border:1px solid var(--texto-tenue);border-radius:10px;background:var(--taller-tarjeta);color:var(--taller-texto);padding:6px 10px;font-size:14px;font-weight:400}.dest{font-size:12px;color:var(--taller-medio)}
.existing-controls{padding:10px 20px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;border-bottom:1px solid var(--taller-linea);background:var(--taller-barra)}
.notice-top{padding:12px 20px;border-bottom:1px solid var(--taller-linea);display:flex;gap:10px;align-items:start;font-size:13px;background:var(--taller-tarjeta);animation:tick var(--cut) var(--ease) both}.notice-top svg{width:16px;height:16px;margin-top:2px;color:var(--error)}
.footer{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;padding:24px 0 0;font-size:12px;color:var(--texto-suave)}
[data-slot=alert-dialog-overlay]{background:var(--overlay)!important;backdrop-filter:none!important;z-index:70!important}[data-slot=alert-dialog-content]{z-index:71!important;width:min(460px,calc(100vw - 40px))!important;max-width:460px!important;max-height:calc(100svh - 48px)!important;overflow:auto!important;background:var(--superficie)!important;color:var(--texto)!important;border:1px solid var(--texto-tenue)!important;border-radius:24px!important;padding:24px!important;gap:20px!important;font:15px/1.5 Geist,system-ui!important;box-shadow:0 18px 60px var(--overlay)!important}[data-slot=alert-dialog-title]{font-size:18px!important;font-weight:600!important;line-height:1.35!important}[data-slot=alert-dialog-description]{font-size:14px!important;color:var(--texto-suave)!important}[data-slot=alert-dialog-footer]{display:flex!important;flex-direction:row!important;flex-wrap:wrap!important;justify-content:flex-start!important;gap:10px!important;background:transparent!important;border:0!important;margin:0!important;padding:0!important}.btn.danger-btn[data-variant]{background:var(--error)!important;color:var(--superficie)!important;border-color:var(--error)!important}
.spinner{animation:turn 900ms linear infinite}
@keyframes row-cut{0%{transform:translateX(-8px)}100%{transform:none}}
@keyframes sheet-cut{0%{transform:translateY(6px)}100%{transform:none}}
@keyframes tick{0%{transform:translateY(-4px)}100%{transform:none}}
@keyframes sweep{0%{transform:scaleX(0)}70%{transform:scaleX(1)}100%{transform:scaleX(1)}}
@keyframes turn{to{transform:rotate(360deg)}}
.app[data-hidden=true] *{animation-play-state:paused!important}
[data-reduced-motion] *,[data-reduced-motion] *::before,[data-reduced-motion] *::after{animation:none!important;transition:none!important}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
@media(min-width:640px) and (max-width:1099px){.app{padding-inline:24px}.masthead{flex-wrap:wrap}.studio-body{grid-template-columns:60px 300px minmax(0,1fr)}.inspector{grid-column:2 / 4;border-left:0;border-top:1px solid var(--taller-linea)}.inspector-tabs{display:none}.item-sheet-body{grid-template-columns:200px minmax(0,1fr);align-items:start}.item-sheet-body>.sheet-mini{grid-row:span 4}.tool-rail{grid-row:span 2}}
@media(max-width:639px){.app{padding:0 20px 24px}.masthead{flex-wrap:wrap;gap:16px}.company{margin-left:0;padding-left:12px}.header-tools{width:100%;justify-content:space-between;gap:12px}.heading{align-items:start;flex-direction:column;gap:16px}.route-nav{gap:24px}.save-header{padding:16px 20px}.existing-controls{padding:12px 20px}.studio-body{display:flex;flex-direction:column}.tool-rail{flex-direction:row;justify-content:space-around;border-right:0;border-bottom:1px solid var(--taller-linea);order:0}.studio-canvas{order:1;min-height:240px;padding:20px}.scene-art{height:200px}.library-panel{order:2;border-right:0;border-top:1px solid var(--taller-linea)}.panel-top{padding:16px 20px 12px}.lib-scroll{padding:4px 12px 16px;overflow:visible}.seg{min-height:40px}.inspector{order:3;border-left:0;border-top:1px solid var(--taller-linea)}.inspector-tabs{display:none}.lib-row{min-height:56px}.tbtn{min-height:44px}.tbtn.ico{width:44px;min-width:44px}.lib-row{grid-template-columns:44px minmax(0,1fr) 20px 44px}.save-block .two{grid-template-columns:1fr}[data-slot=alert-dialog-footer]{flex-direction:column!important;align-items:stretch!important}[data-slot=alert-dialog-footer] .btn{width:100%}.footer{display:block}.footer span{display:block;margin-bottom:8px}}
`;

function Mini({ tipo, big = false }: { tipo: Tipo; big?: boolean }) {
  const vb = '0 0 80 60';
  const balloon = (x: number, y: number, r: number, k: number) => <circle key={k} cx={x} cy={y} r={r} fill="var(--acento)" stroke="var(--taller-acento)" strokeWidth=".8" />;
  return (
    <svg viewBox={vb} aria-hidden="true" fill="none" className={big ? 'big-mini' : undefined}>
      <path d="M6 50 40 42 74 50 40 58Z" fill="var(--taller-panel)" stroke="var(--texto-tenue)" strokeWidth=".6" />
      {tipo === 'estructura' && [[22, 44, 5], [21, 35, 5], [24, 26, 5], [31, 19, 5], [40, 16, 5], [49, 19, 5], [56, 26, 5], [59, 35, 5], [58, 44, 5]].map(([x, y, r], i) => balloon(x, y, r, i))}
      {tipo === 'decoracion' && <>{[[40, 26, 7], [32, 32, 6], [48, 32, 6], [36, 40, 5], [44, 40, 5]].map(([x, y, r], i) => balloon(x, y, r, i))}<path d="M40 45v8" stroke="var(--texto-tenue)" strokeWidth="1.2" /></>}
      {tipo === 'escena' && <><path d="M28 46V22a12 12 0 0 1 24 0v24Z" fill="var(--taller-encima)" stroke="var(--texto-tenue)" />{[[24, 44, 4], [23, 36, 4], [25, 28, 4], [30, 20, 4], [38, 15, 4]].map(([x, y, r], i) => balloon(x, y, r, i))}<ellipse cx="56" cy="47" rx="10" ry="3" fill="var(--taller-tarjeta)" stroke="var(--texto-tenue)" /></>}
      {tipo === 'utileria' && <rect x="30" y="30" width="20" height="16" rx="2" fill="var(--taller-encima)" stroke="var(--texto-tenue)" />}
    </svg>
  );
}

function SceneArt() {
  return (
    <svg className="scene-art" viewBox="0 0 620 330" aria-hidden="true" fill="none">
      <path d="M42 225 265 150 578 225 345 310Z" fill="var(--taller-panel)" stroke="var(--texto-tenue)" />
      <path d="M230 196V88a62 62 0 0 1 124 0v108Z" fill="var(--taller-encima)" stroke="var(--texto-tenue)" strokeWidth="2" />
      <g fill="var(--acento)" stroke="var(--taller-acento)" strokeWidth="1.5">{[[198, 214, 22], [187, 180, 21], [192, 147, 23], [205, 116, 20], [215, 87, 23], [241, 65, 22], [270, 51, 23], [304, 51, 21], [334, 66, 22], [351, 93, 18]].map(([x, y, r], i) => <circle key={i} cx={x} cy={y} r={r} />)}</g>
      <ellipse cx="370" cy="225" rx="76" ry="23" fill="var(--superficie)" stroke="var(--texto-tenue)" strokeWidth="2" />
      <path d="M310 226v43m120-43v43" stroke="var(--texto-tenue)" strokeWidth="6" />
    </svg>
  );
}

function App() {
  const m = useMockup();
  const profile = useMotionProfile();
  const [lang, setLang] = React.useState('es');
  const t = (es: string, en: string) => (lang === 'en' ? en : es);
  const tipoName = (k: Tipo) => (lang === 'en' ? TIPO_EN[k] : TIPO_ES[k]);
  const [hidden, setHidden] = React.useState(document.hidden);
  const [menu, setMenu] = React.useState(false);
  const menuRef = React.useRef<HTMLDetailsElement>(null);

  const staffView = m.view === 'staff';
  const saveView = m.view === 'save';
  const [tab, setTab] = React.useState('mia');
  const [query, setQuery] = React.useState('');
  const [ocasion, setOcasion] = React.useState('');
  const [owner, setOwner] = React.useState(staffView ? 'other' : 'mine');
  const [mine, setMine] = React.useState<Item[]>(MINE);
  const [selected, setSelected] = React.useState<string>(saveView ? '' : staffView ? 'o1' : m.state === 'local' ? 'l1' : 's1');
  const [fresh, setFresh] = React.useState(m.state === 'saved' ? 'n1' : '');
  const [localOpen, setLocalOpen] = React.useState(m.state === 'local');
  const [busy, setBusy] = React.useState<'' | 'save' | 'rename' | 'delete'>(m.state === 'saving' ? 'save' : m.state === 'deleting' ? 'delete' : '');
  const [message, setMessage] = React.useState<{ tone: 'ok' | 'error'; text: string } | null>(null);
  const [placed, setPlaced] = React.useState('');
  const [formOpen, setFormOpen] = React.useState<'' | 'pieza' | 'escena'>(saveView ? 'pieza' : '');
  const [formName, setFormName] = React.useState('Guirnalda de ejemplo');
  const [formOcasion, setFormOcasion] = React.useState('General');
  const [editing, setEditing] = React.useState(m.state === 'renaming' || m.state === 'rename-error');
  const [rename, setRename] = React.useState('');
  const [renameBlank, setRenameBlank] = React.useState(false);
  const [switching, setSwitching] = React.useState(m.state === 'switching');
  const deleteTrigger = React.useRef<HTMLElement | null>(null);
  const timer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const listBlocked = ['loading', 'list-error', 'offline', 'session-expired'].includes(m.state) || switching;
  const readOnlyOwner = staffView && owner === 'other';
  const source = readOnlyOwner ? OTHER : mine;
  const filtered = (arr: Item[]) => arr.filter((i) => (!ocasion || i.ocasion === ocasion) && i.name.toLocaleLowerCase().includes(query.toLocaleLowerCase().trim()));
  const rows = m.state === 'empty' && !readOnlyOwner ? mine.filter((i) => i.pending || i.id === 'n1') : filtered(source);
  const localRows = readOnlyOwner ? [] : filtered(LOCAL);
  const all = [...MINE, ...mine, ...OTHER, ...LOCAL, { id: 'n1', name: formName || 'Guirnalda de ejemplo', tipo: 'decoracion' as Tipo, ocasion: formOcasion, globos: 24 }];
  const current = all.find((i) => i.id === selected) || null;
  const currentReadOnly = !!current && OTHER.some((o) => o.id === current.id);
  const currentLocal = !!current?.local;

  React.useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  React.useEffect(() => { const f = () => setHidden(document.hidden); document.addEventListener('visibilitychange', f); return () => document.removeEventListener('visibilitychange', f); }, []);
  React.useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);
  React.useEffect(() => {
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape' && menuRef.current?.open) { setMenu(false); menuRef.current.querySelector('summary')?.focus(); } };
    const out = (e: MouseEvent) => { if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenu(false); };
    document.addEventListener('keydown', key); document.addEventListener('click', out);
    return () => { document.removeEventListener('keydown', key); document.removeEventListener('click', out); };
  }, []);
  // Deterministic fixture seeds per inspector state.
  React.useEffect(() => {
    if (m.state === 'saved' || m.state === 'saving') {
      setMine((list) => list.some((i) => i.id === 'n1') ? list.map((i) => i.id === 'n1' ? { ...i, pending: m.state === 'saving' } : i) : [...list, { id: 'n1', name: 'Guirnalda de ejemplo', tipo: 'decoracion', ocasion: 'General', globos: 24, pending: m.state === 'saving' }]);
      if (m.state === 'saved') setMessage({ tone: 'ok', text: t('Guardado en tu biblioteca: «Guirnalda de ejemplo» (decoración). Está en tu cuenta.', 'Saved to your library: “Guirnalda de ejemplo” (decoration). It is in your account.') });
    }
    if (m.state === 'save-error') setMessage({ tone: 'error', text: t('No se pudo guardar en tu cuenta. El nombre y la ocasión siguen aquí.', 'Could not save to your account. The name and occasion are kept.') });
    if (m.state === 'rejected') setMessage({ tone: 'error', text: t('Tu cuenta no aceptó esta pieza: es demasiado grande o sus datos no son válidos. Tu escena no cambió.', 'Your account did not accept this piece: it is too large or its data is invalid. Your scene is unchanged.') });
    if (m.state === 'rename-error') setMessage({ tone: 'error', text: t('No se pudo cambiar el nombre. Se conserva «Arco de ejemplo».', 'Could not rename. “Arco de ejemplo” is kept.') });
    if (m.state === 'delete-error') setMessage({ tone: 'error', text: t('No se pudo quitar. Sigue en tu biblioteca.', 'Could not remove it. It is still in your library.') });
    if (m.state === 'renaming' || m.state === 'rename-error') setRename('Arco de ejemplo');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const later = (ms: number, fn: () => void) => { if (timer.current) clearTimeout(timer.current); timer.current = setTimeout(fn, ms); };
  const focusRow = (id: string) => requestAnimationFrame(() => document.querySelector<HTMLElement>(`[data-row="${id}"] .row-open`)?.focus());
  const select = (id: string) => { setSelected(id); setEditing(false); setMessage(null); setPlaced(''); };
  const closeSheet = () => { const id = selected; setSelected(''); setEditing(false); focusRow(id); };

  const save = () => {
    if (busy) return;
    const name = formName.trim() || (formOpen === 'escena' ? t('Mi escena', 'My scene') : 'Guirnalda de ejemplo');
    const tipo: Tipo = formOpen === 'escena' ? 'escena' : 'decoracion';
    if (m.state === 'offline') { setMessage({ tone: 'error', text: t('Sin conexión: no se guardó en tu cuenta. Reintenta al volver a conectar.', 'Offline: not saved to your account. Retry when reconnected.') }); return; }
    setBusy('save'); setMessage(null);
    setMine((list) => [...list.filter((i) => i.id !== 'n1'), { id: 'n1', name, tipo, ocasion: formOcasion, globos: tipo === 'escena' ? 214 : 24, pending: true }]);
    later(800, () => {
      setBusy('');
      if (m.state === 'save-error' || m.state === 'rejected') {
        setMine((list) => list.filter((i) => i.id !== 'n1'));
        setMessage({ tone: 'error', text: m.state === 'rejected' ? t('Tu cuenta no aceptó esta pieza: es demasiado grande o sus datos no son válidos. Tu escena no cambió.', 'Your account did not accept this piece: it is too large or its data is invalid. Your scene is unchanged.') : t('No se pudo guardar en tu cuenta. El nombre y la ocasión siguen aquí.', 'Could not save to your account. The name and occasion are kept.') });
        return;
      }
      setMine((list) => list.map((i) => i.id === 'n1' ? { ...i, pending: false } : i));
      setFresh('n1'); setFormOpen(''); setTab('mia');
      setMessage({ tone: 'ok', text: t(`Guardado en tu biblioteca: «${name}» (${tipoName(tipo).toLowerCase()}). Está en tu cuenta.`, `Saved to your library: “${name}” (${tipoName(tipo).toLowerCase()}). It is in your account.`) });
    });
  };
  const place = (it: Item, replace = false) => { setPlaced(replace ? t(`Escena abierta: «${it.name}». Ctrl+Z recupera la anterior.`, `Scene opened: “${it.name}”. Ctrl+Z restores the previous one.`) : t(`Añadida a tu escena: «${it.name}».`, `Added to your scene: “${it.name}”.`)); };
  const confirmRename = (e: React.FormEvent) => {
    e.preventDefault();
    if (!rename.trim()) { setRenameBlank(true); return; }
    setBusy('rename'); setRenameBlank(false);
    later(600, () => {
      setBusy('');
      if (m.state === 'rename-error') { setMessage({ tone: 'error', text: t('No se pudo cambiar el nombre. Se conserva «Arco de ejemplo».', 'Could not rename. “Arco de ejemplo” is kept.') }); return; }
      setMine((list) => list.map((i) => i.id === selected ? { ...i, name: rename.trim() } : i));
      setEditing(false); setMessage({ tone: 'ok', text: t('Nombre guardado en tu cuenta.', 'Name saved to your account.') });
      requestAnimationFrame(() => document.querySelector<HTMLElement>('.rename-trigger')?.focus());
    });
  };
  const openDelete = () => { deleteTrigger.current = document.activeElement as HTMLElement; m.set('scene', 'delete'); };
  const closeDelete = () => { m.set('scene', ''); requestAnimationFrame(() => { const el = deleteTrigger.current; if (el?.isConnected) el.focus(); else document.querySelector<HTMLElement>('.row-open')?.focus(); }); };
  const doDelete = () => {
    const id = selected;
    setBusy('delete');
    later(700, () => {
      setBusy('');
      if (m.state === 'delete-error') { m.set('scene', ''); setMessage({ tone: 'error', text: t('No se pudo quitar. Sigue en tu biblioteca.', 'Could not remove it. It is still in your library.') }); return; }
      const name = current?.name || '';
      if (!currentLocal) setMine((list) => list.filter((i) => i.id !== id));
      m.set('scene', ''); setSelected(''); setMessage(null);
      setPlaced(currentLocal ? t(`Quitada de este navegador: «${name}».`, `Removed from this browser: “${name}”.`) : t(`Quitada de tu biblioteca: «${name}».`, `Removed from your library: “${name}”.`));
      requestAnimationFrame(() => document.querySelector<HTMLElement>('.row-open')?.focus());
    });
  };
  const changeOwner = (v: string) => {
    setOwner(v); setSelected(''); setSwitching(true); setQuery('');
    later(650, () => { setSwitching(false); setSelected(v === 'other' ? 'o1' : 's1'); });
  };

  const syncText = busy === 'save' ? t('Guardando…', 'Saving…') : m.state === 'offline' ? t('Sin conexión', 'Offline') : listBlocked ? t('Cargando…', 'Loading…') : readOnlyOwner ? t('Solo lectura', 'Read only') : t('Al día con tu cuenta', 'Up to date with your account');
  const countText = readOnlyOwner ? t(`${OTHER.length} en Cuenta de ejemplo`, `${OTHER.length} in Example account`) : t(`${mine.filter((i) => !i.pending).length} en tu cuenta`, `${mine.filter((i) => !i.pending).length} in your account`);

  function row(it: Item, i: number) {
    const kind = it.pending ? 'pending' : it.local ? 'local' : readOnlyOwner ? 'locked' : 'saved';
    return (
      <div key={it.id} className="lib-row" data-row={it.id} data-selected={selected === it.id} data-fresh={fresh === it.id && !it.pending} style={{ '--i': i } as React.CSSProperties}>
        <span className="row-mini"><Mini tipo={it.tipo} /></span>
        <button className="row-open" aria-pressed={selected === it.id} onClick={() => select(it.id)}>
          <span className="row-name">{it.name}</span>
          <span className="row-meta">{tipoName(it.tipo)} · {it.ocasion}{it.pending ? ` · ${t('Guardando…', 'Saving…')}` : ''}</span>
        </button>
        <span className="row-state" data-kind={kind} title={kind === 'saved' ? t('Guardado en tu cuenta', 'Saved to your account') : kind === 'local' ? t('Solo en este navegador', 'Only in this browser') : kind === 'locked' ? t('Solo lectura', 'Read only') : t('Guardando…', 'Saving…')}>
          {kind === 'pending' ? <Loader2 className="spinner" aria-hidden="true" /> : kind === 'local' ? <HardDrive aria-hidden="true" /> : kind === 'locked' ? <Lock aria-hidden="true" /> : <Check aria-hidden="true" />}
          <span className="sr-only">{kind === 'saved' ? t('Guardado en tu cuenta', 'Saved to your account') : kind === 'local' ? t('Solo en este navegador', 'Only in this browser') : kind === 'locked' ? t('Solo lectura', 'Read only') : t('Guardando…', 'Saving…')}</span>
        </span>
        <button className="tbtn ico" disabled={it.pending} aria-label={`${t('Añadir a mi escena', 'Add to my scene')}: ${it.name}`} onClick={() => place(it)}><Plus aria-hidden="true" /></button>
      </div>
    );
  }

  function libraryList() {
    if (m.state === 'session-expired') return <section className="panel-msg" data-tone="error" role="alert"><h3><CircleAlert aria-hidden="true" />{t('Tu sesión ha terminado', 'Your session has ended')}</h3><p>{t('Vuelve a iniciar sesión para ver tu biblioteca. No se muestra nada guardado mientras tanto.', 'Sign in again to see your library. Nothing saved is shown meanwhile.')}</p><div><button className="tbtn" onClick={() => m.set('state', 'normal')}>{t('Iniciar sesión', 'Sign in')}</button></div></section>;
    if (m.state === 'loading' || switching) return <div aria-busy="true"><span className="sr-only" role="status">{switching ? t('Cargando la biblioteca de la cuenta elegida…', 'Loading the chosen account’s library…') : t('Cargando tu biblioteca…', 'Loading your library…')}</span>{[0, 1, 2, 3].map((k) => <div className="skel-row" key={k}><Skeleton style={{ height: 36 }} /><div style={{ display: 'grid', gap: 6 }}><Skeleton style={{ width: '70%' }} /><Skeleton style={{ width: '40%', height: 10 }} /></div></div>)}</div>;
    if (m.state === 'list-error' || m.state === 'offline') return <section className="panel-msg" data-tone={m.state === 'offline' ? 'warning' : 'error'} role="alert"><h3>{m.state === 'offline' ? <CloudOff aria-hidden="true" /> : <CircleAlert aria-hidden="true" />}{m.state === 'offline' ? t('Sin conexión', 'Offline') : t('No se pudo cargar tu biblioteca', 'Could not load your library')}</h3><p>{m.state === 'offline' ? t('Lo de tu cuenta se verá al volver a conectar. Lo guardado solo en este navegador sigue abajo.', 'Your account items will show when you reconnect. Items saved only in this browser remain below.') : t('Reintenta para ver lo guardado en tu cuenta.', 'Retry to see what is saved in your account.')}</p><div><button className="tbtn" onClick={() => m.set('state', 'normal')}>{t('Reintentar', 'Retry')}</button></div></section>;
    if (!rows.length) return <section className="panel-msg" role="status"><h3><BookmarkPlus aria-hidden="true" />{query || ocasion ? t('Nada coincide', 'Nothing matches') : t('Tu biblioteca está vacía', 'Your library is empty')}</h3><p>{query || ocasion ? t('Prueba con otro nombre u ocasión.', 'Try another name or occasion.') : t('Elige una pieza y usa «Guardar en mi biblioteca», o «Guardar toda la escena en mi biblioteca». Se guarda en tu cuenta.', 'Select a piece and use “Save to my library”, or “Save the whole scene to my library”. It is saved to your account.')}</p>{(query || ocasion) && <div><button className="tbtn" onClick={() => { setQuery(''); setOcasion(''); }}>{t('Quitar filtros', 'Clear filters')}</button></div>}</section>;
    let n = 0;
    return <>{GROUPS.map((g) => { const items = rows.filter((r) => r.tipo === g.tipo); if (!items.length) return null; return <section className="lib-group" key={g.tipo} aria-label={t(g.es, g.en)}><h4 className="lib-group-title"><span>{t(g.es, g.en)}</span><span className="mono">{items.length}</span></h4>{items.map((it) => row(it, n++))}</section>; })}</>;
  }

  function localGroup() {
    if (readOnlyOwner || m.state === 'session-expired' || !localRows.length) return null;
    return (
      <details className="local-group" open={localOpen} onToggle={(e) => setLocalOpen(e.currentTarget.open)}>
        <summary><span>{t(`Solo en este navegador · ${localRows.length}`, `Only in this browser · ${localRows.length}`)}</span><ChevronDown aria-hidden="true" /></summary>
        <p className="why">{t('Lo guardaste antes de tener cuenta. Sigue en este navegador, no se importa a tu cuenta en el piloto y no lo verás en otros navegadores.', 'You saved it before having an account. It stays in this browser, is not imported to your account in the pilot and will not show in other browsers.')}</p>
        {localRows.map((it, i) => row(it, i))}
      </details>
    );
  }

  function panel() {
    return (
      <section className="library-panel" aria-label={t('Añadir a la escena', 'Add to the scene')}>
        <div className="panel-top">
          <h2>{t('Añadir a la escena', 'Add to the scene')}</h2>
          <div className="searchbox"><Search aria-hidden="true" /><label htmlFor="anadir-buscar" className="sr-only">{t('Buscar en todo', 'Search everything')}</label><Input id="anadir-buscar" type="search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder={t('Buscar: columna, flor, dorado…', 'Search: column, flower, gold…')} /></div>
          <div className="seg-tabs" role="tablist" aria-label={t('Qué añadir', 'What to add')}>
            {TABS.map((tb) => (
              <button key={tb.id} role="tab" id={`tab-${tb.id}`} aria-selected={tab === tb.id} aria-controls="anadir-contenido" className="seg" onClick={() => setTab(tb.id)}>
                {tab === tb.id && <motion.span layoutId="seg-indicator" className="seg-indicator" transition={profile.reduced ? { duration: 0 } : { duration: profile.profile === 'expressive' ? 0.15 : profile.profile === 'natural' ? 0.12 : 0.09, ease: [0.2, 0, 0, 1] }} />}
                {t(tb.es, tb.en)}
              </button>
            ))}
          </div>
          {tab === 'mia' && <>
            {staffView && <label className="owner-field" htmlFor="owner">{t('Biblioteca de', 'Library of')}<select id="owner" className="chip-select" value={owner} onChange={(e) => changeOwner(e.target.value)}><option value="mine">{t('Mi cuenta', 'My account')}</option><option value="other">{t('Cuenta de ejemplo', 'Example account')}</option></select></label>}
            <div className="filters"><select aria-label={t('Ocasión', 'Occasion')} className="chip-select" value={ocasion} onChange={(e) => setOcasion(e.target.value)}><option value="">{t('Ocasión: todas', 'Occasion: all')}</option>{OCASIONES.map((o) => <option key={o} value={o}>{o}</option>)}</select></div>
            <div className="lib-summary"><span className="mono">{listBlocked ? '—' : countText}</span><span className="sync" role="status" aria-live="polite">{busy === 'save' ? <Loader2 className="spinner" aria-hidden="true" /> : m.state === 'offline' ? <CloudOff aria-hidden="true" /> : readOnlyOwner ? <Lock aria-hidden="true" /> : listBlocked ? null : <Check aria-hidden="true" />}<span className="sync-text" key={syncText}>{syncText}</span></span></div>
          </>}
        </div>
        <div className="lib-scroll" id="anadir-contenido" role="tabpanel" aria-labelledby={`tab-${tab}`}>
          {tab === 'mia' ? <>{libraryList()}{(m.state !== 'loading' && !switching) && localGroup()}</> : (
            <div className="other-tab"><p>{t('Mockup · Contenido existente de la pestaña, sin cambios. Lo de tu biblioteca también aparece aquí, marcado «Tu biblioteca».', 'Mockup · Existing tab content, unchanged. Your library items also appear here, marked “Your library”.')}</p><div className="cards">{[0, 1, 2].map((k) => <div className="card" key={k}><span />{k === 0 ? 'Arco de ejemplo' : t('Pieza del taller', 'Workshop piece')}<small>{k === 0 ? t('Tu biblioteca', 'Your library') : t('Del taller', 'From the workshop')}</small></div>)}</div></div>
          )}
        </div>
      </section>
    );
  }

  function sheet() {
    if (!current) return null;
    if (m.state === 'unavailable') return (
      <div className="item-sheet"><div className="sheet-head"><span className="lbl">{t('Ficha', 'Details')}</span><button className="tbtn ico" aria-label={t('Cerrar la ficha', 'Close details')} onClick={closeSheet}><X aria-hidden="true" /></button></div>
        <div className="item-sheet-body"><section className="panel-msg" data-tone="error" role="alert" style={{ margin: 0 }}><h3><CircleAlert aria-hidden="true" />{t('Esta decoración no está disponible', 'This decoration is not available')}</h3><p>{t('Puede que se haya quitado o que no tengas acceso. No se muestra su contenido.', 'It may have been removed or you may not have access. Its content is not shown.')}</p><div><button className="tbtn" onClick={closeSheet}><ArrowLeft aria-hidden="true" />{t('Volver a la biblioteca', 'Back to the library')}</button></div></section></div></div>
    );
    const ownerKind = currentLocal ? 'local' : currentReadOnly ? 'readonly' : 'saved';
    return (
      <div className="item-sheet" aria-label={`${t('Ficha de', 'Details of')} ${current.name}`} role="region">
        <div className="sheet-head"><span className="lbl">{t('Ficha', 'Details')}</span><button className="tbtn ico" aria-label={t('Cerrar la ficha', 'Close details')} onClick={closeSheet}><X aria-hidden="true" /></button></div>
        <div className="item-sheet-body" key={current.id}>
          <div className="sheet-mini" role="img" aria-label={`${t('Vista de ejemplo de', 'Example view of')} ${current.name}`}><Mini tipo={current.tipo} big /><span className="scene-note">{t('Vista 3D · Mockup', '3D view · Mockup')}</span></div>
          {editing && !currentReadOnly ? (
            <form className="rename-form" onSubmit={confirmRename}>
              <label htmlFor="rename">{t('Nombre', 'Name')}</label>
              <Input id="rename" autoFocus value={rename} maxLength={120} aria-invalid={renameBlank} aria-describedby={renameBlank ? 'rename-error' : undefined} disabled={busy === 'rename'} onChange={(e) => { setRename(e.target.value); setRenameBlank(false); }} onKeyDown={(e) => { if (e.key === 'Escape') { setEditing(false); requestAnimationFrame(() => document.querySelector<HTMLElement>('.rename-trigger')?.focus()); } }} />
              {renameBlank && <p id="rename-error" className="inline-error" role="alert">{t('Escribe un nombre.', 'Enter a name.')}</p>}
              <div className="group-actions"><button type="submit" className="tbtn pri" disabled={busy === 'rename'}>{busy === 'rename' ? <><Loader2 className="spinner" aria-hidden="true" />{t('Guardando el nombre…', 'Saving name…')}</> : t('Guardar el nombre', 'Save name')}</button><button type="button" className="tbtn" disabled={busy === 'rename'} onClick={() => { setEditing(false); requestAnimationFrame(() => document.querySelector<HTMLElement>('.rename-trigger')?.focus()); }}>{t('Cancelar', 'Cancel')}</button></div>
            </form>
          ) : (
            <div className="name-line"><h2>{current.name}</h2>{!currentReadOnly && !currentLocal && <button className="tbtn ico rename-trigger" aria-label={`${t('Cambiar el nombre', 'Rename')}: ${current.name}`} onClick={() => { setRename(current.name); setEditing(true); setMessage(null); }}><Pencil aria-hidden="true" /></button>}</div>
          )}
          <div className="facts"><span className="etq">{tipoName(current.tipo)}</span><span className="etq">{current.ocasion}</span><span className="mono">{t(`${current.globos} globos`, `${current.globos} balloons`)}</span><span className="dots" aria-label={t('Colores de ejemplo', 'Example colours')}><i style={{ background: 'var(--acento)' }} /><i style={{ background: 'var(--taller-tarjeta)' }} /><i style={{ background: 'var(--taller-encima)' }} /></span></div>
          <p className="owner-line" data-kind={ownerKind}>{ownerKind === 'saved' ? <Check aria-hidden="true" /> : ownerKind === 'local' ? <HardDrive aria-hidden="true" /> : <Lock aria-hidden="true" />}<span>{ownerKind === 'saved' ? t('Guardado en tu cuenta · lo ves desde cualquier navegador.', 'Saved to your account · available from any browser.') : ownerKind === 'local' ? t('Solo en este navegador · no está en tu cuenta y no se importa.', 'Only in this browser · not in your account and not imported.') : t('Biblioteca de Cuenta de ejemplo · Solo lectura. Solo la cuenta dueña puede cambiarla o quitarla.', 'Example account’s library · Read only. Only the owning account can change or remove it.')}</span></p>
          <div className="sheet-actions">
            <button className="tbtn pri wide" onClick={() => place(current)}><Plus aria-hidden="true" />{t('Añadir a mi escena', 'Add to my scene')}</button>
            <button className="tbtn wide" onClick={() => place(current, true)}><Replace aria-hidden="true" />{t('Abrir en Escena', 'Open in Scene')}</button>
            <p className="hint">{t('«Abrir en Escena» reemplaza la escena que tienes (Ctrl+Z la recupera). «Añadir a mi escena» la suma a la que tienes.', '“Open in Scene” replaces your current scene (Ctrl+Z restores it). “Add to my scene” adds it to the current one.')}</p>
            <button className="tbtn wide" onClick={() => setPlaced(t('Mockup · Ficha completa existente (vista 3D, productos, de dónde viene).', 'Mockup · Existing full details (3D view, products, source).'))}><Eye aria-hidden="true" />{t('Ver ficha completa', 'View full details')}</button>
            {!currentReadOnly && <button className="tbtn wide danger" disabled={!!busy} onClick={openDelete}><Trash2 aria-hidden="true" />{currentLocal ? t('Quitar de este navegador', 'Remove from this browser') : busy === 'delete' ? t('Quitando…', 'Removing…') : t('Quitar de mi biblioteca', 'Remove from my library')}</button>}
          </div>
          {message && <p className="status-line" data-tone={message.tone} role={message.tone === 'error' ? 'alert' : 'status'}>{message.tone === 'error' ? <CircleAlert aria-hidden="true" /> : <Check aria-hidden="true" />}<span>{message.text}</span></p>}
          {message?.tone === 'error' && m.state === 'rename-error' && !editing && <button className="tbtn" onClick={() => { setEditing(true); setRename('Arco de ejemplo'); }}>{t('Reintentar', 'Retry')}</button>}
          {message?.tone === 'error' && m.state === 'delete-error' && <button className="tbtn" onClick={() => { m.set('state', 'normal'); openDelete(); }}>{t('Reintentar', 'Retry')}</button>}
        </div>
      </div>
    );
  }

  function saveInspector() {
    const blocked = m.state === 'session-expired';
    return (
      <>
        <div className="pieces"><h3>{t('Piezas', 'Pieces')}</h3><div className="piece"><span>{t('Arco de ejemplo', 'Arco de ejemplo')}</span><small>{t('Estructura', 'Structure')}</small></div><div className="piece" data-on="true"><span>Guirnalda de ejemplo</span><small>{t('Decoración', 'Decoration')}</small></div><div className="piece"><span>{t('Mesa', 'Table')}</span><small>{t('Mueble', 'Furniture')}</small></div></div>
        <section className="save-block" aria-label={t('Biblioteca', 'Library')}>
          <h3>{t('Biblioteca', 'Library')}</h3>
          <div className="two">
            <button className="tbtn" onClick={() => setPlaced(t('Mockup · «Ver sola» abre la ficha existente.', 'Mockup · “View alone” opens the existing details.'))}><Eye aria-hidden="true" />{t('Ver sola', 'View alone')}</button>
            <button className="tbtn" aria-expanded={formOpen === 'pieza'} data-on={formOpen === 'pieza'} style={formOpen === 'pieza' ? { background: 'var(--taller-elegido)' } : undefined} onClick={() => { setFormOpen(formOpen === 'pieza' ? '' : 'pieza'); setFormName('Guirnalda de ejemplo'); setMessage(null); }}><BookmarkPlus aria-hidden="true" />{t('Guardar en mi biblioteca', 'Save to my library')}</button>
          </div>
          <button className="save-link" aria-expanded={formOpen === 'escena'} onClick={() => { setFormOpen(formOpen === 'escena' ? '' : 'escena'); setFormName(''); setMessage(null); }}>{t('Guardar toda la escena en mi biblioteca', 'Save the whole scene to my library')}</button>
          {formOpen && (
            <form className="save-form" key={formOpen} onSubmit={(e) => { e.preventDefault(); save(); }}>
              <p className="what">{formOpen === 'escena' ? t('La escena entera (3 piezas).', 'The whole scene (3 pieces).') : t('La pieza sola.', 'The piece alone.')}</p>
              <label htmlFor="save-name">{t('Nombre', 'Name')}<Input id="save-name" value={formName} maxLength={120} disabled={busy === 'save' || blocked} placeholder={formOpen === 'escena' ? t('Mi escena', 'My scene') : 'Guirnalda de ejemplo'} onChange={(e) => setFormName(e.target.value)} /></label>
              <label htmlFor="save-ocasion">{t('Ocasión', 'Occasion')}<select id="save-ocasion" value={formOcasion} disabled={busy === 'save' || blocked} onChange={(e) => setFormOcasion(e.target.value)}>{OCASIONES.map((o) => <option key={o}>{o}</option>)}</select></label>
              <p className="dest">{blocked ? t('Tu sesión ha terminado: inicia sesión para guardar en tu cuenta.', 'Your session has ended: sign in to save to your account.') : t('Se guarda en tu cuenta: la verás en «Mi biblioteca» desde cualquier navegador.', 'Saved to your account: you will see it in “My library” from any browser.')}</p>
              <button type="submit" className="tbtn pri" disabled={busy === 'save' || blocked}>{busy === 'save' ? <><Loader2 className="spinner" aria-hidden="true" />{t('Guardando…', 'Saving…')}</> : t('Guardar', 'Save')}</button>
            </form>
          )}
          {message && <p className="status-line" data-tone={message.tone} role={message.tone === 'error' ? 'alert' : 'status'}>{message.tone === 'error' ? <CircleAlert aria-hidden="true" /> : <Check aria-hidden="true" />}<span>{message.text}</span></p>}
          {message?.tone === 'error' && m.state !== 'rejected' && <button className="tbtn" style={{ justifySelf: 'start' }} onClick={() => { m.set('state', 'normal'); setMessage(null); later(10, save); }}>{t('Reintentar', 'Retry')}</button>}
        </section>
      </>
    );
  }

  const deleting = m.scene === 'delete' || (m.state === 'deleting' && busy === 'delete');
  return (
    <>
      <style>{css}</style>
      <div className="app" data-profile={profile.profile} data-hidden={hidden}>
        <header className="masthead">
          <div className="brand"><span className="brandmark" aria-hidden="true"><svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeOpacity=".65" strokeWidth="1.2" /><circle cx="8" cy="8" r="1.8" fill="currentColor" /></svg></span>Pictures<span className="company">Sempertex</span></div>
          <div className="header-tools">
            <label className="language" htmlFor="language">{t('Idioma', 'Language')}<select className="native" id="language" value={lang} onChange={(e) => setLang(e.target.value)}><option value="es">ES</option><option value="en">EN</option></select></label>
            <details className="user-menu" ref={menuRef} open={menu} onToggle={(e) => setMenu(e.currentTarget.open)}>
              <summary onClick={(e) => { e.preventDefault(); setMenu(!menu); }}><UserRound aria-hidden="true" />{t('Mi cuenta', 'My account')}<ChevronDown aria-hidden="true" /></summary>
              <div className="menu-options"><p>{staffView ? t('Cuenta de ejemplo · Empleado interno', 'Example account · Internal employee') : t('Cuenta de ejemplo · Master Designer', 'Example account · Master Designer')}</p>{['Mi cuenta', 'Planes', 'Cerrar sesión'].map((label) => <Button key={label} variant="outline" data-variant="outline" className="btn" onClick={() => { setMenu(false); setPlaced(label === 'Cerrar sesión' ? t('Mockup · Al cerrar sesión se borra de la pantalla todo lo que vino de tu cuenta.', 'Mockup · Signing out clears everything from your account off the screen.') : t('Mockup · Destino definido por cuentas-admin@v1 y planes@v1.', 'Mockup · Destination defined by cuentas-admin@v1 and planes@v1.')); }}>{label === 'Mi cuenta' ? t(label, 'My account') : label === 'Planes' ? t(label, 'Plans') : t(label, 'Sign out')}</Button>)}</div>
            </details>
          </div>
        </header>
        <div className="heading"><h1 tabIndex={-1}>{t('Taller 3D', '3D workshop')}</h1><Button variant="outline" data-variant="outline" className="btn" onClick={() => setPlaced(t('Mockup · Proyectos se define en proyectos@v1.', 'Mockup · Projects is defined in proyectos@v1.'))}><ArrowLeft aria-hidden="true" />{t('Proyectos', 'Projects')}</Button></div>
        <nav className="route-nav" aria-label={t('Navegación del producto', 'Product navigation')}><a href="/3d" aria-current="page" onClick={(e) => e.preventDefault()}>{t('Taller 3D', '3D workshop')}</a><a href="/proyectos" onClick={(e) => { e.preventDefault(); setPlaced(t('Mockup · Proyectos se define en proyectos@v1.', 'Mockup · Projects is defined in proyectos@v1.')); }}>{t('Proyectos', 'Projects')}</a></nav>

        <section className="workshop" aria-label={t('Taller 3D', '3D workshop')}>
          <div className="save-header"><div className="scene-identity"><strong>{t('Taller 3D', '3D workshop')}</strong><span aria-hidden="true">/</span><span>Proyecto de ejemplo</span><span className="project-status"><Check aria-hidden="true" />{t('Guardado en tu cuenta', 'Saved to your account')}</span></div><div className="group-actions"><button className="tbtn ico" disabled aria-label={t('Deshacer', 'Undo')}><Undo2 aria-hidden="true" /></button><button className="tbtn ico" disabled aria-label={t('Rehacer', 'Redo')}><Redo2 aria-hidden="true" /></button><button className="tbtn" onClick={() => setPlaced(t('Mockup · Herramientas existentes del Taller.', 'Mockup · Existing workshop tools.'))}><Camera aria-hidden="true" />{t('Foto realista', 'Realistic photo')}</button><button className="tbtn" onClick={() => setPlaced(t('Mockup · Herramientas existentes del Taller.', 'Mockup · Existing workshop tools.'))}><ShoppingCart aria-hidden="true" />{t('Lista de compra', 'Shopping list')}</button></div></div>
          <div className="studio-body">
            <nav className="tool-rail" aria-label={t('Paneles del Taller', 'Workshop panels')}>{([[Plus, 'Añadir', 'Add', true], [Box, 'Piezas', 'Pieces', false], [LayoutGrid, 'Plantillas', 'Templates', false], [Settings2, 'Sala', 'Room', false]] as const).map(([Icon, es, en, on]) => <button key={es} className="rail-btn" aria-pressed={on} aria-label={t(es, en)} onClick={() => !on && setPlaced(t('Mockup · Herramientas existentes del Taller.', 'Mockup · Existing workshop tools.'))}><Icon aria-hidden="true" /></button>)}</nav>
            {panel()}
            <div className="studio-canvas" role="img" aria-label={t('Escena de ejemplo con globos, panel y mesa.', 'Example scene with balloons, panel and table.')}>
              <SceneArt />
              <span className="scene-note">{t('Vista de escena · Mockup', 'Scene view · Mockup')}</span>
            </div>
            <aside className="inspector" aria-label={t('Escena e IA', 'Scene and AI')}>
              <div className="inspector-tabs"><span>{t('Escena', 'Scene')}</span><span>IA</span></div>
              {placed && <p className="placed" role="status" style={{ position: 'static', margin: '12px 20px 0' }} key={placed}><Check aria-hidden="true" />{placed}</p>}
              {saveView ? saveInspector() : current ? sheet() : <div className="pieces"><h3>{t('Piezas', 'Pieces')}</h3><p className="hint">{t('Elige algo de «Mi biblioteca» para ver su ficha, o una pieza de la escena para guardarla.', 'Pick something from “My library” to see its details, or a scene piece to save it.')}</p></div>}
            </aside>
          </div>
        </section>
        <footer className="footer"><span>{t('Mockup · Datos y operaciones simulados.', 'Mockup · Simulated data and operations.')}</span><span>decoraciones@v1 · r1 · A</span></footer>
      </div>

      <AlertDialog open={deleting} onOpenChange={(v) => { if (!v && busy !== 'delete') closeDelete(); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{currentLocal ? t(`¿Quitar «${current?.name ?? ''}» de este navegador?`, `Remove “${current?.name ?? ''}” from this browser?`) : t(`¿Quitar «${current?.name ?? 'Arco de ejemplo'}» de tu biblioteca?`, `Remove “${current?.name ?? 'Arco de ejemplo'}” from your library?`)}</AlertDialogTitle>
            <AlertDialogDescription>{currentLocal ? t('Solo se borra de este navegador; no está en tu cuenta. Lo que ya pusiste en tus escenas no cambia.', 'It is only deleted from this browser; it is not in your account. What you already placed in your scenes does not change.') : t('Se quita de tu cuenta y deja de verse en todos tus navegadores. Lo que ya pusiste en tus escenas y proyectos no cambia.', 'It is removed from your account and stops showing in all your browsers. What you already placed in your scenes and projects does not change.')}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <Button className="btn danger-btn" data-variant="default" disabled={busy === 'delete'} onClick={doDelete}>{busy === 'delete' ? <><Loader2 className="spinner" aria-hidden="true" />{t('Quitando…', 'Removing…')}</> : currentLocal ? t('Quitar de este navegador', 'Remove from this browser') : t('Quitar de mi biblioteca', 'Remove from my library')}</Button>
            <AlertDialogCancel className="btn" data-variant="outline" disabled={busy === 'delete'} onClick={closeDelete}>{t('Cancelar', 'Cancel')}</AlertDialogCancel>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

mountMockup(App, {
  title: 'Decoraciones guardadas · A · Biblioteca de trabajo',
  motion: 'expressive',
  views: [
    { id: 'library', label: 'Taller · Mi biblioteca' },
    { id: 'save', label: 'Taller · Guardar en mi biblioteca' },
    { id: 'staff', label: 'Taller · Biblioteca de otra cuenta (personal)' },
  ],
  states: [
    { id: 'normal', label: 'Al día' },
    { id: 'loading', label: 'Cargando' },
    { id: 'empty', label: 'Vacía' },
    { id: 'list-error', label: 'Error al cargar' },
    { id: 'offline', label: 'Sin conexión' },
    { id: 'local', label: 'Solo en este navegador' },
    { id: 'saving', label: 'Guardando' },
    { id: 'saved', label: 'Guardado en tu cuenta' },
    { id: 'save-error', label: 'Error al guardar' },
    { id: 'rejected', label: 'Rechazado por la cuenta' },
    { id: 'renaming', label: 'Cambiando el nombre' },
    { id: 'rename-error', label: 'Error al cambiar el nombre' },
    { id: 'deleting', label: 'Quitando' },
    { id: 'delete-error', label: 'Error al quitar' },
    { id: 'switching', label: 'Cambio de cuenta' },
    { id: 'unavailable', label: 'No disponible' },
    { id: 'session-expired', label: 'Sesión terminada' },
  ],
  scenes: [
    { id: '', label: 'Ninguno' },
    { id: 'delete', label: 'Quitar de mi biblioteca' },
  ],
});
