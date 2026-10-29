import * as React from 'react';
import { motion } from 'motion/react';
import { ArrowLeft, BookmarkPlus, Box, Camera, Check, ChevronDown, ChevronUp, CircleAlert, CloudOff, Eye, GripVertical, LayoutGrid, Loader2, Lock, Pencil, Plus, Redo2, Replace, Search, Settings2, ShoppingCart, Trash2, Undo2, UserRound, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { mountMockup, useMockup } from '@kit/mockup';
import { useMotionProfile } from '@kit/motion';
import bodyFont from '/home/david/dev/pictures-wt/t12/.next/static/media/caa3a2e1cccd8315-s.p.0wgildi0cnwt9.woff2';
import monoFont from '/home/david/dev/pictures-wt/t12/.next/static/media/797e433ab948586e-s.p.0r6juujl39pe6.woff2';

// Explicit fixture: no requests, credentials, customer data or browser-storage writes. Names are neutral mock data.
type Kind = 'conjunto' | 'escena' | 'decoracion';
type Item = { id: string; name: string; kind: Kind; occasion: string; balloons: number; pieces: number; art: 'arch' | 'scene' | 'garland' };
const KIND: Record<Kind, [string, string]> = { conjunto: ['Estructura con decoraciones', 'Structure with decorations'], escena: ['Escena', 'Scene'], decoracion: ['Decoración', 'Decoration'] };
const OCCASIONS: Array<[string, string, string]> = [['general', 'General', 'General'], ['cumpleanos', 'Cumpleaños', 'Birthday'], ['cumpleanos-infantil', 'Cumpleaños infantil', "Kids' birthday"], ['baby-shower', 'Baby shower', 'Baby shower'], ['boda', 'Boda', 'Wedding']];
const OWN: Item[] = [
  { id: 'own-1', name: 'Arco de ejemplo', kind: 'conjunto', occasion: 'cumpleanos', balloons: 84, pieces: 3, art: 'arch' },
  { id: 'own-2', name: 'Escena de ejemplo', kind: 'escena', occasion: 'general', balloons: 212, pieces: 9, art: 'scene' },
  { id: 'own-3', name: 'Decoración de ejemplo', kind: 'decoracion', occasion: 'baby-shower', balloons: 18, pieces: 1, art: 'garland' },
];
const LOCAL: Item[] = [
  { id: 'local-1', name: 'Guardado local de ejemplo', kind: 'escena', occasion: 'boda', balloons: 160, pieces: 7, art: 'scene' },
  { id: 'local-2', name: 'Pieza local de ejemplo', kind: 'decoracion', occasion: 'general', balloons: 12, pieces: 1, art: 'garland' },
];
const FOREIGN: Item[] = [
  { id: 'foreign-1', name: 'Arco de ejemplo · otra cuenta', kind: 'conjunto', occasion: 'boda', balloons: 96, pieces: 4, art: 'arch' },
  { id: 'foreign-2', name: 'Escena de ejemplo · otra cuenta', kind: 'escena', occasion: 'cumpleanos-infantil', balloons: 188, pieces: 8, art: 'scene' },
];

const css = `
@font-face{font-family:Geist;src:url(${bodyFont}) format('woff2');font-weight:100 900;font-display:block}
@font-face{font-family:'Geist Mono';src:url(${monoFont}) format('woff2');font-weight:100 900;font-display:block}
:root,[data-theme=light]{--fondo:#faf9fc;--superficie:#ffffff;--superficie-suave:#faf8fd;--superficie-2:#efe9f8;--borde:#e3daef;--borde-suave:#efe9f8;--texto:#1c1425;--texto-suave:#6b6178;--texto-tenue:#766c85;--acento:#6d3fe0;--acento-hover:#5530b8;--sobre-acento:#ffffff;--exito:#1f7a55;--exito-suave:#dcf5e9;--aviso:#8f5f12;--aviso-suave:#fff3d8;--error:#b23a45;--error-suave:#ffeaec;--taller-barra:#ffffff;--taller-panel:#faf9fc;--taller-visor:#ebe7f1;--taller-tarjeta:#ffffff;--taller-linea:#ebe5f3;--taller-texto:#1c1425;--taller-suave:#675e74;--taller-encima:#f3eefb;--taller-elegido:#ece3fb;--taller-borde:#ddd3ea;--taller-acento:#5530b8;--overlay:rgb(28 20 37 / 0.4);color-scheme:light}
:root.dark,[data-theme=dark]{--fondo:#0b0c10;--superficie:#16181f;--superficie-suave:#1c1e26;--superficie-2:#242733;--borde:#383c48;--borde-suave:#2a2d38;--texto:#f4f5f7;--texto-suave:#9aa1ad;--texto-tenue:#8a91a0;--acento:#9479ff;--acento-hover:#a58dff;--sobre-acento:#120b24;--exito:#78d6a8;--exito-suave:#173b31;--aviso:#f7c46b;--aviso-suave:#3f311c;--error:#ff979f;--error-suave:#43252a;--taller-barra:#121018;--taller-panel:#16131d;--taller-visor:#1a1722;--taller-tarjeta:#1d1926;--taller-linea:#221e2b;--taller-texto:#f2eff7;--taller-suave:#8d85a0;--taller-encima:#231e2e;--taller-elegido:#2a2140;--taller-borde:#2d2838;--taller-acento:#b9a4ff;--overlay:rgb(0 0 0 / 0.6);color-scheme:dark}
:root{--background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--card-foreground:var(--texto);--popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);--secondary:var(--superficie-2);--secondary-foreground:var(--texto);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);--accent:var(--superficie-2);--accent-foreground:var(--texto);--destructive:var(--error);--input:var(--texto-tenue);--border:var(--borde);--ring:var(--acento);--radius:18px;--font-sans:Geist,system-ui,sans-serif}
*{box-sizing:border-box}body{margin:0;background:var(--fondo);color:var(--texto);font:15px/1.5 Geist,system-ui,sans-serif}h1,h2,h3,p{margin:0}details:not([open])>:not(summary){display:none}button,input,select{font:inherit}a,button,summary{-webkit-tap-highlight-color:transparent}button{cursor:pointer}svg{width:18px;height:18px;flex-shrink:0}button,input,select{max-width:100%}h1,h2,h3,p,button,summary{overflow-wrap:anywhere}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.app{--settle:480ms;--quick:160ms;--offset:45ms;--ease:cubic-bezier(.3,1.45,.6,1);max-width:1520px;margin:auto;padding:0 40px 32px;min-height:calc(100svh - var(--mockup-bar-h))}.app[data-profile=natural]{--settle:300ms;--quick:130ms;--offset:25ms}.app[data-profile=subtle]{--settle:150ms;--quick:90ms;--offset:10ms}
.masthead{min-height:76px;display:flex;align-items:center;justify-content:space-between;gap:20px;padding:16px 0;border-bottom:1px solid var(--borde-suave)}.brand{display:flex;align-items:center;gap:12px;font-size:16px;font-weight:600;white-space:nowrap}.brandmark{width:28px;height:28px;display:grid;place-items:center;background:var(--acento);color:var(--sobre-acento);border-radius:8px}.brandmark svg{width:16px;height:16px}.company{font:12px 'Geist Mono',monospace;border-left:1px solid var(--texto);margin-left:12px;padding-left:16px}.header-tools{display:flex;gap:16px;align-items:center;flex-wrap:wrap}.language{display:flex;gap:8px;align-items:center;font-size:13px}.native{min-height:44px;border:1px solid var(--texto-tenue);border-radius:999px;padding:10px 16px;background:var(--superficie);color:var(--texto)}.user-menu{position:relative}.user-menu summary{list-style:none;display:flex;gap:10px;align-items:center;min-height:44px;padding:10px 16px;border:1px solid var(--texto-tenue);border-radius:999px;cursor:pointer;font-size:13px}.user-menu summary::-webkit-details-marker{display:none}.menu-options{position:absolute;right:0;top:calc(100% + 8px);z-index:30;display:grid;gap:12px;width:260px;max-width:calc(100vw - 40px);padding:20px;background:var(--superficie);border:1px solid var(--texto-tenue);border-radius:24px;box-shadow:0 12px 24px var(--overlay)}.menu-options p{font-size:13px;color:var(--texto-suave)}
.heading{display:flex;align-items:center;justify-content:space-between;gap:24px;padding:24px 0}.heading h1{font-size:24px;line-height:1.25;font-weight:600;letter-spacing:-.4px}.route-nav{display:flex;gap:32px;flex-wrap:wrap;min-height:58px;align-items:stretch;margin-bottom:24px;border-block:1px solid var(--borde-suave)}.route-nav a{display:flex;align-items:center;min-height:52px;padding:12px 0;color:var(--texto-suave);text-decoration:none;border-bottom:3px solid transparent}.route-nav a[aria-current=page]{color:var(--texto);border-bottom-color:var(--texto)}
.btn{min-height:44px!important;height:auto!important;line-height:1.35!important;border-radius:999px!important;padding:11px 18px!important;white-space:normal!important;font-weight:600!important;gap:8px!important;transition:transform var(--quick,160ms) var(--ease,ease),background-color 160ms!important}.btn[data-variant=default]{background:var(--acento)!important;color:var(--sobre-acento)!important}.btn[data-variant=outline]{background:var(--superficie)!important;color:var(--texto)!important;border:1px solid var(--texto-tenue)!important}.btn[data-variant=ghost]{background:transparent!important;color:var(--texto)!important;border:1px solid transparent!important}.btn[data-tone=danger]{color:var(--error)!important}.btn:hover:not(:disabled){transform:scale(1.025)}.btn:active:not(:disabled){transform:scale(.96) translateY(1px)}.btn:disabled{opacity:1!important;color:var(--texto-suave)!important;background:var(--superficie-2)!important;border-color:var(--texto-tenue)!important;cursor:not-allowed}.btn svg{transition:transform var(--quick,160ms) var(--ease,ease)}.btn:hover:not(:disabled) svg{transform:translateY(-2px)}.btn.icon{padding:11px!important;min-width:44px}:where(a,button,input,select,summary,[tabindex]):focus-visible{outline:3px solid var(--acento)!important;outline-offset:4px!important;box-shadow:none!important}
[data-slot=input]{min-height:44px!important;height:auto!important;border:1px solid var(--texto-tenue)!important;border-radius:14px!important;padding:10px 14px!important;background:var(--superficie)!important;color:var(--texto)!important;box-shadow:none!important;font-size:15px!important}[data-slot=input]::placeholder{color:var(--texto-suave)!important;opacity:1}.field{display:grid;gap:6px;min-width:0}.field label,.field-label{font-size:13px;font-weight:600}.field-error{color:var(--error);font-size:13px}.group-actions{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.notice{padding:20px 24px;border:1px solid var(--borde);border-radius:20px;background:var(--superficie);display:flex;align-items:start;gap:14px;animation:notice-settle var(--settle) var(--ease) both}.notice-body{min-width:0;display:grid;gap:8px;flex:1}.notice h2{font-size:16px;font-weight:600;line-height:1.4}.notice p{font-size:14px;color:var(--texto-suave);max-width:70ch}.notice[data-tone=error]{border-color:var(--error)}.notice[data-tone=error]>svg{color:var(--error)}.notice[data-tone=warning]>svg{color:var(--aviso)}.notice[data-tone=success]>svg{color:var(--exito)}.notice>svg{margin-top:3px}.page-notice{margin-bottom:20px}
.workshop{border:1px solid var(--borde);border-radius:24px;overflow:hidden;background:var(--taller-panel);color:var(--taller-texto)}.save-header{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;padding:14px 20px;background:var(--taller-barra);border-bottom:1px solid var(--taller-linea)}.scene-identity{display:flex;gap:12px;align-items:center;min-width:0;flex-wrap:wrap;font-size:14px}.scene-identity .project{font-weight:600}.save-status{display:flex;align-items:center;gap:8px;font-size:13px;color:var(--texto-suave);min-height:44px}.save-status svg{width:16px;height:16px;color:var(--exito)}.existing-controls{padding:12px 20px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;border-bottom:1px solid var(--taller-linea)}
.studio-body{display:grid;grid-template-columns:60px minmax(300px,340px) minmax(0,1fr) 280px;min-height:560px}.tool-rail{display:flex;flex-direction:column;gap:12px;align-items:center;background:var(--taller-barra);padding:16px 8px;border-right:1px solid var(--taller-linea)}.tool-rail .btn[aria-pressed=true]{background:var(--taller-elegido)!important;color:var(--taller-acento)!important;border-color:var(--taller-acento)!important}
.lib-panel{min-width:0;display:flex;flex-direction:column;gap:14px;padding:18px 16px;border-right:1px solid var(--taller-linea);background:var(--taller-panel)}.lib-panel>h2{font-size:15px;font-weight:600}.panel-search{position:relative}.panel-search>svg{position:absolute;left:14px;top:13px;color:var(--texto-suave)}.panel-search [data-slot=input]{padding-left:42px!important}
.lib-seg{display:flex;flex-wrap:wrap;gap:4px;padding:4px;border:1px solid var(--taller-borde);border-radius:14px;background:var(--taller-barra)}.lib-seg button{min-height:44px;flex:1 1 auto;border:0;border-radius:10px;background:transparent;color:var(--taller-suave);font-size:13px;font-weight:500;padding:6px 10px;transition:transform var(--quick) var(--ease),background-color var(--quick)}.lib-seg button[aria-pressed=true]{background:var(--taller-elegido);color:var(--taller-texto);font-weight:600}.lib-seg button:active{transform:scale(.95)}.seg-count{display:inline-grid;place-items:center;min-width:22px;height:22px;margin-left:6px;padding:0 6px;border-radius:999px;background:var(--superficie);color:var(--taller-texto);font-size:12px;font-weight:600;border:1px solid var(--taller-borde)}.seg-count[data-bump=true]{animation:count-bump var(--settle) var(--ease) both}
.owner-pick{display:grid;gap:6px}.owner-pick .native{border-radius:14px;width:100%}.filters{display:flex;gap:8px}.filters .native{flex:1;border-radius:14px;min-width:0;font-size:14px;padding:10px 12px}
.group-label{display:flex;justify-content:space-between;align-items:center;gap:10px;font-size:13px;color:var(--taller-suave)}.group-label strong{color:var(--taller-texto);font-weight:600}
.lib-list{display:flex;flex-direction:column;gap:8px;margin:0;padding:0;list-style:none}.lib-row{border:1px solid var(--taller-borde);border-radius:16px;background:var(--taller-tarjeta);transform-origin:50% 0;animation:row-settle var(--settle) var(--ease) backwards;animation-delay:calc(var(--i,0)*var(--offset))}.lib-row[data-open=true]{border-color:var(--taller-acento)}.lib-row[data-new=true]{animation:row-drop var(--settle) var(--ease) both}.lib-row[draggable=true]{cursor:grab}
.row-toggle{width:100%;display:grid;grid-template-columns:52px minmax(0,1fr) auto;gap:12px;align-items:center;text-align:left;padding:8px 10px;min-height:64px;border:0;background:transparent;color:inherit;border-radius:16px}.row-mini{width:52px;height:44px;border-radius:10px;background:var(--taller-encima);display:grid;place-items:center;overflow:hidden;transform-origin:50% 60%}.row-mini svg{width:100%;height:100%}.lib-row[data-open=true] .row-mini{animation:mini-seat var(--settle) var(--ease) both}.row-name{display:block;font-size:14px;font-weight:600;line-height:1.35}.row-meta{display:block;font-size:12px;color:var(--taller-suave);line-height:1.4;margin-top:2px}.row-toggle>svg{color:var(--taller-suave)}
.row-detail{padding:0 12px 14px;display:grid;gap:12px;transform-origin:50% 0;animation:detail-unfold var(--settle) var(--ease) both}.row-stage{height:120px;border-radius:12px;background:var(--taller-visor);display:grid;place-items:center;position:relative;overflow:hidden}.row-stage svg{width:70%;height:100%}.row-stage .scene-note{bottom:8px;left:10px}.row-facts{display:flex;flex-wrap:wrap;gap:6px 12px;font-size:12px;color:var(--taller-suave)}.row-facts b{font:600 12px 'Geist Mono',monospace;color:var(--taller-texto)}.row-actions{display:flex;flex-wrap:wrap;gap:8px}.row-actions .btn{padding:10px 14px!important;font-size:13px}.owner-tools{display:flex;flex-wrap:wrap;gap:8px;padding-top:10px;border-top:1px solid var(--taller-linea)}
.name-edit{display:flex;gap:6px;align-items:center;transform-origin:left center;animation:field-seat var(--settle) var(--ease) both}.name-edit [data-slot=input]{flex:1;min-width:0}.rename-button{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:8px 12px;border:1px dashed var(--texto-tenue);border-radius:12px;background:transparent;color:var(--taller-texto);font-size:14px;font-weight:600;text-align:left;transition:transform var(--quick) var(--ease),background-color var(--quick)}.rename-button:hover{background:var(--taller-elegido)}.rename-button svg{width:15px;height:15px;color:var(--taller-suave)}
.readonly-tag{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;color:var(--taller-texto);padding:4px 10px;border-radius:999px;border:1px solid var(--texto-tenue);background:var(--superficie)}.readonly-tag svg{width:13px;height:13px}
.local-group{border:1px dashed var(--texto-tenue);border-radius:16px;padding:4px 12px 12px}.local-group summary{min-height:44px;display:flex;align-items:center;justify-content:space-between;gap:10px;cursor:pointer;font-size:13px;font-weight:600;list-style:none}.local-group summary::-webkit-details-marker{display:none}.local-group>p{font-size:12px;color:var(--taller-suave);margin-bottom:10px}
.panel-message{padding:20px 16px;border:1px solid var(--taller-borde);border-radius:16px;background:var(--taller-tarjeta);display:grid;gap:10px;animation:notice-settle var(--settle) var(--ease) both}.panel-message h3{font-size:15px;font-weight:600}.panel-message p{font-size:13px;color:var(--taller-suave)}.panel-message[data-tone=error]{border-color:var(--error)}.panel-message[data-tone=error] h3{color:var(--error)}.skeleton-row{display:grid;grid-template-columns:52px 1fr;gap:12px;align-items:center;padding:12px 14px;border:1px solid var(--taller-borde);border-radius:16px;background:var(--taller-tarjeta)}[data-slot=skeleton]{background:var(--superficie-2);animation:none;border-radius:10px}
.studio-canvas{position:relative;min-width:0;background:var(--taller-visor);display:grid;place-items:center;padding:24px;transition:outline-offset var(--quick) var(--ease),background-color var(--quick)}.studio-canvas[data-drop=true]{outline:3px dashed var(--acento);outline-offset:-14px}.scene-art{width:100%;max-width:620px;height:340px;display:block}.scene-note{position:absolute;bottom:16px;left:20px;font-size:12px;padding:6px 12px;border-radius:999px;background:var(--superficie);color:var(--texto-suave)}.placed{position:absolute;bottom:60px;left:50%;translate:-50% 0;display:flex;gap:8px;align-items:center;padding:8px 14px;border-radius:999px;background:var(--superficie);border:1px solid var(--exito);color:var(--texto);font-size:13px;animation:place-settle var(--settle) var(--ease) both;max-width:calc(100% - 40px)}.placed svg{color:var(--exito);width:16px;height:16px}.drop-hint{position:absolute;top:16px;left:20px;max-width:calc(100% - 40px);font-size:12px;color:var(--texto-suave);display:flex;gap:6px;align-items:center}.drop-hint svg{width:14px;height:14px}
.inspector{min-width:0;padding:20px;display:flex;flex-direction:column;gap:16px;border-left:1px solid var(--taller-linea);background:var(--taller-panel)}.inspector h2{font-size:15px;font-weight:600}.inspector .sub{font-size:13px;color:var(--taller-suave)}.inspector-tabs{display:flex;gap:20px;border-bottom:1px solid var(--taller-linea);padding-bottom:12px;font-size:14px}.inspector-tabs span:first-child{font-weight:600}.piece-card{display:grid;gap:4px;padding:12px;border-radius:14px;background:var(--taller-tarjeta);border:1px solid var(--taller-borde)}.piece-card strong{font-size:14px}.piece-card span{font-size:12px;color:var(--taller-suave)}.save-pair{display:grid;grid-template-columns:1fr;gap:8px}.save-pair .btn{padding:10px 14px!important;font-size:13px;justify-content:flex-start!important;width:100%}.scene-link{min-height:44px;align-self:start;border:0;background:transparent;color:var(--taller-acento);font-size:13px;font-weight:600;text-decoration:underline;text-underline-offset:4px;padding:10px 0}
.save-form{display:grid;gap:12px;padding:14px;border-radius:16px;background:var(--superficie-2);transform-origin:50% 0;animation:form-unfold var(--settle) var(--ease) both}.save-form>p{font-size:12px;color:var(--texto-suave)}.save-form .native{border-radius:14px;width:100%}.save-form .destination{display:flex;gap:8px;align-items:start;font-size:12px;color:var(--taller-texto)}.save-form .destination svg{width:15px;height:15px;color:var(--taller-acento);margin-top:2px}
.receipt{display:grid;gap:8px;padding:12px 14px;border-radius:14px;border:1px solid var(--borde);background:var(--superficie)}.receipt p{font-size:13px;display:flex;gap:8px;align-items:start}.receipt .status-icon{width:16px;height:16px;margin-top:2px;color:var(--exito);animation:status-seat var(--settle) var(--ease) both}.receipt[data-tone=error]{border-color:var(--error)}.receipt[data-tone=error] .status-icon{color:var(--error)}.receipt[data-tone=warning] .status-icon{color:var(--aviso)}.spinner{animation:turn 1.1s linear infinite}
.tool-footer{display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;padding:16px 20px;background:var(--taller-barra);border-top:1px solid var(--taller-linea)}.tool-footer p{font-size:12px;color:var(--texto-suave)}
.footer{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;padding:28px 0 0;font-size:12px;color:var(--texto-suave)}
[data-slot=dialog-overlay],[data-slot=alert-dialog-overlay]{background:var(--overlay)!important;backdrop-filter:none!important;z-index:70!important}[data-slot=dialog-content],[data-slot=alert-dialog-content]{z-index:71!important;width:min(620px,calc(100vw - 40px))!important;max-width:620px!important;max-height:calc(100svh - 48px)!important;overflow:auto!important;background:var(--superficie)!important;color:var(--texto)!important;border:1px solid var(--texto-tenue)!important;border-radius:28px!important;padding:28px!important;gap:20px!important;font:15px/1.5 Geist,system-ui!important;box-shadow:0 18px 60px var(--overlay)!important}[data-slot=alert-dialog-content]{width:min(480px,calc(100vw - 40px))!important}[data-slot=dialog-title],[data-slot=alert-dialog-title]{font-size:20px!important;font-weight:600!important;line-height:1.3!important}[data-slot=dialog-description],[data-slot=alert-dialog-description]{font-size:14px!important;color:var(--texto-suave)!important}[data-slot=alert-dialog-footer]{display:flex!important;flex-wrap:wrap!important;gap:12px!important;justify-content:flex-start!important;background:transparent!important;border:0!important;margin:0!important;padding:0!important}
.ficha{display:grid;gap:16px}.ficha-tags{display:flex;flex-wrap:wrap;gap:8px}.tag{font-size:12px;padding:4px 10px;border-radius:999px;background:var(--superficie-2);color:var(--texto)}.ficha-stage{height:220px;border-radius:20px;background:var(--taller-visor);display:grid;place-items:center;position:relative}.ficha-stage svg{width:60%;height:100%}.ficha-section{display:grid;gap:6px;padding:14px 16px;border:1px solid var(--borde);border-radius:18px}.ficha-section h3{font-size:14px;font-weight:600}.ficha-section p{font-size:13px;color:var(--texto-suave)}.readonly-banner{display:flex;gap:12px;align-items:start;padding:14px 16px;border-radius:18px;background:var(--superficie-2)}.readonly-banner p{font-size:13px}.dialog-actions{display:flex;flex-wrap:wrap;gap:10px}
@keyframes row-settle{0%{transform:translateY(8px) scale(.985)}55%{transform:translateY(-2px) scale(1.004)}100%{transform:none}}
@keyframes row-drop{0%{transform:translateY(-14px) scale(.96)}55%{transform:translateY(3px) scale(1.012)}80%{transform:translateY(-1px)}100%{transform:none}}
@keyframes mini-seat{0%{transform:scale(.9)}60%{transform:scale(1.04)}100%{transform:none}}
@keyframes detail-unfold{0%{transform:scaleY(.94) translateY(-4px)}60%{transform:scaleY(1.01)}100%{transform:none}}
@keyframes form-unfold{0%{transform:scaleY(.92) translateY(-6px)}55%{transform:scaleY(1.012) translateY(1px)}100%{transform:none}}
@keyframes field-seat{0%{transform:scaleX(.95)}60%{transform:scaleX(1.012)}100%{transform:none}}
@keyframes status-seat{0%{transform:rotate(-16deg) scale(.8)}60%{transform:rotate(6deg) scale(1.1)}100%{transform:none}}
@keyframes count-bump{0%{transform:scale(1.3)}50%{transform:scale(.92)}100%{transform:none}}
@keyframes place-settle{0%{transform:translateY(-16px) scale(.94)}55%{transform:translateY(3px) scale(1.02)}100%{transform:none}}
@keyframes notice-settle{0%{transform:translateY(-6px) scaleY(.97)}65%{transform:translateY(1px) scaleY(1.006)}100%{transform:none}}
@keyframes turn{to{transform:rotate(360deg)}}
.app[data-hidden=true] *,[data-hidden=true] *::before,[data-hidden=true] *::after{animation-play-state:paused!important}
[data-reduced-motion] *,[data-reduced-motion] *::before,[data-reduced-motion] *::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
@media(min-width:640px) and (max-width:1099px){.app{padding-inline:24px}.masthead{flex-wrap:wrap}.studio-body{grid-template-columns:60px minmax(280px,320px) minmax(0,1fr)}.inspector{grid-column:1/-1;border-left:0;border-top:1px solid var(--taller-linea);display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);align-items:start}.inspector>*{grid-column:auto}.inspector-tabs{grid-column:1/-1}.scene-art{height:300px}}
@media(max-width:639px){.app{padding:0 20px 24px}.masthead{flex-wrap:wrap;gap:16px}.company{margin-left:0;padding-left:12px}.header-tools{width:100%;justify-content:space-between;gap:12px}.heading{flex-direction:column;align-items:start;gap:16px}.route-nav{gap:24px}.save-header{padding:16px 20px;align-items:start}.existing-controls{padding:12px 20px}.studio-body{display:flex;flex-direction:column}.tool-rail{display:none}.lib-panel{border-right:0;border-bottom:1px solid var(--taller-linea);padding:20px}.inspector{border-left:0;border-top:1px solid var(--taller-linea);padding:20px}.studio-canvas{min-height:260px;padding:20px}.scene-art{height:240px}.studio-body[data-focus=save] .studio-canvas{order:1}.studio-body[data-focus=save] .inspector{order:2}.studio-body[data-focus=save] .lib-panel{order:3;border-bottom:0;border-top:1px solid var(--taller-linea)}.studio-body[data-focus=library] .lib-panel{order:1}.studio-body[data-focus=library] .studio-canvas{order:2}.studio-body[data-focus=library] .inspector{order:3}.drop-hint{display:none}.footer{display:block}.footer span{display:block;margin-bottom:8px}[data-slot=dialog-content],[data-slot=alert-dialog-content]{padding:24px!important;border-radius:24px!important}.dialog-actions,[data-slot=alert-dialog-footer]{flex-direction:column!important;align-items:stretch!important}.dialog-actions .btn,[data-slot=alert-dialog-footer] .btn{width:100%}}
`;

function Action({ children, primary = false, ghost = false, danger = false, ...props }: React.ComponentProps<typeof Button> & { primary?: boolean; ghost?: boolean; danger?: boolean }) {
  const variant = primary ? 'default' : ghost ? 'ghost' : 'outline';
  return <Button variant={variant} data-variant={variant} data-tone={danger ? 'danger' : undefined} {...props} className={`btn ${props.className || ''}`}>{children}</Button>;
}
function Art({ kind }: { kind: Item['art'] }) {
  if (kind === 'garland') return <svg viewBox="0 0 160 100" aria-hidden="true">{[[20,50],[38,40],[56,48],[74,38],[92,47],[110,37],[128,46],[144,38]].map(([x,y],i)=><circle key={i} cx={x} cy={y} r={11} fill={i%2?'var(--acento)':'var(--taller-elegido)'} stroke="var(--taller-acento)" strokeWidth="1.2"/>)}</svg>;
  if (kind === 'scene') return <svg viewBox="0 0 160 100" aria-hidden="true"><path d="M8 78 80 58 152 78 80 96Z" fill="var(--taller-panel)" stroke="var(--texto-tenue)"/><rect x="58" y="24" width="44" height="44" rx="6" fill="var(--taller-encima)" stroke="var(--texto-tenue)"/>{[[50,62],[48,46],[54,32],[106,32],[112,46],[110,62]].map(([x,y],i)=><circle key={i} cx={x} cy={y} r={8} fill={i%2?'var(--acento)':'var(--taller-elegido)'} stroke="var(--taller-acento)"/>)}<ellipse cx="80" cy="80" rx="22" ry="6" fill="var(--superficie)" stroke="var(--texto-tenue)"/></svg>;
  return <svg viewBox="0 0 160 100" aria-hidden="true"><path d="M50 94V44a30 30 0 0 1 60 0v50" fill="none" stroke="var(--texto-tenue)" strokeWidth="2"/>{[[48,84],[46,66],[50,49],[60,34],[75,25],[92,26],[105,36],[111,52],[112,70],[110,86]].map(([x,y],i)=><circle key={i} cx={x} cy={y} r={9} fill={i%2?'var(--acento)':'var(--taller-elegido)'} stroke="var(--taller-acento)"/>)}</svg>;
}
function SceneArt({ placed }: { placed: boolean }) {
  return <svg className="scene-art" viewBox="0 0 620 330" aria-hidden="true" fill="none"><path d="M42 225 265 150 578 225 345 310Z" fill="var(--taller-panel)" stroke="var(--texto-tenue)"/><path d="M230 196V88a62 62 0 0 1 124 0v108Z" fill="var(--taller-encima)" stroke="var(--texto-tenue)" strokeWidth="2"/><g fill="var(--acento)" stroke="var(--taller-acento)" strokeWidth="1.5">{[[198,214,22],[187,180,21],[192,147,23],[205,116,20],[215,87,23],[241,65,22],[270,51,23],[304,51,21],[334,66,22],[351,93,18]].map(([x,y,r],i)=><circle key={i} cx={x} cy={y} r={r}/>)}</g><ellipse cx="370" cy="225" rx="76" ry="23" fill="var(--superficie)" stroke="var(--texto-tenue)" strokeWidth="2"/><path d="M310 226v43m120-43v43" stroke="var(--texto-tenue)" strokeWidth="6"/>{placed&&<g fill="var(--taller-elegido)" stroke="var(--taller-acento)" strokeWidth="1.5">{[[440,190],[462,176],[486,168],[510,172],[530,186]].map(([x,y],i)=><circle key={i} cx={x} cy={y} r={14}/>)}</g>}</svg>;
}
function Notice({ tone = 'normal', title, children, actions, className = '' }: { tone?: string; title: string; children: React.ReactNode; actions?: React.ReactNode; className?: string }) {
  return <section className={`notice ${className}`} data-tone={tone} role={tone === 'error' ? 'alert' : 'status'}>{tone === 'success' ? <Check aria-hidden="true" /> : tone === 'warning' ? <CloudOff aria-hidden="true" /> : <CircleAlert aria-hidden="true" />}<div className="notice-body"><h2>{title}</h2><p>{children}</p>{actions && <div className="group-actions">{actions}</div>}</div></section>;
}

function App() {
  const m = useMockup(); const profile = useMotionProfile();
  const [lang, setLang] = React.useState('es'); const t = (es: string, en: string) => (lang === 'en' ? en : es);
  const occ = (id: string) => { const o = OCCASIONS.find((x) => x[0] === id); return o ? (lang === 'en' ? o[2] : o[1]) : id; };
  const kindName = (k: Kind) => (lang === 'en' ? KIND[k][1] : KIND[k][0]);
  const [hidden, setHidden] = React.useState(document.hidden);
  const [menu, setMenu] = React.useState(false); const menuRef = React.useRef<HTMLDetailsElement>(null);
  const staffView = m.view === 'personal';
  const [owner, setOwner] = React.useState(staffView ? 'other' : 'mine');
  const foreign = staffView && owner === 'other';
  const [own, setOwn] = React.useState<Item[]>(m.state === 'empty' ? [] : OWN);
  const [open, setOpen] = React.useState<string>(m.state === 'rename' ? 'own-1' : staffView ? 'foreign-1' : 'own-1');
  const [renaming, setRenaming] = React.useState<string>(m.state === 'rename' ? 'own-1' : '');
  const [draftName, setDraftName] = React.useState(m.state === 'rename' ? '' : OWN[0].name);
  const [renameError, setRenameError] = React.useState(m.state === 'rename');
  const [renameBusy, setRenameBusy] = React.useState('');
  const [newId, setNewId] = React.useState(m.state === 'saved' ? 'own-new' : '');
  const [bump, setBump] = React.useState(false);
  const [placed, setPlaced] = React.useState<string>(m.state === 'placed' ? OWN[0].name : '');
  const [drop, setDrop] = React.useState(false);
  const [target, setTarget] = React.useState<string>(staffView ? 'foreign-1' : 'own-1');
  const [occasion, setOccasion] = React.useState('');
  const [segment, setSegment] = React.useState('mine');
  const [feedback, setFeedback] = React.useState('');
  // Inspector: piece selected in the «taller» view; nothing selected in the library-first views.
  const pieceSelected = m.view === 'taller';
  const [formOpen, setFormOpen] = React.useState<'' | 'pieza' | 'escena'>(m.view === 'taller' && !['switching', 'saved'].includes(m.state) ? 'pieza' : '');
  const [saveName, setSaveName] = React.useState('Arco');
  const [saveOcc, setSaveOcc] = React.useState('cumpleanos');
  const [saveStatus, setSaveStatus] = React.useState<'' | 'saving' | 'saved' | 'error' | 'offline' | 'session'>(
    m.state === 'saving' ? 'saving' : m.state === 'saved' ? 'saved' : m.state === 'save-error' ? 'error' : m.state === 'offline' ? 'offline' : m.state === 'session-expired' ? 'session' : '');
  const [savedLabel, setSavedLabel] = React.useState(m.state === 'saved' ? 'Arco' : '');
  const timer = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const trigger = React.useRef<HTMLElement | null>(null);

  React.useEffect(() => { document.documentElement.lang = lang; }, [lang]);
  React.useEffect(() => { const c = () => setHidden(document.hidden); document.addEventListener('visibilitychange', c); return () => document.removeEventListener('visibilitychange', c); }, []);
  React.useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);
  React.useEffect(() => { const k = (e: KeyboardEvent) => { if (e.key === 'Escape' && menuRef.current?.open) { setMenu(false); menuRef.current.querySelector('summary')?.focus(); } }; const out = (e: MouseEvent) => { if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenu(false); }; document.addEventListener('keydown', k); document.addEventListener('click', out); return () => { document.removeEventListener('keydown', k); document.removeEventListener('click', out); }; }, []);

  const listLoading = m.state === 'loading' || m.state === 'switching';
  const listError = m.state === 'load-error';
  const savedItem: Item | null = m.state === 'saved' || newId ? { id: 'own-new', name: savedLabel || 'Arco', kind: formOpen === 'escena' ? 'escena' : 'conjunto', occasion: saveOcc, balloons: 84, pieces: 3, art: formOpen === 'escena' ? 'scene' : 'arch' } : null;
  const ownRows = savedItem && !own.some((i) => i.id === 'own-new') ? [savedItem, ...own] : own;
  const base = foreign ? FOREIGN : ownRows;
  const rows = base.filter((i) => !occasion || i.occasion === occasion);
  const all = [...ownRows, ...LOCAL, ...FOREIGN];
  const targetItem = all.find((i) => i.id === target) || (foreign ? FOREIGN[0] : OWN[0]);
  const targetForeign = FOREIGN.some((i) => i.id === targetItem.id);
  const targetLocal = LOCAL.some((i) => i.id === targetItem.id);

  const openDialog = (scene: string, id: string) => { trigger.current = document.activeElement as HTMLElement; setTarget(id); m.set('scene', scene); };
  const closeDialog = () => { m.set('scene', ''); requestAnimationFrame(() => { const el = trigger.current; if (el?.isConnected) el.focus(); else document.querySelector<HTMLElement>('.lib-panel h2, h1')?.focus(); }); };
  const place = (item: Item) => { setPlaced(item.name); setFeedback(''); };
  const submitSave = (e: React.FormEvent) => {
    e.preventDefault();
    const finalName = saveName.trim() || (formOpen === 'escena' ? t('Mi escena', 'My scene') : 'Arco');
    setSaveStatus('saving');
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => { setSavedLabel(finalName); setNewId('own-new'); setOpen('own-new'); setSaveStatus('saved'); setBump(true); setFormOpen(''); setTimeout(() => setBump(false), 700); requestAnimationFrame(() => document.querySelector<HTMLElement>('.receipt')?.focus()); }, 800);
  };
  const startRename = (item: Item) => { setRenaming(item.id); setDraftName(item.name); setRenameError(false); };
  const cancelRename = () => { const id = renaming; setRenaming(''); setRenameError(false); requestAnimationFrame(() => document.querySelector<HTMLElement>(`[data-rename="${id}"]`)?.focus()); };
  const confirmRename = (e: React.FormEvent) => {
    e.preventDefault();
    if (!draftName.trim()) { setRenameError(true); return; }
    const id = renaming; const name = draftName.trim();
    setRenameBusy(id); setRenaming('');
    setTimeout(() => { setOwn((list) => list.map((i) => (i.id === id ? { ...i, name } : i))); if (id === 'own-new') setSavedLabel(name); setRenameBusy(''); setFeedback(t(`Nombre cambiado en tu cuenta: «${name}».`, `Name changed in your account: “${name}”.`)); requestAnimationFrame(() => document.querySelector<HTMLElement>(`[data-rename="${id}"]`)?.focus()); }, 600);
  };
  const remove = () => { const id = target; const name = targetItem.name; setOwn((l) => l.filter((i) => i.id !== id)); if (id === 'own-new') setNewId(''); m.set('scene', ''); setFeedback(t(`Quitada de tu biblioteca: «${name}».`, `Removed from your library: “${name}”.`)); requestAnimationFrame(() => document.querySelector<HTMLElement>('.lib-panel h2')?.focus()); };

  const ownCount = ownRows.length;
  const status = saveStatus;

  function Row({ item, i, mode }: { item: Item; i: number; mode: 'own' | 'local' | 'foreign' }) {
    const isOpen = open === item.id;
    const busy = renameBusy === item.id;
    return <li className="lib-row" data-open={isOpen} data-new={item.id === newId} style={{ '--i': i } as React.CSSProperties}
      draggable={mode !== 'foreign'} onDragStart={(e) => { e.dataTransfer.setData('text/plain', item.id); e.dataTransfer.effectAllowed = 'copy'; }}>
      <motion.button type="button" className="row-toggle" aria-expanded={isOpen} aria-controls={`detail-${item.id}`} transition={profile.spring} whileTap={profile.reduced ? undefined : { scale: 0.975 }} onClick={() => { setOpen(isOpen ? '' : item.id); setRenaming(''); }}>
        <span className="row-mini" aria-hidden="true"><Art kind={item.art} /></span>
        <span><span className="row-name">{item.name}</span><span className="row-meta">{kindName(item.kind)} · {occ(item.occasion)}{mode === 'foreign' ? ` · ${t('Solo lectura', 'Read only')}` : mode === 'local' ? ` · ${t('Solo en este navegador', 'This browser only')}` : busy ? ` · ${t('Guardando…', 'Saving…')}` : ''}</span></span>
        {isOpen ? <ChevronUp aria-hidden="true" /> : <ChevronDown aria-hidden="true" />}
      </motion.button>
      {isOpen && <div className="row-detail" id={`detail-${item.id}`}>
        <div className="row-stage" role="img" aria-label={t(`Vista de ${item.name} · Mockup`, `View of ${item.name} · Mockup`)}><Art kind={item.art} /><span className="scene-note">{t('Vista 3D · Mockup', '3D view · Mockup')}</span></div>
        <p className="row-facts"><span><b>{item.balloons}</b> {t('globos', 'balloons')}</span><span><b>{item.pieces}</b> {item.pieces === 1 ? t('pieza', 'piece') : t('piezas', 'pieces')}</span><span>{mode === 'foreign' ? t('Cuenta de ejemplo', 'Example account') : mode === 'local' ? t('Guardada en este navegador', 'Saved in this browser') : t('Guardada en tu cuenta', 'Saved to your account')}</span></p>
        {mode === 'foreign' ? <>
          <span className="readonly-tag"><Lock aria-hidden="true" />{t('Solo lectura · Solo la cuenta dueña la cambia o la quita', 'Read only · Only the owning account can change or remove it')}</span>
          <div className="row-actions"><Action primary onClick={() => openDialog('ficha', item.id)}><Eye aria-hidden="true" />{t('Ver ficha', 'View details')}</Action></div>
        </> : <>
          <div className="row-actions">
            <Action primary onClick={() => place(item)}><Plus aria-hidden="true" />{t('Añadir a mi escena', 'Add to my scene')}</Action>
            <Action onClick={() => setFeedback(t('Mockup · «Abrir en Escena» sigue la guarda de proyectos@v1 (escena nueva sin guardar).', 'Mockup · “Open in Scene” follows the proyectos@v1 guard (new unsaved scene).'))}><Replace aria-hidden="true" />{t('Abrir en Escena', 'Open in Scene')}</Action>
            <Action ghost onClick={() => openDialog('ficha', item.id)}><Eye aria-hidden="true" />{t('Ver ficha', 'View details')}</Action>
          </div>
          {mode === 'own' && <div className="owner-tools">
            {renaming === item.id ? <form className="name-edit" onSubmit={confirmRename} style={{ width: '100%', flexWrap: 'wrap' }}>
              <label htmlFor={`rename-${item.id}`} className="sr-only">{t('Nombre de la decoración', 'Decoration name')}</label>
              <Input id={`rename-${item.id}`} autoFocus value={draftName} maxLength={120} aria-invalid={renameError} aria-describedby={renameError ? `rename-error-${item.id}` : undefined} onChange={(e) => { setDraftName(e.target.value); setRenameError(false); }} onKeyDown={(e) => { if (e.key === 'Escape') { e.preventDefault(); cancelRename(); } }} />
              <Action type="submit" className="icon" aria-label={t('Confirmar nombre', 'Confirm name')}><Check aria-hidden="true" /></Action>
              <Action type="button" className="icon" aria-label={t('Cancelar', 'Cancel')} onClick={cancelRename}><X aria-hidden="true" /></Action>
              {renameError && <p id={`rename-error-${item.id}`} className="field-error" role="alert" style={{ width: '100%' }}>{t('Escribe un nombre para la decoración.', 'Enter a name for the decoration.')}</p>}
            </form> : <motion.button type="button" className="rename-button" data-rename={item.id} transition={profile.spring} whileTap={profile.reduced ? undefined : { scale: 0.965 }} disabled={busy} onClick={() => startRename(item)} aria-label={`${t('Cambiar nombre', 'Rename')}: ${item.name}`}>{busy ? <Loader2 className="spinner" aria-hidden="true" /> : <Pencil aria-hidden="true" />}{busy ? t('Guardando…', 'Saving…') : t('Cambiar nombre', 'Rename')}</motion.button>}
            {renaming !== item.id && <Action ghost danger onClick={() => openDialog('quitar', item.id)}><Trash2 aria-hidden="true" />{t('Quitar de mi biblioteca', 'Remove from my library')}</Action>}
          </div>}
        </>}
      </div>}
    </li>;
  }

  function LibraryPanel() {
    return <section className="lib-panel" aria-labelledby="panel-title">
      <h2 id="panel-title" tabIndex={-1}>{t('Añadir a la escena', 'Add to the scene')}</h2>
      <div className="field panel-search"><label htmlFor="panel-q" className="sr-only">{t('Buscar', 'Search')}</label><Search aria-hidden="true" /><Input id="panel-q" placeholder={t('Buscar', 'Search')} /></div>
      <div className="lib-seg" role="group" aria-label={t('Secciones de Añadir', 'Add sections')}>
        {[['estructuras', t('Estructuras', 'Structures')], ['decoraciones', t('Decoraciones', 'Decorations')], ['utileria', t('Utilería', 'Props')], ['ideas', t('Ideas', 'Ideas')], ['mine', t('Mi biblioteca', 'My library')]].map(([id, label]) =>
          <button key={id} type="button" aria-pressed={segment === id} onClick={() => setSegment(id)}>{label}{id === 'mine' && !listLoading && !foreign && <span className="seg-count" data-bump={bump} aria-label={t(`${ownCount} en tu cuenta`, `${ownCount} in your account`)}>{ownCount}</span>}</button>)}
      </div>
      {segment !== 'mine' ? <div className="panel-message"><h3>{t('Catálogo existente del Taller', 'Existing workshop catalogue')}</h3><p>{t('Mockup · Esta sección no cambia. Lo que guardas está en «Mi biblioteca».', 'Mockup · This section is unchanged. What you save is in “My library”.')}</p></div> : <>
        {staffView && <div className="owner-pick"><label className="field-label" htmlFor="owner">{t('Biblioteca de', 'Library of')}</label><select id="owner" className="native" value={owner} onChange={(e) => { setOwner(e.target.value); setOpen(e.target.value === 'other' ? 'foreign-1' : 'own-1'); setRenaming(''); }}><option value="mine">{t('Mi cuenta', 'My account')}</option><option value="other">{t('Cuenta de ejemplo', 'Example account')}</option></select></div>}
        <div className="filters"><label htmlFor="occasion" className="sr-only">{t('Ocasión', 'Occasion')}</label><select id="occasion" className="native" value={occasion} onChange={(e) => setOccasion(e.target.value)}><option value="">{t('Ocasión: todas', 'Occasion: all')}</option>{OCCASIONS.map(([id]) => <option key={id} value={id}>{occ(id)}</option>)}</select></div>
        {m.state === 'forbidden' && <div className="panel-message" data-tone="error" role="alert"><h3>{t('No se cambió nada', 'Nothing was changed')}</h3><p>{t('Solo la cuenta dueña puede cambiar o quitar esta decoración.', 'Only the owning account can change or remove this decoration.')}</p></div>}
        {listLoading ? <div className="lib-list" aria-busy="true"><span className="sr-only" role="status">{m.state === 'switching' ? t('Cargando la biblioteca de la cuenta que inició sesión…', 'Loading the library of the signed-in account…') : t('Cargando tu biblioteca…', 'Loading your library…')}</span>
          {m.state === 'switching' && <div className="panel-message" role="status"><h3>{t('Cambiaste de cuenta', 'You switched account')}</h3><p>{t('Las decoraciones de la cuenta anterior ya no se muestran.', 'The previous account’s decorations are no longer shown.')}</p></div>}
          {[0, 1, 2].map((i) => <div className="skeleton-row" key={i}><Skeleton style={{ height: 44, width: 52 }} /><div style={{ display: 'grid', gap: 8 }}><Skeleton style={{ height: 14, width: '70%' }} /><Skeleton style={{ height: 12, width: '45%' }} /></div></div>)}
        </div> : listError ? <div className="panel-message" data-tone="error" role="alert"><h3>{t('No se pudo cargar tu biblioteca', 'Could not load your library')}</h3><p>{t('Lo guardado en tu cuenta no se perdió. Vuelve a intentarlo.', 'What is saved in your account is not lost. Try again.')}</p><div><Action onClick={() => m.set('state', 'normal')}>{t('Reintentar', 'Retry')}</Action></div></div>
          : <>
            <p className="group-label"><strong>{foreign ? t('Cuenta de ejemplo', 'Example account') : t('En tu cuenta', 'In your account')}</strong><span>{rows.length} {rows.length === 1 ? t('guardada', 'saved') : t('guardadas', 'saved')}</span></p>
            {rows.length === 0 ? <div className="panel-message"><h3>{own.length === 0 && !occasion ? t('Todavía no has guardado decoraciones', 'You have not saved any decorations yet') : t('Ninguna coincide', 'None match')}</h3><p>{own.length === 0 && !occasion ? t('Elige una pieza en la escena y usa «Guardar en mi biblioteca», o guarda toda la escena. Quedará en tu cuenta.', 'Choose a piece in the scene and use “Save to my library”, or save the whole scene. It stays in your account.') : t('Prueba con otra ocasión.', 'Try another occasion.')}</p>{occasion && <div><Action onClick={() => setOccasion('')}>{t('Quitar filtros', 'Clear filters')}</Action></div>}</div>
              : <ul className="lib-list">{rows.map((item, i) => <React.Fragment key={item.id}>{Row({ item, i, mode: foreign ? 'foreign' : 'own' })}</React.Fragment>)}</ul>}
            {!foreign && <details className="local-group" open={m.state === 'legacy'}>
              <summary>{t('En este navegador', 'In this browser')} · {LOCAL.length}<ChevronDown aria-hidden="true" /></summary>
              <p>{t('Guardadas antes en este navegador. Siguen aquí y no se pasan a tu cuenta en el piloto.', 'Saved earlier in this browser. They stay here and are not moved to your account in the pilot.')}</p>
              <ul className="lib-list">{LOCAL.map((item, i) => <React.Fragment key={item.id}>{Row({ item, i, mode: 'local' })}</React.Fragment>)}</ul>
            </details>}
          </>}
      </>}
    </section>;
  }

  function Inspector() {
    const sceneForm = formOpen === 'escena';
    return <aside className="inspector" aria-label={t('Escena e IA', 'Scene and AI')}>
      <div className="inspector-tabs"><span>{t('Escena', 'Scene')}</span><span>IA</span></div>
      <div style={{ display: 'grid', gap: 12 }}>
        {pieceSelected ? <div className="piece-card"><strong>{t('Pieza elegida · Arco', 'Selected piece · Arch')}</strong><span>{t('Estructura con decoraciones · Mockup', 'Structure with decorations · Mockup')}</span></div> : <p className="sub">{t('Ninguna pieza elegida.', 'No piece selected.')}</p>}
        {pieceSelected && <div className="save-pair">
          <Action onClick={() => setFeedback(t('Mockup · «Ver con sus decoraciones» abre la ficha existente.', 'Mockup · “View with its decorations” opens the existing detail.'))}><Eye aria-hidden="true" />{t('Ver con sus decoraciones', 'View with its decorations')}</Action>
          <Action primary={formOpen === 'pieza'} aria-expanded={formOpen === 'pieza'} aria-controls="save-form" onClick={() => { setFormOpen(formOpen === 'pieza' ? '' : 'pieza'); setSaveName('Arco'); setSaveStatus(''); }}><BookmarkPlus aria-hidden="true" />{t('Guardar en mi biblioteca', 'Save to my library')}</Action>
        </div>}
        <button type="button" className="scene-link" aria-expanded={sceneForm} aria-controls="save-form" onClick={() => { setFormOpen(sceneForm ? '' : 'escena'); setSaveName(''); setSaveStatus(''); }}>{t('Guardar toda la escena en mi biblioteca', 'Save the whole scene to my library')}</button>
      </div>
      <div style={{ display: 'grid', gap: 12 }}>
        {formOpen && <form className="save-form" id="save-form" onSubmit={submitSave} aria-label={t('Guardar en mi biblioteca', 'Save to my library')}>
          <p>{sceneForm ? t('La escena entera (9 piezas).', 'The whole scene (9 pieces).') : t('La estructura con todo lo que cuelga de ella y lo pegado a sus globos.', 'The structure with everything hanging from it and attached to its balloons.')}</p>
          <div className="field"><label htmlFor="save-name">{t('Nombre', 'Name')}</label><Input id="save-name" value={saveName} maxLength={120} placeholder={sceneForm ? t('Mi escena', 'My scene') : 'Arco'} disabled={status === 'saving'} onChange={(e) => setSaveName(e.target.value)} /></div>
          <div className="field"><label htmlFor="save-occ">{t('Ocasión', 'Occasion')}</label><select id="save-occ" className="native" value={saveOcc} disabled={status === 'saving'} onChange={(e) => setSaveOcc(e.target.value)}>{OCCASIONS.map(([id]) => <option key={id} value={id}>{occ(id)}</option>)}</select></div>
          <p className="destination"><UserRound aria-hidden="true" />{t('Se guarda en tu cuenta: la verás en «Mi biblioteca» desde cualquier navegador.', 'Saved to your account: you will see it in “My library” from any browser.')}</p>
          <div className="group-actions"><Action primary type="submit" disabled={status === 'saving'}>{status === 'saving' ? <><Loader2 className="spinner" aria-hidden="true" />{t('Guardando…', 'Saving…')}</> : t('Guardar', 'Save')}</Action><Action type="button" ghost disabled={status === 'saving'} onClick={() => setFormOpen('')}>{t('Cancelar', 'Cancel')}</Action></div>
        </form>}
        {status === 'saved' && <div className="receipt" tabIndex={-1} role="status"><p><Check className="status-icon" aria-hidden="true" />{t(`Guardado en tu biblioteca: «${savedLabel}» (${sceneForm ? 'escena' : 'estructura con decoraciones'}).`, `Saved to your library: “${savedLabel}” (${sceneForm ? 'scene' : 'structure with decorations'}).`)}</p><div><Action onClick={() => { setSegment('mine'); setOpen('own-new'); requestAnimationFrame(() => document.querySelector<HTMLElement>('.lib-row[data-new=true] .row-toggle')?.focus()); }}>{t('Ver en Mi biblioteca', 'View in My library')}</Action></div></div>}
        {(status === 'error' || status === 'offline' || status === 'session') && <div className="receipt" data-tone={status === 'offline' ? 'warning' : 'error'} role="alert"><p>{status === 'offline' ? <CloudOff className="status-icon" aria-hidden="true" /> : <CircleAlert className="status-icon" aria-hidden="true" />}{status === 'offline' ? t('Sin conexión: no se guardó en tu cuenta. El nombre y la ocasión siguen aquí.', 'Offline: not saved to your account. The name and occasion are still here.') : status === 'session' ? t('Tu sesión ha terminado: no se guardó. Vuelve a iniciar sesión con la misma cuenta.', 'Your session has ended: not saved. Sign in again with the same account.') : t('No se pudo guardar en tu cuenta. El nombre y la ocasión siguen aquí.', 'Could not save to your account. The name and occasion are still here.')}</p>{status !== 'session' ? <div><Action onClick={() => { if (!formOpen) setFormOpen('pieza'); setSaveStatus('saving'); timer.current = setTimeout(() => { setSavedLabel(saveName.trim() || 'Arco'); setNewId('own-new'); setOpen('own-new'); setSaveStatus('saved'); setBump(true); setFormOpen(''); setTimeout(() => setBump(false), 700); }, 800); }}>{t('Reintentar', 'Retry')}</Action></div> : <div><Action onClick={() => setFeedback(t('Mockup · Inicio de sesión definido por cuentas-admin@v1.', 'Mockup · Sign-in defined by cuentas-admin@v1.'))}>{t('Iniciar sesión', 'Sign in')}</Action></div>}</div>}
        {status === 'saving' && !formOpen && <div className="receipt" role="status"><p><Loader2 className="status-icon spinner" aria-hidden="true" />{t('Guardando…', 'Saving…')}</p></div>}
      </div>
    </aside>;
  }

  const focus = m.view === 'taller' ? 'save' : 'library';
  return <><style>{css}</style><div className="app" data-profile={profile.profile} data-hidden={hidden}>
    <header className="masthead"><div className="brand"><span className="brandmark" aria-hidden="true"><svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeOpacity=".65" strokeWidth="1.2" /><circle cx="8" cy="8" r="1.8" fill="currentColor" /></svg></span>Pictures<span className="company">Sempertex</span></div>
      <div className="header-tools"><label className="language" htmlFor="language">{t('Idioma', 'Language')}<select className="native" id="language" value={lang} onChange={(e) => setLang(e.target.value)}><option value="es">ES</option><option value="en">EN</option></select></label>
        <details className="user-menu" ref={menuRef} open={menu} onToggle={(e) => setMenu(e.currentTarget.open)}><summary onClick={(e) => { e.preventDefault(); setMenu(!menu); }}><UserRound aria-hidden="true" />{t('Mi cuenta', 'My account')}<ChevronDown aria-hidden="true" /></summary><div className="menu-options"><p>{staffView ? t('Cuenta de ejemplo · Empleado interno', 'Example account · Internal employee') : t('Cuenta de ejemplo · Usuario · Master Designer', 'Example account · User · Master Designer')}</p>{[['Mi cuenta', 'My account'], ['Planes', 'Plans'], ['Cerrar sesión', 'Sign out']].map(([es, en]) => <Action key={es} onClick={() => { setMenu(false); setFeedback(es === 'Cerrar sesión' ? t('Mockup · Al cerrar sesión o cambiar de cuenta se vacía «Mi biblioteca» antes de mostrar la siguiente cuenta (estado «Cambio de cuenta»).', 'Mockup · Signing out or switching account empties “My library” before the next account is shown (“Account switch” state).') : t('Mockup · Destino definido por cuentas-admin@v1 y planes@v1.', 'Mockup · Destination defined by cuentas-admin@v1 and planes@v1.')); }}>{t(es, en)}</Action>)}</div></details></div></header>
    <div className="heading"><h1 tabIndex={-1}>{t('Taller 3D', '3D workshop')}</h1><Action onClick={() => setFeedback(t('Mockup · La lista de proyectos es proyectos@v1.', 'Mockup · The project list is proyectos@v1.'))}><ArrowLeft aria-hidden="true" />{t('Proyectos', 'Projects')}</Action></div>
    <nav className="route-nav" aria-label={t('Navegación del producto', 'Product navigation')}><a href="/3d" aria-current="page" onClick={(e) => e.preventDefault()}>{t('Taller 3D', '3D workshop')}</a><a href="/proyectos" onClick={(e) => { e.preventDefault(); setFeedback(t('Mockup · La lista de proyectos es proyectos@v1.', 'Mockup · The project list is proyectos@v1.')); }}>{t('Proyectos', 'Projects')}</a></nav>
    {feedback && <Notice className="page-notice" tone="success" title={t('Hecho', 'Done')} actions={<Action ghost onClick={() => setFeedback('')}>{t('Cerrar aviso', 'Dismiss')}</Action>}>{feedback}</Notice>}
    <section className="workshop" aria-label={t('Taller 3D', '3D workshop')}>
      <div className="save-header"><div className="scene-identity"><strong>{t('Taller 3D', '3D workshop')}</strong><span aria-hidden="true">/</span><span className="project">{t('Proyecto de ejemplo', 'Example project')}</span><span className="save-status"><Check aria-hidden="true" />{t('Guardado en tu cuenta', 'Saved to your account')}</span></div>
        <div className="group-actions"><Action className="icon" disabled aria-label={t('Deshacer', 'Undo')}><Undo2 aria-hidden="true" /></Action><Action className="icon" disabled aria-label={t('Rehacer', 'Redo')}><Redo2 aria-hidden="true" /></Action></div></div>
      <div className="existing-controls"><p className="sub" style={{ fontSize: 12, color: 'var(--texto-suave)' }}>{t('Mockup · Herramientas existentes del Taller sin cambios.', 'Mockup · Existing workshop tools unchanged.')}</p><div className="group-actions"><Action onClick={() => setFeedback(t('Mockup · Herramientas existentes del Taller.', 'Mockup · Existing workshop tools.'))}><Camera aria-hidden="true" />{t('Foto realista', 'Realistic photo')}</Action><Action onClick={() => setFeedback(t('Mockup · Herramientas existentes del Taller.', 'Mockup · Existing workshop tools.'))}><ShoppingCart aria-hidden="true" />{t('Lista de compra', 'Shopping list')}</Action></div></div>
      <div className="studio-body" data-focus={focus}>
        <nav className="tool-rail" aria-label={t('Paneles del Taller', 'Workshop panels')}>{[[Plus, 'Añadir', 'Add', true], [Box, 'Piezas', 'Pieces', false], [LayoutGrid, 'Plantillas', 'Templates', false], [Settings2, 'Sala', 'Room', false]].map(([Icon, es, en, on]) => <Action key={es as string} className="icon" aria-pressed={on as boolean} aria-label={t(es as string, en as string)} onClick={() => setFeedback(t('Mockup · Herramientas existentes del Taller.', 'Mockup · Existing workshop tools.'))}>{React.createElement(Icon as React.ComponentType<{ 'aria-hidden': boolean }>, { 'aria-hidden': true })}</Action>)}</nav>
        {LibraryPanel()}
        <div className="studio-canvas" data-drop={drop} role="region" aria-label={t('Visor de la escena · Mockup', 'Scene viewer · Mockup')}
          onDragOver={(e) => { e.preventDefault(); setDrop(true); }} onDragLeave={() => setDrop(false)} onDrop={(e) => { e.preventDefault(); setDrop(false); const id = e.dataTransfer.getData('text/plain'); const it = all.find((x) => x.id === id); if (it && !FOREIGN.some((f) => f.id === id)) place(it); }}>
          <SceneArt placed={!!placed} />
          {placed && <p className="placed" role="status" key={placed}><Check aria-hidden="true" />{t(`Añadida a tu escena: «${placed}».`, `Added to your scene: “${placed}”.`)}</p>}
          <span className="scene-note">{t('Vista de escena · Mockup', 'Scene view · Mockup')}</span>
          <span className="drop-hint"><GripVertical aria-hidden="true" />{t('Arrastra una fila de tu biblioteca aquí, o usa «Añadir a mi escena».', 'Drag a row from your library here, or use “Add to my scene”.')}</span>
        </div>
        {Inspector()}
      </div>
      <div className="tool-footer"><p>{t('Lo que guardas en «Mi biblioteca» queda en tu cuenta; el catálogo de decoraciones del Taller es aparte.', 'What you save in “My library” stays in your account; the workshop decorations catalogue is separate.')}</p></div>
    </section>
    <footer className="footer"><span>{t('Mockup · Datos y operaciones simulados.', 'Mockup · Simulated data and operations.')}</span><span>decoraciones@v1 · r1 · C</span></footer>
  </div>
    <Dialog open={m.scene === 'ficha'} onOpenChange={(v) => { if (!v) closeDialog(); }}>
      <DialogContent showCloseButton={false}>
        <DialogHeader><DialogTitle>{targetItem.name}</DialogTitle><DialogDescription>{targetForeign ? t('Ficha de una decoración de otra cuenta.', 'Details of another account’s decoration.') : targetLocal ? t('Ficha de una decoración guardada en este navegador.', 'Details of a decoration saved in this browser.') : t('Ficha de una decoración de tu biblioteca.', 'Details of a decoration in your library.')}</DialogDescription></DialogHeader>
        <div className="ficha">
          <div className="ficha-tags"><span className="tag">{kindName(targetItem.kind)}</span><span className="tag">{occ(targetItem.occasion)}</span></div>
          {targetForeign && <div className="readonly-banner" role="note"><Lock aria-hidden="true" /><p>{t('Cuenta de ejemplo · Solo lectura. Solo la cuenta dueña puede cambiar el nombre o quitarla.', 'Example account · Read only. Only the owning account can rename or remove it.')}</p></div>}
          <div className="ficha-stage" role="img" aria-label={t(`Vista 3D de ${targetItem.name} · Mockup`, `3D view of ${targetItem.name} · Mockup`)}><Art kind={targetItem.art} /><span className="scene-note">{t('Vista 3D · Mockup', '3D view · Mockup')}</span></div>
          <section className="ficha-section"><h3>{t('De dónde viene', 'Where it comes from')}</h3><p>{targetForeign ? t('Biblioteca de Cuenta de ejemplo · Guardado desde el Taller 3D', 'Example account’s library · Saved from the 3D workshop') : targetLocal ? t('Tu biblioteca en este navegador · Guardado desde el Taller 3D', 'Your library in this browser · Saved from the 3D workshop') : t('Tu biblioteca · Guardado desde el Taller 3D', 'Your library · Saved from the 3D workshop')}</p></section>
          <section className="ficha-section"><h3>{t('Productos', 'Products')}</h3><p>{t(`Mockup · La lista de productos existente no cambia (${targetItem.balloons} globos).`, `Mockup · The existing product list is unchanged (${targetItem.balloons} balloons).`)}</p></section>
          <div className="dialog-actions">
            {!targetForeign && <><Action primary onClick={() => { place(targetItem); closeDialog(); }}><Plus aria-hidden="true" />{t('Añadir a mi escena', 'Add to my scene')}</Action><Action onClick={() => { closeDialog(); setFeedback(t('Mockup · «Abrir en Escena» sigue la guarda de proyectos@v1.', 'Mockup · “Open in Scene” follows the proyectos@v1 guard.')); }}><Replace aria-hidden="true" />{t('Abrir en Escena', 'Open in Scene')}</Action></>}
            {!targetForeign && !targetLocal && <Action ghost danger onClick={() => { m.set('scene', 'quitar'); }}><Trash2 aria-hidden="true" />{t('Quitar de mi biblioteca', 'Remove from my library')}</Action>}
            <Action ghost onClick={closeDialog}><ArrowLeft aria-hidden="true" />{t('Volver a la biblioteca', 'Back to the library')}</Action>
          </div>
        </div>
      </DialogContent>
    </Dialog>
    <AlertDialog open={m.scene === 'quitar'} onOpenChange={(v) => { if (!v) closeDialog(); }}>
      <AlertDialogContent>
        <AlertDialogHeader><AlertDialogTitle>{t(`¿Quitar «${targetForeign || targetLocal ? OWN[0].name : targetItem.name}» de tu biblioteca?`, `Remove “${targetForeign || targetLocal ? OWN[0].name : targetItem.name}” from your library?`)}</AlertDialogTitle><AlertDialogDescription>{t('Se quita de tu cuenta en todos los navegadores. Lo que ya añadiste a tus escenas se queda en ellas.', 'It is removed from your account in every browser. What you already added to your scenes stays there.')}</AlertDialogDescription></AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel className="btn" data-variant="outline">{t('Conservar', 'Keep it')}</AlertDialogCancel>
          <AlertDialogAction className="btn" data-variant="default" onClick={remove}>{t('Quitar de mi biblioteca', 'Remove from my library')}</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  </>;
}

mountMockup(App, {
  title: 'Decoraciones guardadas · C · Manipulación directa', motion: 'expressive',
  views: [{ id: 'taller', label: 'Taller 3D · Guardar pieza' }, { id: 'biblioteca', label: 'Taller 3D · Mi biblioteca' }, { id: 'personal', label: 'Personal · Biblioteca de otra cuenta' }],
  states: [{ id: 'normal', label: 'Normal' }, { id: 'loading', label: 'Cargando' }, { id: 'empty', label: 'Vacía' }, { id: 'load-error', label: 'Error al cargar' }, { id: 'saving', label: 'Guardando' }, { id: 'saved', label: 'Guardado' }, { id: 'save-error', label: 'Error al guardar' }, { id: 'offline', label: 'Sin conexión' }, { id: 'rename', label: 'Cambiar nombre · vacío' }, { id: 'placed', label: 'Añadida a la escena' }, { id: 'legacy', label: 'Guardadas en este navegador' }, { id: 'forbidden', label: 'Cambio rechazado · no es dueña' }, { id: 'switching', label: 'Cambio de cuenta' }, { id: 'session-expired', label: 'Sesión terminada' }],
  scenes: [{ id: '', label: 'Ninguno' }, { id: 'ficha', label: 'Ficha' }, { id: 'quitar', label: 'Quitar de mi biblioteca' }],
});
