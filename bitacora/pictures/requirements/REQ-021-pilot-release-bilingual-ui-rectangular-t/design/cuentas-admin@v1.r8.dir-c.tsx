// Direction C · «Tablero de ganchos»: the decorator's workshop pegboard. Passes, people and permissions hang from
// fuchsia hooks; pressing compresses like latex and every hung piece settles with a damped swing.
import "@fontsource-variable/fraunces/full.css";
import "@fontsource-variable/bricolage-grotesque/index.css";
import React, { useEffect, useRef, useState } from "react";
import { motion } from "motion/react";
import { ArrowRight, Check, Copy, KeyRound, LogOut, Plus, ShieldCheck, Users, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogContent, AlertDialogDescription, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { mountMockup, useMockup } from "@kit/mockup";
import { useMotionProfile } from "@kit/motion";

// Pictures semantic names (--fondo, --superficie, --texto, --acento…) mapped onto the kit's shadcn roles.
// The green board and fuchsia hook are an exploration proposal, not an approved token migration.
const css = String.raw`
:root,[data-theme="light"]{
  --fondo:#dfe9e2;--tablero:#245c43;--perfo:#1a4733;--sobre-tablero:#ffffff;--sobre-tablero-suave:#e3f1e8;
  --superficie:#fffdf8;--superficie-2:#edf3ee;--texto:#13261d;--texto-suave:#44574c;
  --acento:#b8144f;--sobre-acento:#ffffff;--acento-suave:#fde3ee;--borde:#5e7568;--cordel:#7d8f84;
  --error:#a3122f;--error-suave:#fde6ea;--exito:#17613e;--exito-suave:#ddf1e5;--aviso:#7a4a00;
  --globo-a:#ff8cc0;--globo-b:#ffd166;--globo-c:#fffdf8;
  --background:var(--fondo);--foreground:var(--texto);--card:var(--superficie);--card-foreground:var(--texto);
  --popover:var(--superficie);--popover-foreground:var(--texto);--primary:var(--acento);--primary-foreground:var(--sobre-acento);
  --secondary:var(--superficie-2);--secondary-foreground:var(--texto);--muted:var(--superficie-2);--muted-foreground:var(--texto-suave);
  --accent:var(--superficie-2);--accent-foreground:var(--texto);--border:var(--borde);--input:var(--borde);--ring:var(--acento);
  --destructive:var(--error);--destructive-foreground:#ffffff;--success:var(--exito);--success-soft:var(--exito-suave);
  --primary-soft:var(--acento-suave);--destructive-soft:var(--error-suave);--radius:1.1rem;color-scheme:light}
.dark,[data-theme="dark"]{
  --fondo:#0b1a13;--tablero:#0f241b;--perfo:#1d3d2f;--sobre-tablero:#effaf4;--sobre-tablero-suave:#bcd3c5;
  --superficie:#163228;--superficie-2:#1f4134;--texto:#eefaf3;--texto-suave:#bcd3c5;
  --acento:#ff8cc0;--sobre-acento:#2a0716;--acento-suave:#4a1d33;--borde:#8fb3a0;--cordel:#8fb3a0;
  --error:#ffabb9;--error-suave:#4b2333;--exito:#95e3b5;--exito-suave:#183e32;--aviso:#ffdf7c;
  --globo-a:#ff8cc0;--globo-b:#ffd166;--globo-c:#effaf4;--destructive-foreground:#35101a;color-scheme:dark}

/* motion tokens: tactile compression and damped settling, scaled by the profile */
:root{--swing:1100ms;--drop:760ms;--settle:460ms;--press:120ms;--gap-i:70ms;
  --ease-settle:cubic-bezier(.22,1.65,.36,1);--ease-press:cubic-bezier(.3,0,.6,1)}
[data-motion="natural"]{--swing:720ms;--drop:520ms;--settle:340ms;--gap-i:50ms}
[data-motion="subtle"]{--swing:380ms;--drop:300ms;--settle:220ms;--gap-i:25ms;--ease-settle:cubic-bezier(.2,.9,.3,1)}

body{font-family:'Bricolage Grotesque Variable',system-ui,sans-serif;font-size:15px;line-height:1.5;background:var(--background);color:var(--foreground)}
*{box-sizing:border-box}button,input,select{font:inherit}h1,h2,h3,p,ul,dl{margin:0}ul{padding-left:20px}
button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible,[role=checkbox]:focus-visible{outline:3px solid var(--ring)!important;outline-offset:3px!important;box-shadow:none!important}
.board button:focus-visible,.board select:focus-visible{outline-color:var(--sobre-tablero)!important}
.board .pass :focus-visible{outline-color:var(--ring)!important}
button{cursor:pointer}button:disabled{cursor:not-allowed;opacity:1!important;color:var(--muted-foreground)!important;background:var(--muted)!important;border-color:var(--borde)!important}
svg{flex-shrink:0}
.pegs{background-color:var(--fondo);background-image:radial-gradient(circle,color-mix(in srgb,var(--borde) 34%,transparent) 2.6px,transparent 3.2px);background-size:30px 30px}
.board{background-color:var(--tablero);background-image:radial-gradient(circle,var(--perfo) 3px,transparent 3.6px);background-size:30px 30px;color:var(--sobre-tablero)}

/* type: Fraunces inflated (SOFT 100, WONK 1) for display, Bricolage for work */
.display-title{font-family:'Fraunces Variable',Georgia,serif;font-weight:900;font-variation-settings:'SOFT' 100,'WONK' 1,'opsz' 144;
  font-size:clamp(46px,7vw,98px);line-height:.92;letter-spacing:-.035em;max-width:11ch;transform-origin:0 100%;
  animation:inflate var(--drop) var(--ease-settle) both}
.title-sm{font-family:'Fraunces Variable',Georgia,serif;font-weight:800;font-variation-settings:'SOFT' 100,'WONK' 0,'opsz' 48;letter-spacing:-.02em}
@keyframes inflate{0%{font-variation-settings:'SOFT' 0,'WONK' 0,'opsz' 144;font-weight:560;transform:scale(.97,.9)}
  60%{font-variation-settings:'SOFT' 100,'WONK' 1,'opsz' 144;font-weight:960;transform:scale(1.01,1.03)}
  100%{font-variation-settings:'SOFT' 100,'WONK' 1,'opsz' 144;font-weight:900;transform:none}}

/* buttons: latex press */
.btn{min-height:48px;padding:0 22px;border-radius:999px;border:2px solid var(--borde);background:var(--card);color:var(--foreground);
  font-weight:700;font-size:15px;display:inline-flex;align-items:center;justify-content:center;gap:10px;
  transition:transform var(--settle) var(--ease-settle),background-color 140ms,box-shadow 140ms;box-shadow:0 4px 0 color-mix(in srgb,var(--borde) 55%,transparent)}
.btn:hover:not(:disabled){transform:translateY(-2px)}
.btn:active:not(:disabled){transform:translateY(3px) scale(1.04,.9);box-shadow:0 1px 0 color-mix(in srgb,var(--borde) 55%,transparent);transition-duration:var(--press);transition-timing-function:var(--ease-press)}
.btn.primary{background:var(--acento);color:var(--sobre-acento);border-color:var(--acento);box-shadow:0 4px 0 color-mix(in srgb,var(--acento) 55%,#000)}
.btn.primary:hover:not(:disabled){background:color-mix(in srgb,var(--acento) 88%,var(--texto))}
.btn.danger{background:var(--card);color:var(--error);border-color:var(--error)}
.btn.ghost{box-shadow:none}

/* fields */
.field{display:grid;gap:7px}.field label,.field>span{font-weight:700;font-size:14px}
.field small,.help{font-size:13px;color:var(--muted-foreground)}
.field input,.native{min-height:48px;border-radius:14px;border:2px solid var(--input)!important;background:var(--card);color:var(--foreground);padding:0 14px;font-size:15px}
.native{width:100%;appearance:auto}
.field input[aria-invalid]{border-color:var(--error)!important}
.form-stack{display:grid;gap:18px}

/* public pages: the board */
.board-page{min-height:calc(100svh - var(--mockup-bar-h,0px));display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,.95fr);gap:48px;padding:40px 56px 56px;align-items:start}
.board-brand{display:flex;align-items:center;gap:12px;font-weight:800;font-size:22px;letter-spacing:-.02em}
.board-copy{display:grid;gap:22px;padding-top:24px}
.board-copy .lede{max-width:40ch;color:var(--sobre-tablero-suave);font-size:17px}
.ring-mark{width:30px;height:30px}
.balloon-cluster{width:min(100%,380px);height:250px;overflow:visible;margin-top:8px}
.balloon{transform-box:fill-box;transform-origin:50% 100%;animation:bob 5.4s ease-in-out infinite}
.balloon:nth-of-type(2){animation-duration:6.2s;animation-delay:-1.6s}.balloon:nth-of-type(3){animation-duration:4.8s;animation-delay:-3s}
@keyframes bob{0%,100%{transform:translateY(0) rotate(-2.5deg)}50%{transform:translateY(-9px) rotate(2.5deg)}}
.paused .balloon,[data-page-hidden] .balloon{animation-play-state:paused}
.hang{position:relative;padding-top:54px;justify-self:center;width:min(100%,460px)}
.hook{position:absolute;top:0;left:50%;width:34px;height:96px;margin-left:-17px;z-index:2;pointer-events:none}
.pass{position:relative;background:var(--superficie);color:var(--texto);border:2px solid var(--borde);border-radius:28px 28px 34px 34px;padding:44px 32px 28px;
  transform-origin:50% 0;animation:swing var(--swing) ease-in-out both;box-shadow:0 18px 0 -8px color-mix(in srgb,#000 22%,transparent)}
.eyelet{position:absolute;top:14px;left:50%;width:26px;height:26px;margin-left:-13px;border-radius:50%;border:3px solid var(--borde);background:var(--tablero)}
@keyframes swing{0%{transform:rotate(-7deg)}28%{transform:rotate(4.5deg)}52%{transform:rotate(-2.2deg)}74%{transform:rotate(1deg)}100%{transform:rotate(0)}}
.pass h2{font-size:32px;line-height:1.1}.pass .intro{color:var(--texto-suave);margin:8px 0 24px}
.pass-footer{margin-top:22px;padding-top:16px;border-top:2px dashed var(--borde);font-size:13px;color:var(--texto-suave)}
.notice{border:2px solid var(--borde);border-radius:16px;padding:18px;background:var(--superficie-2);max-height:260px;overflow:auto;display:grid;gap:12px}
.notice h3{font-size:16px}.notice p{font-size:14px}
.check-line{display:flex;gap:12px;align-items:flex-start;font-size:14px;font-weight:600}
.check-line [role=checkbox]{margin-top:2px;width:22px;height:22px;border:2px solid var(--borde)!important;border-radius:7px;background:var(--card)}
.check-line [role=checkbox][data-checked],.check-line [role=checkbox][aria-checked=true]{background:var(--acento)!important;border-color:var(--acento)!important;color:var(--sobre-acento)!important}

/* signed-in shell */
.shell{min-height:calc(100svh - var(--mockup-bar-h,0px));padding:28px 56px 48px}
.shell-inner{max-width:1180px;margin:0 auto}
.mast{display:flex;align-items:center;justify-content:space-between;gap:24px}
.wordmark{display:flex;align-items:center;gap:12px;font-weight:800;font-size:24px;letter-spacing:-.02em}
.rail{position:relative;display:flex;gap:28px;align-items:flex-start;margin:22px 0 34px;padding:0 24px;height:96px}
.rail:before{content:"";position:absolute;left:0;right:0;top:0;height:8px;border-radius:8px;background:var(--cordel)}
.hook-tab{position:relative;margin-top:8px;padding-top:30px;background:none;border:0;color:var(--texto);transition:transform var(--settle) var(--ease-settle)}
.hook-tab:before{content:"";position:absolute;top:0;left:50%;width:4px;height:30px;margin-left:-2px;background:var(--acento);border-radius:4px}
.hook-tab span{display:inline-flex;align-items:center;gap:10px;min-height:46px;padding:0 20px;border-radius:14px 14px 22px 22px;border:2px solid var(--borde);background:var(--card);font-weight:700}
.hook-tab:hover{transform:rotate(-3deg)}
.hook-tab[aria-current=page]{transform:translateY(10px)}
.hook-tab[aria-current=page] span{background:var(--acento);color:var(--sobre-acento);border-color:var(--acento)}
.account{position:relative}
.account-tag{display:flex;align-items:center;gap:12px;min-height:52px;padding:6px 18px 6px 8px;border-radius:999px;border:2px solid var(--borde);background:var(--card);color:var(--texto);text-align:left}
.account-tag .dot{width:36px;height:36px;border-radius:50%;background:var(--acento);color:var(--sobre-acento);display:grid;place-items:center;font-weight:800}
.account-tag strong{display:block;font-size:14px}.account-tag small{display:block;font-size:12px;color:var(--texto-suave)}
.account-menu{position:absolute;right:16px;top:calc(100% + 14px);width:260px;padding:22px 18px 18px;border-radius:20px;border:2px solid var(--borde);background:var(--popover);z-index:30;
  transform-origin:85% -14px;animation:swing var(--swing) ease-in-out both;box-shadow:0 14px 28px #0003;display:grid;gap:10px}
.account-menu:before{content:"";position:absolute;top:-16px;right:44px;width:4px;height:16px;background:var(--acento);border-radius:4px}
.account-menu .btn{width:100%}
.heading{display:flex;justify-content:space-between;align-items:flex-end;gap:24px;margin-bottom:28px}
.heading p{margin-top:14px;max-width:56ch;color:var(--texto-suave);font-size:16px}
.sheet{background:var(--superficie);border:2px solid var(--borde);border-radius:28px;padding:28px}
.status-strip{display:flex;gap:14px;align-items:center;justify-content:space-between;border:2px solid var(--borde);border-radius:18px;padding:14px 18px;margin-bottom:22px;background:var(--superficie);
  animation:stamp var(--settle) var(--ease-settle) both}
.status-strip strong{display:block}.status-strip.success{border-color:var(--exito);background:var(--exito-suave)}.status-strip.error{border-color:var(--error);background:var(--error-suave)}
.status-strip>div{display:flex;gap:12px;align-items:flex-start}
@keyframes stamp{0%{transform:scale(1.05) rotate(-1.2deg)}60%{transform:scale(.985)}100%{transform:none}}

/* accounts: tags threaded on one cord */
.filters{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr) minmax(0,1fr);gap:18px;margin-bottom:26px}
.cord-list{position:relative;display:grid;gap:16px;padding-left:34px}
.cord-list:before{content:"";position:absolute;left:12px;top:-8px;bottom:-8px;width:4px;border-radius:4px;background:var(--cordel)}
.person-tag{position:relative;display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1.3fr) minmax(0,.8fr) auto;gap:18px;align-items:center;
  padding:20px 22px 20px 34px;border:2px solid var(--borde);border-radius:14px 28px 28px 14px;background:var(--superficie);
  transform-origin:-22px 50%;animation:tag-drop var(--drop) var(--ease-settle) both;animation-delay:calc(var(--i,0)*var(--gap-i))}
.person-tag:before{content:"";position:absolute;left:-26px;top:50%;width:26px;height:4px;background:var(--cordel)}
.person-tag .eyelet-s{position:absolute;left:10px;top:50%;width:14px;height:14px;margin-top:-7px;border-radius:50%;border:3px solid var(--borde);background:var(--fondo)}
@keyframes tag-drop{0%{transform:translateY(-16px) rotate(-3deg)}55%{transform:translateY(3px) rotate(1.2deg)}100%{transform:none}}
.person-tag h2{font-size:19px;line-height:1.2;font-weight:700}.person-tag p,.person-tag .meta span{font-size:13px;color:var(--texto-suave)}
.person-tag .meta{display:grid;gap:2px}.person-tag .meta strong{font-size:14px}
.status{display:inline-flex;gap:8px;align-items:center;font-weight:700;font-size:14px}
.status i{width:12px;height:12px;border-radius:50%;background:var(--exito)}.status.invited i{background:var(--aviso)}.status.off i{background:transparent;border:2px solid var(--texto-suave)}
.empty{display:grid;gap:14px;justify-items:start;padding:12px 4px}.empty .actions{display:flex;gap:12px;flex-wrap:wrap}
.fineprint{margin-top:22px;font-size:13px;color:var(--texto-suave)}
.skeleton-list{display:grid;gap:16px}.skeleton-list [data-slot=skeleton]{height:76px;border-radius:14px 28px 28px 14px;background:var(--superficie-2)}

/* roles: one strip of board per role, permissions hang as tool tokens */
.role-board{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px}
.role-strip{border:2px solid var(--borde);border-radius:24px;background:var(--superficie);padding:22px;display:grid;gap:14px;grid-template-rows:auto auto 1fr auto}
.role-strip .tokens{align-content:start}
.role-strip .kind{font-size:13px;color:var(--texto-suave);font-weight:600}
.role-strip h2{font-size:22px;line-height:1.15}
.tokens{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0}
.tokens li{position:relative;padding:6px 12px 6px 22px;border-radius:999px;border:2px solid var(--borde);background:var(--superficie-2);font-size:13px;font-weight:600}
.tokens li:before{content:"";position:absolute;left:9px;top:50%;width:6px;height:6px;margin-top:-3px;border-radius:50%;background:var(--acento)}
.role-strip .actions{display:flex;gap:10px;flex-wrap:wrap}

/* own account */
.account-layout{display:grid;grid-template-columns:minmax(0,.85fr) minmax(0,1.15fr);gap:36px;align-items:start}
.own-pass{position:relative;padding-top:54px}
.account-layout>.sheet{margin-top:54px}
.own-pass .pass{animation-delay:120ms}
.own-pass dl{display:grid;gap:14px;margin-top:20px}.own-pass dt{font-size:13px;color:var(--texto-suave)}.own-pass dd{margin:0;font-weight:700}

/* dialogs */
.crew-dialog{border:2px solid var(--borde)!important;border-radius:26px!important;background:var(--popover)!important;color:var(--texto)!important;padding:28px!important;max-height:min(88svh,760px);overflow:auto;width:min(100vw - 32px,580px)!important;max-width:580px!important;display:grid;gap:18px}
.crew-dialog h2{font-size:26px;line-height:1.15}
.dialog-heading{display:flex;justify-content:space-between;gap:16px;align-items:flex-start}
.close-btn{width:44px;height:44px;border-radius:50%;border:2px solid var(--borde);background:var(--card);color:var(--texto);display:grid;place-items:center}
.actions{display:flex;gap:12px;flex-wrap:wrap}
.link-once{display:grid;gap:12px;border:2px dashed var(--acento);border-radius:18px;padding:18px;background:var(--acento-suave)}
.link-once code{font-size:13px;word-break:break-all;background:var(--superficie);border:2px solid var(--borde);border-radius:10px;padding:10px 12px;color:var(--texto)}
.perm-groups{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.perm-group{border:2px solid var(--borde);border-radius:18px;padding:14px;margin:0;display:grid;gap:10px;align-content:start}
.perm-group legend{padding:0 6px;font-weight:800;font-size:14px}
.peg-token{position:relative;display:flex;align-items:center;gap:10px;min-height:44px;padding:8px 12px;border-radius:12px;border:2px solid var(--borde);background:var(--superficie-2);font-size:14px;font-weight:600;
  transition:transform var(--settle) var(--ease-settle),background-color 160ms,border-color 160ms;cursor:pointer}
.peg-token:active{transform:scale(1.03,.9);transition-duration:var(--press)}
.peg-token.on{background:var(--acento-suave);border-color:var(--acento);transform:translateY(3px)}
.peg-token .peg{position:absolute;right:12px;top:-2px;width:4px;height:14px;border-radius:4px;background:var(--acento);transform:scaleY(0);transform-origin:top;transition:transform var(--settle) var(--ease-settle)}
.peg-token.on .peg{transform:scaleY(1)}
.peg-token [role=checkbox]{width:22px;height:22px;border:2px solid var(--borde)!important;border-radius:7px;background:var(--card)}
.peg-token [role=checkbox][data-checked]{background:var(--acento)!important;border-color:var(--acento)!important;color:var(--sobre-acento)!important}

@media(min-width:768px) and (max-width:1023px){
  .board-page{grid-template-columns:1fr;padding:32px 40px 48px;gap:24px}.balloon-cluster{display:none}
  .shell{padding:24px 32px 40px}.role-board{grid-template-columns:repeat(2,minmax(0,1fr))}
  .person-tag{grid-template-columns:minmax(0,1.4fr) minmax(0,1.2fr) auto}.person-tag .status{grid-column:2}.person-tag .btn{grid-row:1 / span 2;grid-column:3}
  .account-layout{grid-template-columns:1fr}.account-layout>.sheet{margin-top:0}}
@media(max-width:767px){
  .board-page{grid-template-columns:1fr;padding:24px 20px 40px;gap:20px}.board-copy{padding-top:0;gap:14px}.balloon-cluster{display:none}
  .display-title{font-size:46px}.pass{padding:40px 20px 22px}.pass h2{font-size:26px}
  .shell{padding:20px 20px 32px}.wordmark{font-size:20px}.account-tag{padding:4px 12px 4px 4px}.account-tag small{display:none}
  .rail{gap:14px;padding:0 6px;height:88px;margin-bottom:22px}.hook-tab span{padding:0 14px}
  .heading{flex-direction:column;align-items:stretch}.heading .btn{width:100%}
  .filters{grid-template-columns:1fr;gap:14px}.cord-list{padding-left:24px}.cord-list:before{left:6px}.person-tag:before{left:-18px;width:18px}
  .person-tag{grid-template-columns:1fr;gap:12px;padding:18px 18px 18px 30px}.person-tag .btn{width:100%}
  .role-board{grid-template-columns:1fr}.sheet{padding:20px}.account-layout{grid-template-columns:1fr;gap:20px}.account-layout>.sheet{margin-top:0}
  .crew-dialog{padding:20px!important}.perm-groups{grid-template-columns:1fr}.actions .btn{flex:1 1 100%}
  .account-menu{right:0}}

/* reduced motion and ?still=1: no travel, no ambient loop, final geometry at once */
[data-reduced-motion] *,[data-reduced-motion] *:before,[data-reduced-motion] *:after{animation:none!important;transition-duration:0ms!important}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition-duration:0ms!important}}
`;
const style = document.createElement("style");
style.textContent = css;
document.head.append(style);

const systemRoles = ["Usuario · Plan 1", "Usuario · Plan 2", "Usuario · Plan 3", "Empleado interno", "Administrador"];
const rolePermissions = [
  ["Chat asistido", "Contador de globos", "Catálogo"],
  ["Chat asistido", "Contador de globos", "Catálogo", "Calculadora de costos", "Explorar decoraciones"],
  ["Todo el Plan 2", "Taller 3D e IA de escena", "Planos, ficha de montaje y exportación", "Proyectos y decoraciones propios"],
  ["Todo el Plan 3", "Proyectos de todas las cuentas", "Consumo IA", "Herramientas internas"],
  ["Todo lo de Empleado interno", "Administrar cuentas", "Administrar roles", "Corregir textos en inglés"],
];
const permissionGroups: [string, string[]][] = [
  ["Asistencia", ["Chat asistido", "Contador de globos", "Calculadora de costos"]],
  ["Catálogo", ["Catálogo", "Explorar decoraciones"]],
  ["Taller y proyectos", ["Taller 3D", "Proyectos de todas las cuentas"]],
  ["Administración", ["Consumo IA", "Herramientas internas", "Administrar cuentas", "Administrar roles", "Corregir textos en inglés"]],
];
const people = [
  { name: "Ana Ríos", email: "ana@globoyfiesta.co", company: "Globo y Fiesta", role: systemRoles[1], status: "Activa", last: "Hoy, 09:42", work: true },
  { name: "Camila Mesa", email: "camila@momentos.co", company: "Momentos", role: systemRoles[2], status: "Invitada", last: "Aún no entra", work: false },
  { name: "Julián Ortega", email: "julian@sempertex.example", company: "Sempertex", role: systemRoles[3], status: "Activa", last: "Ayer, 17:20", work: true },
  { name: "David Torres", email: "david@sempertex.example", company: "Sempertex", role: systemRoles[4], status: "Activa", last: "Hoy, 08:15", work: false },
  { name: "Lucía Vélez", email: "lucia@decorarte.co", company: "Decorarte", role: "Montaje de eventos", status: "Desactivada", last: "24 oct, 14:06", work: false },
];
type Person = (typeof people)[number];

const esNotice = "[RAZÓN SOCIAL DE SEMPERTEX] tratará tus datos personales —nombre, correo, empresa (si la indicas), el rol y el plan que te asignen, y las fechas de invitación, activación y último acceso— para darte acceso a Pictures durante el piloto, administrar tu cuenta y medir el uso de las herramientas, incluido el consumo de inteligencia artificial. Los proyectos y decoraciones que guardes quedan asociados a tu cuenta. Puedes conocer, actualizar, rectificar o pedir la supresión de tus datos, y revocar esta autorización, escribiendo a [CORREO PARA DERECHOS]. La política de tratamiento de datos está en [URL DE LA POLÍTICA]. Al activar tu cuenta declaras que leíste este aviso y autorizas el tratamiento descrito, conforme a la Ley 1581 de 2012.";
const enNotice = "[SEMPERTEX LEGAL NAME] will process your personal data —name, email, company (if you provide it), the role and plan assigned to you, and the dates of invitation, activation and last access— to give you access to Pictures during the pilot, manage your account and measure the use of the tools, including artificial-intelligence usage. The projects and decorations you save are linked to your account. You can access, update, correct or request deletion of your data, and withdraw this authorization, by writing to [RIGHTS CONTACT EMAIL]. The data-processing policy is at [POLICY URL]. By activating your account you confirm that you have read this notice and authorize the processing described, under Colombian Law 1581 of 2012.";

function Btn({ children, variant = "secondary", className = "", ...props }: React.ComponentProps<typeof Button> & { variant?: "primary" | "secondary" | "danger" | "ghost" }) {
  return <Button {...props} className={`btn ${variant} ${className}`}>{children}</Button>;
}

function Field({ id, label, type = "text", hint, disabled, value, onChange, required = true, name }: { id: string; label: string; type?: string; hint?: string; disabled?: boolean; value?: string; onChange?: (v: string) => void; required?: boolean; name?: string }) {
  const auto = type === "password" ? (id.includes("current") || id === "password" ? "current-password" : "new-password") : type === "email" ? "email" : undefined;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <Input id={id} name={name ?? id} type={type} required={required} disabled={disabled} minLength={type === "password" ? 8 : undefined} autoComplete={auto}
        aria-describedby={hint ? `${id}-help` : undefined}
        {...(onChange ? { value: value ?? "", onChange: (e: React.ChangeEvent<HTMLInputElement>) => onChange(e.target.value) } : { defaultValue: value })} />
      {hint && <small id={`${id}-help`}>{hint}</small>}
    </div>
  );
}

function RingMark() {
  return (
    <svg className="ring-mark" viewBox="0 0 30 30" aria-hidden="true">
      <circle cx="15" cy="15" r="11" fill="none" stroke="currentColor" strokeWidth="4" />
      <circle cx="15" cy="15" r="3.5" fill="var(--acento)" />
    </svg>
  );
}

function Hook() {
  return (
    <svg className="hook" viewBox="0 0 34 96" aria-hidden="true">
      <rect x="9" y="0" width="16" height="10" rx="4" fill="var(--cordel)" />
      <path d="M17 10v66c0 11 -11 11 -11 1" fill="none" stroke="var(--acento)" strokeWidth="5" strokeLinecap="round" />
    </svg>
  );
}

function Balloons() {
  const ref = useRef<SVGSVGElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el || !("IntersectionObserver" in window)) return;
    const io = new IntersectionObserver(([e]) => el.classList.toggle("paused", !e.isIntersecting));
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <svg ref={ref} className="balloon-cluster" viewBox="0 0 380 250" aria-hidden="true">
      <path d="M40 6h300" stroke="var(--perfo)" strokeWidth="8" strokeLinecap="round" />
      <g className="balloon"><path d="M92 6v40" stroke="var(--sobre-tablero-suave)" strokeWidth="2" /><ellipse cx="92" cy="112" rx="52" ry="64" fill="var(--globo-a)" /><path d="M66 78q-12 20 -4 40" stroke="#fff" strokeOpacity=".7" strokeWidth="8" fill="none" strokeLinecap="round" /><path d="m86 176h12l-6 10z" fill="var(--globo-a)" /></g>
      <g className="balloon"><path d="M196 6v20" stroke="var(--sobre-tablero-suave)" strokeWidth="2" /><ellipse cx="196" cy="96" rx="46" ry="58" fill="var(--globo-b)" /><path d="M174 66q-10 18 -3 34" stroke="#fff" strokeOpacity=".7" strokeWidth="7" fill="none" strokeLinecap="round" /><path d="m190 154h12l-6 10z" fill="var(--globo-b)" /></g>
      <g className="balloon"><path d="M294 6v54" stroke="var(--sobre-tablero-suave)" strokeWidth="2" /><ellipse cx="294" cy="134" rx="44" ry="56" fill="var(--globo-c)" /><path d="M274 106q-9 16 -3 30" stroke="var(--globo-a)" strokeOpacity=".5" strokeWidth="6" fill="none" strokeLinecap="round" /><path d="m288 190h12l-6 10z" fill="var(--globo-c)" /></g>
    </svg>
  );
}

function Notice({ accepted, setAccepted, disabled }: { accepted: boolean; setAccepted: (v: boolean) => void; disabled: boolean }) {
  const [language, setLanguage] = useState(navigator.language.startsWith("en") ? "en" : "es");
  const es = language === "es";
  return (
    <>
      <div className="field">
        <label htmlFor="notice-lang">Idioma del aviso / Notice language</label>
        <select id="notice-lang" className="native" value={language} onChange={(e) => { setLanguage(e.target.value); setAccepted(false); }}>
          <option value="es">Español</option>
          <option value="en">English</option>
        </select>
      </div>
      <section className="notice" lang={language} tabIndex={0} aria-label={es ? "Texto del aviso" : "Notice text"}>
        <h3>{es ? "Aviso de tratamiento de datos personales" : "Personal data notice"} · v1</h3>
        <p>{es ? esNotice : enNotice}</p>
        <p><strong>{es ? "Borrador · campos entre corchetes pendientes de revisión legal." : "Draft · bracketed fields pending legal review."}</strong></p>
      </section>
      <label className="check-line" lang={language}>
        <Checkbox checked={accepted} onCheckedChange={(v) => setAccepted(v === true)} disabled={disabled} />
        <span>{es ? "He leído el aviso v1 y autorizo el tratamiento descrito." : "I have read notice v1 and authorize the processing described."}</span>
      </label>
    </>
  );
}

function Screen() {
  const m = useMockup();
  const profile = useMotionProfile();
  const [menu, setMenu] = useState(false);
  const [accepted, setAccepted] = useState(false);
  const [query, setQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [records, setRecords] = useState(people);
  const [selected, setSelected] = useState<Person>(people[0]);
  const [chosenRole, setChosenRole] = useState(people[0].role);
  const [message, setMessage] = useState("");
  const [once, setOnce] = useState("");
  const [copied, setCopied] = useState(false);
  const [typed, setTyped] = useState("");
  const [roleName, setRoleName] = useState("Montaje de eventos");
  const [permissions, setPermissions] = useState<string[]>(["Chat asistido", "Taller 3D"]);
  const [readonly, setReadonly] = useState(false);
  const [roleIndex, setRoleIndex] = useState(0);
  const [deleteRole, setDeleteRole] = useState(false);
  const [customRoles, setCustomRoles] = useState(["Montaje de eventos"]);
  const [localError, setLocalError] = useState("");
  const opener = useRef<HTMLElement | null>(null);

  const signed = ["cuenta", "cuentas", "roles", "aviso"].includes(m.view);
  const busy = ["loading", "pending", "disabled", "offline"].includes(m.state);
  const denied = m.state === "permission-denied" && ["cuentas", "roles"].includes(m.view);
  const allRoles = [...systemRoles, ...customRoles];

  useEffect(() => {
    const hidden = () => document.documentElement.toggleAttribute("data-page-hidden", document.hidden);
    document.addEventListener("visibilitychange", hidden);
    return () => document.removeEventListener("visibilitychange", hidden);
  }, []);
  useEffect(() => {
    if (m.scene) { setOnce(""); setCopied(false); setTyped(""); setMessage(""); setLocalError(""); }
  }, [m.scene]);
  useEffect(() => {
    if (!menu) return;
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") { setMenu(false); document.getElementById("account-tag")?.focus(); } };
    document.addEventListener("keydown", esc);
    return () => document.removeEventListener("keydown", esc);
  }, [menu]);

  const scene = (v: string) => { opener.current = document.activeElement as HTMLElement; m.set("scene", v); };
  const close = () => { m.set("scene", ""); setTimeout(() => opener.current?.focus(), 0); };
  const notify = (text: string) => { setMessage(text); setLocalError(""); };

  function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (busy) return;
    const data = new FormData(e.currentTarget);
    const pw = data.get("new-password"), again = data.get("repeat-password");
    if (pw !== null && pw !== again) { setLocalError("Las contraseñas no coinciden. Revisa ambos campos."); return; }
    if ((m.view === "activar" || m.view === "aviso") && !accepted) return;
    if (m.view === "login") notify("Sesión iniciada · simulación. Vuelves a la página que pediste si tu rol la permite; si no, a tu primera herramienta, o a Mi cuenta.");
    else if (m.view === "activar") notify("Cuenta activada · simulación. Entras con sesión abierta a la primera herramienta de tu rol.");
    else if (m.view === "cuenta") notify("Contraseña cambiada · simulación. Se cierran tus otras sesiones y este navegador recibe una sesión nueva.");
    else if (m.view === "restablecer") notify("Contraseña restablecida · simulación. Se cerraron las sesiones anteriores. Ya puedes iniciar sesión.");
    else notify("Aviso v1 aceptado · simulación. Se guardan la versión y la fecha; sigues a la página que pediste.");
  }

  const titles: Record<string, [string, string]> = {
    login: ["Cuelga tu pase.", "Entra con el correo de tu invitación. Pictures es un piloto cerrado de Sempertex."],
    activar: ["Tu pase ya tiene nombre.", "Te invitaron a Pictures. Elige tu contraseña y acepta el aviso de datos."],
    restablecer: ["Un gancho nuevo.", "Tu administrador generó este enlace para que elijas otra contraseña."],
    aviso: ["Antes de seguir.", "El aviso de datos cambió. Acepta la versión vigente para abrir cualquier otra página."],
    cuenta: ["Tu pase.", "Revisa tu acceso y cambia tu contraseña."],
    cuentas: ["El equipo.", "Invita personas y decide con qué rol entra cada una."],
    roles: ["Roles.", "Cada rol cuelga las herramientas que una persona puede usar."],
  };

  function banner() {
    if (message) return <div className="status-strip success" role="status"><div><Check size={22} /><span><strong>Listo</strong>{message}</span></div></div>;
    if (localError) return <div className="status-strip error" role="alert"><div><X size={22} /><span>{localError}</span></div></div>;
    const map: Record<string, [string, string]> = {
      error: m.view === "login"
        ? ["No pudimos iniciar sesión.", "El correo o la contraseña no son válidos, o la cuenta no puede entrar. Tras varios intentos fallidos, espera quince minutos."]
        : ["No pudimos completar la operación.", "Tus datos siguen en pantalla. Reintenta en un momento."],
      success: ["Cambio guardado · simulación", "El resultado se muestra sin peticiones al servidor."],
      validation: ["Revisa los campos marcados.", "Todavía no se guardó nada."],
      disabled: ["Acción no disponible", "En este estado de ejemplo los controles están bloqueados."],
      offline: ["Sin conexión", "Puedes revisar esta copia. Para guardar o generar enlaces, vuelve a conectarte."],
      stale: ["Datos de hace un rato", "Actualiza antes de confirmar un cambio de acceso."],
      pending: ["Guardando…", "Espera la confirmación antes de compartir un enlace."],
      loading: ["Cargando", "Estamos colgando la información."],
    };
    const x = map[m.state];
    if (!x) return null;
    const bad = ["error", "validation"].includes(m.state);
    return (
      <div className={`status-strip ${bad ? "error" : m.state === "success" ? "success" : ""}`} role={bad ? "alert" : "status"}>
        <span><strong>{x[0]}</strong>{x[1]}</span>
        {["error", "offline", "stale"].includes(m.state) && <Btn onClick={() => m.set("state", "ready")}>{m.state === "stale" ? "Actualizar" : "Reintentar"}</Btn>}
      </div>
    );
  }

  function accessPass() {
    const activation = m.view === "activar", reset = m.view === "restablecer", notice = m.view === "aviso";
    const invalid = m.state === "expired" && (activation || reset);
    return (
      <div className="hang">
        <Hook />
        <section className="pass" aria-labelledby="pass-title">
          <span className="eyelet" aria-hidden="true" />
          <h2 id="pass-title" className="title-sm">{activation ? "Activa tu cuenta" : reset ? "Elige otra contraseña" : notice ? "Aviso de datos · v1" : "Entra a Pictures"}</h2>
          <p className="intro">{activation ? "Ana Ríos · ana@globoyfiesta.co" : reset ? "camila@momentos.co" : notice ? "Ana Ríos · versión anterior aceptada: v0" : "Usa el correo con el que te invitaron."}</p>
          {banner()}
          {invalid ? (
            <div className="form-stack" role="alert">
              <p><strong>Este enlace ya no sirve.</strong></p>
              <p>Ya se usó o venció. Pide a tu administrador un enlace nuevo.</p>
              <Btn onClick={() => m.set("view", "login")}>Ir a iniciar sesión</Btn>
            </div>
          ) : m.state === "loading" ? (
            <div className="form-stack" aria-label="Cargando formulario"><Skeleton style={{ height: 48 }} /><Skeleton style={{ height: 48 }} /><Skeleton style={{ height: 48 }} /></div>
          ) : (
            <form className="form-stack" onSubmit={submit} noValidate={m.state === "validation"}>
              {!notice && !reset && !activation && <Field id="login-email" type="email" label="Correo" value="ana@globoyfiesta.co" disabled={busy} />}
              {!notice && (
                <Field id={activation || reset ? "new-password" : "password"} name={activation || reset ? "new-password" : "password"} type="password"
                  label={activation || reset ? "Contraseña nueva" : "Contraseña"} hint={activation || reset ? "Mínimo 8 caracteres." : undefined} disabled={busy} />
              )}
              {(activation || reset) && <Field id="repeat-password" type="password" label="Repite la contraseña" disabled={busy} />}
              {(activation || notice) && <Notice accepted={accepted} setAccepted={setAccepted} disabled={busy} />}
              <Btn variant="primary" type="submit" disabled={busy || ((activation || notice) && !accepted)}>
                {activation ? "Activar cuenta" : reset ? "Guardar contraseña" : notice ? "Aceptar y continuar" : "Entrar"}<ArrowRight size={18} />
              </Btn>
              {(activation || notice) && !accepted && <p className="help">Marca la casilla del aviso para continuar.</p>}
            </form>
          )}
          <footer className="pass-footer">
            {activation ? "Enlace de invitación de un solo uso." : reset ? "Enlace de restablecimiento de un solo uso." : notice ? "Mientras no aceptes, solo puedes cerrar sesión." : "¿Sin acceso u olvidaste la contraseña? Pide un enlace a tu administrador. No hay registro abierto."}
          </footer>
        </section>
      </div>
    );
  }

  function publicPage() {
    return (
      <div className="board board-page">
        <section className="board-copy">
          <div className="board-brand"><RingMark />Pictures</div>
          <h1 className="display-title">{titles[m.view][0]}</h1>
          <p className="lede">{titles[m.view][1]}</p>
          <Balloons />
        </section>
        {accessPass()}
      </div>
    );
  }

  function accounts() {
    const filtered = records.filter((p) => (!query || `${p.name} ${p.email}`.toLowerCase().includes(query.toLowerCase())) && (!roleFilter || p.role === roleFilter) && (!statusFilter || p.status === statusFilter));
    const filteredOut = !!(query || roleFilter || statusFilter);
    return (
      <section className="sheet" aria-label="Cuentas">
        <div className="filters">
          <div className="field"><label htmlFor="account-search">Buscar por nombre o correo</label><Input id="account-search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="ana@…" /></div>
          <div className="field"><label htmlFor="role-filter">Rol</label><select className="native" id="role-filter" value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}><option value="">Todos los roles</option>{allRoles.map((r) => <option key={r}>{r}</option>)}</select></div>
          <div className="field"><label htmlFor="status-filter">Estado</label><select className="native" id="status-filter" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}><option value="">Todos los estados</option>{["Activa", "Invitada", "Desactivada"].map((s) => <option key={s}>{s}</option>)}</select></div>
        </div>
        {m.state === "loading" ? (
          <div className="skeleton-list" aria-label="Cargando cuentas"><Skeleton /><Skeleton /><Skeleton /></div>
        ) : m.state === "empty" || !filtered.length ? (
          <div className="empty">
            <h2 className="title-sm" style={{ fontSize: 26 }}>{filteredOut ? "Nadie cuelga con esos filtros." : "Todavía no hay nadie más."}</h2>
            <p>{filteredOut ? "Cambia la búsqueda o limpia los filtros." : "Invita a la primera persona y elige su rol."}</p>
            <div className="actions">
              {filteredOut && <Btn onClick={() => { setQuery(""); setRoleFilter(""); setStatusFilter(""); }}>Limpiar filtros</Btn>}
              <Btn variant="primary" onClick={() => scene("invitar")}><Plus size={18} />Invitar persona</Btn>
            </div>
          </div>
        ) : (
          <ul className="cord-list" style={{ listStyle: "none", margin: 0 }}>
            {filtered.map((p, i) => (
              <li className="person-tag" style={{ "--i": i } as React.CSSProperties} key={p.email}>
                <span className="eyelet-s" aria-hidden="true" />
                <div><h2>{p.name}</h2><p>{p.email}</p><p>{p.company}</p></div>
                <div className="meta"><strong>{p.role}</strong><span>Último acceso: {p.last}</span></div>
                <div className={`status ${p.status === "Desactivada" ? "off" : p.status === "Invitada" ? "invited" : ""}`}><i aria-hidden="true" />{p.status}</div>
                <Btn disabled={busy} onClick={() => { setSelected(p); setChosenRole(p.role); scene("gestionar"); }} aria-label={`Gestionar a ${p.name}`}>Gestionar<ArrowRight size={18} /></Btn>
              </li>
            ))}
          </ul>
        )}
        <p className="fineprint">Datos ilustrativos: {records.length} cuentas de ejemplo; los filtros operan sobre esta muestra.</p>
      </section>
    );
  }

  function roles() {
    return (
      <section aria-label="Roles">
        {m.state === "loading" ? (
          <div className="role-board" aria-label="Cargando roles"><Skeleton style={{ height: 220, borderRadius: 24 }} /><Skeleton style={{ height: 220, borderRadius: 24 }} /><Skeleton style={{ height: 220, borderRadius: 24 }} /></div>
        ) : (
          <div className="role-board">
            {systemRoles.map((r, i) => (
              <article className="role-strip" key={r}>
                <span className="kind">Rol de sistema · solo lectura</span>
                <h2 className="title-sm">{r}</h2>
                <ul className="tokens">{rolePermissions[i].map((p) => <li key={p}>{p}</li>)}</ul>
                <div className="actions"><Btn onClick={() => { setReadonly(true); setRoleIndex(i); setRoleName(r); scene("rol"); }}><ShieldCheck size={18} />Ver permisos</Btn></div>
              </article>
            ))}
            {m.state === "empty" ? (
              <article className="role-strip">
                <span className="kind">Roles propios</span>
                <h2 className="title-sm">Aún no hay roles propios.</h2>
                <p>Crea uno eligiendo herramientas; necesita al menos un permiso.</p>
                <div className="actions"><Btn variant="primary" onClick={() => { setReadonly(false); setRoleName(""); setPermissions([]); scene("rol"); }}><Plus size={18} />Crear rol</Btn></div>
              </article>
            ) : customRoles.map((r) => (
              <article className="role-strip" key={r}>
                <span className="kind">Rol propio · 1 cuenta asignada</span>
                <h2 className="title-sm">{r}</h2>
                <ul className="tokens"><li>Chat asistido</li><li>Taller 3D</li></ul>
                <div className="actions">
                  <Btn disabled={busy} onClick={() => { setReadonly(false); setRoleName(r); scene("rol"); }}>Editar permisos</Btn>
                  <Btn variant="danger" disabled={busy} onClick={() => { setDeleteRole(true); scene("eliminar"); }}>Eliminar rol</Btn>
                </div>
              </article>
            ))}
          </div>
        )}
        <p className="fineprint">Los cinco roles de sistema no se editan ni se eliminan. Un rol con cuentas asignadas no se puede eliminar.</p>
      </section>
    );
  }

  function ownAccount() {
    return (
      <div className="account-layout">
        <div className="own-pass">
          <Hook />
          <section className="pass" aria-labelledby="own-title">
            <span className="eyelet" aria-hidden="true" />
            <h2 id="own-title" className="title-sm">David Torres</h2>
            <p className="intro" style={{ marginBottom: 0 }}>david@sempertex.example</p>
            <dl>
              <div><dt>Empresa</dt><dd>Sempertex</dd></div>
              <div><dt>Rol</dt><dd>Administrador</dd></div>
              <div><dt>Aviso de datos aceptado</dt><dd>v1 · 27 oct 2026, 09:40</dd></div>
            </dl>
            <footer className="pass-footer">Tu rol y tu empresa los cambia un administrador.</footer>
          </section>
        </div>
        <section className="sheet" aria-labelledby="pw-title">
          <h2 id="pw-title" className="title-sm" style={{ fontSize: 28 }}>Cambiar contraseña</h2>
          <p className="help" style={{ margin: "8px 0 22px" }}>Al cambiarla se cierran todas tus sesiones y este navegador recibe una nueva.</p>
          {m.state === "loading" ? (
            <div className="form-stack"><Skeleton style={{ height: 48 }} /><Skeleton style={{ height: 48 }} /><Skeleton style={{ height: 48 }} /></div>
          ) : (
            <form className="form-stack" onSubmit={submit}>
              <Field id="current-password" type="password" label="Contraseña actual" disabled={busy} />
              <Field id="own-new" name="new-password" type="password" label="Contraseña nueva" hint="Mínimo 8 caracteres." disabled={busy} />
              <Field id="own-repeat" name="repeat-password" type="password" label="Repite la contraseña nueva" disabled={busy} />
              <div className="actions"><Btn type="submit" variant="primary" disabled={busy}><KeyRound size={18} />Cambiar contraseña</Btn></div>
            </form>
          )}
        </section>
      </div>
    );
  }

  const trapped = (e: React.KeyboardEvent) => {
    if (e.key !== "Tab") return;
    const nodes = Array.from(e.currentTarget.querySelectorAll<HTMLElement>("button:not([disabled]),input:not([disabled]),select:not([disabled]),[role=checkbox]:not([data-disabled]),a[href]")).filter((x) => x.getBoundingClientRect().height > 0);
    const first = nodes[0], last = nodes[nodes.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus(); }
  };
  const lastAdmin = selected.role === "Administrador";
  const blockedDelete = deleteRole || selected.work || lastAdmin;
  async function copyLink() {
    try { await navigator.clipboard.writeText(once); setCopied(true); }
    catch { setLocalError("No se pudo copiar solo. Selecciona el enlace y cópialo."); }
  }
  const makeLink = (kind: string) => { setOnce(`https://pictures.example/${kind}/DEMO-NO-VALIDO`); setCopied(false); setMessage(""); };
  const linkBlock = (kind: string) => (
    <motion.div className="link-once" initial={profile.reduced ? false : { y: -14, rotate: -1.5 }} animate={{ y: 0, rotate: 0 }} transition={profile.reduced ? { duration: 0 } : profile.spring}>
      <strong>{kind} · simulación</strong>
      <p>Se muestra una sola vez: cópialo antes de cerrar. Los enlaces anteriores sin usar de este tipo dejan de servir.</p>
      <code>{once}</code>
      <div className="actions"><Btn variant="primary" onClick={copyLink}>{copied ? <Check size={18} /> : <Copy size={18} />}{copied ? "Copiado" : "Copiar enlace"}</Btn></div>
      <p className="help">Ejemplo no válido; no abre ni activa una cuenta real.</p>
    </motion.div>
  );

  const dialogTitle = m.scene === "invitar" ? "Invitar persona" : m.scene === "gestionar" ? selected.name : readonly ? "Permisos del rol" : roleName ? "Editar rol" : "Crear rol";
  const dialogText = m.scene === "invitar" ? "Pictures no envía correos: copias el enlace y lo compartes tú."
    : m.scene === "gestionar" ? `${selected.email} · ${selected.company}`
    : readonly ? `${roleName}: rol de sistema, sus permisos no se editan.` : "Elige al menos un permiso. Están agrupados por herramienta.";

  const shell = (
    <div className="pegs shell">
      <div className="shell-inner">
        <header className="mast">
          <div className="wordmark"><RingMark />Pictures</div>
          <div className="account">
            <button id="account-tag" className="account-tag" aria-expanded={menu} aria-controls="account-menu" onClick={() => setMenu(!menu)}>
              <span className="dot" aria-hidden="true">DT</span>
              <span><strong>David Torres</strong><small>Administrador</small></span>
            </button>
            {menu && (
              <div id="account-menu" className="account-menu" role="group" aria-label="Menú de cuenta">
                <strong>David Torres</strong>
                <span className="help">Administrador</span>
                <Btn disabled={m.view === "aviso"} onClick={() => { setMenu(false); m.set("view", "cuenta"); }}><Users size={18} />Mi cuenta</Btn>
                {m.view === "aviso" && <p className="help">Acepta el aviso para abrir otras páginas.</p>}
                <Btn onClick={() => { setMenu(false); m.set("view", "login"); }}><LogOut size={18} />Cerrar sesión</Btn>
              </div>
            )}
          </div>
        </header>
        {m.view !== "aviso" ? (
          <nav className="rail" aria-label="Administración">
            <button className="hook-tab" aria-current={m.view === "cuentas" ? "page" : undefined} onClick={() => m.set("view", "cuentas")}><span><Users size={18} />Cuentas</span></button>
            <button className="hook-tab" aria-current={m.view === "roles" ? "page" : undefined} onClick={() => m.set("view", "roles")}><span><ShieldCheck size={18} />Roles</span></button>
          </nav>
        ) : <div style={{ height: 34 }} />}
        <div className="heading">
          <div><h1 className="display-title">{titles[m.view][0]}</h1><p>{titles[m.view][1]}</p></div>
          {["cuentas", "roles"].includes(m.view) && !denied && (
            <Btn variant="primary" disabled={busy} onClick={() => { setReadonly(false); setRoleName(""); setPermissions([]); scene(m.view === "cuentas" ? "invitar" : "rol"); }}>
              <Plus size={18} />{m.view === "cuentas" ? "Invitar persona" : "Crear rol"}
            </Btn>
          )}
        </div>
        {m.view === "aviso" ? (
          <div style={{ maxWidth: 620 }}>{accessPass()}</div>
        ) : (
          <>
            {banner()}
            {denied ? (
              <section className="sheet empty" role="alert">
                <h2 className="title-sm" style={{ fontSize: 26 }}>No tienes permiso para abrir esta página.</h2>
                <p>Pide a un administrador el acceso que necesitas. Mi cuenta sigue disponible.</p>
                <Btn onClick={() => { m.set("view", "cuenta"); m.set("state", "ready"); }}>Ir a Mi cuenta</Btn>
              </section>
            ) : m.view === "cuentas" ? accounts() : m.view === "roles" ? roles() : ownAccount()}
          </>
        )}
        <p className="fineprint">Mockup · Tablero de ganchos / C · datos de ejemplo; no se envían solicitudes ni correos.</p>
      </div>
    </div>
  );

  return (
    <>
      {signed ? shell : publicPage()}
      <Dialog open={!!m.scene && m.scene !== "eliminar" && !denied} onOpenChange={(open) => { if (!open) close(); }}>
        <DialogContent className="crew-dialog" showCloseButton={false} onKeyDown={trapped}>
          <div className="dialog-heading">
            <div><DialogTitle className="title-sm">{dialogTitle}</DialogTitle><DialogDescription>{dialogText}</DialogDescription></div>
            <button className="close-btn" aria-label="Cerrar diálogo" onClick={close}><X size={20} /></button>
          </div>
          {localError && <div className="status-strip error" role="alert"><span>{localError}</span></div>}
          {message && <div className="status-strip success" role="status"><span>{message}</span></div>}

          {m.scene === "invitar" && (once ? linkBlock("Enlace de invitación") : (
            <form className="form-stack" onSubmit={(e) => {
              e.preventDefault();
              const d = new FormData(e.currentTarget);
              if (records.some((p) => p.email === d.get("invite-email"))) { setLocalError("Ese correo ya tiene cuenta. Búscalo en Cuentas."); return; }
              makeLink("activar");
            }}>
              <Field id="invite-name" label="Nombre" value="Mariana López" disabled={busy} />
              <Field id="invite-email" type="email" label="Correo" value={m.state === "validation" ? "ana@globoyfiesta.co" : "mariana@florece.co"} disabled={busy} />
              <Field id="invite-company" label="Empresa (opcional)" value="Florece Eventos" required={false} disabled={busy} />
              <div className="field"><label htmlFor="invite-role">Rol o plan de acceso</label><select id="invite-role" className="native" defaultValue={systemRoles[1]} disabled={busy}>{allRoles.map((r) => <option key={r}>{r}</option>)}</select></div>
              <p className="help">Generar otra invitación para esta persona invalida las anteriores sin usar.</p>
              <div className="actions"><Btn type="submit" variant="primary" disabled={busy}>Generar invitación<ArrowRight size={18} /></Btn><Btn variant="ghost" type="button" onClick={close}>Cancelar</Btn></div>
            </form>
          ))}

          {m.scene === "gestionar" && (
            <div className="form-stack">
              <p><strong>{selected.status}</strong> · Último acceso: {selected.last}</p>
              <div className="field">
                <label htmlFor="assigned-role">Rol</label>
                <select id="assigned-role" className="native" value={chosenRole} onChange={(e) => setChosenRole(e.target.value)} disabled={busy || lastAdmin}>{allRoles.map((r) => <option key={r}>{r}</option>)}</select>
                {lastAdmin && <small>Es el último administrador: conserva su rol y su cuenta activa.</small>}
              </div>
              <div className="actions">
                <Btn variant="primary" disabled={busy || lastAdmin || m.state === "stale" || chosenRole === selected.role} onClick={() => { setRecords(records.map((p) => p.email === selected.email ? { ...p, role: chosenRole } : p)); setSelected({ ...selected, role: chosenRole }); notify("Rol cambiado · simulación. Su próxima petición ya usa los permisos nuevos."); }}>Guardar rol</Btn>
                <Btn disabled={busy || lastAdmin} onClick={() => { const status = selected.status === "Desactivada" ? "Activa" : "Desactivada"; setSelected({ ...selected, status }); setRecords(records.map((p) => p.email === selected.email ? { ...p, status } : p)); notify(status === "Activa" ? "Cuenta reactivada · simulación." : "Cuenta desactivada · simulación. Sus sesiones se cierran."); }}>{selected.status === "Desactivada" ? "Reactivar cuenta" : "Desactivar cuenta"}</Btn>
                <Btn disabled={busy} onClick={() => makeLink(selected.status === "Invitada" ? "activar" : "restablecer")}><KeyRound size={18} />{selected.status === "Invitada" ? "Nueva invitación" : "Enlace de restablecimiento"}</Btn>
              </div>
              {once && linkBlock(selected.status === "Invitada" ? "Enlace de invitación" : "Enlace de restablecimiento")}
              <p className="help">{selected.work ? "Tiene trabajo guardado: no se puede eliminar. Puedes desactivarla." : lastAdmin ? "No se puede eliminar al último administrador." : "Sin trabajo guardado: se puede eliminar escribiendo su correo. Su consumo IA se conserva sin datos personales."}</p>
              <div className="actions"><Btn variant="danger" onClick={() => { setDeleteRole(false); scene("eliminar"); }}>Eliminar cuenta…</Btn><Btn variant="ghost" onClick={close}>{once ? "Cerrar y ocultar enlace" : "Volver"}</Btn></div>
            </div>
          )}

          {m.scene === "rol" && (
            <form className="form-stack" onSubmit={(e) => {
              e.preventDefault();
              if (!permissions.length) { setLocalError("Un rol necesita al menos un permiso (ROL_SIN_PERMISOS)."); return; }
              if (roleName && !customRoles.includes(roleName)) setCustomRoles([...customRoles, roleName]);
              notify("Rol guardado · simulación. Sus cuentas usan los permisos nuevos en la próxima petición.");
            }}>
              <Field id="role-name" label="Nombre del rol" value={roleName} onChange={setRoleName} disabled={readonly || busy} />
              {readonly ? (
                <ul className="tokens">{rolePermissions[roleIndex].map((p) => <li key={p}>{p}</li>)}</ul>
              ) : (
                <div className="perm-groups">
                  {permissionGroups.map(([group, items]) => (
                    <fieldset className="perm-group" key={group}>
                      <legend>{group}</legend>
                      {items.map((p) => {
                        const on = permissions.includes(p);
                        return (
                          <label className={`peg-token ${on ? "on" : ""}`} key={p}>
                            <span className="peg" aria-hidden="true" />
                            <Checkbox checked={on} disabled={busy} onCheckedChange={(v) => setPermissions(v ? [...permissions, p] : permissions.filter((x) => x !== p))} />
                            <span>{p}</span>
                          </label>
                        );
                      })}
                    </fieldset>
                  ))}
                </div>
              )}
              <div className="actions">
                {!readonly && <Btn type="submit" variant="primary" disabled={busy}>Guardar rol</Btn>}
                <Btn variant="ghost" type="button" onClick={close}>{readonly ? "Cerrar" : "Cancelar"}</Btn>
              </div>
              {readonly && <p className="help">Los cinco roles de sistema son de solo lectura.</p>}
            </form>
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog open={m.scene === "eliminar" && !denied} onOpenChange={(open) => { if (!open) close(); }}>
        <AlertDialogContent className="crew-dialog" onKeyDown={trapped}>
          <AlertDialogTitle className="title-sm">{deleteRole ? "Este rol se queda" : blockedDelete ? "Esta cuenta se queda" : `Eliminar a ${selected.name}`}</AlertDialogTitle>
          <AlertDialogDescription>
            {deleteRole ? "Montaje de eventos tiene 1 cuenta asignada. Cambia esa cuenta a otro rol antes de eliminarlo."
              : selected.work ? "Tiene proyectos o decoraciones guardados (CUENTA_CON_TRABAJO). No se elimina ni cambia nada. Puedes desactivarla."
              : lastAdmin ? "Es el último administrador. Debe quedar al menos una cuenta administradora activa."
              : `Se elimina la cuenta. Su consumo IA se conserva como «Cuenta eliminada», sin nombre, correo ni empresa.`}
          </AlertDialogDescription>
          {!blockedDelete && <Field id="confirm-email" type="email" label="Escribe su correo para confirmar" value={typed} onChange={setTyped} hint={selected.email} />}
          <div className="actions">
            {!blockedDelete && <Btn variant="danger" disabled={typed !== selected.email || busy} onClick={() => { setRecords(records.filter((p) => p.email !== selected.email)); close(); notify("Cuenta eliminada · simulación. El consumo IA se conserva sin datos personales."); }}>Eliminar cuenta</Btn>}
            {selected.work && !deleteRole && <Btn onClick={() => { setRecords(records.map((p) => p.email === selected.email ? { ...p, status: "Desactivada" } : p)); close(); notify("Cuenta desactivada · simulación. Su trabajo se conserva."); }}>Desactivar cuenta</Btn>}
            <Btn variant="ghost" onClick={close}>{blockedDelete ? "Entendido" : "Cancelar"}</Btn>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

mountMockup(Screen, {
  title: "Pictures · Tablero de ganchos / C",
  motion: "expressive",
  views: [
    { id: "login", label: "Iniciar sesión" }, { id: "activar", label: "Activar invitación" }, { id: "restablecer", label: "Restablecer contraseña" },
    { id: "aviso", label: "Aceptar nuevo aviso" }, { id: "cuenta", label: "Mi cuenta" }, { id: "cuentas", label: "Administrar cuentas" }, { id: "roles", label: "Administrar roles" },
  ],
  states: [
    { id: "ready", label: "Listo" }, { id: "loading", label: "Cargando" }, { id: "empty", label: "Vacío" }, { id: "error", label: "Error" },
    { id: "success", label: "Éxito" }, { id: "validation", label: "Validación" }, { id: "disabled", label: "Deshabilitado" },
    { id: "permission-denied", label: "Sin permiso" }, { id: "stale", label: "Datos antiguos" }, { id: "offline", label: "Sin conexión" },
    { id: "expired", label: "Enlace inválido" }, { id: "pending", label: "Pendiente" },
  ],
  scenes: [
    { id: "", label: "Ninguno" }, { id: "invitar", label: "Invitar persona" }, { id: "gestionar", label: "Gestionar cuenta" },
    { id: "rol", label: "Permisos del rol" }, { id: "eliminar", label: "Eliminar" },
  ],
});
