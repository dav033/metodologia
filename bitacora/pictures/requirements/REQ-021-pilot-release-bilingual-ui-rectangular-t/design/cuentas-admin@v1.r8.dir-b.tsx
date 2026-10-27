// cuentas-admin@v1 · round 8 · direction B «Escenario de inflado» (exploration only, not the contract).
// A bottle-green event stage holds tethered latex; a helium-gauge needle is the navigation; working panels inflate
// from their knot corner and travel in the order of the gauge. Built from the installed shadcn/Base UI + Animate UI
// components; custom pieces: gauge navigation, letter inflation, balloon identifiers, ambient tethered balloons.
import * as React from "react";
import { motion, AnimatePresence } from "motion/react";
import "@fontsource-variable/unbounded";
import "@fontsource-variable/bricolage-grotesque";
import { ArrowRight, Check, ChevronDown, Copy, KeyRound, Link2, Lock, LogOut, Plus, Power, RotateCcw, Search, ShieldCheck, Trash2, TriangleAlert, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogContent, AlertDialogTitle, AlertDialogDescription } from "@/components/ui/alert-dialog";
import { mountMockup, useMockup } from "@kit/mockup";
import { useMotionProfile } from "@kit/motion";

/* ───────────────────────── tokens, shapes and motion language ───────────────────────── */
const CSS = `
:root{
  --display:"Unbounded Variable","Unbounded",system-ui,sans-serif;
  --text:"Bricolage Grotesque Variable","Bricolage Grotesque",system-ui,sans-serif;
  --bg:#eef2ec; --surface:#ffffff; --surface-2:#f3f7f2; --field:#ffffff;
  --ink:#10241b; --muted:#40534a; --line:#66796e; --rule:#cdd8d0;
  --stage:#123a2c; --stage-2:#0d2c21; --stage-ink:#f2f7f1; --stage-muted:#bcd2c4; --stage-line:#8fb3a0;
  --accent:#b23f08; --accent-hover:#953406; --accent-ink:#ffffff; --latex:#f76707; --latex-soft:#ffd9bd;
  --pill-on:#ff8f3f; --pill-on-ink:#1d0c02; --focus:#b23f08; --stage-focus:#ffc08f;
  --ok:#1b6a45; --ok-soft:#dff3e7; --warn:#835400; --warn-soft:#fff1d1; --bad:#b42318; --bad-soft:#fde8e5;
  --av-plan:#ffbf8f; --av-plan-ink:#3b1602; --av-int:#a8dcc0; --av-int-ink:#0c2b1f; --av-admin:#10241b; --av-admin-ink:#f2f7f1;
  --av-own:#f4d27a; --av-own-ink:#3a2a00; --av-off:#d5dcd7; --av-off-ink:#33433a;
  --shadow:0 1px 0 rgb(16 36 27 / .08), 0 18px 40px -24px rgb(16 36 27 / .45);
  --k:1; --elastic:cubic-bezier(.34,1.56,.64,1); --squeeze:cubic-bezier(.5,0,.2,1.4);
  --background:var(--bg); --foreground:var(--ink); --card:var(--surface); --card-foreground:var(--ink);
  --popover:var(--surface); --popover-foreground:var(--ink); --primary:var(--accent); --primary-foreground:var(--accent-ink);
  --secondary:var(--surface-2); --secondary-foreground:var(--ink); --muted-foreground:var(--muted);
  --accent-foreground:var(--ink); --destructive:var(--bad); --border:var(--line); --input:var(--line); --ring:var(--focus);
  color-scheme:light;
}
:root.dark{
  --bg:#0b1511; --surface:#13221b; --surface-2:#1a2c23; --field:#0f1c16;
  --ink:#eaf2ec; --muted:#a9beb2; --line:#829d8e; --rule:#2c4237;
  --stage:#0f2e22; --stage-2:#0a2219; --stage-ink:#eef6f0; --stage-muted:#b3cbbd; --stage-line:#8db39f;
  --accent:#ff8f3f; --accent-hover:#ffa560; --accent-ink:#1d0c02; --latex:#ff8f3f; --latex-soft:#4a2410;
  --pill-on:#ff8f3f; --pill-on-ink:#1d0c02; --focus:#ffb27a; --stage-focus:#ffc08f;
  --ok:#7bd7a6; --ok-soft:#123326; --warn:#f2c35f; --warn-soft:#33270b; --bad:#ff9a8f; --bad-soft:#3a1714;
  --av-plan:#ffb27a; --av-plan-ink:#2d1002; --av-int:#7bd7a6; --av-int-ink:#082016; --av-admin:#eaf2ec; --av-admin-ink:#10241b;
  --av-own:#f2c35f; --av-own-ink:#2a1e00; --av-off:#3a4a41; --av-off-ink:#e1e9e3;
  --shadow:0 1px 0 rgb(0 0 0 / .4), 0 22px 44px -24px rgb(0 0 0 / .8);
  color-scheme:dark;
}
:root[data-motion="natural"]{--k:.62}
:root[data-motion="subtle"]{--k:.36}

#app{background:var(--bg);color:var(--ink);font:400 15px/1.5 var(--text);font-variant-numeric:tabular-nums}
#app *,#app *::before,#app *::after,.dlg *{box-sizing:border-box}
.sr-only{position:absolute!important;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
#app :focus-visible,.dlg :focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.col :focus-visible,.stage :focus-visible{outline-color:var(--stage-focus)}

/* real components restyled into latex: pill buttons that squash on press, fields with a 1.5px edge */
#app [data-slot=button],.dlg [data-slot=button]{height:44px;border-radius:999px;padding:0 20px;gap:8px;font:600 15px/1 var(--text);
  transition:transform calc(var(--k)*260ms) var(--elastic),background-color 160ms ease,box-shadow 160ms ease,color 160ms ease}
#app [data-slot=button]:hover:not(:disabled),.dlg [data-slot=button]:hover:not(:disabled){transform:translateY(-2px)}
#app [data-slot=button]:active:not(:disabled),.dlg [data-slot=button]:active:not(:disabled){transform:scale(.95,.88);transition-duration:90ms}
[data-slot=button][data-variant=default]{background:var(--accent);color:var(--accent-ink)}
[data-slot=button][data-variant=default]:hover:not(:disabled){background:var(--accent-hover)}
[data-slot=button][data-variant=outline]{background:var(--surface);color:var(--ink);border:1.5px solid var(--line)}
[data-slot=button][data-variant=ghost]{background:transparent;color:var(--ink)}
[data-slot=button][data-variant=ghost]:hover:not(:disabled){background:var(--surface-2)}
[data-slot=button][data-variant=destructive]{background:var(--bad-soft);color:var(--bad);border:1.5px solid var(--bad)}
#app [data-slot=button]:disabled,.dlg [data-slot=button]:disabled{opacity:1;background:var(--surface-2);color:var(--muted);border:1.5px dashed var(--line)}
#app [data-slot=button].sm{height:36px;padding:0 14px;font-size:14px}
#app [data-slot=input],.dlg [data-slot=input]{height:46px;border-radius:14px;border:1.5px solid var(--line);background:var(--field);color:var(--ink);
  padding:0 14px;font:400 15px/1 var(--text);opacity:1;transition:border-color 160ms ease,box-shadow 200ms var(--elastic)}
#app [data-slot=input]:focus-visible,.dlg [data-slot=input]:focus-visible{outline:none;border-color:var(--focus);box-shadow:0 0 0 3px var(--focus)}
#app [data-slot=input][aria-invalid=true],.dlg [data-slot=input][aria-invalid=true]{border-color:var(--bad)}
#app [data-slot=input]:read-only{background:var(--surface-2)}
#app [data-slot=input]::placeholder,.dlg [data-slot=input]::placeholder{color:var(--muted)}
#app [data-slot=checkbox],.dlg [data-slot=checkbox]{width:22px;height:22px;border-radius:7px;border:1.5px solid var(--line);background:var(--field);flex:none;
  transition:transform calc(var(--k)*240ms) var(--elastic),background-color 140ms}
#app [data-slot=checkbox][data-checked],.dlg [data-slot=checkbox][data-checked]{background:var(--accent);border-color:var(--accent);color:var(--accent-ink);transform:scale(1.06)}
#app [data-slot=checkbox] svg{width:15px;height:15px}
#app [data-slot=skeleton]{background:var(--rule);border-radius:999px}
.native{position:relative;display:inline-flex;align-items:center}
.native select{appearance:none;height:44px;border-radius:999px;border:1.5px solid var(--line);background:var(--field);color:var(--ink);
  font:500 15px/1 var(--text);padding:0 40px 0 16px;min-width:0;width:100%}
.native svg{position:absolute;right:14px;pointer-events:none;width:16px;height:16px;color:var(--ink)}
.native select:focus-visible{outline:3px solid var(--focus);outline-offset:2px}

/* type: inflated display face for names of places, characterful grotesque for work */
.display{font-family:var(--display);font-weight:760;letter-spacing:-.025em;line-height:.98}
.word{display:inline-block;white-space:nowrap}
.ch{display:inline-block;transform-origin:50% 90%}
.lede{font-size:17px;line-height:1.5}
.meta{font-size:13px;color:var(--muted)}
.label{display:block;font:600 14px/1.3 var(--text);margin-bottom:8px}
.hint{font-size:13px;color:var(--muted);margin-top:6px}
.field{display:grid}

/* ambient latex: floats, tethers sway; paused offscreen, in hidden tabs and when motion is reduced */
.amb{position:absolute;pointer-events:none}
.balloon{position:absolute;border-radius:50% 50% 47% 53%/56% 56% 44% 44%;background:var(--latex);
  box-shadow:inset -10px -14px 0 rgb(0 0 0 / .12), inset 8px 8px 0 rgb(255 255 255 / .22)}
.balloon::after{content:"";position:absolute;left:50%;bottom:-7px;margin-left:-5px;border:5px solid transparent;border-bottom:7px solid currentColor;transform:rotate(180deg);color:inherit}
.balloon.b1{animation:floatA calc(9s / max(var(--k),.4)) ease-in-out infinite}
.balloon.b2{animation:floatB calc(11s / max(var(--k),.4)) ease-in-out infinite}
.balloon.b3{animation:floatA calc(13s / max(var(--k),.4)) ease-in-out -4s infinite}
.tether{position:absolute;width:1.5px;background:var(--stage-line);transform-origin:50% 0;animation:sway calc(7s / max(var(--k),.4)) ease-in-out infinite}
@keyframes floatA{0%,100%{transform:translate3d(0,0,0) rotate(-3deg)}50%{transform:translate3d(4px,-14px,0) rotate(3deg)}}
@keyframes floatB{0%,100%{transform:translate3d(0,-6px,0) rotate(4deg)}50%{transform:translate3d(-5px,8px,0) rotate(-2deg)}}
@keyframes sway{0%,100%{transform:rotate(-4deg)}50%{transform:rotate(4deg)}}
.paused .balloon,.paused .tether,:root[data-tab-hidden] .balloon,:root[data-tab-hidden] .tether{animation-play-state:paused}

/* state feedback */
@keyframes wobble{0%{transform:translateX(0)}18%{transform:translateX(-9px) rotate(-.6deg)}36%{transform:translateX(7px) rotate(.4deg)}54%{transform:translateX(-4px)}72%{transform:translateX(2px)}100%{transform:translateX(0)}}
@keyframes pop{0%{transform:scale(.62) rotate(-8deg)}60%{transform:scale(1.08) rotate(2deg)}100%{transform:scale(1) rotate(0)}}
@keyframes draw{from{stroke-dashoffset:30}to{stroke-dashoffset:0}}
@keyframes unroll{from{clip-path:inset(0 100% 0 0 round 14px)}to{clip-path:inset(0 0 0 0 round 14px)}}
@keyframes rise{0%{transform:translateY(46px) rotate(-1.6deg) scale(.96)}62%{transform:translateY(-6px) rotate(.5deg) scale(1.01)}100%{transform:none}}
@keyframes knot{0%,100%{transform:scale(1)}50%{transform:scale(1.18)}}
.note{display:flex;gap:12px;align-items:flex-start;border-radius:18px 18px 18px 6px;padding:14px 16px;border:1.5px solid;font-size:14px;line-height:1.45}
.note svg{flex:none;width:18px;height:18px;margin-top:2px}
.note strong{display:block;font-weight:650;margin-bottom:2px}
.note.bad{background:var(--bad-soft);border-color:var(--bad);color:var(--ink)}
.note.bad svg{color:var(--bad)}
.note.ok{background:var(--ok-soft);border-color:var(--ok);color:var(--ink)}
.note.ok svg{color:var(--ok)}
.note.warn{background:var(--warn-soft);border-color:var(--warn);color:var(--ink)}
.note.warn svg{color:var(--warn)}
.note.info{background:var(--surface-2);border-color:var(--line);color:var(--ink)}
.wobble{animation:wobble calc(var(--k)*560ms) cubic-bezier(.36,.07,.19,.97) both}
.pop{animation:pop calc(var(--k)*620ms) var(--elastic) both}
.seal{width:46px;height:46px;border-radius:50% 50% 47% 53%/56% 56% 44% 44%;background:var(--ok);color:var(--surface);display:grid;place-items:center;flex:none}
.seal path{stroke-dasharray:30;animation:draw calc(var(--k)*520ms) ease-out calc(var(--k)*220ms) both}

/* ───── public stage (sign-in, activation, reset, notice gate, invalid link) ───── */
.public{display:grid;grid-template-columns:minmax(0,1.08fr) minmax(0,1fr);min-height:calc(100svh - var(--mockup-bar-h,0px))}
.stage{position:relative;overflow:hidden;background:var(--stage);color:var(--stage-ink);padding:32px 48px 104px;display:flex;flex-direction:column;
  background-image:radial-gradient(120% 70% at 78% 0%,rgb(255 143 63 / .16),transparent 60%)}
.stage-top{display:flex;align-items:center;justify-content:space-between;gap:16px;position:relative;z-index:2}
.brand{display:inline-flex;align-items:center;gap:12px;font:700 17px/1 var(--display);letter-spacing:-.01em;color:inherit}
.brand-mark{width:30px;height:36px;position:relative}
.brand-mark .balloon{inset:0 0 6px 0;background:var(--pill-on);color:var(--pill-on)}
.brand small{display:block;font:500 12px/1.3 var(--text);letter-spacing:0;color:var(--stage-muted);margin-top:4px}
.stage .native select{background:var(--stage-2);color:var(--stage-ink);border-color:var(--stage-line);height:40px;font-size:14px}
.stage .native svg{color:var(--stage-ink)}
.stage .native span{font-size:13px;color:var(--stage-muted);margin-right:8px}
.stage-copy{margin-top:auto;position:relative;z-index:2;max-width:620px}
.stage-copy h1{font-size:clamp(34px,4.7vw,62px);margin:0 0 18px}
.stage-copy p{margin:0;color:var(--stage-muted);max-width:44ch}
.floor{position:absolute;left:0;right:0;bottom:0;height:72px;background:repeating-linear-gradient(90deg,var(--stage-2) 0 46px,transparent 46px 49px);
  border-top:2px solid var(--stage-line);transform-origin:50% 100%}
.cluster{right:9%;top:84px;width:240px;height:280px}
.cluster .balloon{color:var(--latex)}
.cluster .c2{background:#f2f7f1;color:#f2f7f1}
.cluster .c3{background:#ffb27a;color:#ffb27a}
.desk{display:flex;align-items:center;justify-content:center;padding:48px 40px}
.sheet{width:min(440px,100%);display:grid;gap:22px}
.sheet-card{background:var(--surface);border:1.5px solid var(--rule);border-radius:30px 30px 30px 8px;padding:32px;box-shadow:var(--shadow);display:grid;gap:20px;transform-origin:0 100%}
.sheet-card h2{margin:0;font:700 24px/1.15 var(--display);letter-spacing:-.02em}
.sheet-foot{font-size:14px;color:var(--muted);padding:0 4px}
.sheet-foot strong{color:var(--ink);font-weight:600}
.invitee{display:flex;align-items:center;gap:14px;border-radius:18px;background:var(--surface-2);padding:14px 16px}
.invitee b{display:block;font-weight:650}
.notice{border:1.5px solid var(--line);border-radius:18px;padding:16px;max-height:188px;overflow:auto;font-size:14px;line-height:1.55;background:var(--field)}
.notice h3{font:650 14px/1.3 var(--text);margin:0 0 8px}
.notice p{margin:0}
.notice mark{background:var(--warn-soft);color:var(--ink);border-bottom:1.5px dashed var(--warn);padding:0 2px}
.accept{display:flex;gap:12px;align-items:flex-start;font-size:15px;line-height:1.4;cursor:pointer}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.acct-chip{display:flex;align-items:center;gap:10px;border:1.5px solid var(--stage-line);border-radius:999px;padding:6px 6px 6px 14px;font-size:14px}
.acct-chip b{font-weight:650}

/* ───── signed-in shell: gauge column + inflating stage ───── */
.shell{display:grid;grid-template-columns:256px minmax(0,1fr);min-height:calc(100svh - var(--mockup-bar-h,0px))}
.col{position:sticky;top:var(--mockup-bar-h,0px);height:calc(100svh - var(--mockup-bar-h,0px));background:var(--stage);color:var(--stage-ink);
  display:flex;flex-direction:column;gap:24px;padding:28px 24px 24px;overflow:hidden;z-index:3}
.gauge-wrap{display:grid;gap:18px;position:relative;z-index:2}
.gauge{position:relative;width:176px;height:112px;margin:0 auto}
.gauge svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}
.needle{position:absolute;left:calc(50% - 3px);bottom:10px;width:6px;height:82px;border-radius:6px 6px 3px 3px;background:var(--pill-on);transform-origin:50% calc(100% - 3px)}
.hub{position:absolute;left:calc(50% - 11px);bottom:2px;width:22px;height:22px;border-radius:50%;background:var(--stage-ink);border:4px solid var(--stage-2);animation:knot calc(2.4s / max(var(--k),.4)) ease-in-out infinite}
.stops{display:grid;gap:6px;margin:0;padding:0;list-style:none}
.nav-stop{width:100%;display:flex;align-items:center;gap:12px;min-height:46px;padding:0 16px;border:0;border-radius:999px;background:transparent;color:var(--stage-ink);
  font:600 15px/1 var(--text);cursor:pointer;text-align:left;transition:transform calc(var(--k)*300ms) var(--elastic),background-color 160ms}
.nav-stop:hover{background:var(--stage-2);transform:translateX(5px)}
.nav-stop[aria-current=page]{background:var(--pill-on);color:var(--pill-on-ink)}
.nav-stop .tick{width:10px;height:10px;border-radius:50%;border:2px solid currentColor;flex:none}
.nav-stop[aria-current=page] .tick{background:currentColor}
.nav-stop .pos{margin-left:auto;font:500 12px/1 var(--text);opacity:1}
.col-amb{left:0;right:0;bottom:120px;height:200px;z-index:1}
.col .floor{height:44px}
.acct{position:relative;margin-top:auto;z-index:4}
.acct-btn{width:100%;display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:20px 20px 20px 6px;border:1.5px solid var(--stage-line);
  background:var(--stage-2);color:var(--stage-ink);font:inherit;text-align:left;cursor:pointer;transition:transform calc(var(--k)*260ms) var(--elastic)}
.acct-btn:hover{transform:translateY(-2px)}
.acct-btn b{display:block;font-weight:650;font-size:14px}
.acct-btn span.r{display:block;font-size:13px;color:var(--stage-muted)}
.acct-btn svg.chev{margin-left:auto;transition:transform calc(var(--k)*300ms) var(--elastic)}
.acct-btn[aria-expanded=true] svg.chev{transform:rotate(180deg)}
.menu{position:absolute;left:0;right:0;bottom:calc(100% + 10px);background:var(--surface);color:var(--ink);border:1.5px solid var(--rule);border-radius:22px 22px 22px 6px;
  box-shadow:var(--shadow);padding:16px;display:grid;gap:6px;transform-origin:20px 100%;z-index:20}
.menu-head{padding:4px 4px 12px;border-bottom:1px solid var(--rule);margin-bottom:6px}
.menu-head b{display:block;font-weight:650}
.menu-item{display:flex;align-items:center;gap:10px;min-height:44px;padding:0 12px;border-radius:999px;border:0;background:transparent;color:var(--ink);font:500 15px/1 var(--text);cursor:pointer;text-align:left}
.menu-item:hover{background:var(--surface-2)}
.menu-item:disabled{color:var(--muted);cursor:not-allowed}
.menu-item:disabled:hover{background:transparent}
.menu-why{font-size:13px;color:var(--muted);padding:0 12px 6px 40px}
.work{padding:36px 40px 56px;min-width:0}
.head{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;flex-wrap:wrap;margin-bottom:24px}
.head h1{font-size:46px;margin:0 0 10px}
.head .meta{font-size:14px}
.latex{background:var(--surface);border:1.5px solid var(--rule);border-radius:34px 34px 34px 8px;padding:24px;box-shadow:var(--shadow);transform-origin:0% 100%}
.filters{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr) minmax(0,1fr) auto;gap:12px;align-items:end;margin-bottom:12px}
.search{position:relative}
.search svg{position:absolute;left:14px;top:50%;margin-top:-9px;width:18px;height:18px;color:var(--muted);pointer-events:none}
#app .search [data-slot=input]{padding-left:42px}
.roster{width:100%;border-collapse:separate;border-spacing:0}
.roster th{font:500 13px/1.2 var(--text);color:var(--muted);text-align:left;padding:14px 12px 10px;border-bottom:1.5px solid var(--rule)}
.roster td{padding:14px 12px;border-bottom:1px solid var(--rule);vertical-align:middle;font-size:14px}
.roster td.c-act{text-align:right}
.person-row{transition:background-color 160ms}
.person-row:hover td{background:var(--surface-2)}
.person-row[data-open] td{background:var(--surface-2);border-bottom-color:transparent}
.who{display:flex;align-items:center;gap:14px;min-width:0}
.who b{display:block;font-weight:650;font-size:15px}
.who .meta{overflow-wrap:anywhere}
.av{position:relative;width:40px;height:46px;flex:none;border-radius:50% 50% 47% 53%/56% 56% 44% 44%;display:grid;place-items:center;font:700 13px/1 var(--display);
  margin-bottom:6px;transition:transform calc(var(--k)*360ms) var(--elastic)}
.av::after{content:"";position:absolute;left:50%;bottom:-6px;margin-left:-5px;border-left:5px solid transparent;border-right:5px solid transparent;border-top:7px solid;border-top-color:inherit}
.person-row:hover .av{transform:translateY(-4px) rotate(-4deg)}
.av.plan{background:var(--av-plan);color:var(--av-plan-ink);border-color:var(--av-plan)}
.av.int{background:var(--av-int);color:var(--av-int-ink);border-color:var(--av-int)}
.av.admin{background:var(--av-admin);color:var(--av-admin-ink);border-color:var(--av-admin)}
.av.own{background:var(--av-own);color:var(--av-own-ink);border-color:var(--av-own)}
.av.off{background:var(--av-off);color:var(--av-off-ink);border-color:var(--av-off)}
.av.inv{background:transparent;color:var(--ink);border:2px dashed var(--line)}
.av.inv::after{border-top-color:var(--line)}
.state{display:inline-flex;align-items:center;gap:8px;border:1.5px solid var(--rule);border-radius:999px;padding:6px 12px;font-size:13px;line-height:1.2;white-space:nowrap;background:var(--surface)}
.state i{width:9px;height:9px;border-radius:50%;flex:none}
.state.on i{background:var(--ok)}.state.off i{background:var(--muted)}.state.inv i{background:var(--warn)}
.tray-row td{padding:0 12px 14px;border-bottom:1px solid var(--rule)}
.tray{background:var(--surface-2);border-radius:0 0 26px 8px;padding:20px 20px 22px;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px;transform-origin:50% 0}
.tray h3{font:650 14px/1.3 var(--text);margin:0 0 6px}
.tray p{margin:0 0 12px;font-size:13px;color:var(--muted)}
.tray .act{display:flex;flex-direction:column;align-items:flex-start;min-width:0}
.tray .act .native,.tray .act .native select{width:100%}
.why{display:flex;gap:8px;align-items:flex-start;font-size:13px;color:var(--ink);background:var(--surface);border:1.5px dashed var(--line);border-radius:14px;padding:12px;margin-top:10px}
.why svg{flex:none;width:16px;height:16px;margin-top:1px;color:var(--warn)}
.toast{position:fixed;right:28px;bottom:28px;z-index:30;display:flex;gap:14px;align-items:center;max-width:420px;background:var(--surface);color:var(--ink);border:1.5px solid var(--ok);
  border-radius:24px 24px 24px 6px;padding:16px 18px;box-shadow:var(--shadow)}
.toast b{display:block;font-weight:650}
.empty{display:grid;justify-items:start;gap:14px;padding:28px 12px 12px}
.empty h2{font:700 24px/1.15 var(--display);margin:0;letter-spacing:-.02em}
.empty p{margin:0;color:var(--muted);max-width:52ch}
.empty .acts{display:flex;gap:10px;flex-wrap:wrap}
.sk-row{display:grid;grid-template-columns:40px 1.6fr 1fr 1fr .8fr 90px;gap:16px;align-items:center;padding:16px 12px;border-bottom:1px solid var(--rule)}

/* roles */
.roles{display:grid;grid-template-columns:300px minmax(0,1fr);gap:24px;align-items:start}
.rack{display:grid;gap:18px}
.rack h2{font:600 13px/1.2 var(--text);color:var(--muted);margin:0 0 8px}
.rack ul{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.role-btn{width:100%;display:flex;align-items:center;gap:12px;min-height:52px;padding:8px 16px;border-radius:999px;border:1.5px solid transparent;background:transparent;color:var(--ink);
  font:inherit;text-align:left;cursor:pointer;transition:transform calc(var(--k)*300ms) var(--elastic),background-color 160ms}
.role-btn:hover{background:var(--surface);transform:translateX(4px)}
.role-btn[aria-pressed=true]{background:var(--surface);border-color:var(--accent);box-shadow:var(--shadow)}
.role-btn b{font-weight:650;font-size:15px;display:block}
.role-btn .meta{display:block}
.role-btn svg{width:16px;height:16px;flex:none;color:var(--muted)}
.rack-empty{border:1.5px dashed var(--line);border-radius:22px 22px 22px 6px;padding:16px;font-size:14px;color:var(--muted)}
.editor{display:grid;gap:20px}
.editor-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap}
.editor-head h2{font:700 30px/1.1 var(--display);margin:0 0 6px;letter-spacing:-.02em}
.tools{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.tool{border:1.5px solid var(--rule);border-radius:22px 22px 22px 6px;padding:16px;display:grid;gap:10px;align-content:start;background:var(--surface);
  transition:border-color 160ms,transform calc(var(--k)*300ms) var(--elastic)}
.tool:hover{transform:translateY(-2px)}
.tool h3{font:650 15px/1.2 var(--text);margin:0}
.perm{display:flex;gap:12px;align-items:flex-start;font-size:14px;line-height:1.35;cursor:pointer}
.perm.ro{cursor:default}
.perm.ro svg{width:18px;height:18px;flex:none;margin-top:1px}
.perm.ro .yes{color:var(--ok)}.perm.ro .no{color:var(--muted)}
.perm small{display:block;color:var(--muted);font-size:12px;margin-top:2px}
.editor-foot{display:flex;gap:12px;flex-wrap:wrap;align-items:center;justify-content:space-between;border-top:1px solid var(--rule);padding-top:18px}

/* mi cuenta */
.mine{display:grid;grid-template-columns:minmax(0,.9fr) minmax(0,1.1fr);gap:24px;align-items:start}
.facts{display:grid;gap:0;margin:0}
.facts div{display:grid;grid-template-columns:120px 1fr;gap:12px;padding:12px 0;border-bottom:1px solid var(--rule)}
.facts dt{color:var(--muted);font-size:14px}.facts dd{margin:0;font-weight:550}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.chip{border:1.5px solid var(--rule);border-radius:999px;padding:6px 12px;font-size:13px}
.form{display:grid;gap:18px}
.form h2,.latex>h2{font:700 22px/1.2 var(--display);margin:0;letter-spacing:-.02em}

/* dialogs: float up like released latex */
[data-slot=dialog-overlay],[data-slot=alert-dialog-overlay]{background:rgb(6 22 15 / .62)!important;backdrop-filter:none!important}
[data-slot=dialog-content],[data-slot=alert-dialog-content]{max-width:min(540px,calc(100vw - 32px))!important;width:100%;padding:0!important;border-radius:34px 34px 34px 8px!important;
  background:var(--surface)!important;color:var(--ink)!important;border:1.5px solid var(--rule);box-shadow:var(--shadow);font:400 15px/1.5 var(--text);gap:0!important;max-height:calc(100svh - 32px);overflow:auto}
.dlg{padding:30px;display:grid;gap:20px;animation:rise calc(var(--k)*720ms) var(--elastic) both}
.dlg h2{font:700 24px/1.15 var(--display)!important;margin:0;letter-spacing:-.02em;color:var(--ink)}
.dlg .desc{margin:0;color:var(--muted);font-size:15px}
.dlg-foot{display:flex;justify-content:flex-end;gap:10px;flex-wrap:wrap}
.link-box{display:flex;gap:10px;align-items:center;border:1.5px solid var(--line);border-radius:14px;padding:12px 12px 12px 16px;background:var(--field);animation:unroll calc(var(--k)*760ms) cubic-bezier(.22,1,.36,1) both}
.link-box code{flex:1;min-width:0;font:500 14px/1.4 var(--text);overflow-wrap:anywhere;color:var(--ink)}
.copied{display:inline-flex;align-items:center;gap:6px;color:var(--ok);font-weight:600;font-size:14px}

/* reduced motion and still mode: no travel, no loops, final content immediately */
:root[data-reduced-motion] .balloon,:root[data-reduced-motion] .tether,:root[data-reduced-motion] .hub,:root[data-reduced-motion] [data-slot=skeleton]{animation:none!important}
:root[data-reduced-motion] .wobble,:root[data-reduced-motion] .pop,:root[data-reduced-motion] .dlg,:root[data-reduced-motion] .link-box,:root[data-reduced-motion] .seal path{animation:none!important}
:root[data-reduced-motion] #app *,:root[data-reduced-motion] .dlg *{transition-duration:0s!important}
:root[data-reduced-motion] .nav-stop:hover,:root[data-reduced-motion] .role-btn:hover,:root[data-reduced-motion] .tool:hover,:root[data-reduced-motion] .acct-btn:hover,
:root[data-reduced-motion] .person-row:hover .av,:root[data-reduced-motion] [data-slot=button]:hover{transform:none!important}

/* tablet: the gauge column becomes a top rail */
@media (max-width:1023px){
  .shell{grid-template-columns:1fr}
  .col{position:sticky;height:auto;flex-direction:row;align-items:center;flex-wrap:wrap;gap:12px 20px;padding:14px 24px}
  .col .brand{order:0}
  .gauge-wrap{order:2;grid-template-columns:auto 1fr;align-items:center;gap:14px;flex:1 1 100%}
  .gauge{width:64px;height:42px;margin:0}
  .needle{height:30px;width:4px;left:calc(50% - 2px);bottom:5px}
  .hub{width:12px;height:12px;left:calc(50% - 6px);bottom:1px;border-width:2px}
  .stops{grid-auto-flow:column;grid-auto-columns:max-content;gap:6px}
  .nav-stop{min-height:44px;padding:0 14px}
  .nav-stop:hover{transform:translateY(-2px)}
  .nav-stop .pos{display:none}
  .col-amb,.col .floor{display:none}
  .acct{margin-top:0;margin-left:auto;order:1;width:auto}
  .acct-btn{padding:6px 12px}
  .menu{bottom:auto;top:calc(100% + 10px);left:auto;right:0;width:300px;transform-origin:100% 0}
  .work{padding:28px 24px 48px}
  .filters{grid-template-columns:1fr 1fr}
  .filters .search{grid-column:1/-1}
  .tray{grid-template-columns:1fr 1fr}
  .roles,.mine{grid-template-columns:1fr}
  .public{grid-template-columns:1fr}
  .stage{min-height:300px;padding:24px 24px 88px}
  .cluster{right:4%;top:70px;transform:scale(.7);transform-origin:100% 0}
  .desk{padding:32px 24px 48px}
}
/* phone */
@media (max-width:767px){
  .col{padding:12px 20px}
  .brand{font-size:15px}
  .gauge-wrap{grid-template-columns:1fr}
  .gauge{display:none}
  .stops{grid-auto-columns:1fr}
  .nav-stop{justify-content:center;padding:0 8px;font-size:14px}
  .nav-stop .tick{display:none}
  .acct-btn .chev{display:none}
  .menu{width:min(320px,calc(100vw - 40px))}
  .work{padding:24px 20px 40px}
  .head h1{font-size:34px}
  .head [data-slot=button]{width:100%}
  .head>div{width:100%}
  .latex{padding:20px;border-radius:28px 28px 28px 8px}
  .filters{grid-template-columns:1fr}
  .roster thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
  .roster,.roster tbody{display:block}
  .roster tr.person-row{display:grid;grid-template-columns:1fr auto;gap:10px 12px;padding:16px 14px;border-bottom:1px solid var(--rule);border-radius:20px 20px 20px 6px}
  .roster tr.person-row td{display:block;padding:0;border:0;background:transparent!important}
  .roster tr.person-row[data-open]{background:var(--surface-2);border-bottom-color:transparent;border-radius:20px 20px 0 0}
  .person-row:hover td{background:transparent}
  .roster td.c-who{grid-column:1/-1}
  .roster td.c-co,.roster td.c-last{display:none!important}
  .roster td.c-act{grid-column:1/-1;text-align:left}
  .roster td.c-act [data-slot=button]{width:100%}
  .tray-row{display:block}
  .tray-row td{display:block;padding:0 0 14px;border:0}
  .tray{grid-template-columns:1fr;border-radius:0 0 22px 6px;padding:18px 14px}
  .sk-row{grid-template-columns:40px 1fr 90px}
  .sk-row .sk-x{display:none}
  .toast{left:20px;right:20px;bottom:20px;max-width:none}
  .tools{grid-template-columns:1fr}
  .row2{grid-template-columns:1fr}
  .stage{min-height:250px;padding:20px 20px 80px}
  .stage-top{flex-wrap:wrap}
  .stage .native span{display:none}
  .cluster{display:none}
  .stage-copy h1{font-size:34px}
  .desk{padding:24px 20px 40px}
  .sheet-card{padding:24px 20px}
  .acct-chip span.r{display:none}
  .dlg{padding:24px 20px}
  .dlg-foot [data-slot=button]{flex:1 1 100%}
  .facts div{grid-template-columns:1fr;gap:2px}
}
`;

/* ───────────────────────── mock data (illustrative; one source for every count) ───────────────────────── */
type Person = { id: string; name: string; email: string; company: string; role: string; tone: "plan" | "int" | "admin" | "own"; state: "on" | "off" | "inv"; last: string; work: number };
const PEOPLE: Person[] = [
  { id: "lg", name: "Lucía Gómez", email: "lucia@globosyeventos.co", company: "Globos y Eventos Lucía", role: "Usuario · Plan 2", tone: "plan", state: "on", last: "Hoy, 9:42", work: 3 },
  { id: "ar", name: "Andrés Rojas", email: "andres.rojas@sempertex.com", company: "Sempertex", role: "Empleado interno", tone: "int", state: "on", last: "Hoy, 8:15", work: 12 },
  { id: "dt", name: "David Torres", email: "davidt@sempertex.com", company: "Sempertex", role: "Administrador", tone: "admin", state: "on", last: "Ahora", work: 7 },
  { id: "jh", name: "Julián Herrera", email: "julian@decorarte.co", company: "Decorarte", role: "Montaje local", tone: "own", state: "on", last: "Ayer, 18:03", work: 0 },
  { id: "cs", name: "Camila Suárez", email: "camila.suarez@gmail.com", company: "Sin empresa", role: "Usuario · Plan 3", tone: "plan", state: "inv", last: "Sin activar", work: 0 },
  { id: "mp", name: "María Pérez", email: "maria@fiestasmp.com", company: "Fiestas MP", role: "Usuario · Plan 1", tone: "plan", state: "off", last: "12 oct", work: 0 },
];
const ROLE_NAMES = ["Usuario · Plan 1", "Usuario · Plan 2", "Usuario · Plan 3", "Empleado interno", "Administrador", "Montaje local", "Comercial feria"];
const STATE_LABEL = { on: "Activa", off: "Desactivada", inv: "Invitación pendiente" } as const;

type Perm = { key: string; label: string };
const TOOLS: { tool: string; perms: Perm[] }[] = [
  { tool: "Chat asistido", perms: [{ key: "chat.usar", label: "Usar el chat asistido" }] },
  { tool: "Contador de globos", perms: [{ key: "contador.usar", label: "Contar globos de una decoración" }] },
  { tool: "Catálogo", perms: [{ key: "catalogo.ver", label: "Ver el catálogo de productos" }] },
  { tool: "Calculadora de costos", perms: [{ key: "costos.usar", label: "Calcular costos de una decoración" }] },
  { tool: "Decoraciones listas", perms: [{ key: "decoraciones.explorar", label: "Explorar decoraciones listas" }] },
  { tool: "Taller 3D", perms: [{ key: "taller.usar", label: "Diseñar en el Taller 3D, exportar y guardar lo propio" }] },
  { tool: "Equipo interno", perms: [{ key: "proyectos.ver_todos", label: "Ver los proyectos de todas las cuentas" }, { key: "gasto.ver", label: "Ver el gasto de IA" }, { key: "internas.usar", label: "Usar las herramientas internas" }] },
  { tool: "Administración", perms: [{ key: "cuentas.administrar", label: "Administrar cuentas" }, { key: "roles.administrar", label: "Administrar roles" }, { key: "textos.corregir", label: "Corregir textos en inglés" }] },
];
const P1 = ["chat.usar", "contador.usar", "catalogo.ver"];
const P2 = [...P1, "costos.usar", "decoraciones.explorar"];
const P3 = [...P2, "taller.usar"];
const INT = [...P3, "proyectos.ver_todos", "gasto.ver", "internas.usar"];
const ALL = TOOLS.flatMap((t) => t.perms.map((p) => p.key));
type Role = { id: string; name: string; system: boolean; perms: string[] };
const ROLES: Role[] = [
  { id: "p1", name: "Usuario · Plan 1", system: true, perms: P1 },
  { id: "p2", name: "Usuario · Plan 2", system: true, perms: P2 },
  { id: "p3", name: "Usuario · Plan 3", system: true, perms: P3 },
  { id: "int", name: "Empleado interno", system: true, perms: INT },
  { id: "adm", name: "Administrador", system: true, perms: ALL },
  { id: "ml", name: "Montaje local", system: false, perms: [...P2] },
  { id: "cf", name: "Comercial feria", system: false, perms: ["catalogo.ver", "costos.usar"] },
];
const countFor = (name: string) => PEOPLE.filter((p) => p.role === name).length;
const initials = (n: string) => n.split(" ").map((w) => w[0]).slice(0, 2).join("");

const NOTICE = {
  es: { title: "Aviso de tratamiento de datos personales", body: (<>
    <mark>[RAZÓN SOCIAL DE SEMPERTEX]</mark> tratará tus datos personales —nombre, correo, empresa (si la indicas), el rol y el plan que te asignen, y las fechas de invitación, activación y último acceso— para darte acceso a Pictures durante el piloto, administrar tu cuenta y medir el uso de las herramientas, incluido el consumo de inteligencia artificial. Los proyectos y decoraciones que guardes quedan asociados a tu cuenta. Puedes conocer, actualizar, rectificar o pedir la supresión de tus datos, y revocar esta autorización, escribiendo a <mark>[CORREO PARA DERECHOS]</mark>. La política de tratamiento de datos está en <mark>[URL DE LA POLÍTICA]</mark>. Al activar tu cuenta declaras que leíste este aviso y autorizas el tratamiento descrito, conforme a la Ley 1581 de 2012.
  </>) },
  en: { title: "Personal data notice", body: (<>
    <mark>[SEMPERTEX LEGAL NAME]</mark> will process your personal data —name, email, company (if you provide it), the role and plan assigned to you, and the dates of invitation, activation and last access— to give you access to Pictures during the pilot, manage your account and measure the use of the tools, including artificial-intelligence usage. The projects and decorations you save are linked to your account. You can access, update, correct or request deletion of your data, and withdraw this authorization, by writing to <mark>[RIGHTS CONTACT EMAIL]</mark>. The data-processing policy is at <mark>[POLICY URL]</mark>. By activating your account you confirm that you have read this notice and authorize the processing described, under Colombian Law 1581 of 2012.
  </>) },
};

/* ───────────────────────── motion language: elastic inflation ───────────────────────── */
const SPRINGS = {
  expressive: { type: "spring", stiffness: 250, damping: 12, mass: 0.85 },
  natural: { type: "spring", stiffness: 330, damping: 24 },
  subtle: { type: "spring", stiffness: 520, damping: 44, mass: 0.6 },
} as const;
const STAGGER = { expressive: 0.034, natural: 0.022, subtle: 0.01 } as const;
const ORDER = ["cuentas", "roles", "mi-cuenta"];
const ANGLE: Record<string, number> = { cuentas: -52, roles: 0, "mi-cuenta": 52 };
// what changed since the previous mount: the runtime remounts the product on every view/state switch
const memory = { first: true, view: "", state: "" };

function useMove() {
  const p = useMotionProfile();
  const { view, state } = useMockup();
  const [entry] = React.useState(() => {
    const kind = memory.first ? "load" : memory.view !== view ? "view" : memory.state !== state ? "state" : "none";
    const from = ORDER.indexOf(memory.view), to = ORDER.indexOf(view);
    return { kind, dir: from < 0 || to < 0 ? 1 : Math.sign(to - from) || 1, fromView: memory.view };
  });
  React.useEffect(() => { memory.first = false; memory.view = view; memory.state = state; }, [view, state]);
  const play = !p.reduced;
  return { ...entry, play, reduced: p.reduced, spring: p.reduced ? { duration: 0 } : SPRINGS[p.profile], stagger: STAGGER[p.profile], d: p.distance };
}

// display headings inflate letter by letter from below, overshoot and settle (no opacity: legible on every frame)
function Inflate({ text, as: Tag = "h1", className }: { text: string; as?: "h1" | "h2"; className?: string }) {
  const m = useMove();
  const animate = m.play && (m.kind === "load" || m.kind === "view");
  let n = 0;
  return (
    <Tag className={`display ${className || ""}`}>
      <span className="sr-only">{text}</span>
      <span aria-hidden="true">
        {text.split(" ").map((w, wi, all) => (
          <React.Fragment key={wi}>
            <span className="word">
              {[...w].map((ch, ci) => {
                const i = n++;
                return (
                  <motion.span key={ci} className="ch"
                    initial={animate ? { y: "0.5em", scale: 0.5, rotate: i % 2 ? 9 : -9 } : false}
                    animate={{ y: 0, scale: 1, rotate: 0 }}
                    transition={{ ...m.spring, delay: i * m.stagger }}>{ch}</motion.span>
                );
              })}
            </span>
            {wi < all.length - 1 ? " " : ""}
          </React.Fragment>
        ))}
      </span>
    </Tag>
  );
}

// a working panel inflates from its knot corner and arrives from where its destination sits on the gauge
function Panel({ className = "", children, i = 0, as = "section", ...rest }: { className?: string; children: React.ReactNode; i?: number; as?: "section" | "div" } & Record<string, unknown>) {
  const m = useMove();
  const go = m.play && (m.kind === "load" || m.kind === "view");
  const C = as === "div" ? motion.div : motion.section;
  return (
    <C className={className} {...rest}
      initial={go ? { x: m.dir * m.d * 3.2, y: m.d * 0.8, scale: 0.93, rotate: m.dir * 1.4 } : false}
      animate={{ x: 0, y: 0, scale: 1, rotate: 0 }}
      transition={{ ...m.spring, delay: go ? 0.06 + i * 0.07 : 0 }}>
      {children}
    </C>
  );
}

// ambient tethered latex; paused when offscreen
function Cluster({ className, items }: { className: string; items: { c: string; w: number; h: number; x: number; y: number; t: number; cls?: string }[] }) {
  const ref = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver(([e]) => el.classList.toggle("paused", !e.isIntersecting));
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return (
    <div ref={ref} className={`amb ${className}`} aria-hidden="true">
      {items.map((b, k) => (
        <React.Fragment key={k}>
          <span className="tether" style={{ left: b.x + b.w / 2, top: b.y + b.h + 6, height: b.t }} />
          <span className={`balloon ${b.c} ${b.cls || ""}`} style={{ left: b.x, top: b.y, width: b.w, height: b.h }} />
        </React.Fragment>
      ))}
    </div>
  );
}

function Native({ id, label, value, options, onChange, hideLabel, className }: { id: string; label: string; value: string; options: string[] | { v: string; l: string }[]; onChange?: (v: string) => void; hideLabel?: boolean; className?: string }) {
  const opts = (options as (string | { v: string; l: string })[]).map((o) => (typeof o === "string" ? { v: o, l: o } : o));
  return (
    <div className={`field ${className || ""}`}>
      <label className={hideLabel ? "sr-only" : "label"} htmlFor={id}>{label}</label>
      <span className="native">
        <select id={id} value={value} onChange={(e) => onChange?.(e.target.value)}>
          {opts.map((o) => <option key={o.v} value={o.v}>{o.l}</option>)}
        </select>
        <ChevronDown aria-hidden="true" />
      </span>
    </div>
  );
}

function Field({ id, label, hint, error, ...input }: { id: string; label: string; hint?: string; error?: string } & React.ComponentProps<typeof Input>) {
  return (
    <div className="field">
      <label className="label" htmlFor={id}>{label}</label>
      <Input id={id} aria-invalid={error ? true : undefined} aria-describedby={hint || error ? `${id}-d` : undefined} {...input} />
      {(error || hint) && <p id={`${id}-d`} className="hint" style={error ? { color: "var(--bad)", fontWeight: 600 } : undefined}>{error || hint}</p>}
    </div>
  );
}

function Note({ tone, title, children, anim, icon }: { tone: "bad" | "ok" | "warn" | "info"; title: string; children?: React.ReactNode; anim?: boolean; icon?: React.ReactNode }) {
  const m = useMove();
  const cls = anim && m.play ? (tone === "bad" ? " wobble" : tone === "ok" ? " pop" : "") : "";
  return (
    <div className={`note ${tone}${cls}`} role={tone === "bad" ? "alert" : "status"}>
      {icon || (tone === "ok" ? <Check /> : tone === "info" ? <Lock /> : <TriangleAlert />)}
      <div><strong>{title}</strong>{children}</div>
    </div>
  );
}

function Seal() {
  return (
    <span className="seal pop" aria-hidden="true">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><path d="M5 12.5l4.5 4.5L19 7.5" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" /></svg>
    </span>
  );
}

function Brand({ sub }: { sub?: boolean }) {
  return (
    <span className="brand">
      <span className="brand-mark" aria-hidden="true"><span className="balloon" /></span>
      <span>Pictures{sub && <small>Decoración con globos · piloto</small>}</span>
    </span>
  );
}

/* ───────────────────────── public stage screens ───────────────────────── */
function PublicStage({ title, lede, children, chip, lang, setLang }: { title: string; lede: string; children: React.ReactNode; chip?: React.ReactNode; lang?: string; setLang?: (v: string) => void }) {
  const m = useMove();
  return (
    <div className="public">
      <aside className="stage" aria-label="Pictures">
        <div className="stage-top">
          <Brand sub />
          {chip || (setLang && (
            <span className="native">
              <label htmlFor="idioma"><span>Idioma</span></label>
              <select id="idioma" value={lang} onChange={(e) => setLang(e.target.value)}>
                <option value="es">Español</option><option value="en">English</option>
              </select>
              <ChevronDown aria-hidden="true" />
            </span>
          ))}
        </div>
        <Cluster className="cluster" items={[
          { c: "b1", w: 92, h: 108, x: 70, y: 0, t: 150 },
          { c: "b2", w: 64, h: 76, x: 150, y: 58, t: 140, cls: "c2" },
          { c: "b3", w: 58, h: 68, x: 20, y: 96, t: 120, cls: "c3" },
        ]} />
        <div className="stage-copy">
          <Inflate text={title} />
          <p className="lede">{lede}</p>
        </div>
        <motion.div className="floor" aria-hidden="true" initial={m.play && m.kind === "load" ? { scaleY: 0.2 } : false} animate={{ scaleY: 1 }} transition={m.spring} />
      </aside>
      <div className="desk">{children}</div>
    </div>
  );
}

function SubmitButton({ busy, label, busyLabel, disabled, onClick }: { busy?: boolean; label: string; busyLabel: string; disabled?: boolean; onClick?: () => void }) {
  return (
    <Button type="submit" size="lg" className="w-full" disabled={busy || disabled} aria-busy={busy || undefined} onClick={onClick}>
      {busy ? <RotateCcw className="spin" aria-hidden="true" /> : <ArrowRight aria-hidden="true" />}{busy ? busyLabel : label}
    </Button>
  );
}

function InvalidLink() {
  return (
    <PublicStage title="Este enlace ya no sirve" lede="Los enlaces de invitación vencen a los 7 días y los de restablecimiento a las 24 horas; cada uno sirve una sola vez.">
      <div className="sheet">
        <Panel className="sheet-card">
          <h2>Pide un enlace nuevo</h2>
          <Note tone="warn" title="El enlace ya se usó o venció" anim>
            Pide a la persona que administra tu acceso que genere uno nuevo; el anterior deja de servir en cuanto lo haga.
          </Note>
          <Button variant="outline" size="lg">Ir a iniciar sesión</Button>
        </Panel>
      </div>
    </PublicStage>
  );
}

function Login() {
  const { state } = useMockup();
  const busy = state === "cargando";
  const failed = state === "error" || state === "rechazo";
  const blank = state === "vacio";
  return (
    <PublicStage title="Entra a Pictures" lede="Usa el correo y la contraseña de tu invitación. No hay registro abierto: cada cuenta la crea un administrador.">
      <div className="sheet">
        <Panel className="sheet-card" as="div">
          <form className="form" onSubmit={(e) => e.preventDefault()} noValidate>
            <h2>Iniciar sesión</h2>
            {failed && (
              <Note tone="bad" title="No pudimos iniciar sesión con esos datos" anim>
                Revisa el correo y la contraseña. Después de varios intentos fallidos tendrás que esperar 15 minutos para volver a intentarlo.
              </Note>
            )}
            {state === "exito" && <Note tone="ok" title="Sesión iniciada" anim>Volviendo a Calculadora de costos…</Note>}
            <Field id="correo" label="Correo" type="email" autoComplete="email" defaultValue={blank ? "" : "lucia@globosyeventos.co"} placeholder="nombre@empresa.com" disabled={busy} error={failed ? " " : undefined} />
            <Field id="clave" label="Contraseña" type="password" autoComplete="current-password" defaultValue={blank ? "" : "globos-lucia-26"} disabled={busy} />
            <SubmitButton busy={busy || state === "exito"} label="Entrar" busyLabel={state === "exito" ? "Entrando…" : "Comprobando…"} />
          </form>
        </Panel>
        <p className="sheet-foot">Después de entrar vuelves a <strong>Calculadora de costos</strong>. ¿Olvidaste tu contraseña? Pide a tu administrador un enlace para restablecerla.</p>
      </div>
    </PublicStage>
  );
}

function NoticeBox({ lang, version }: { lang: "es" | "en"; version: number }) {
  const n = NOTICE[lang];
  return (
    <div className="field">
      <span className="label" id="aviso-t">{lang === "es" ? `${n.title} · versión ${version}` : `${n.title} · version ${version}`}</span>
      <div className="notice" tabIndex={0} role="region" aria-labelledby="aviso-t">
        <p>{n.body}</p>
      </div>
      <p className="hint">Mostrado en {lang === "es" ? "español, el idioma de tu navegador" : "inglés (English), el idioma elegido"}. Los campos entre corchetes esperan la revisión legal de Sempertex.</p>
    </div>
  );
}

function Activate() {
  const { state } = useMockup();
  const [lang, setLang] = React.useState<"es" | "en">("es");
  const [ok, setOk] = React.useState(state === "normal" || state === "cargando" || state === "exito");
  if (state === "rechazo") return <InvalidLink />;
  const busy = state === "cargando";
  const blank = state === "vacio";
  return (
    <PublicStage title="Activa tu cuenta" lede="Elige tu contraseña y acepta el aviso de datos. Al activar entras directo a tu primera herramienta." lang={lang} setLang={(v) => setLang(v as "es" | "en")}>
      <div className="sheet">
        <Panel className="sheet-card" as="div">
          <form className="form" onSubmit={(e) => e.preventDefault()} noValidate>
            <h2>Tu invitación</h2>
            <div className="invitee"><span className="av plan">CS</span><div><b>Camila Suárez</b><span className="meta">camila.suarez@gmail.com · Usuario · Plan 3</span></div></div>
            {state === "error" && <Note tone="bad" title="Las contraseñas no coinciden" anim>Escribe la misma contraseña en los dos campos; debe tener al menos 8 caracteres.</Note>}
            {state === "exito" && <div className="note ok pop" role="status"><Seal /><div><strong>Cuenta activada</strong>Entrando a Chat asistido, tu primera herramienta…</div></div>}
            <div className="row2">
              <Field id="nueva" label="Contraseña" type="password" autoComplete="new-password" hint="Mínimo 8 caracteres." defaultValue={blank ? "" : "camila-globos"} disabled={busy} error={state === "error" ? "No coincide con la confirmación." : undefined} />
              <Field id="repite" label="Repite la contraseña" type="password" autoComplete="new-password" defaultValue={blank ? "" : state === "error" ? "camila-globo" : "camila-globos"} disabled={busy} />
            </div>
            <NoticeBox lang={lang} version={1} />
            <label className="accept" htmlFor="acepto">
              <Checkbox id="acepto" checked={ok && !blank} onCheckedChange={(v) => setOk(Boolean(v))} disabled={busy} />
              <span>Leí el aviso y autorizo el tratamiento de mis datos personales.</span>
            </label>
            <SubmitButton busy={busy} label="Activar cuenta" busyLabel="Activando…" disabled={!ok || blank} />
            {(!ok || blank) && <p className="hint" style={{ marginTop: -8 }}>Acepta el aviso para poder activar la cuenta.</p>}
          </form>
        </Panel>
        <p className="sheet-foot">Invitación enviada por <strong>David Torres</strong>. Vence el 3 nov a las 10:20.</p>
      </div>
    </PublicStage>
  );
}

function Reset() {
  const { state } = useMockup();
  if (state === "rechazo") return <InvalidLink />;
  const busy = state === "cargando";
  const blank = state === "vacio";
  return (
    <PublicStage title="Nueva contraseña" lede="Tu administrador generó este enlace. Sirve una vez y vence 24 horas después de creado.">
      <div className="sheet">
        <Panel className="sheet-card" as="div">
          <form className="form" onSubmit={(e) => e.preventDefault()} noValidate>
            <h2>Restablecer contraseña</h2>
            <div className="invitee"><span className="av plan">LG</span><div><b>Lucía Gómez</b><span className="meta">lucia@globosyeventos.co</span></div></div>
            {state === "error" && <Note tone="bad" title="La contraseña es muy corta" anim>Usa al menos 8 caracteres y repítela igual en los dos campos.</Note>}
            {state === "exito" ? (
              <>
                <div className="note ok pop" role="status"><Seal /><div><strong>Contraseña guardada</strong>Cerramos tus otras sesiones. Ya puedes iniciar sesión con la nueva.</div></div>
                <Button size="lg"><ArrowRight aria-hidden="true" />Ir a iniciar sesión</Button>
              </>
            ) : (
              <>
                <Field id="r-nueva" label="Nueva contraseña" type="password" hint="Mínimo 8 caracteres." defaultValue={blank ? "" : state === "error" ? "globo" : "lucia-arco-2026"} disabled={busy} error={state === "error" ? "Tiene 5 caracteres; faltan 3." : undefined} />
                <Field id="r-repite" label="Repite la contraseña" type="password" defaultValue={blank ? "" : state === "error" ? "globo" : "lucia-arco-2026"} disabled={busy} />
                <SubmitButton busy={busy} label="Guardar contraseña" busyLabel="Guardando…" />
              </>
            )}
          </form>
        </Panel>
        <p className="sheet-foot">¿No pediste este cambio? Avisa a tu administrador; el enlace deja de servir cuando genera otro.</p>
      </div>
    </PublicStage>
  );
}

function NoticeGate() {
  const { state } = useMockup();
  const [ok, setOk] = React.useState(state === "exito" || state === "cargando");
  const [menu, setMenu] = React.useState(false);
  const busy = state === "cargando";
  const chip = (
    <div className="acct" style={{ marginTop: 0 }}>
      <button type="button" className="acct-btn" aria-expanded={menu} aria-controls="menu-aviso" onClick={() => setMenu(!menu)} style={{ padding: "6px 12px" }}>
        <span className="av plan" style={{ width: 30, height: 34, marginBottom: 4 }}>LG</span>
        <span><b>Lucía Gómez</b><span className="r">Usuario · Plan 2</span></span>
        <ChevronDown className="chev" aria-hidden="true" />
      </button>
      {menu && (
        <div className="menu" id="menu-aviso" style={{ bottom: "auto", top: "calc(100% + 10px)", left: "auto", right: 0, width: 300 }}>
          <div className="menu-head"><b>Lucía Gómez</b><span className="meta">Usuario · Plan 2 · lucia@globosyeventos.co</span></div>
          <button type="button" className="menu-item" disabled><Lock aria-hidden="true" />Mi cuenta</button>
          <p className="menu-why">Disponible cuando aceptes el aviso.</p>
          <button type="button" className="menu-item"><LogOut aria-hidden="true" />Cerrar sesión</button>
        </div>
      )}
    </div>
  );
  return (
    <PublicStage title="Aviso de datos, versión 2" lede="Cambió el aviso de tratamiento de datos. Léelo y acéptalo para seguir usando Pictures; hasta entonces no se abre ninguna otra página." chip={chip}>
      <div className="sheet">
        <Panel className="sheet-card" as="div">
          <form className="form" onSubmit={(e) => e.preventDefault()} noValidate>
            <h2>Antes de seguir</h2>
            {state === "rechazo" && <Note tone="warn" title="Primero acepta el aviso" anim>Pediste abrir Calculadora de costos. Se abrirá en cuanto aceptes la versión 2.</Note>}
            {state === "error" && <Note tone="bad" title="No guardamos tu aceptación" anim>Se perdió la conexión. Vuelve a intentarlo; nada cambió en tu cuenta.</Note>}
            {state === "exito" && <div className="note ok pop" role="status"><Seal /><div><strong>Aviso aceptado</strong>Guardamos la versión 2 y la fecha. Abriendo Calculadora de costos…</div></div>}
            <NoticeBox lang="es" version={2} />
            <label className="accept" htmlFor="acepto-v2">
              <Checkbox id="acepto-v2" checked={ok && state !== "vacio"} onCheckedChange={(v) => setOk(Boolean(v))} disabled={busy} />
              <span>Leí la versión 2 del aviso y autorizo el tratamiento de mis datos.</span>
            </label>
            <SubmitButton busy={busy} label="Aceptar y continuar" busyLabel="Guardando…" disabled={!ok || state === "vacio"} />
          </form>
        </Panel>
        <p className="sheet-foot">Aceptaste la versión 1 el 2 nov 2026. Si no aceptas, puedes cerrar sesión desde tu menú.</p>
      </div>
    </PublicStage>
  );
}

/* ───────────────────────── signed-in shell with the gauge ───────────────────────── */
function Gauge({ view }: { view: string }) {
  const m = useMove();
  const [hover, setHover] = React.useState<string | null>(null);
  const from = m.kind === "view" && ANGLE[m.fromView] !== undefined ? ANGLE[m.fromView] : m.kind === "load" ? -90 : ANGLE[view];
  const angle = ANGLE[hover || view] ?? 0;
  const { set } = useMockup();
  const ticks = Array.from({ length: 13 }, (_, k) => -90 + k * 15);
  return (
    <div className="gauge-wrap">
      <div className="gauge" aria-hidden="true">
        <svg viewBox="0 0 176 112">
          <path d="M14 100 A74 74 0 0 1 162 100" fill="none" stroke="var(--stage-line)" strokeWidth="2" />
          {ticks.map((a) => {
            const r = (a - 90) * Math.PI / 180, big = [-52, 0, 52].includes(a) || a % 45 === 0;
            const x1 = 88 + Math.cos(r) * 74, y1 = 100 + Math.sin(r) * 74, x2 = 88 + Math.cos(r) * (big ? 60 : 66), y2 = 100 + Math.sin(r) * (big ? 60 : 66);
            return <line key={a} x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--stage-muted)" strokeWidth={big ? 2.5 : 1.2} strokeLinecap="round" />;
          })}
          {Object.entries(ANGLE).map(([k, a]) => {
            const r = (a - 90) * Math.PI / 180;
            return <circle key={k} cx={88 + Math.cos(r) * 74} cy={100 + Math.sin(r) * 74} r={k === view ? 7 : 4.5} fill={k === view ? "var(--pill-on)" : "var(--stage-ink)"} />;
          })}
        </svg>
        <motion.span className="needle" initial={m.play ? { rotate: from } : false} animate={{ rotate: angle }}
          transition={m.reduced ? { duration: 0 } : { type: "spring", stiffness: hover ? 420 : 210, damping: hover ? 18 : 9, mass: 0.9 }} />
        <span className="hub" />
      </div>
      <nav aria-label="Administración">
        <ul className="stops">
          {[["cuentas", "Cuentas", "6"], ["roles", "Roles", "7"], ["mi-cuenta", "Mi cuenta", ""]].map(([id, label, n]) => (
            <li key={id}>
              <button type="button" className="nav-stop" aria-current={view === id ? "page" : undefined}
                onMouseEnter={() => setHover(id)} onMouseLeave={() => setHover(null)} onFocus={() => setHover(id)} onBlur={() => setHover(null)}
                onClick={() => set("view", id)}>
                <span className="tick" aria-hidden="true" />{label}{n && <span className="pos">{n}</span>}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}

function AccountMenu({ open, setOpen }: { open: boolean; setOpen: (v: boolean) => void }) {
  const { set } = useMockup();
  const m = useMove();
  return (
    <div className="acct">
      <AnimatePresence>
        {open && (
          <motion.div className="menu" id="menu-cuenta" initial={m.play ? { scale: 0.86, y: 14, rotate: -2 } : false} animate={{ scale: 1, y: 0, rotate: 0 }}
            exit={m.play ? { scale: 0.9, y: 10, opacity: 0 } : undefined} transition={m.spring}>
            <div className="menu-head"><b>David Torres</b><span className="meta">Administrador · davidt@sempertex.com</span></div>
            <button type="button" className="menu-item" onClick={() => { setOpen(false); set("scene", ""); set("view", "mi-cuenta"); }}><KeyRound aria-hidden="true" />Mi cuenta</button>
            <button type="button" className="menu-item" onClick={() => set("view", "login")}><LogOut aria-hidden="true" />Cerrar sesión</button>
          </motion.div>
        )}
      </AnimatePresence>
      <button type="button" className="acct-btn" aria-expanded={open} aria-controls="menu-cuenta" onClick={() => setOpen(!open)}>
        <span className="av admin" style={{ width: 34, height: 40, marginBottom: 4 }}>DT</span>
        <span><b>David Torres</b><span className="r">Administrador</span></span>
        <ChevronDown className="chev" aria-hidden="true" />
      </button>
    </div>
  );
}

function Shell({ view, children }: { view: string; children: React.ReactNode }) {
  const { scene, set } = useMockup();
  const [open, setOpen] = React.useState(scene === "menu");
  React.useEffect(() => setOpen(scene === "menu"), [scene]);
  return (
    <div className="shell">
      <aside className="col">
        <Brand />
        <Gauge view={view} />
        <Cluster className="col-amb" items={[
          { c: "b1", w: 46, h: 54, x: 34, y: 20, t: 92 },
          { c: "b2", w: 34, h: 40, x: 92, y: 52, t: 80, cls: "c2" },
          { c: "b3", w: 30, h: 36, x: 150, y: 30, t: 96, cls: "c3" },
        ]} />
        <div className="floor" aria-hidden="true" />
        <AccountMenu open={open} setOpen={(v) => { setOpen(v); if (!v && scene === "menu") set("scene", ""); }} />
      </aside>
      <main className="work">{children}</main>
    </div>
  );
}

/* ───────────────────────── accounts ───────────────────────── */
function StateTag({ s }: { s: Person["state"] }) {
  return <span className={`state ${s}`}><i aria-hidden="true" />{STATE_LABEL[s]}</span>;
}

function Tray({ p }: { p: Person }) {
  const { set } = useMockup();
  const lastAdmin = p.role === "Administrador";
  const blocked = lastAdmin ? "Es el único administrador. Nombra a otra persona Administrador antes de eliminar esta cuenta." :
    p.work > 0 ? `Tiene ${p.work} ${p.work === 1 ? "proyecto o decoración guardada" : "proyectos y decoraciones guardados"}. Desactívala para cerrar su acceso sin perder ese trabajo.` : "";
  const m = useMove();
  return (
    <motion.div className="tray" id={`tray-${p.id}`} initial={m.play ? { scaleY: 0.7, y: -10 } : false} animate={{ scaleY: 1, y: 0 }} transition={m.spring}>
      <div className="act">
        <Native id={`rol-${p.id}`} label="Rol" value={p.role} options={ROLE_NAMES.filter((r) => r !== "Comercial feria" || true)} />
        <p style={{ marginTop: 8 }}>Aplica en su próxima solicitud.</p>
        <Button className="sm" variant="outline" disabled={lastAdmin}>Guardar rol</Button>
      </div>
      <div className="act">
        <h3>{p.state === "off" ? "Reactivar" : "Desactivar"}</h3>
        <p>{p.state === "off" ? "Vuelve a entrar con su contraseña de antes." : "Cierra sus sesiones al instante. Su trabajo se conserva."}</p>
        <Button className="sm" variant="outline" disabled={lastAdmin} onClick={() => set("scene", "desactivar")}><Power aria-hidden="true" />{p.state === "off" ? "Reactivar cuenta" : "Desactivar cuenta"}</Button>
        {lastAdmin && <p className="why"><TriangleAlert aria-hidden="true" />Necesitas otro administrador activo para desactivarla.</p>}
      </div>
      <div className="act">
        <h3>{p.state === "inv" ? "Invitación" : "Contraseña"}</h3>
        <p>{p.state === "inv" ? "Genera un enlace nuevo de 7 días; el anterior sin usar deja de servir." : "Genera un enlace de 24 horas; el anterior sin usar deja de servir."}</p>
        <Button className="sm" variant="outline" onClick={() => set("scene", p.state === "inv" ? "enlace-invitacion" : "enlace-restablecer")}><Link2 aria-hidden="true" />{p.state === "inv" ? "Nueva invitación" : "Enlace para restablecer"}</Button>
      </div>
      <div className="act">
        <h3>Eliminar</h3>
        <p>Su gasto de IA queda como «Cuenta eliminada», sin datos personales.</p>
        <Button className="sm" variant="destructive" disabled={!!blocked} onClick={() => set("scene", "eliminar")}><Trash2 aria-hidden="true" />Eliminar cuenta</Button>
        {blocked && <p className="why"><TriangleAlert aria-hidden="true" />{blocked}</p>}
      </div>
    </motion.div>
  );
}

function Accounts() {
  const { state, set } = useMockup();
  const m = useMove();
  const [open, setOpen] = React.useState<string | null>(state === "rechazo" ? "lg" : state === "normal" ? "jh" : null);
  const empty = state === "vacio";
  const [q, setQ] = React.useState(empty ? "zapata" : "");
  const [role, setRole] = React.useState(empty ? "Usuario · Plan 3" : "Todos los roles");
  const [st, setSt] = React.useState(empty ? "Activa" : "Todos los estados");
  const rows = PEOPLE.filter((p) => (!q || (p.name + p.email).toLowerCase().includes(q.toLowerCase())) && (role === "Todos los roles" || p.role === role) && (st === "Todos los estados" || STATE_LABEL[p.state] === st));
  const rowsAnimate = m.play && (m.kind === "load" || m.kind === "view");
  return (
    <>
      <div className="head">
        <div>
          <Inflate text="Cuentas" />
          <p className="meta">6 cuentas · 4 activas · 1 invitación pendiente · 1 desactivada</p>
        </div>
        <Button size="lg" onClick={() => set("scene", "invitar")}><Plus aria-hidden="true" />Invitar persona</Button>
      </div>
      <Panel className="latex" aria-label="Lista de cuentas">
        <div className="filters">
          <div className="field search">
            <label className="label" htmlFor="buscar">Buscar por nombre o correo</label>
            <div style={{ position: "relative" }}><Search aria-hidden="true" /><Input id="buscar" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ej. Lucía o @decorarte.co" /></div>
          </div>
          <Native id="f-rol" label="Rol" value={role} onChange={setRole} options={["Todos los roles", ...ROLE_NAMES]} />
          <Native id="f-estado" label="Estado" value={st} onChange={setSt} options={["Todos los estados", "Activa", "Invitación pendiente", "Desactivada"]} />
          {(q || role !== "Todos los roles" || st !== "Todos los estados") ? (
            <Button variant="ghost" onClick={() => { setQ(""); setRole("Todos los roles"); setSt("Todos los estados"); }}><X aria-hidden="true" />Quitar filtros</Button>
          ) : <span />}
        </div>
        {state === "rechazo" && (
          <Note tone="warn" title="Lucía Gómez no se puede eliminar" anim>Tiene 3 proyectos y decoraciones guardados. Puedes desactivarla: cierra su acceso y conserva su trabajo.</Note>
        )}
        {state === "error" ? (
          <div className="empty">
            <Note tone="bad" title="No pudimos cargar las cuentas" anim>Revisa tu conexión y vuelve a intentarlo. No se cambió ninguna cuenta.</Note>
            <Button variant="outline"><RotateCcw aria-hidden="true" />Reintentar</Button>
          </div>
        ) : state === "cargando" ? (
          <div aria-busy="true" aria-label="Cargando cuentas">
            {PEOPLE.map((p) => (
              <div className="sk-row" key={p.id}>
                <Skeleton style={{ width: 40, height: 46, borderRadius: "50% 50% 47% 53%/56% 56% 44% 44%" }} />
                <div style={{ display: "grid", gap: 8 }}><Skeleton style={{ height: 14, width: "70%" }} /><Skeleton style={{ height: 12, width: "90%" }} /></div>
                <Skeleton className="sk-x" style={{ height: 14, width: "80%" }} />
                <Skeleton className="sk-x" style={{ height: 14, width: "70%" }} />
                <Skeleton className="sk-x" style={{ height: 28, width: "90%" }} />
                <Skeleton style={{ height: 36, width: 90 }} />
              </div>
            ))}
          </div>
        ) : rows.length === 0 ? (
          <div className="empty">
            <h2>Ninguna cuenta coincide</h2>
            <p>No hay cuentas con «{q}» en {role} · {st}. Quita los filtros o invita a esa persona.</p>
            <div className="acts">
              <Button variant="outline" onClick={() => { setQ(""); setRole("Todos los roles"); setSt("Todos los estados"); }}><X aria-hidden="true" />Quitar filtros</Button>
              <Button onClick={() => set("scene", "invitar")}><Plus aria-hidden="true" />Invitar persona</Button>
            </div>
          </div>
        ) : (
          <table className="roster">
            <caption className="sr-only">Cuentas de Pictures</caption>
            <thead><tr><th>Persona</th><th>Empresa</th><th>Rol</th><th>Estado</th><th>Último acceso</th><th><span className="sr-only">Acciones</span></th></tr></thead>
            <tbody>
              {rows.map((p, i) => (
                <React.Fragment key={p.id}>
                  <motion.tr className="person-row" data-open={open === p.id ? "" : undefined}
                    initial={rowsAnimate ? { y: m.d * 1.3, rotate: i % 2 ? 1.2 : -1.2 } : false} animate={{ y: 0, rotate: 0 }}
                    transition={{ ...m.spring, delay: rowsAnimate ? 0.18 + i * 0.05 : 0 }}>
                    <td className="c-who"><div className="who"><span className={`av ${p.state === "off" ? "off" : p.state === "inv" ? "inv" : p.tone}`} aria-hidden="true">{initials(p.name)}</span>
                      <div style={{ minWidth: 0 }}><b>{p.name}</b><span className="meta">{p.email}</span></div></div></td>
                    <td className="c-co">{p.company}</td>
                    <td className="c-role">{p.role}</td>
                    <td className="c-state"><StateTag s={p.state} /></td>
                    <td className="c-last">{p.last}</td>
                    <td className="c-act">
                      <Button className="sm" variant="outline" aria-expanded={open === p.id} aria-controls={`tray-${p.id}`} onClick={() => setOpen(open === p.id ? null : p.id)}>
                        Gestionar<ChevronDown aria-hidden="true" style={{ transform: open === p.id ? "rotate(180deg)" : undefined, transition: "transform calc(var(--k)*300ms) var(--elastic)" }} />
                      </Button>
                    </td>
                  </motion.tr>
                  {open === p.id && <tr className="tray-row"><td colSpan={6}><Tray p={p} /></td></tr>}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
      {state === "exito" && (
        <div className="toast pop" role="status"><Seal /><div><b>Rol cambiado</b>Lucía Gómez ahora es Usuario · Plan 3. Abre el Taller 3D en su próxima solicitud.</div></div>
      )}
    </>
  );
}

/* ───────────────────────── roles ───────────────────────── */
function Roles() {
  const { state } = useMockup();
  const empty = state === "vacio";
  const roles = empty ? ROLES.filter((r) => r.system) : ROLES;
  const [sel, setSel] = React.useState<string>(empty || state === "error" ? "nuevo" : "ml");
  const role = roles.find((r) => r.id === sel);
  const [checked, setChecked] = React.useState<string[]>(state === "error" || empty ? [] : role?.perms || []);
  const pick = (id: string) => { setSel(id); setChecked(ROLES.find((r) => r.id === id)?.perms || []); };
  const isNew = sel === "nuevo";
  const name = isNew ? (state === "error" ? "Feria Bogotá" : "") : role?.name || "";
  const n = isNew ? 0 : countFor(name);
  const toggle = (k: string, v: boolean) => setChecked((c) => (v ? [...c, k] : c.filter((x) => x !== k)));
  return (
    <>
      <div className="head">
        <div>
          <Inflate text="Roles" />
          <p className="meta">5 roles del sistema, solo lectura · {empty ? 0 : 2} roles propios</p>
        </div>
        <Button size="lg" onClick={() => { setSel("nuevo"); setChecked([]); }}><Plus aria-hidden="true" />Crear rol</Button>
      </div>
      {state === "cargando" ? (
        <div className="roles" aria-busy="true" aria-label="Cargando roles">
          <div className="rack">{Array.from({ length: 7 }, (_, k) => <Skeleton key={k} style={{ height: 52 }} />)}</div>
          <div className="latex"><div style={{ display: "grid", gap: 14 }}><Skeleton style={{ height: 30, width: "40%" }} /><div className="tools">{Array.from({ length: 6 }, (_, k) => <Skeleton key={k} style={{ height: 96, borderRadius: "22px 22px 22px 6px" }} />)}</div></div></div>
        </div>
      ) : (
        <div className="roles">
          <Panel className="rack" as="div" i={0}>
            <div>
              <h2 id="sys-h">Roles del sistema · solo lectura</h2>
              <ul aria-labelledby="sys-h">
                {roles.filter((r) => r.system).map((r) => (
                  <li key={r.id}><button type="button" className="role-btn" aria-pressed={sel === r.id} onClick={() => pick(r.id)}>
                    <Lock aria-hidden="true" /><span><b>{r.name}</b><span className="meta">{countFor(r.name)} {countFor(r.name) === 1 ? "cuenta" : "cuentas"} · {r.perms.length} permisos</span></span></button></li>
                ))}
              </ul>
            </div>
            <div>
              <h2 id="own-h">Roles propios</h2>
              {empty ? (
                <p className="rack-empty">Aún no hay roles propios. Crea uno con su nombre y los permisos que necesita; debe tener al menos uno.</p>
              ) : (
                <ul aria-labelledby="own-h">
                  {roles.filter((r) => !r.system).map((r) => (
                    <li key={r.id}><button type="button" className="role-btn" aria-pressed={sel === r.id} onClick={() => pick(r.id)}>
                      <ShieldCheck aria-hidden="true" /><span><b>{r.name}</b><span className="meta">{countFor(r.name)} {countFor(r.name) === 1 ? "cuenta" : "cuentas"} · {r.perms.length} permisos</span></span></button></li>
                  ))}
                </ul>
              )}
            </div>
          </Panel>
          <Panel className="latex editor" i={1} aria-labelledby="ed-h">
            {role?.system ? (
              <>
                <div className="editor-head">
                  <div><h2 id="ed-h">{role.name}</h2><p className="meta">Rol del sistema · {n} {n === 1 ? "cuenta" : "cuentas"} · no se edita ni se elimina</p></div>
                </div>
                <div className="tools">
                  {TOOLS.map((t) => (
                    <div className="tool" key={t.tool}><h3>{t.tool}</h3>
                      {t.perms.map((p) => {
                        const yes = role.perms.includes(p.key);
                        return <div className="perm ro" key={p.key}>{yes ? <Check className="yes" aria-hidden="true" /> : <X className="no" aria-hidden="true" />}<span>{p.label}<small>{yes ? "Incluido" : "No incluido"}</small></span></div>;
                      })}
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <form className="editor" onSubmit={(e) => e.preventDefault()} noValidate>
                <div className="editor-head">
                  <div><h2 id="ed-h">{isNew ? "Rol nuevo" : name}</h2><p className="meta">{isNew ? "Rol propio · elige al menos un permiso" : `Rol propio · ${n} ${n === 1 ? "cuenta" : "cuentas"} · ${checked.length} permisos`}</p></div>
                </div>
                {state === "error" && <Note tone="bad" title="Elige al menos un permiso" anim>Un rol sin permisos no se puede guardar. Marca las herramientas que este rol debe abrir.</Note>}
                {state === "exito" && <div className="note ok pop" role="status"><Seal /><div><strong>Rol «Montaje local» guardado</strong>Julián Herrera recibe los cambios en su próxima solicitud.</div></div>}
                {state === "rechazo" && <Note tone="warn" title="«Montaje local» no se puede eliminar" anim>Tiene 1 cuenta (Julián Herrera). Muévela a otro rol en Cuentas y vuelve a intentarlo.</Note>}
                <Field id="rol-nombre" label="Nombre del rol" defaultValue={name} placeholder="Ej. Montaje local" />
                <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
                  <legend className="label">Permisos por herramienta</legend>
                  <div className="tools">
                    {TOOLS.map((t) => (
                      <div className="tool" key={t.tool} style={t.perms.some((p) => checked.includes(p.key)) ? { borderColor: "var(--accent)" } : undefined}>
                        <h3>{t.tool}</h3>
                        {t.perms.map((p) => (
                          <label className="perm" key={p.key} htmlFor={`pm-${p.key}`}>
                            <Checkbox id={`pm-${p.key}`} checked={checked.includes(p.key)} onCheckedChange={(v) => toggle(p.key, Boolean(v))} />
                            <span>{p.label}</span>
                          </label>
                        ))}
                      </div>
                    ))}
                  </div>
                </fieldset>
                <div className="editor-foot">
                  <div style={{ display: "grid", gap: 8, maxWidth: 420 }}>
                    {!isNew && (
                      <>
                        <Button variant="destructive" className="sm" disabled={n > 0} style={{ justifySelf: "start" }}><Trash2 aria-hidden="true" />Eliminar rol</Button>
                        {n > 0 && <p className="hint" style={{ margin: 0 }}>Tiene {n} {n === 1 ? "cuenta" : "cuentas"}: muévelas a otro rol para poder eliminarlo.</p>}
                      </>
                    )}
                  </div>
                  <Button size="lg"><Check aria-hidden="true" />{isNew ? "Crear rol" : "Guardar rol"}</Button>
                </div>
              </form>
            )}
          </Panel>
        </div>
      )}
    </>
  );
}

/* ───────────────────────── mi cuenta ───────────────────────── */
function Mine() {
  const { state } = useMockup();
  const busy = state === "cargando";
  const blank = state === "vacio";
  return (
    <>
      <div className="head">
        <div><Inflate text="Mi cuenta" /><p className="meta">Tu acceso a Pictures y tu contraseña</p></div>
      </div>
      <div className="mine">
        <Panel className="latex" i={0} aria-labelledby="mine-h">
          <h2 id="mine-h">David Torres</h2>
          <dl className="facts">
            <div><dt>Correo</dt><dd>davidt@sempertex.com</dd></div>
            <div><dt>Empresa</dt><dd>Sempertex</dd></div>
            <div><dt>Rol</dt><dd>Administrador</dd></div>
            <div><dt>Aviso de datos</dt><dd>Versión 1, aceptada el 2 nov 2026</dd></div>
          </dl>
          <div className="chips" aria-label="Herramientas de tu rol">
            {["Chat asistido", "Contador de globos", "Catálogo", "Calculadora de costos", "Decoraciones listas", "Taller 3D", "Gasto de IA", "Cuentas y roles"].map((c) => <span className="chip" key={c}>{c}</span>)}
          </div>
        </Panel>
        <Panel className="latex" i={1} aria-labelledby="pw-h">
          <form className="form" onSubmit={(e) => e.preventDefault()} noValidate>
            <h2 id="pw-h">Cambiar contraseña</h2>
            {state === "error" && <Note tone="bad" title="La contraseña actual no coincide" anim>Escríbela de nuevo. Después de varios intentos fallidos tendrás que esperar 15 minutos.</Note>}
            {state === "rechazo" && <Note tone="bad" title="La nueva contraseña no sirve" anim>Debe tener al menos 8 caracteres y ser igual en los dos campos.</Note>}
            {state === "exito" && <div className="note ok pop" role="status"><Seal /><div><strong>Contraseña cambiada</strong>Cerramos tus sesiones en otros navegadores; esta sigue abierta.</div></div>}
            <Field id="actual" label="Contraseña actual" type="password" autoComplete="current-password" defaultValue={blank ? "" : "arco-de-globos"} disabled={busy} error={state === "error" ? "No coincide con la guardada." : undefined} />
            <div className="row2">
              <Field id="m-nueva" label="Nueva contraseña" type="password" autoComplete="new-password" hint="Mínimo 8 caracteres." defaultValue={blank ? "" : state === "rechazo" ? "globo" : "guirnalda-2026"} disabled={busy} error={state === "rechazo" ? "Tiene 5 caracteres." : undefined} />
              <Field id="m-repite" label="Repite la nueva" type="password" autoComplete="new-password" defaultValue={blank ? "" : state === "rechazo" ? "globo" : "guirnalda-2026"} disabled={busy} />
            </div>
            <p className="hint" style={{ marginTop: -6 }}>Al cambiarla se cierran tus sesiones en otros navegadores.</p>
            <SubmitButton busy={busy} label="Cambiar contraseña" busyLabel="Guardando…" />
          </form>
        </Panel>
      </div>
    </>
  );
}

/* ───────────────────────── dialogs (scenes) ───────────────────────── */
function Dialogs() {
  const { scene, set } = useMockup();
  const close = () => set("scene", "");
  const [copied, setCopied] = React.useState(false);
  const [typed, setTyped] = React.useState("julian@decorarte.co");
  const invite = scene === "invitar" || scene === "invitar-duplicado";
  const link = scene === "enlace-invitacion" || scene === "enlace-restablecer";
  const dup = scene === "invitar-duplicado";
  return (
    <>
      <Dialog open={invite} onOpenChange={(o) => !o && close()}>
        <DialogContent showCloseButton={false}>
          <form className="dlg" onSubmit={(e) => e.preventDefault()} noValidate>
            <div><DialogTitle>Invitar persona</DialogTitle>
              <DialogDescription className="desc">Recibirás un enlace de un solo uso, válido 7 días, para enviárselo tú mismo.</DialogDescription></div>
            {dup && <Note tone="bad" title="Ese correo ya tiene cuenta" anim>lucia@globosyeventos.co pertenece a Lucía Gómez. Búscala en Cuentas para cambiar su rol o generar un enlace.</Note>}
            <div className="row2">
              <Field id="i-nombre" label="Nombre" defaultValue={dup ? "Lucía Gómez" : "Camila Suárez"} />
              <Field id="i-correo" label="Correo" type="email" defaultValue={dup ? "lucia@globosyeventos.co" : "camila.suarez@gmail.com"} error={dup ? "Ya registrado." : undefined} />
            </div>
            <div className="row2">
              <Field id="i-empresa" label="Empresa (opcional)" placeholder="Ej. Decorarte" />
              <Native id="i-rol" label="Rol o plan" value="Usuario · Plan 3" options={ROLE_NAMES} />
            </div>
            <div className="dlg-foot">
              <Button variant="ghost" type="button" onClick={close}>Cancelar</Button>
              <Button type="submit" onClick={() => !dup && set("scene", "enlace-invitacion")}><Link2 aria-hidden="true" />Crear invitación</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      <Dialog open={link} onOpenChange={(o) => !o && close()}>
        <DialogContent showCloseButton={false}>
          <div className="dlg">
            <div style={{ display: "flex", gap: 14, alignItems: "center" }}><Seal />
              <div><DialogTitle>{scene === "enlace-invitacion" ? "Invitación creada" : "Enlace para restablecer"}</DialogTitle>
                <DialogDescription className="desc">{scene === "enlace-invitacion" ? "Para Camila Suárez · Usuario · Plan 3 · vence el 3 nov a las 10:20." : "Para Lucía Gómez · vence mañana a las 10:20 (24 horas)."}</DialogDescription></div></div>
            <div className="link-box">
              <code id="enlace">{scene === "enlace-invitacion" ? "https://demo-decoracion.vercel.app/activar/q7Lw-29fK-xa4T-mB8e" : "https://demo-decoracion.vercel.app/restablecer/R3ta-k81P-zz0Q-wYc5"}</code>
              <Button className="sm" variant={copied ? "outline" : "default"} onClick={() => setCopied(true)} aria-describedby="enlace">
                {copied ? <><Check aria-hidden="true" />Copiado</> : <><Copy aria-hidden="true" />Copiar enlace</>}
              </Button>
            </div>
            <Note tone="warn" title="Solo lo verás esta vez">Cópialo y envíalo por tu canal habitual. Si se pierde, genera uno nuevo: el anterior sin usar deja de servir.</Note>
            <div className="dlg-foot"><Button onClick={close}>Listo</Button></div>
          </div>
        </DialogContent>
      </Dialog>

      <AlertDialog open={scene === "desactivar"} onOpenChange={(o) => !o && close()}>
        <AlertDialogContent>
          <div className="dlg">
            <div><AlertDialogTitle>¿Desactivar a Julián Herrera?</AlertDialogTitle>
              <AlertDialogDescription className="desc">Se cierran sus sesiones al instante y no podrá entrar. Su rol y su trabajo se conservan; puedes reactivarla cuando quieras.</AlertDialogDescription></div>
            <div className="dlg-foot"><Button variant="ghost" onClick={close}>Cancelar</Button><Button onClick={close}><Power aria-hidden="true" />Desactivar cuenta</Button></div>
          </div>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={scene === "eliminar"} onOpenChange={(o) => !o && close()}>
        <AlertDialogContent>
          <form className="dlg" onSubmit={(e) => e.preventDefault()} noValidate>
            <div><AlertDialogTitle>¿Eliminar la cuenta de Julián Herrera?</AlertDialogTitle>
              <AlertDialogDescription className="desc">No tiene proyectos ni decoraciones guardados. Se borran su nombre, correo y empresa; su gasto de IA queda como «Cuenta eliminada». No se puede deshacer.</AlertDialogDescription></div>
            <Field id="confirma" label="Escribe su correo para confirmar: julian@decorarte.co" value={typed} onChange={(e) => setTyped(e.target.value)} autoComplete="off" />
            <div className="dlg-foot"><Button variant="ghost" type="button" onClick={close}>Cancelar</Button>
              <Button variant="destructive" type="submit" disabled={typed !== "julian@decorarte.co"}><Trash2 aria-hidden="true" />Eliminar cuenta</Button></div>
          </form>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={scene === "eliminar-rol"} onOpenChange={(o) => !o && close()}>
        <AlertDialogContent>
          <div className="dlg">
            <div><AlertDialogTitle>¿Eliminar el rol «Comercial feria»?</AlertDialogTitle>
              <AlertDialogDescription className="desc">No tiene cuentas asignadas. Desaparece de la lista de roles y de los filtros; no afecta a nadie.</AlertDialogDescription></div>
            <div className="dlg-foot"><Button variant="ghost" onClick={close}>Cancelar</Button><Button variant="destructive" onClick={close}><Trash2 aria-hidden="true" />Eliminar rol</Button></div>
          </div>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

/* ───────────────────────── root ───────────────────────── */
function App() {
  const { view } = useMockup();
  React.useEffect(() => {
    const hidden = () => document.documentElement.toggleAttribute("data-tab-hidden", document.hidden);
    hidden();
    document.addEventListener("visibilitychange", hidden);
    return () => document.removeEventListener("visibilitychange", hidden);
  }, []);
  const signedIn = ORDER.includes(view);
  return (
    <>
      <style>{CSS}</style>
      {view === "login" && <Login />}
      {view === "activar" && <Activate />}
      {view === "restablecer" && <Reset />}
      {view === "aviso" && <NoticeGate />}
      {signedIn && (
        <Shell view={view}>
          {view === "cuentas" && <Accounts />}
          {view === "roles" && <Roles />}
          {view === "mi-cuenta" && <Mine />}
        </Shell>
      )}
      {signedIn && <Dialogs />}
    </>
  );
}

mountMockup(App, {
  title: "Cuentas y administración · dirección B · Escenario de inflado",
  views: [
    { id: "login", label: "Iniciar sesión" },
    { id: "activar", label: "Activar invitación" },
    { id: "restablecer", label: "Restablecer contraseña" },
    { id: "aviso", label: "Aviso de datos nuevo" },
    { id: "cuentas", label: "Cuentas (admin)" },
    { id: "roles", label: "Roles (admin)" },
    { id: "mi-cuenta", label: "Mi cuenta" },
  ],
  states: [
    { id: "normal", label: "Normal" },
    { id: "cargando", label: "Cargando" },
    { id: "vacio", label: "Vacío" },
    { id: "error", label: "Error" },
    { id: "rechazo", label: "Rechazo / enlace inválido" },
    { id: "exito", label: "Éxito" },
  ],
  scenes: [
    { id: "", label: "Ninguno" },
    { id: "menu", label: "Menú de cuenta abierto" },
    { id: "invitar", label: "Invitar persona" },
    { id: "invitar-duplicado", label: "Invitar · correo ya registrado" },
    { id: "enlace-invitacion", label: "Enlace de invitación (una vez)" },
    { id: "enlace-restablecer", label: "Enlace para restablecer" },
    { id: "desactivar", label: "Desactivar cuenta" },
    { id: "eliminar", label: "Eliminar cuenta (escribir correo)" },
    { id: "eliminar-rol", label: "Eliminar rol sin cuentas" },
  ],
  motion: "expressive",
});
