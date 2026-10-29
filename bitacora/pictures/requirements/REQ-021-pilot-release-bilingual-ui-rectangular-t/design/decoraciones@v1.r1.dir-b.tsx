import * as React from 'react';
import { motion } from 'motion/react';
import { ArrowLeft, BookmarkPlus, Box, Camera, Check, ChevronDown, CircleAlert, CloudOff, Eye, LayoutGrid, Library, LoaderCircle, Lock, Monitor, Pencil, Plus, Redo2, Replace, Settings2, ShoppingCart, Trash, Undo2, UserRound } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel } from '@/components/ui/alert-dialog';
import { mountMockup, useMockup } from '@kit/mockup';
import { useMotionProfile } from '@kit/motion';
import bodyFont from '/home/david/dev/pictures-wt/t12/.next/static/media/caa3a2e1cccd8315-s.p.0wgildi0cnwt9.woff2';
import monoFont from '/home/david/dev/pictures-wt/t12/.next/static/media/797e433ab948586e-s.p.0r6juujl39pe6.woff2';

// Explicit mock fixture: no requests, credentials, customer data or browser-storage writes.
type Kind = 'decoracion' | 'conjunto' | 'estructura' | 'escena';
type Item = { id: string; name: string; kind: Kind; occasion: string; where: 'account' | 'browser'; owner: 'mine' | 'other' };
const OWN: Item[] = [
 { id: 'flor', name: 'Flor de ejemplo', kind: 'decoracion', occasion: 'general', where: 'account', owner: 'mine' },
 { id: 'arco', name: 'Arco de ejemplo', kind: 'conjunto', occasion: 'cumpleanos', where: 'account', owner: 'mine' },
 { id: 'escena', name: 'Escena de ejemplo', kind: 'escena', occasion: 'boda', where: 'account', owner: 'mine' },
 { id: 'columna', name: 'Columna de ejemplo', kind: 'estructura', occasion: 'general', where: 'account', owner: 'mine' },
];
const OTHER: Item[] = [
 { id: 'guirnalda-o', name: 'Guirnalda de ejemplo', kind: 'conjunto', occasion: 'general', where: 'account', owner: 'other' },
 { id: 'escena-o', name: 'Escena de ejemplo · 2', kind: 'escena', occasion: 'cumpleanos', where: 'account', owner: 'other' },
 { id: 'flor-o', name: 'Flor de ejemplo · 2', kind: 'decoracion', occasion: 'boda', where: 'account', owner: 'other' },
];
const BROWSER: Item[] = [
 { id: 'mi-escena', name: 'Mi escena', kind: 'escena', occasion: 'general', where: 'browser', owner: 'mine' },
 { id: 'racimo', name: 'Racimo de ejemplo', kind: 'decoracion', occasion: 'cumpleanos', where: 'browser', owner: 'mine' },
];
const SAVED: Item = { id: 'guirnalda', name: 'Guirnalda de ejemplo', kind: 'conjunto', occasion: 'general', where: 'account', owner: 'mine' };
const KIND: Record<Kind, [string, string]> = { decoracion: ['Decoración', 'Decoration'], conjunto: ['Estructura con decoraciones', 'Structure with decorations'], estructura: ['Estructura', 'Structure'], escena: ['Escena', 'Scene'] };
const OCCASION: Record<string, [string, string]> = { general: ['General', 'General'], cumpleanos: ['Cumpleaños', 'Birthday'], boda: ['Boda', 'Wedding'] };

const css = `
@font-face{font-family:Geist;src:url(${bodyFont}) format('woff2');font-weight:100 900;font-display:block}
@font-face{font-family:'Geist Mono';src:url(${monoFont}) format('woff2');font-weight:100 900;font-display:block}
:root,[data-theme=light]{--fondo:#faf9fc;--superficie:#ffffff;--superficie-suave:#faf8fd;--superficie-2:#efe9f8;--borde:#e3daef;--borde-suave:#efe9f8;--texto:#1c1425;--texto-suave:#6b6178;--texto-tenue:#766c85;--acento:#6d3fe0;--acento-hover:#5530b8;--sobre-acento:#ffffff;--exito:#1f7a55;--exito-suave:#dcf5e9;--aviso:#8f5f12;--aviso-suave:#fff3d8;--error:#b23a45;--error-suave:#ffeaec;--taller-barra:#ffffff;--taller-panel:#faf9fc;--taller-visor:#ebe7f1;--taller-tarjeta:#ffffff;--taller-linea:#ebe5f3;--taller-texto:#1c1425;--taller-suave:#675e74;--taller-encima:#f3eefb;--taller-elegido:#ece3fb;--taller-borde:#ddd3ea;--taller-acento:#5530b8;--overlay:rgb(28 20 37 / 0.4);color-scheme:light}
:root.dark,[data-theme=dark]{--fondo:#0b0c10;--superficie:#16181f;--superficie-suave:#1c1e26;--superficie-2:#242733;--borde:#383c48;--borde-suave:#2a2d38;--texto:#f4f5f7;--texto-suave:#9aa1ad;--texto-tenue:#8a91a0;--acento:#9479ff;--acento-hover:#a58dff;--sobre-acento:#120b24;--exito:#78d6a8;--exito-suave:#173b31;--aviso:#f7c46b;--aviso-suave:#3f311c;--error:#ff979f;--error-suave:#43252a;--taller-barra:#121018;--taller-panel:#16131d;--taller-visor:#1a1722;--taller-tarjeta:#1d1926;--taller-linea:#221e2b;--taller-texto:#f2eff7;--taller-suave:#8d85a0;--taller-encima:#231e2e;--taller-elegido:#2a2140;--taller-borde:#2d2838;--taller-acento:#b9a4ff;--overlay:rgb(0 0 0 / 0.6);color-scheme:dark}
:root{--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--card-foreground:var(--texto);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-hover:var(--acento-hover);--primary-foreground:var(--sobre-acento);--secondary:var(--superficie-2);--secondary-foreground:var(--texto);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--superficie-2);--accent-foreground:var(--texto);--destructive:var(--error);--destructive-hover:var(--error);--destructive-foreground:#ffffff;--destructive-soft:var(--error-suave);--success:var(--exito);--success-soft:var(--exito-suave);--warning:var(--aviso);--warning-soft:var(--aviso-suave);--info:var(--acento);--info-soft:var(--fondo);--primary-soft:var(--fondo);--input:var(--texto-tenue);--border:var(--borde);--ring:var(--acento);--radius:18px;--font-sans:Geist,system-ui,sans-serif}
:root[data-theme=dark]{--destructive-foreground:#3a0f13}
*{box-sizing:border-box}body{margin:0;background:var(--fondo);color:var(--texto);font:15px/1.5 Geist,system-ui,sans-serif}h1,h2,h3,p,ul{margin:0}ul{padding:0;list-style:none}details:not([open])>:not(summary){display:none}button,input,select{font:inherit}a,button,summary{-webkit-tap-highlight-color:transparent}a{color:var(--acento);text-underline-offset:4px}button{cursor:pointer}svg{width:18px;height:18px;flex-shrink:0}button,input,select{max-width:100%}h1,h2,h3,p,button,a,summary{overflow-wrap:anywhere}.muted{color:var(--texto-suave)}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.app{--travel:460ms;--quick:150ms;--stagger:40ms;--spring:cubic-bezier(.3,1.5,.55,1);max-width:1520px;margin:auto;padding:0 40px 32px;min-height:calc(100svh - var(--mockup-bar-h))}.app[data-profile=natural]{--travel:300ms;--quick:130ms;--stagger:24ms}.app[data-profile=subtle]{--travel:150ms;--quick:90ms;--stagger:8ms}
.masthead{min-height:76px;display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 0;border-bottom:1px solid var(--borde-suave)}.brand{display:flex;align-items:center;gap:12px;font-size:16px;font-weight:600;white-space:nowrap}.brandmark{width:28px;height:28px;display:grid;place-items:center;background:var(--acento);color:var(--sobre-acento);border-radius:8px}.brandmark svg{width:16px;height:16px}.company{font:12px 'Geist Mono',monospace;border-left:1px solid var(--texto);margin-left:12px;padding-left:16px}.header-tools{display:flex;gap:16px;align-items:center;flex-wrap:wrap}.language{display:flex;gap:8px;align-items:center;font-size:13px}.native{min-height:44px;border:1px solid var(--texto-tenue);border-radius:999px;padding:10px 16px;background:var(--superficie);color:var(--texto)}.user-menu{position:relative}.user-menu summary{list-style:none;display:flex;gap:10px;align-items:center;min-height:44px;padding:10px 16px;border:1px solid var(--texto-tenue);border-radius:999px;cursor:pointer;font-size:13px}.user-menu summary::-webkit-details-marker{display:none}.menu-options{position:absolute;right:0;top:calc(100% + 8px);z-index:30;display:grid;gap:12px;width:260px;max-width:calc(100vw - 40px);padding:20px;background:var(--superficie);border:1px solid var(--texto-tenue);border-radius:24px;box-shadow:0 12px 24px var(--overlay)}
.heading{display:flex;align-items:center;justify-content:space-between;gap:24px;padding:24px 0}.heading h1{font-size:24px;line-height:1.25;font-weight:600;letter-spacing:-.4px}.route-nav{display:flex;gap:32px;flex-wrap:wrap;min-height:58px;align-items:stretch;margin-bottom:24px;border-block:1px solid var(--borde-suave)}.route-nav a{display:flex;align-items:center;min-height:52px;padding:12px 0;color:var(--texto-suave);text-decoration:none;border-bottom:3px solid transparent}.route-nav a[aria-current=page]{color:var(--texto);border-bottom-color:var(--texto)}
.btn{min-height:44px!important;height:auto!important;line-height:1.35!important;border-radius:999px!important;padding:11px 18px!important;white-space:normal!important;font-weight:600!important;gap:8px!important;transition:transform var(--quick,150ms) var(--spring,ease),background-color 150ms!important}.btn[data-variant=default]{background:var(--acento)!important;color:var(--sobre-acento)!important}.btn[data-variant=outline]{background:var(--superficie)!important;color:var(--texto)!important;border:1px solid var(--texto-tenue)!important}.btn[data-variant=destructive]{background:var(--error)!important;color:var(--destructive-foreground)!important}.btn:hover:not(:disabled){transform:translateX(1px) scale(1.02)}.btn:active:not(:disabled){transform:scale(.97)}.btn:disabled{opacity:1!important;color:var(--texto-suave)!important;background:var(--superficie-2)!important;border-color:var(--texto-tenue)!important;cursor:not-allowed}.btn svg{transition:transform var(--quick,150ms) var(--spring,ease)}.btn:hover:not(:disabled) svg{transform:translateX(2px)}:where(a,button,input,select,summary,[tabindex]):focus-visible{outline:3px solid var(--acento)!important;outline-offset:4px!important;box-shadow:none!important}
[data-slot=input]{min-height:46px!important;height:auto!important;border:1px solid var(--texto-tenue)!important;border-radius:18px!important;padding:11px 16px!important;background:var(--superficie)!important;color:var(--texto)!important;box-shadow:none!important}[data-slot=input]::placeholder{color:var(--texto-suave)!important;opacity:1}.field{display:grid;gap:8px;min-width:0}.field label,.field>span{font-size:14px;font-weight:600}.field .native{border-radius:18px;width:100%}.group-actions{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.workshop{border:1px solid var(--borde);border-radius:24px;overflow:hidden;background:var(--taller-panel);color:var(--taller-texto)}.save-header{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;padding:16px 20px;background:var(--taller-barra);border-bottom:1px solid var(--taller-linea)}.scene-identity{display:flex;gap:12px;align-items:center;min-width:0;flex-wrap:wrap}.scene-title{padding:10px 14px;border:1px solid var(--texto-tenue);border-radius:18px;background:var(--taller-tarjeta);display:flex;align-items:center;gap:12px;color:var(--taller-texto);min-height:44px;font-size:14px}.save-status{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--texto-suave);min-height:44px}.save-status .status-icon{width:16px;height:16px;color:var(--exito)}.existing-controls{padding:16px 20px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;border-bottom:1px solid var(--taller-linea)}
.studio-body{display:grid;grid-template-columns:60px minmax(0,1fr) 340px;grid-template-rows:minmax(300px,1fr) auto;min-height:560px}.tool-rail{grid-row:1 / span 2;display:flex;flex-direction:column;gap:12px;align-items:center;background:var(--taller-barra);padding:16px 8px;border-right:1px solid var(--taller-linea)}.tool-rail .btn{padding:11px!important;min-width:44px}.tool-rail .btn[aria-pressed=true]{background:var(--taller-elegido)!important;border-color:var(--texto)!important}
.studio-canvas{grid-column:2;grid-row:1;position:relative;min-width:0;background:var(--taller-visor);display:grid;place-items:center;padding:24px;overflow:hidden}.scene-art{width:100%;max-width:620px;height:300px;display:block}.scene-note{position:absolute;bottom:16px;left:20px;font-size:12px;padding:6px 12px;border-radius:999px;background:var(--superficie);color:var(--texto-suave)}
.place-ghost{position:absolute;right:28px;top:24px;display:flex;align-items:center;gap:10px;padding:8px 14px 8px 8px;border-radius:999px;background:var(--superficie);border:1px solid var(--texto-tenue);box-shadow:0 10px 24px var(--overlay);font-size:13px;color:var(--texto)}.place-ghost .thumb{width:40px;height:32px;border-radius:12px}.place-ring{position:absolute;left:50%;top:50%;width:180px;height:180px;margin:-90px 0 0 -90px;border-radius:50%;border:2px solid var(--acento);pointer-events:none;animation:ring-out calc(var(--travel)*2.2) ease-out 1 both}
.inspector{grid-column:3;grid-row:1 / span 2;border-left:1px solid var(--taller-linea);min-width:0;background:var(--taller-panel)}.inspector-pane{padding:24px 20px;display:flex;flex-direction:column;gap:18px;transform-origin:0 100%}.inspector-pane[data-mode=ficha]{animation:ficha-rise var(--travel) var(--spring) both}.inspector-pane[data-mode=pieza]{animation:pane-return var(--travel) var(--spring) both}.inspector-tabs{display:flex;gap:20px;border-bottom:1px solid var(--taller-linea);padding-bottom:14px;font-size:14px}.inspector-tabs span:first-child{font-weight:600}.inspector h2{font-size:16px;font-weight:600;line-height:1.35}.inspector p{font-size:13px;color:var(--texto-suave)}.pair{display:grid;grid-template-columns:1fr 1fr;gap:10px}.pair .btn{padding:10px 12px!important;font-size:13px!important;justify-content:center}.btn[aria-expanded=true]{background:var(--taller-elegido)!important;border-color:var(--texto)!important}.link-action{min-height:44px;align-self:start;background:none;border:0;padding:10px 0;color:var(--taller-acento);font-size:14px;text-decoration:underline;text-underline-offset:4px;text-align:left}
.save-form{display:grid;gap:16px;padding:18px;border-radius:20px;background:var(--superficie);border:1px solid var(--borde)}.destination{display:flex;gap:10px;align-items:start;font-size:13px;color:var(--texto-suave)}.destination svg{color:var(--texto);margin-top:1px}
.notice{padding:16px 18px;border:1px solid var(--borde);border-radius:18px;background:var(--superficie);display:flex;align-items:start;gap:12px;animation:notice-slide var(--travel) var(--spring) both}.notice>svg{margin-top:2px}.notice-body{display:grid;gap:10px;min-width:0;flex:1}.notice h3{font-size:14px;font-weight:600}.notice p{font-size:13px;color:var(--texto-suave)}.notice[data-tone=error]{border-color:var(--error)}.notice[data-tone=error]>svg{color:var(--error)}.notice[data-tone=success]>svg{color:var(--exito)}.notice[data-tone=lock]>svg,.notice[data-tone=local]>svg{color:var(--texto)}
.ficha-back{align-self:start}.tags{display:flex;gap:8px;flex-wrap:wrap}.tag{display:inline-flex;align-items:center;gap:6px;padding:4px 10px;border-radius:999px;background:var(--superficie-2);color:var(--texto);font-size:12px}.tag svg{width:13px;height:13px}.ficha-thumb{height:170px;border-radius:20px;border:1px solid var(--borde)}.ficha-name{font-size:20px!important;line-height:1.3!important;letter-spacing:-.2px}.ficha-actions{display:grid;gap:10px}.ficha-actions .btn{justify-content:center}.owner-actions{display:flex;gap:10px;flex-wrap:wrap;padding-top:14px;border-top:1px solid var(--taller-linea)}.rename{display:grid;gap:12px;animation:notice-slide var(--travel) var(--spring) both;transform-origin:0 0}
.shelf{grid-column:2;grid-row:2;min-width:0;background:var(--taller-barra);border-top:1px solid var(--taller-linea);position:relative}.shelf-rule{position:absolute;left:0;right:0;top:-1px;height:2px;background:var(--texto-tenue);transform-origin:0 50%;animation:rule-draw calc(var(--travel)*1.4) var(--spring) both}.shelf-head{display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;padding:16px 20px 12px}.shelf-id{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;min-width:0}.shelf-title{font-size:16px;font-weight:600;line-height:1.35}.shelf-meta{font-size:13px;color:var(--texto-suave)}.shelf-controls{display:flex;gap:12px;align-items:center;flex-wrap:wrap}.shelf-scope{display:flex;gap:8px;align-items:center;font-size:13px}.shelf-scope .native{min-height:44px;padding:9px 14px}.shelf-source{display:inline-flex;padding:3px;border-radius:999px;border:1px solid var(--texto-tenue);background:var(--superficie)}.shelf-source button{min-height:38px;border:0;border-radius:999px;padding:8px 14px;background:transparent;color:var(--texto-suave);font-size:13px;font-weight:600;position:relative}.shelf-source button[aria-pressed=true]{color:var(--texto)}.source-pill{position:absolute;inset:0;border-radius:999px;background:var(--superficie-2);z-index:0}.shelf-source button span{position:relative;z-index:1;display:inline-flex;gap:6px;align-items:center}.shelf-source svg{width:14px;height:14px}.shelf-toggle svg:last-child{transition:transform var(--travel) var(--spring)}.shelf-toggle[aria-expanded=false] svg:last-child{transform:rotate(-180deg)}
.shelf-track{display:grid;grid-auto-flow:column;grid-auto-columns:176px;gap:12px;overflow-x:auto;overscroll-behavior-x:contain;scroll-snap-type:x mandatory;padding:4px 20px 14px;scroll-padding-inline:20px}.shelf-track>li{scroll-snap-align:start;min-width:0}.shelf-card{position:relative;width:100%;display:grid;gap:8px;padding:12px;text-align:left;border:1px solid var(--taller-borde);border-radius:18px;background:var(--taller-tarjeta);color:var(--taller-texto);animation:shelf-slide var(--travel) var(--spring) backwards;animation-delay:calc(var(--i)*var(--stagger));transition:transform var(--quick) var(--spring),border-color var(--quick)}.shelf-card:hover{transform:translateY(-3px);border-color:var(--texto-tenue)}.shelf-card[aria-pressed=true]{border-color:var(--texto);background:var(--taller-elegido)}.shelf-card[data-new=true]{animation:card-drop calc(var(--travel)*1.4) var(--spring) both}.shelf-card .thumb{height:92px;border-radius:12px}.card-name{font-size:14px;font-weight:600;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.card-meta{font-size:12px;color:var(--texto-suave);display:flex;gap:6px;align-items:center}.card-meta svg{width:13px;height:13px}.shelf-pick{position:absolute;left:14px;right:14px;bottom:-1px;height:3px;border-radius:3px;background:var(--texto)}.shelf-hint{font-size:12px;color:var(--taller-suave);padding:0 20px 16px}.shelf-body{display:grid;gap:0}.shelf-body[hidden]{display:none}.shelf-message{margin:4px 20px 16px;padding:18px;border-radius:18px;border:1px dashed var(--taller-borde);display:grid;gap:10px;justify-items:start;font-size:13px;color:var(--texto-suave)}.shelf-message strong{font-size:14px;color:var(--texto)}.shelf-message[data-tone=error]{border-style:solid;border-color:var(--error)}.shelf-message[data-tone=error] strong{color:var(--error)}.skeleton-card{display:grid;gap:8px;padding:12px;border:1px solid var(--taller-borde);border-radius:18px;background:var(--taller-tarjeta)}[data-slot=skeleton]{background:var(--superficie-2);animation:none;height:14px;border-radius:10px}.sk-thumb{height:92px!important}.pending-card{display:grid;gap:8px;place-items:center;align-content:center;height:100%;min-height:156px;border:1px dashed var(--texto-tenue);border-radius:18px;font-size:13px;color:var(--texto-suave)}
.thumb{display:block;width:100%;background:#efedf2}
.spinner{animation:spin 1s linear infinite}
@keyframes shelf-slide{0%{transform:translateX(28px)}60%{transform:translateX(-3px)}100%{transform:none}}
@keyframes card-drop{0%{transform:translate(64px,-72px) rotate(-5deg) scale(.92)}60%{transform:translate(-2px,3px) rotate(1deg) scale(1.01)}100%{transform:none}}
@keyframes ficha-rise{0%{transform:translate(-18px,28px) scale(.98)}65%{transform:translate(1px,-2px) scale(1.004)}100%{transform:none}}
@keyframes pane-return{0%{transform:translateX(20px)}65%{transform:translateX(-2px)}100%{transform:none}}
@keyframes notice-slide{0%{transform:translateY(10px)}65%{transform:translateY(-1px)}100%{transform:none}}
@keyframes rule-draw{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes ring-out{0%{transform:scale(.55);opacity:.9}100%{transform:scale(1.5);opacity:0}}
@keyframes spin{to{transform:rotate(360deg)}}
.app[data-hidden=true] *,[data-hidden=true] *::before,[data-hidden=true] *::after{animation-play-state:paused!important}
[data-reduced-motion] *,[data-reduced-motion] *::before,[data-reduced-motion] *::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}
[data-reduced-motion] .place-ring{display:none}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}.place-ring{display:none}}
[data-slot=dialog-overlay],[data-slot=alert-dialog-overlay]{background:var(--overlay)!important;backdrop-filter:none!important;z-index:70!important}[data-slot=dialog-content],[data-slot=alert-dialog-content]{z-index:71!important;width:min(560px,calc(100vw - 40px))!important;max-width:560px!important;max-height:calc(100svh - 48px)!important;overflow:auto!important;background:var(--superficie)!important;color:var(--texto)!important;border:1px solid var(--texto-tenue)!important;border-radius:32px!important;padding:28px!important;gap:24px!important;font:15px/1.5 Geist,system-ui!important;box-shadow:0 18px 60px var(--overlay)!important}[data-slot=dialog-header],[data-slot=alert-dialog-header]{gap:12px!important;place-items:start!important;text-align:left!important}[data-slot=dialog-title],[data-slot=alert-dialog-title]{font-size:20px!important;font-weight:600!important;line-height:1.3!important}[data-slot=dialog-description],[data-slot=alert-dialog-description]{font-size:14px!important;color:var(--texto-suave)!important;text-wrap:pretty}.dialog-actions{display:flex;flex-wrap:wrap;gap:12px}
@media(min-width:640px) and (max-width:1099px){.app{padding-inline:24px}.masthead{flex-wrap:wrap}.studio-body{grid-template-columns:60px minmax(0,1fr);grid-template-rows:minmax(280px,auto) auto auto}.tool-rail{grid-row:1 / span 3}.inspector{grid-column:2;grid-row:3;border-left:0;border-top:1px solid var(--taller-linea)}.inspector-pane{max-width:640px}}
@media(max-width:639px){.app{padding:0 20px 24px}.masthead{flex-wrap:wrap;padding:16px 0;gap:16px}.company{margin-left:0;padding-left:12px}.header-tools{width:100%;justify-content:space-between;gap:12px}.heading{align-items:start;flex-direction:column;gap:16px}.route-nav{gap:24px}.save-header,.existing-controls{padding:16px 20px;align-items:start}.studio-body{display:flex;flex-direction:column;min-height:0}.tool-rail{display:none}.studio-canvas{min-height:240px;padding:20px}.scene-art{height:220px}.place-ghost{right:20px;top:16px}.shelf-head{padding:16px 20px 12px;align-items:start}.shelf-controls{width:100%}.shelf-scope{width:100%;flex-wrap:wrap}.shelf-scope .native{width:100%}.shelf-track{grid-auto-columns:150px}.inspector{border-left:0;border-top:1px solid var(--taller-linea)}.inspector-pane{padding:20px}.save-form{padding:14px}.pair{grid-template-columns:1fr}[data-slot=dialog-content],[data-slot=alert-dialog-content]{padding:24px!important;border-radius:24px!important}.dialog-actions{flex-direction:column;align-items:stretch}.dialog-actions .btn{width:100%}}
`;

function Action({ children, primary = false, danger = false, ...props }: React.ComponentProps<typeof Button> & { primary?: boolean; danger?: boolean }) {
 const v = danger ? 'destructive' : primary ? 'default' : 'outline';
 return <Button variant={v as 'default'} data-variant={v} {...props} className={`btn ${props.className || ''}`}>{children}</Button>;
}

function SceneArt() { return <svg className="scene-art" viewBox="0 0 620 330" aria-hidden="true" fill="none"><path d="M42 225 265 150 578 225 345 310Z" fill="var(--taller-panel)" stroke="var(--texto-tenue)" /><path d="M230 196V88a62 62 0 0 1 124 0v108Z" fill="var(--taller-encima)" stroke="var(--texto-tenue)" strokeWidth="2" /><g fill="var(--acento)" stroke="var(--taller-acento)" strokeWidth="1.5">{[[198, 214, 22], [187, 180, 21], [192, 147, 23], [205, 116, 20], [215, 87, 23], [241, 65, 22], [270, 51, 23], [304, 51, 21], [334, 66, 22], [351, 93, 18]].map(([x, y, r], i) => <circle key={i} cx={x} cy={y} r={r} />)}</g><ellipse cx="370" cy="225" rx="76" ry="23" fill="var(--superficie)" stroke="var(--texto-tenue)" strokeWidth="2" /><path d="M310 226v43m120-43v43" stroke="var(--texto-tenue)" strokeWidth="6" /></svg>; }

// Neutral illustrative thumbnails (the product draws real 3D/SVG thumbnails; these only distinguish item kinds).
function Thumb({ kind, className = '' }: { kind: Kind; className?: string }) {
 const balloons: Record<Kind, number[][]> = {
  decoracion: [[60, 34, 11], [74, 44, 11], [70, 60, 11], [50, 60, 11], [46, 44, 11], [60, 48, 7]],
  conjunto: [[24, 66, 9], [26, 50, 9], [34, 36, 9], [47, 26, 9], [62, 22, 9], [77, 26, 9], [90, 36, 9], [97, 50, 9], [99, 66, 9], [60, 40, 6]],
  estructura: [[60, 70, 10], [60, 54, 10], [60, 38, 10], [60, 22, 10]],
  escena: [[38, 50, 8], [36, 37, 8], [42, 25, 8], [54, 18, 8], [67, 22, 8], [74, 33, 8]],
 };
 return <svg className={`thumb ${className}`} viewBox="0 0 120 90" preserveAspectRatio="xMidYMid meet" aria-hidden="true">
  {kind === 'escena' && <><path d="M8 74 60 60 112 74 66 86Z" fill="#faf9fc" stroke="#766c85" /><ellipse cx="86" cy="70" rx="14" ry="4.5" fill="#fff" stroke="#766c85" /></>}
  {kind === 'estructura' && <path d="M60 80v6" stroke="#766c85" strokeWidth="3" />}
  <g fill="#6d3fe0" stroke="#5530b8" strokeWidth="1">{balloons[kind].map(([x, y, r], i) => <circle key={i} cx={x} cy={y} r={r} fillOpacity={i % 2 ? .78 : 1} />)}</g>
 </svg>;
}

function Notice({ tone = 'normal', title, children, actions }: { tone?: string; title: string; children?: React.ReactNode; actions?: React.ReactNode }) {
 const icon = tone === 'success' ? <Check aria-hidden="true" /> : tone === 'lock' ? <Lock aria-hidden="true" /> : tone === 'local' ? <Monitor aria-hidden="true" /> : tone === 'offline' ? <CloudOff aria-hidden="true" /> : <CircleAlert aria-hidden="true" />;
 return <section className="notice" data-tone={tone} role={tone === 'error' ? 'alert' : 'status'}>{icon}<div className="notice-body"><h3>{title}</h3>{children && <p>{children}</p>}{actions && <div className="group-actions">{actions}</div>}</div></section>;
}

function App() {
 const m = useMockup(); const profile = useMotionProfile();
 const [lang, setLang] = React.useState(document.documentElement.lang === 'en' ? 'en' : 'es'); const t = (es: string, en: string) => lang === 'en' ? en : es;
 const [hidden, setHidden] = React.useState(document.hidden);
 const [menu, setMenu] = React.useState(false); const menuRef = React.useRef<HTMLDetailsElement>(null);
 const staff = m.view === 'personal';
 const S = m.state;
 const [scope, setScope] = React.useState(staff && S !== 'forbidden' ? 'other' : 'mine');
 const [source, setSource] = React.useState<'account' | 'browser'>(S === 'legacy' && m.view === 'ficha' ? 'browser' : 'account');
 const [shelfOpen, setShelfOpen] = React.useState(true);
 const [removed, setRemoved] = React.useState<string[]>(S === 'removed' ? ['columna'] : []);
 const [names, setNames] = React.useState<Record<string, string>>({});
 const [savedItem, setSavedItem] = React.useState<Item | null>(S === 'saved' ? SAVED : null);
 const [saving, setSaving] = React.useState(S === 'saving');
 const [saveError, setSaveError] = React.useState(S === 'save-error');
 const [form, setForm] = React.useState<'pieza' | 'escena' | null>(m.view === 'taller' || ['saving', 'save-error'].includes(S) ? 'pieza' : null);
 const [formName, setFormName] = React.useState(S === 'saving' || S === 'save-error' ? 'Guirnalda de ejemplo' : '');
 const [formOccasion, setFormOccasion] = React.useState('general');
 const [status, setStatus] = React.useState(S === 'saved' ? 'saved' : S === 'removed' ? 'removed' : '');
 const [project, setProject] = React.useState<'saved' | 'saving'>('saved');
 const [placed, setPlaced] = React.useState<string | null>(S === 'placed' ? (staff ? 'Guirnalda de ejemplo' : 'Flor de ejemplo') : null);
 const [placeKey, setPlaceKey] = React.useState(0);
 const [loading, setLoading] = React.useState(S === 'loading' || S === 'account-switch');
 const [loadError, setLoadError] = React.useState(S === 'error');
 const [renaming, setRenaming] = React.useState(S === 'renaming');
 const [renameValue, setRenameValue] = React.useState('');
 const [renameInvalid, setRenameInvalid] = React.useState(false);
 const session = S === 'session'; const forbidden = S === 'forbidden'; const empty = S === 'empty';
 const trigger = React.useRef<HTMLElement | null>(null); const timers = React.useRef<ReturnType<typeof setTimeout>[]>([]);
 const later = (fn: () => void, ms: number) => { timers.current.push(setTimeout(fn, ms)); };
 React.useEffect(() => () => timers.current.forEach(clearTimeout), []);
 React.useEffect(() => { document.documentElement.lang = lang; }, [lang]);
 React.useEffect(() => { const c = () => setHidden(document.hidden); document.addEventListener('visibilitychange', c); return () => document.removeEventListener('visibilitychange', c); }, []);
 React.useEffect(() => { const fn = (e: KeyboardEvent) => { if (e.key === 'Escape' && menuRef.current?.open) { setMenu(false); menuRef.current.querySelector('summary')?.focus(); } }; const out = (e: MouseEvent) => { if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenu(false); }; document.addEventListener('keydown', fn); document.addEventListener('click', out); return () => { document.removeEventListener('keydown', fn); document.removeEventListener('click', out); }; }, []);

 const accountItems = (staff ? (scope === 'other' ? OTHER : OWN.slice(0, 2)) : OWN).filter(i => !removed.includes(i.id));
 const visible: Item[] = session || forbidden || empty ? [] : source === 'browser' ? BROWSER : [...(savedItem ? [savedItem] : []), ...accountItems];
 const firstPick = m.view === 'ficha' || staff || S === 'renaming' || S === 'placed' ? visible[0]?.id ?? null : null;
 const [picked, setPicked] = React.useState<string | null>(firstPick);
 const current = visible.find(i => i.id === picked) || null;
 const mode: 'ficha' | 'pieza' = current && !loading && !loadError ? 'ficha' : 'pieza';
 const readOnly = current?.owner === 'other';
 const local = current?.where === 'browser';
 const nameOf = (i: Item) => names[i.id] ?? i.name;
 const kindLabel = (k: Kind) => t(...KIND[k]);
 const occLabel = (o: string) => t(...(OCCASION[o] || OCCASION.general));
 const existing = () => setStatus('tool');

 const pick = (id: string) => { setPicked(id); setRenaming(false); setStatus(''); setPlaced(null); requestAnimationFrame(() => document.querySelector<HTMLElement>('.ficha-name')?.focus()); };
 const back = () => { const from = picked; setPicked(null); setRenaming(false); requestAnimationFrame(() => document.querySelector<HTMLElement>(`[data-card="${from}"]`)?.focus()); };
 const openForm = (which: 'pieza' | 'escena') => { setForm(form === which ? null : which); setFormName(which === 'pieza' ? 'Guirnalda de ejemplo' : ''); setSaveError(false); setStatus(''); };
 const submitSave = (e?: React.FormEvent) => {
  e?.preventDefault(); if (saving || session) return;
  const name = formName.trim() || (form === 'escena' ? t('Mi escena', 'My scene') : 'Guirnalda de ejemplo');
  setSaving(true); setSaveError(false); setStatus('');
  later(() => { setSaving(false); setForm(null); setSource('account'); setSavedItem({ ...SAVED, id: `nuevo-${Date.now()}`, name, kind: form === 'escena' ? 'escena' : 'conjunto', occasion: formOccasion }); setStatus('saved'); setShelfOpen(true); }, 900);
 };
 const place = (replace: boolean, force = false) => {
  if (!current) return;
  if (replace && project === 'saving' && !force) { trigger.current = document.activeElement as HTMLElement; m.set('scene', 'abrir'); return; }
  setPlaced(nameOf(current)); setPlaceKey(k => k + 1); setStatus(replace ? 'opened' : 'placed'); setProject('saving');
  later(() => setProject('saved'), 1200);
 };
 const startRename = () => { if (!current) return; setRenaming(true); setRenameValue(nameOf(current)); setRenameInvalid(false); requestAnimationFrame(() => document.getElementById('rename-input')?.focus()); };
 const submitRename = (e: React.FormEvent) => { e.preventDefault(); if (!current) return; const v = renameValue.trim(); if (!v) { setRenameInvalid(true); return; } setNames(n => ({ ...n, [current.id]: v })); setRenaming(false); setStatus('renamed'); requestAnimationFrame(() => document.querySelector<HTMLElement>('.ficha-name')?.focus()); };
 const askRemove = () => { trigger.current = document.activeElement as HTMLElement; m.set('scene', 'quitar'); };
 const closeDialog = () => { m.set('scene', ''); requestAnimationFrame(() => { const el = trigger.current; if (el?.isConnected) el.focus(); else document.querySelector<HTMLElement>('.shelf-title')?.focus(); }); };
 const confirmRemove = () => { if (current) { setRemoved(r => [...r, current.id]); setStatus('removed'); setPicked(null); } m.set('scene', ''); requestAnimationFrame(() => document.querySelector<HTMLElement>('.shelf-title')?.focus()); };
 const retryLoad = () => { setLoadError(false); setLoading(true); later(() => setLoading(false), 900); };
 const removedName = S === 'removed' && !current ? 'Columna de ejemplo' : '';

 const shelfTitle = staff && scope === 'other' ? t('Biblioteca de Cuenta de ejemplo', 'Library of Example account') : t('Mi biblioteca', 'My library');
 const shelfMeta = loading || loadError || session || forbidden ? '' : source === 'browser' ? t(`${BROWSER.length} en este navegador`, `${BROWSER.length} in this browser`) : staff && scope === 'other' ? t(`${visible.length} guardadas · Solo lectura`, `${visible.length} saved · Read only`) : t(`${visible.length} guardadas · en tu cuenta`, `${visible.length} saved · in your account`);
 const statusText = status === 'saved' && savedItem ? t(`Guardado en tu biblioteca: «${savedItem.name}» (${kindLabel(savedItem.kind).toLowerCase()}). Ya está en tu cuenta.`, `Saved to your library: “${savedItem.name}” (${kindLabel(savedItem.kind).toLowerCase()}). It is in your account now.`)
  : status === 'removed' ? t(`Quitada de tu biblioteca: «${removedName || 'Columna de ejemplo'}».`, `Removed from your library: “${removedName || 'Columna de ejemplo'}”.`)
  : status === 'placed' && placed ? t(`Añadida a tu escena: «${placed}».`, `Added to your scene: “${placed}”.`)
  : status === 'opened' && placed ? t(`Abierta en Escena: «${placed}». Ctrl+Z recupera la escena anterior.`, `Opened in Scene: “${placed}”. Ctrl+Z restores the previous scene.`)
  : status === 'renamed' ? t('Nombre cambiado en tu cuenta.', 'Name changed in your account.')
  : status === 'tool' ? t('Mockup · Herramientas existentes del Taller.', 'Mockup · Existing workshop tools.') : '';
 const placedShown = placed && (S === 'placed' || status === 'placed' || status === 'opened');

 function Shelf() {
  return <section className="shelf" aria-labelledby="shelf-title" id="shelf">
   <span className="shelf-rule" aria-hidden="true" />
   <div className="shelf-head">
    <div className="shelf-id"><h2 className="shelf-title" id="shelf-title" tabIndex={-1}>{shelfTitle}</h2>{shelfMeta && <span className="shelf-meta">{shelfMeta}</span>}</div>
    <div className="shelf-controls">
     {staff && !session && <label className="shelf-scope" htmlFor="scope">{t('Biblioteca de', 'Library of')}<select id="scope" className="native" value={forbidden ? 'mine' : scope} onChange={e => { setScope(e.target.value); setPicked(e.target.value === 'other' ? OTHER[0].id : null); }}><option value="mine">{t('Mi cuenta', 'My account')}</option><option value="other">Cuenta de ejemplo</option></select></label>}
     {S === 'legacy' && !staff && <div className="shelf-source" role="group" aria-label={t('Dónde está guardado', 'Where it is saved')}>
      {(['account', 'browser'] as const).map(s => <button key={s} type="button" aria-pressed={source === s} onClick={() => { setSource(s); setPicked(null); }}>{source === s && <motion.span layoutId="source-pill" className="source-pill" transition={profile.reduced ? { duration: 0 } : profile.spring} />}<span>{s === 'account' ? <><UserRound aria-hidden="true" />{t('En tu cuenta', 'In your account')}</> : <><Monitor aria-hidden="true" />{t(`En este navegador · ${BROWSER.length}`, `In this browser · ${BROWSER.length}`)}</>}</span></button>)}
     </div>}
     <Action className="shelf-toggle" aria-expanded={shelfOpen} aria-controls="shelf-body" onClick={() => setShelfOpen(o => !o)}><Library aria-hidden="true" />{shelfOpen ? t('Ocultar estante', 'Hide shelf') : t('Mostrar estante', 'Show shelf')}<ChevronDown aria-hidden="true" /></Action>
    </div>
   </div>
   <div className="shelf-body" id="shelf-body" hidden={!shelfOpen}>
    {S === 'account-switch' && <div className="shelf-message" role="status"><strong>{t('Cargando la biblioteca de la cuenta con la que entraste…', 'Loading the library of the account you signed in with…')}</strong>{t('Lo de la cuenta anterior ya no se muestra.', 'Items from the previous account are no longer shown.')}</div>}
    {session ? <div className="shelf-message" data-tone="error" role="alert"><strong>{t('Tu sesión terminó', 'Your session ended')}</strong>{t('Inicia sesión otra vez para ver tu biblioteca y guardar en ella. Tu escena sigue aquí.', 'Sign in again to see your library and save to it. Your scene stays here.')}<Action onClick={existing}><UserRound aria-hidden="true" />{t('Iniciar sesión', 'Sign in')}</Action></div>
     : forbidden ? <div className="shelf-message" data-tone="error" role="alert"><strong>{t('No tienes acceso a esa biblioteca', 'You do not have access to that library')}</strong>{t('Solo el personal autorizado puede abrir la biblioteca de otra cuenta. Tu biblioteca sigue disponible.', 'Only authorised staff can open another account’s library. Your library is still available.')}<Action onClick={() => m.set('state', 'normal')}><ArrowLeft aria-hidden="true" />{t('Volver a mi biblioteca', 'Back to my library')}</Action></div>
     : loadError ? <div className="shelf-message" data-tone="error" role="alert"><strong>{t('No se pudo cargar tu biblioteca', 'Your library could not be loaded')}</strong>{t('Lo que guardaste sigue en tu cuenta. Revisa la conexión y vuelve a intentarlo.', 'What you saved is still in your account. Check the connection and try again.')}<Action onClick={retryLoad}><Check aria-hidden="true" />{t('Reintentar', 'Retry')}</Action></div>
     : loading ? <ul className="shelf-track" aria-busy="true" aria-label={t('Cargando tu biblioteca', 'Loading your library')}>{[0, 1, 2, 3].map(i => <li key={i}><div className="skeleton-card"><Skeleton className="sk-thumb" /><Skeleton style={{ width: '80%' }} /><Skeleton style={{ width: '55%' }} /></div></li>)}</ul>
     : visible.length === 0 && !saving ? <div className="shelf-message" role="status"><strong>{staff && scope === 'other' ? t('Esta cuenta todavía no guarda nada en su biblioteca.', 'This account has not saved anything to its library yet.') : t('Todavía no guardas nada en tu biblioteca.', 'You have not saved anything to your library yet.')}</strong>{!(staff && scope === 'other') && t('Elige una pieza y pulsa «Guardar en mi biblioteca», o guarda toda la escena.', 'Pick a piece and press “Save to my library”, or save the whole scene.')}</div>
     : <ul className="shelf-track" aria-label={shelfTitle}>
      {saving && <li><div className="pending-card" role="status"><LoaderCircle className="spinner" aria-hidden="true" />{t('Guardando…', 'Saving…')}</div></li>}
      {visible.map((item, i) => <li key={item.id}><button type="button" className="shelf-card" data-card={item.id} data-new={savedItem?.id === item.id && status === 'saved'} aria-pressed={picked === item.id} style={{ '--i': i } as React.CSSProperties} onClick={() => pick(item.id)}>
       <Thumb kind={item.kind} />
       <span className="card-name">{nameOf(item)}</span>
       <span className="card-meta">{item.owner === 'other' ? <Lock aria-hidden="true" /> : item.where === 'browser' ? <Monitor aria-hidden="true" /> : null}{kindLabel(item.kind)} · {occLabel(item.occasion)}</span>
       {picked === item.id && <motion.span layoutId="shelf-pick" className="shelf-pick" aria-hidden="true" transition={profile.reduced ? { duration: 0 } : profile.spring} />}
      </button></li>)}
     </ul>}
    {!loading && !loadError && !session && !forbidden && visible.length > 0 && <p className="shelf-hint">{t('Arrastra una tarjeta al visor: se marca en verde dónde puede ir. O tócala y elige dónde.', 'Drag a card onto the viewer: green marks where it can go. Or tap it and choose where.')}</p>}
   </div>
  </section>;
 }

 function Pieza() {
  return <div className="inspector-pane" data-mode="pieza" key="pieza">
   <div className="inspector-tabs"><span>{t('Escena', 'Scene')}</span><span>IA</span></div>
   <div><h2>Guirnalda de ejemplo</h2><p>{t('Pieza elegida · Estructura con decoraciones', 'Selected piece · Structure with decorations')}</p></div>
   <div className="pair"><Action onClick={existing}><Eye aria-hidden="true" />{t('Ver con sus decoraciones', 'View with its decorations')}</Action><Action aria-expanded={form === 'pieza'} aria-controls="save-form" onClick={() => openForm('pieza')} disabled={session}><BookmarkPlus aria-hidden="true" />{t('Guardar en mi biblioteca', 'Save to my library')}</Action></div>
   <button type="button" className="link-action" aria-expanded={form === 'escena'} aria-controls="save-form" onClick={() => openForm('escena')} disabled={session}>{t('Guardar toda la escena en mi biblioteca', 'Save the whole scene to my library')}</button>
   {form && !session && <form className="save-form" id="save-form" onSubmit={submitSave} aria-busy={saving}>
    <p>{form === 'escena' ? t('La escena entera (3 piezas).', 'The whole scene (3 pieces).') : t('La estructura con todo lo que cuelga de ella y lo pegado a sus globos.', 'The structure with everything hanging from it and attached to its balloons.')}</p>
    <div className="field"><label htmlFor="save-name">{t('Nombre', 'Name')}</label><Input id="save-name" value={formName} maxLength={120} placeholder={form === 'escena' ? t('Mi escena', 'My scene') : 'Guirnalda de ejemplo'} onChange={e => setFormName(e.target.value)} disabled={saving} /></div>
    <div className="field"><label htmlFor="save-occasion">{t('Ocasión', 'Occasion')}</label><select id="save-occasion" className="native" value={formOccasion} onChange={e => setFormOccasion(e.target.value)} disabled={saving}>{Object.keys(OCCASION).map(o => <option key={o} value={o}>{occLabel(o)}</option>)}</select></div>
    <p className="destination"><UserRound aria-hidden="true" />{t('Se guarda en tu cuenta: la verás desde cualquier navegador en el que entres.', 'It is saved to your account: you will see it from any browser you sign in on.')}</p>
    {saveError && <Notice tone="error" title={t('No se pudo guardar en tu cuenta', 'It could not be saved to your account')}>{t('Tu escena no cambió y el nombre sigue aquí. Revisa la conexión y vuelve a intentarlo.', 'Your scene did not change and the name is still here. Check the connection and try again.')}</Notice>}
    <Action primary type="submit" disabled={saving}>{saving ? <><LoaderCircle className="spinner" aria-hidden="true" />{t('Guardando…', 'Saving…')}</> : saveError ? t('Reintentar', 'Retry') : t('Guardar', 'Save')}</Action>
   </form>}
   {session && <Notice tone="error" title={t('Inicia sesión para guardar', 'Sign in to save')}>{t('Guardar en tu biblioteca necesita tu cuenta.', 'Saving to your library needs your account.')}</Notice>}
  </div>;
 }

 function Ficha() {
  if (!current) return null;
  return <div className="inspector-pane" data-mode="ficha" key={`ficha-${current.id}`}>
   <Action className="ficha-back" onClick={back}><ArrowLeft aria-hidden="true" />{t('Volver al inspector', 'Back to inspector')}</Action>
   <div className="tags"><span className="tag">{kindLabel(current.kind)}</span><span className="tag">{occLabel(current.occasion)}</span>{readOnly ? <span className="tag"><Lock aria-hidden="true" />{t('Solo lectura', 'Read only')}</span> : local ? <span className="tag"><Monitor aria-hidden="true" />{t('En este navegador', 'In this browser')}</span> : <span className="tag"><UserRound aria-hidden="true" />{t('Tuya · en tu cuenta', 'Yours · in your account')}</span>}</div>
   <Thumb kind={current.kind} className="ficha-thumb" />
   {renaming && !readOnly && !local ? <form className="rename" onSubmit={submitRename}>
    <div className="field"><label htmlFor="rename-input">{t('Nombre', 'Name')}</label><Input id="rename-input" value={renameValue} maxLength={120} aria-invalid={renameInvalid} aria-describedby={renameInvalid ? 'rename-error' : undefined} onChange={e => { setRenameValue(e.target.value); setRenameInvalid(false); }} onKeyDown={e => { if (e.key === 'Escape') { setRenaming(false); requestAnimationFrame(() => document.querySelector<HTMLElement>('.rename-trigger')?.focus()); } }} />{renameInvalid && <span id="rename-error" className="muted" style={{ color: 'var(--error)', fontSize: 13 }}>{t('Escribe un nombre.', 'Type a name.')}</span>}</div>
    <div className="group-actions"><Action primary type="submit"><Check aria-hidden="true" />{t('Guardar nombre', 'Save name')}</Action><Action type="button" onClick={() => setRenaming(false)}>{t('Cancelar', 'Cancel')}</Action></div>
   </form> : <h2 className="ficha-name" tabIndex={-1}>{nameOf(current)}</h2>}
   {readOnly && <Notice tone="lock" title={t('De Cuenta de ejemplo · Solo lectura', 'From Example account · Read only')}>{t('Puedes verla y ponerla en tu escena. Solo la cuenta dueña puede cambiarla o quitarla.', 'You can view it and place it in your scene. Only the owning account can change or remove it.')}</Notice>}
   {local && <Notice tone="local" title={t('Está solo en este navegador', 'It is only in this browser')}>{t('Se guardó antes de las cuentas. En el piloto no se importa a tu cuenta: no la verás en otros navegadores.', 'It was saved before accounts. In the pilot it is not imported into your account: you will not see it in other browsers.')}</Notice>}
   <div className="ficha-actions"><Action primary onClick={() => place(true)}><Replace aria-hidden="true" />{t('Abrir en Escena', 'Open in Scene')}</Action><Action onClick={() => place(false)}><Plus aria-hidden="true" />{t('Añadir a mi escena', 'Add to my scene')}</Action></div>
   <p>{t('«Abrir en Escena» reemplaza la escena que tienes (Ctrl+Z la recupera). «Añadir a mi escena» la suma a la que tienes, con su armado: la estructura y sus decoraciones juntas.', '“Open in Scene” replaces your current scene (Ctrl+Z restores it). “Add to my scene” adds it to the one you have, assembled: the structure and its decorations together.')}</p>
   {!readOnly && !local && <div className="owner-actions"><Action className="rename-trigger" onClick={startRename} aria-expanded={renaming}><Pencil aria-hidden="true" />{t('Renombrar', 'Rename')}</Action><Action onClick={askRemove}><Trash aria-hidden="true" />{t('Quitar de mi biblioteca', 'Remove from my library')}</Action></div>}
  </div>;
 }

 return <><style>{css}</style><main id="app-main" className="app" data-profile={profile.profile} data-hidden={hidden}>
  <header className="masthead"><div className="brand"><span className="brandmark" aria-hidden="true"><svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeOpacity=".65" strokeWidth="1.2" /><circle cx="8" cy="8" r="1.8" fill="currentColor" /></svg></span>Pictures<span className="company">Sempertex</span></div><div className="header-tools"><label className="language" htmlFor="language">{t('Idioma', 'Language')}<select className="native" id="language" value={lang} onChange={e => setLang(e.target.value)}><option value="es">ES</option><option value="en">EN</option></select></label><details className="user-menu" ref={menuRef} open={menu} onToggle={e => setMenu(e.currentTarget.open)}><summary onClick={e => { e.preventDefault(); setMenu(!menu); }}><UserRound aria-hidden="true" />{t('Mi cuenta', 'My account')}<ChevronDown aria-hidden="true" /></summary><div className="menu-options"><p className="muted">{staff ? t('Cuenta de ejemplo · Empleado', 'Example account · Employee') : t('Cuenta de ejemplo · Master Designer', 'Example account · Master Designer')}</p>{[['Mi cuenta', 'My account'], ['Planes', 'Plans'], ['Cerrar sesión', 'Sign out']].map(([es, en]) => <Action key={es} onClick={() => { setMenu(false); existing(); }}>{t(es, en)}</Action>)}</div></details></div></header>
  <div className="heading"><h1 tabIndex={-1}>{t('Taller 3D', '3D workshop')}</h1><Action onClick={existing}><ArrowLeft aria-hidden="true" />{t('Proyectos', 'Projects')}</Action></div>
  <nav className="route-nav" aria-label={t('Navegación del producto', 'Product navigation')}><a href="/3d" aria-current="page" onClick={e => e.preventDefault()}>{t('Taller 3D', '3D workshop')}</a><a href="/proyectos" onClick={e => { e.preventDefault(); existing(); }}>{t('Proyectos', 'Projects')}</a></nav>
  <section className="workshop" aria-label={t('Taller 3D', '3D workshop')}>
   <div className="save-header"><div className="scene-identity"><span className="scene-title"><Box aria-hidden="true" />Proyecto de ejemplo</span><span className="save-status" role="status">{project === 'saving' ? <><LoaderCircle className="status-icon spinner" aria-hidden="true" />{t('Guardando…', 'Saving…')}</> : <><Check className="status-icon" aria-hidden="true" />{t('Guardado en tu cuenta', 'Saved to your account')}</>}</span></div><span className="muted" style={{ fontSize: 13 }}>{t('Proyecto · proyectos@v1', 'Project · proyectos@v1')}</span></div>
   <div className="existing-controls"><div className="group-actions"><Action disabled aria-label={t('Deshacer', 'Undo')}><Undo2 aria-hidden="true" /></Action><Action disabled aria-label={t('Rehacer', 'Redo')}><Redo2 aria-hidden="true" /></Action></div><div className="group-actions"><Action onClick={existing}><Camera aria-hidden="true" />{t('Foto realista', 'Realistic photo')}</Action><Action onClick={existing}><ShoppingCart aria-hidden="true" />{t('Lista de compra', 'Shopping list')}</Action></div></div>
   {statusText && <div style={{ padding: '16px 20px 0' }}><Notice tone={status === 'tool' ? 'normal' : 'success'} title={statusText} /></div>}
   <div className="studio-body" data-layout="shelf">
    <nav className="tool-rail" aria-label={t('Paneles del Taller', 'Workshop panels')}>{([[Plus, 'Añadir', 'Add'], [Box, 'Piezas', 'Pieces'], [LayoutGrid, 'Plantillas', 'Templates'], [Settings2, 'Sala', 'Room']] as const).map(([Icon, es, en]) => <Action key={es} aria-label={t(es, en)} onClick={existing}><Icon aria-hidden="true" /></Action>)}<Action aria-label={t('Mi biblioteca', 'My library')} aria-pressed={shelfOpen} aria-controls="shelf-body" onClick={() => { setShelfOpen(o => !o); requestAnimationFrame(() => document.querySelector<HTMLElement>('.shelf-title')?.focus()); }}><Library aria-hidden="true" /></Action></nav>
    <div className="studio-canvas" role="img" aria-label={t('Escena de ejemplo con globos, panel y mesa.', 'Example scene with balloons, panel and table.')}>
     <SceneArt />
     {placedShown && <React.Fragment key={placeKey}><span className="place-ring" aria-hidden="true" /><motion.div className="place-ghost" initial={profile.reduced ? false : { y: 160, x: -120, scale: .6, rotate: -8 }} animate={{ y: 0, x: 0, scale: 1, rotate: 0 }} transition={profile.reduced ? { duration: 0 } : profile.spring}><Thumb kind={current?.kind || 'decoracion'} /><span>{placed} · {t('en tu escena', 'in your scene')}</span></motion.div></React.Fragment>}
     <span className="scene-note">{t('Vista de escena · Mockup', 'Scene view · Mockup')}</span>
    </div>
    {Shelf()}
    <aside className="inspector" aria-label={mode === 'ficha' ? t('Ficha', 'Item card') : t('Escena e IA', 'Scene and AI')}>{mode === 'ficha' ? Ficha() : Pieza()}</aside>
   </div>
  </section>
 </main>
 <Dialog open={m.scene === 'abrir'} onOpenChange={v => { if (!v) closeDialog(); }}><DialogContent showCloseButton={false}>
  <DialogHeader><DialogTitle>{t('Antes de abrir una escena nueva', 'Before opening a new scene')}</DialogTitle><DialogDescription>{t('«Abrir en Escena» reemplaza la escena que tienes. Sus últimos cambios todavía se están guardando en tu cuenta.', '“Open in Scene” replaces your current scene. Its latest changes are still being saved to your account.')}</DialogDescription></DialogHeader>
  <div className="dialog-actions"><Action primary onClick={() => { closeDialog(); setProject('saved'); place(true, true); }}>{t('Guardar y continuar', 'Save and continue')}</Action><Action onClick={closeDialog}>{t('Cancelar', 'Cancel')}</Action></div>
 </DialogContent></Dialog>
 <AlertDialog open={m.scene === 'quitar'} onOpenChange={v => { if (!v) closeDialog(); }}><AlertDialogContent>
  <AlertDialogHeader><AlertDialogTitle>{t('Quitar de mi biblioteca', 'Remove from my library')}</AlertDialogTitle><AlertDialogDescription>{t(`«${current ? nameOf(current) : 'Flor de ejemplo'}» se quita de tu cuenta y deja de verse en tus otros navegadores. Lo que ya pusiste en tus escenas se queda como está.`, `“${current ? nameOf(current) : 'Flor de ejemplo'}” is removed from your account and no longer appears in your other browsers. What you already placed in your scenes stays as it is.`)}</AlertDialogDescription></AlertDialogHeader>
  <div className="dialog-actions"><AlertDialogAction className="btn" data-variant="destructive" variant="destructive" onClick={confirmRemove}><Trash aria-hidden="true" />{t('Quitar de mi biblioteca', 'Remove from my library')}</AlertDialogAction><AlertDialogCancel className="btn" data-variant="outline">{t('Cancelar', 'Cancel')}</AlertDialogCancel></div>
 </AlertDialogContent></AlertDialog>
 </>;
}

mountMockup(App, {
 title: 'Decoraciones · B · Estante bajo el visor', motion: 'expressive',
 views: [{ id: 'taller', label: 'Taller · Guardar en mi biblioteca' }, { id: 'ficha', label: 'Taller · Ficha propia' }, { id: 'personal', label: 'Personal · Otra cuenta (solo lectura)' }],
 states: [{ id: 'normal', label: 'Con decoraciones' }, { id: 'loading', label: 'Cargando' }, { id: 'empty', label: 'Vacía' }, { id: 'error', label: 'Error al cargar' }, { id: 'saving', label: 'Guardando' }, { id: 'saved', label: 'Guardado' }, { id: 'save-error', label: 'Error al guardar' }, { id: 'placed', label: 'Añadida a la escena' }, { id: 'renaming', label: 'Renombrando' }, { id: 'removed', label: 'Quitada' }, { id: 'legacy', label: 'Biblioteca del navegador' }, { id: 'account-switch', label: 'Cambio de cuenta' }, { id: 'forbidden', label: 'Sin acceso' }, { id: 'session', label: 'Sesión terminada' }],
 scenes: [{ id: '', label: 'Ninguno' }, { id: 'quitar', label: 'Quitar de mi biblioteca' }, { id: 'abrir', label: 'Antes de abrir en Escena' }],
});
