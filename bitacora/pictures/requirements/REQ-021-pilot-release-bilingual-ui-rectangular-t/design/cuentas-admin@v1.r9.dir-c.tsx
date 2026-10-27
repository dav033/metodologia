// Direction C (r9) for cuentas-admin@v1 — «Medidor y tubo 260».
// Tactile/playful: the decorator's own tools become the interface. Access screens sit under a balloon sizer ring whose
// latex balloon inflates with the password; administration navigates on a twisted modelling balloon (Sempertex 260);
// people are latex balloons that deflate when their account is deactivated; permissions are latex dots that inflate.
// Real shadcn/Base UI + Animate UI components, Motion springs, offline fonts (Unbounded display, Manrope text).
import * as React from "react";
import { AnimatePresence, motion } from "motion/react";
import { AlertCircle, Check, ChevronDown, Copy, KeyRound, Link2, Lock, LogOut, Plus, RotateCcw, Search, ShieldCheck, Trash2, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogContent, AlertDialogDescription, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { CopyButton } from "@animate-ui/react/primitives/buttons/copy";
import { mountMockup, useMockup } from "@kit/mockup";
import { useMotionProfile } from "@kit/motion";
import unbounded from "@fontsource-variable/unbounded/files/unbounded-latin-wght-normal.woff2";
import manrope from "@fontsource-variable/manrope/files/manrope-latin-wght-normal.woff2";
import mono from "@fontsource-variable/jetbrains-mono/files/jetbrains-mono-latin-wght-normal.woff2";

/* ---------- tokens: Pictures' own latex magenta (--acento-2 #d6216f, deepened for AA) on talc-mint, ink green ---------- */
// One line on purpose: kit/contrast.py reads this block from the built HTML exactly as it is applied.
const TOKENS = `<style id="c-tokens">:root,[data-theme=light]{--background:#eef6f2;--foreground:#14201d;--card:#ffffff;--card-foreground:#14201d;--popover:#ffffff;--popover-foreground:#14201d;--primary:#b0124c;--primary-foreground:#ffffff;--primary-hover:#930c3e;--primary-soft:#fde3ec;--secondary:#dceae4;--secondary-foreground:#14201d;--muted:#e3eee9;--muted-foreground:#43534e;--accent:#d6e7df;--accent-foreground:#14201d;--destructive:#b3261e;--destructive-foreground:#ffffff;--destructive-hover:#8f1d17;--destructive-soft:#fde4e1;--border:#c4d4cc;--input:#62776f;--ring:#b0124c;--success:#0f6b47;--success-soft:#dcf3e8;--warning:#7a5200;--warning-soft:#fff1cc;--info:#1d5f8a;--info-soft:#e0eef8;--sidebar:#e3eee9;--sidebar-foreground:#14201d;--sidebar-primary:#b0124c;--sidebar-primary-foreground:#ffffff;--sidebar-accent:#d6e7df;--sidebar-accent-foreground:#14201d;--sidebar-border:#c4d4cc;--sidebar-ring:#b0124c;--chart-1:#b0124c;--chart-2:#0f766e;--chart-3:#7a5200;--chart-4:#1d5f8a;--chart-5:#62776f;--overlay:rgb(20 32 29 / .52);--c-ground:#e2efe9;color-scheme:light}[data-theme=dark],.dark{--background:#0d1513;--foreground:#eef7f3;--card:#16211e;--card-foreground:#eef7f3;--popover:#1b2824;--popover-foreground:#eef7f3;--primary:#ff6aa0;--primary-foreground:#2a0514;--primary-hover:#ff8db6;--primary-soft:#3d1a28;--secondary:#22302c;--secondary-foreground:#eef7f3;--muted:#1f2c28;--muted-foreground:#a7bbb3;--accent:#263632;--accent-foreground:#eef7f3;--destructive:#ff8a7a;--destructive-foreground:#2a0805;--destructive-hover:#ffa699;--destructive-soft:#3d1f1b;--border:#2f413b;--input:#7f978f;--ring:#ff6aa0;--success:#6ee7b7;--success-soft:#14302a;--warning:#fcd34d;--warning-soft:#33290f;--info:#7cc4f5;--info-soft:#132c3d;--sidebar:#1f2c28;--sidebar-foreground:#eef7f3;--sidebar-primary:#ff6aa0;--sidebar-primary-foreground:#2a0514;--sidebar-accent:#263632;--sidebar-accent-foreground:#eef7f3;--sidebar-border:#2f413b;--sidebar-ring:#ff6aa0;--chart-1:#ff6aa0;--chart-2:#5eead4;--chart-3:#fcd34d;--chart-4:#7cc4f5;--chart-5:#7f978f;--overlay:rgb(4 8 7 / .72);--c-ground:#111c19;color-scheme:dark}</style>`;

const CSS = `
@font-face{font-family:"C Display";src:url(${unbounded}) format("woff2");font-weight:200 900;font-display:block}
@font-face{font-family:"C Text";src:url(${manrope}) format("woff2");font-weight:200 800;font-display:block}
@font-face{font-family:"C Mono";src:url(${mono}) format("woff2");font-weight:100 800;font-display:block}
:root{--c-k:1;--c-latex:cubic-bezier(.3,1.65,.45,1);--c-squash:cubic-bezier(.5,1.8,.4,.8);--c-settle:cubic-bezier(.2,.9,.25,1);
 --b-adm:#ff9cc2;--b-emp:#7ee0cf;--b-p1:#ffe27a;--b-p2:#ffc48a;--b-p3:#b8e986;--b-coord:#a8d1ff;--b-off:#c3ccc8;--b-ink:#14201d}
:root[data-motion=natural]{--c-k:.62}:root[data-motion=subtle]{--c-k:.36}
#app,[data-slot=dialog-content],[data-slot=alert-dialog-content],[data-slot=dropdown-menu-content]{font-family:"C Text",ui-sans-serif,system-ui,sans-serif;font-size:15px;line-height:1.5;color:var(--foreground)}
#app{background:var(--background)}
[data-slot=dialog-overlay],[data-slot=alert-dialog-overlay]{backdrop-filter:none!important;background:var(--overlay)!important}
.c-display,.c-title{font-family:"C Display",ui-sans-serif,system-ui,sans-serif;letter-spacing:-.02em;color:var(--foreground);margin:0}
.c-display{font-size:38px;line-height:1.08;font-weight:760}
.c-title{font-size:40px;line-height:1.05;font-weight:720}
.c-h2{font-family:"C Display",ui-sans-serif,system-ui,sans-serif;font-size:19px;line-height:1.25;font-weight:640;margin:0;letter-spacing:-.01em}
.c-lede{margin:0;color:var(--muted-foreground);font-size:16px;max-width:46ch}
.c-small{font-size:13px;color:var(--muted-foreground);margin:0}
.c-mono{font-family:"C Mono",ui-monospace,monospace;font-size:13px;font-variant-numeric:tabular-nums}
/* per-letter puff: display type inflates letter by letter (transform only, no layout shift) */
.c-word{display:inline-block;white-space:nowrap}
.c-l{display:inline-block;transform-origin:50% 85%;animation:c-puff calc(640ms*var(--c-k)) var(--c-settle) both;animation-delay:calc(var(--i)*32ms*var(--c-k) + 120ms*var(--c-k))}
@keyframes c-puff{0%{transform:scale(.35,.25) translateY(.25em)}55%{transform:scale(1.16,1.12) translateY(-.04em)}80%{transform:scale(.97,1.02)}100%{transform:none}}
/* focus: the ring snaps tight like a tied knot */
#app :focus-visible,[data-slot$=content] :focus-visible,[data-slot$=content]:focus-visible{outline:3px solid var(--ring);outline-offset:2px;animation:c-knot-ring calc(240ms*var(--c-k)) var(--c-latex)}
@keyframes c-knot-ring{from{outline-offset:8px}to{outline-offset:2px}}
/* buttons: latex press — squash on press, lift on hover */
.c-btn{height:46px;padding:0 22px;border-radius:999px;font:700 15px/1 "C Text",ui-sans-serif,system-ui,sans-serif;gap:8px;border:2px solid transparent;
 transition:transform calc(180ms*var(--c-k)) var(--c-latex),background-color 160ms ease,border-color 160ms ease,color 160ms ease;transform-origin:50% 100%}
.c-btn:hover:not(:disabled){transform:translateY(-2px)}
.c-btn:active:not(:disabled){transform:scale(.95,1.05) translateY(1px);transition-duration:90ms}
.c-btn svg{width:18px;height:18px}
.c-btn-pri{background:var(--primary);color:var(--primary-foreground);border-color:var(--primary)}
.c-btn-pri:hover:not(:disabled){background:var(--primary-hover);border-color:var(--primary-hover)}
.c-btn-out{background:var(--card);color:var(--foreground);border-color:var(--input)}
.c-btn-out:hover:not(:disabled){background:var(--muted)}
.c-btn-ghost{background:transparent;color:var(--foreground);border-color:transparent}
.c-btn-ghost:hover:not(:disabled){background:var(--muted)}
.c-btn-danger{background:var(--destructive);color:var(--destructive-foreground);border-color:var(--destructive)}
.c-btn-danger:hover:not(:disabled){background:var(--destructive-hover)}
.c-btn-danger-out{background:var(--card);color:var(--destructive);border-color:var(--destructive)}
.c-btn:disabled{opacity:1!important;background:var(--muted);color:var(--muted-foreground);border-color:var(--input);cursor:not-allowed}
.c-btn-sm{height:38px;padding:0 16px;font-size:14px}
.c-btn-block{width:100%}
/* fields */
.c-field{display:grid;gap:6px}
.c-label{font-weight:700;font-size:14px;color:var(--foreground)}
.c-input{height:46px!important;border-radius:16px!important;border:2px solid var(--input)!important;background:var(--card)!important;padding:0 14px!important;font:500 15px "C Text",ui-sans-serif,system-ui,sans-serif!important;color:var(--foreground)!important;box-shadow:none!important;transition:border-color 160ms ease,transform calc(200ms*var(--c-k)) var(--c-latex)}
.c-input:focus-visible{transform:scale(1.01)}
.c-input[aria-invalid=true]{border-color:var(--destructive)!important}
.c-input:disabled{opacity:1!important;background:var(--muted)!important}
.c-input::placeholder{color:var(--muted-foreground)}
.c-hint{font-size:13px;color:var(--muted-foreground);margin:0}
.c-err{font-size:13px;color:var(--destructive);margin:0;font-weight:600}
.c-select{height:46px;border-radius:16px;border:2px solid var(--input);background:var(--card);color:var(--foreground);padding:0 38px 0 14px;font:600 14px "C Text",ui-sans-serif,system-ui,sans-serif;appearance:none;
 background-image:linear-gradient(45deg,transparent 50%,currentColor 50%),linear-gradient(135deg,currentColor 50%,transparent 50%);background-position:calc(100% - 20px) 50%,calc(100% - 14px) 50%;background-size:6px 6px;background-repeat:no-repeat}
.c-alert{display:grid;grid-template-columns:22px 1fr;gap:10px;align-items:start;padding:14px 16px;border-radius:18px;border:2px solid var(--destructive);background:var(--destructive-soft);color:var(--foreground)}
.c-alert svg{color:var(--destructive);width:22px;height:22px}
.c-alert b{display:block;margin-bottom:2px}
.c-alert p{margin:0;font-size:14px}
.c-alert-ok{border-color:var(--success);background:var(--success-soft)}.c-alert-ok svg{color:var(--success)}
.c-alert-warn{border-color:var(--warning);background:var(--warning-soft)}.c-alert-warn svg{color:var(--warning)}
/* latex dot checkbox (Animate UI checkbox restyled): inflates when checked */
.c-latex{width:24px!important;height:24px!important;border-radius:50%!important;border:2px solid var(--input)!important;background:var(--card)!important;flex:none;
 transition:transform calc(200ms*var(--c-k)) var(--c-latex),background-color 140ms ease}
.c-latex[data-checked]{background:var(--primary)!important;border-color:var(--primary)!important;color:var(--primary-foreground)!important;animation:c-inflate-dot calc(380ms*var(--c-k)) var(--c-settle)}
.c-latex:active{transform:scale(.86,1.1)}
.c-latex[data-disabled]{opacity:1!important;cursor:default}
.c-latex[data-disabled][data-checked]{background:var(--muted-foreground)!important;border-color:var(--muted-foreground)!important;color:var(--card)!important;animation:none}
@keyframes c-inflate-dot{0%{transform:scale(.55)}55%{transform:scale(1.2)}80%{transform:scale(.95)}100%{transform:none}}
.c-check{display:flex;gap:12px;align-items:flex-start;cursor:pointer;font-size:14px;line-height:1.45;padding:4px 0}
.c-check>span{padding-top:2px}
/* stage + sizer ring */
.c-stage{position:relative;overflow:hidden;min-height:calc(100svh - var(--mockup-bar-h,0px));display:flex;flex-direction:column;align-items:center;padding:40px 20px 56px;background:
 radial-gradient(circle at 12% 18%,var(--c-ground) 0 120px,transparent 121px),radial-gradient(circle at 90% 82%,var(--c-ground) 0 170px,transparent 171px),var(--background)}
.c-float{position:absolute;width:140px;pointer-events:none;z-index:0;animation:c-bob calc(5200ms) ease-in-out infinite alternate}
.c-float.f1{left:4%;top:14%;width:120px;color:var(--b-p1)}.c-float.f2{right:5%;top:8%;width:150px;color:var(--b-emp);animation-delay:-1.8s}.c-float.f3{right:9%;bottom:6%;width:110px;color:var(--b-adm);animation-delay:-3.1s}
@keyframes c-bob{from{transform:translateY(0) rotate(-2deg)}to{transform:translateY(-14px) rotate(3deg)}}
.c-hidden .c-float,.c-hidden .c-bob-soft{animation-play-state:paused}
.c-column{position:relative;z-index:1;width:min(480px,100%);display:flex;flex-direction:column;align-items:center}
.c-column.wide{width:min(620px,100%)}
.c-ring{position:relative;z-index:2;width:156px;height:156px;border-radius:50%;padding:14px;background:var(--card);border:3px dashed var(--input);display:grid;place-items:center;box-shadow:0 0 0 10px var(--background)}
.c-ring-in{width:100%;height:100%;display:grid;place-items:end center}
.c-ring .c-bob-soft{width:92px;animation:c-bob 4200ms ease-in-out infinite alternate}
.c-gauge{width:92px;color:var(--primary);transform-origin:50% 88%}
.c-ring[data-mood=deflated] .c-gauge{color:var(--b-off)}
.c-ring[data-mood=deflated]{border-style:solid}
.c-ring[data-mood=busy] .c-gauge{animation:c-breathe 900ms ease-in-out infinite alternate}
@keyframes c-breathe{from{transform:scale(.9,.86)}to{transform:scale(1.04,1.02)}}
.c-board{position:relative;z-index:1;width:100%;margin-top:-72px;padding:96px 32px 28px;background:var(--card);border:2px solid var(--border);border-radius:36px;display:flex;flex-direction:column;gap:20px;
 transform-origin:50% 0;animation:c-board-in calc(760ms*var(--c-k)) var(--c-settle) both}
@keyframes c-board-in{0%{transform:translateY(26px) scale(.92,.8)}55%{transform:translateY(-4px) scale(1.03,.98)}80%{transform:scale(.995,1.01)}100%{transform:none}}
.c-board[data-wobble=true]{animation:c-board-in calc(760ms*var(--c-k)) var(--c-settle) both,c-wobble calc(520ms*var(--c-k)) var(--c-latex) calc(780ms*var(--c-k)) 1}
@keyframes c-wobble{0%,100%{transform:none}20%{transform:translateX(-8px) scale(1.02,.98)}40%{transform:translateX(7px) scale(.99,1.01)}60%{transform:translateX(-4px)}80%{transform:translateX(2px)}}
.c-rivet{position:absolute;width:10px;height:10px;border-radius:50%;background:var(--border)}
.c-rivet.r1{left:18px;top:18px}.c-rivet.r2{right:18px;top:18px}
.c-brand{display:flex;align-items:center;gap:10px;font:700 15px "C Display",ui-sans-serif,system-ui,sans-serif;color:var(--foreground)}
.c-brand svg{width:22px;color:var(--primary)}
.c-form{display:flex;flex-direction:column;gap:16px}
.c-who{display:grid;grid-template-columns:auto 1fr;gap:12px;align-items:center;padding:14px 16px;border-radius:20px;background:var(--muted);border:2px solid var(--border)}
.c-who b{display:block;font-size:16px}.c-who span{font-size:14px;color:var(--muted-foreground)}
.c-notice{max-height:210px;overflow:auto;padding:16px 18px;border-radius:20px;border:2px solid var(--input);background:var(--background);font-size:14px;line-height:1.6}
.c-notice h3{margin:0 0 8px;font:700 15px "C Text",ui-sans-serif,system-ui,sans-serif}
.c-notice p{margin:0}
.c-notice mark{background:var(--warning-soft);color:var(--foreground);border-bottom:2px dashed var(--warning);padding:0 3px;border-radius:4px}
.c-legal{display:inline-flex;align-items:center;gap:6px;margin-bottom:10px;padding:5px 10px;border-radius:999px;background:var(--warning-soft);color:var(--foreground);font-size:12px;font-weight:700;border:1.5px solid var(--warning)}
.c-meter{display:flex;align-items:center;gap:10px;font-size:13px;color:var(--muted-foreground)}
.c-meter .c-ok{color:var(--success);font-weight:700}
.c-success{display:flex;flex-direction:column;gap:14px}
.c-foot{border-top:2px dashed var(--border);padding-top:16px;font-size:13px;color:var(--muted-foreground);margin:0}
/* signed-in shell */
.c-shell{min-height:calc(100svh - var(--mockup-bar-h,0px));background:var(--background)}
.c-head{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:16px;padding:14px 24px;background:var(--card);border-bottom:2px solid var(--border)}
.c-head .c-brand{justify-self:start}
.c-head-end{justify-self:end}
.c-tube{display:flex;align-items:center;justify-content:center}
.c-seg{position:relative;height:44px;min-width:112px;padding:0 22px;border-radius:999px;border:2px solid var(--input);background:var(--card);color:var(--foreground);font:700 14px "C Text",ui-sans-serif,system-ui,sans-serif;cursor:pointer;
 transition:transform calc(220ms*var(--c-k)) var(--c-latex);transform-origin:50% 50%}
.c-seg:hover{transform:scale(1.05,.93)}
.c-seg:active{transform:scale(.94,1.06);transition-duration:90ms}
.c-seg[aria-current=page]{color:var(--primary-foreground);border-color:var(--primary)}
.c-bulge{position:absolute;inset:-2px;border-radius:999px;background:var(--primary);z-index:0;animation:c-bulge calc(560ms*var(--c-k)) var(--c-settle) both}
@keyframes c-bulge{0%{transform:scale(.6,.5)}55%{transform:scale(1.1,1.12)}80%{transform:scale(.97,.98)}100%{transform:none}}
.c-seg-label{position:relative;z-index:1}
.c-twist{width:14px;height:20px;background:var(--input);clip-path:polygon(0 0,100% 0,62% 50%,100% 100%,0 100%,38% 50%);flex:none}
.c-account{display:inline-flex;align-items:center;gap:10px;height:48px;padding:3px 14px 3px 4px;border-radius:999px;border:2px solid var(--input);background:var(--card);color:var(--foreground);cursor:pointer;text-align:left;
 transition:transform calc(200ms*var(--c-k)) var(--c-latex)}
.c-account:hover{transform:translateY(-2px)}
.c-account b{display:block;font-size:14px;line-height:1.2}.c-account small{display:block;font-size:12px;line-height:1.2;color:var(--muted-foreground)}
.c-account svg.c-chev{width:16px;height:16px;color:var(--muted-foreground)}
.c-menu{min-width:250px!important;padding:8px!important;border-radius:20px!important;border:2px solid var(--border);box-shadow:0 18px 40px -18px rgb(0 0 0 / .35)!important}
.c-menu-who{padding:10px 12px 12px;display:grid;gap:2px}
.c-menu-who b{font-size:15px}.c-menu-who span{font-size:13px;color:var(--muted-foreground)}
.c-menu [data-slot=dropdown-menu-item]{min-height:42px;border-radius:14px;padding:0 12px;font-size:14px;font-weight:600;gap:10px}
.c-main{max-width:1180px;margin:0 auto;padding:32px 24px 56px;display:flex;flex-direction:column;gap:24px;transform-origin:50% 0;animation:c-squeeze calc(560ms*var(--c-k)) var(--c-settle) both}
@keyframes c-squeeze{0%{transform:translateY(14px) scale(.975,1.02)}60%{transform:translateY(-2px) scale(1.005,.997)}100%{transform:none}}
.c-titlebar{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;flex-wrap:wrap}
.c-titlebar>div{display:grid;gap:8px}
.c-tools{display:grid;grid-template-columns:minmax(220px,1fr) 220px 200px;gap:12px}
.c-search{position:relative}
.c-search svg{position:absolute;left:14px;top:50%;width:18px;height:18px;transform:translateY(-50%);color:var(--muted-foreground);pointer-events:none}
.c-search .c-input{padding-left:42px!important;width:100%}
.c-panel{background:var(--card);border:2px solid var(--border);border-radius:28px;padding:8px 24px}
.c-row{display:grid;grid-template-columns:minmax(230px,2.2fr) minmax(120px,1.1fr) minmax(150px,1.3fr) minmax(130px,1fr) minmax(110px,.9fr) auto;gap:16px;align-items:center;padding:14px 0;border-top:1.5px solid var(--border)}
.c-row:first-child{border-top:0}
.c-row-head{font-size:13px;color:var(--muted-foreground);font-weight:600;padding:10px 0}
.c-row-in{animation:c-string calc(600ms*var(--c-k)) var(--c-settle) both;animation-delay:calc(var(--i)*50ms*var(--c-k));transform-origin:30% 0}
@keyframes c-string{0%{transform:translateY(-14px) rotate(-1.4deg)}60%{transform:translateY(2px) rotate(.4deg)}100%{transform:none}}
.c-person{display:grid;grid-template-columns:auto 1fr;gap:12px;align-items:center;min-width:0}
.c-person b{display:block;font-size:15px}.c-person span{display:block;font-size:13px;color:var(--muted-foreground);overflow-wrap:anywhere}
.c-av{position:relative;width:38px;height:46px;flex:none;display:grid;place-items:start center;transition:transform calc(560ms*var(--c-k)) var(--c-squash);transform-origin:50% 100%}
.c-av svg{position:absolute;inset:0;width:100%;height:100%}
.c-av i{position:relative;font:800 12px/1 "C Display",ui-sans-serif,system-ui,sans-serif;font-style:normal;color:var(--b-ink);margin-top:12px}
.c-av[data-off=true]{transform:scale(1.08,.66)}
.c-av.lg{width:64px;height:78px}.c-av.lg i{font-size:18px;margin-top:20px}
.c-pill{display:inline-flex;align-items:center;gap:7px;padding:5px 11px;border-radius:999px;font-size:13px;font-weight:700;border:1.5px solid currentColor;white-space:nowrap;justify-self:start}
.c-pill::before{content:"";width:8px;height:8px;border-radius:50%;background:currentColor}
.c-pill.activa{color:var(--success);background:var(--success-soft)}
.c-pill.desactivada{color:var(--muted-foreground);background:var(--muted)}
.c-pill.pendiente{color:var(--warning);background:var(--warning-soft)}
.c-lbl{display:none;font-size:12px;color:var(--muted-foreground);font-weight:600}
.c-empty{display:grid;grid-template-columns:auto 1fr;gap:20px;align-items:center;padding:28px 4px}
.c-empty .c-gauge{width:64px;color:var(--b-off)}
.c-empty>div{display:grid;gap:10px;justify-items:start}
/* roles */
.c-roles{display:grid;grid-template-columns:300px 1fr;gap:24px;align-items:start}
.c-rail{display:flex;flex-direction:column;gap:6px;padding:18px;background:var(--card);border:2px solid var(--border);border-radius:28px}
.c-rail h2{font-size:13px;font-weight:700;color:var(--muted-foreground);margin:8px 6px 4px}
.c-rail h2:first-child{margin-top:0}
.c-tag{display:grid;grid-template-columns:auto 1fr auto;gap:10px;align-items:center;min-height:48px;padding:6px 12px;border-radius:16px;border:2px solid transparent;background:transparent;color:var(--foreground);text-align:left;cursor:pointer;font:600 14px "C Text",ui-sans-serif,system-ui,sans-serif;
 transition:transform calc(200ms*var(--c-k)) var(--c-latex),background-color 140ms ease}
.c-tag:hover{background:var(--muted);transform:translateX(3px)}
.c-tag[aria-pressed=true]{background:var(--primary-soft);border-color:var(--primary)}
.c-tag .c-dot{width:14px;height:17px;border-radius:50% 50% 46% 46%/56% 56% 44% 44%}
.c-tag small{font-size:12px;color:var(--muted-foreground);display:inline-flex;gap:4px;align-items:center}
.c-tag small svg{width:13px;height:13px}
.c-editor{display:flex;flex-direction:column;gap:20px;padding:28px;background:var(--card);border:2px solid var(--border);border-radius:28px}
.c-boards{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}
.c-tool{padding:16px 18px;border-radius:22px;border:2px solid var(--border);background:var(--background);display:flex;flex-direction:column;gap:6px}
.c-tool header{display:flex;align-items:baseline;justify-content:space-between;gap:10px;margin-bottom:4px}
.c-tool header b{font-size:15px}
.c-tool.wide{grid-column:1/-1}
.c-tool.wide .c-tool-list{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));column-gap:16px}
.c-readonly{display:flex;gap:10px;align-items:center;padding:12px 16px;border-radius:18px;background:var(--muted);border:2px solid var(--border);font-size:14px}
.c-readonly svg{width:18px;height:18px;color:var(--muted-foreground);flex:none}
.c-editor-foot{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;border-top:2px dashed var(--border);padding-top:18px}
/* mi cuenta */
.c-me{display:grid;grid-template-columns:360px 1fr;gap:24px;align-items:start}
.c-badge-card{display:flex;flex-direction:column;gap:16px;padding:28px;background:var(--card);border:2px solid var(--border);border-radius:28px;position:relative}
.c-badge-card .c-hole{width:44px;height:12px;border-radius:999px;background:var(--background);border:2px solid var(--border);align-self:center}
.c-facts{display:grid;gap:10px;margin:0}
.c-facts div{display:grid;grid-template-columns:110px 1fr;gap:10px;font-size:14px}
.c-facts dt{color:var(--muted-foreground)}.c-facts dd{margin:0;font-weight:600;overflow-wrap:anywhere}
.c-chips{display:flex;flex-wrap:wrap;gap:8px}
.c-chip{padding:5px 12px;border-radius:999px;background:var(--muted);border:1.5px solid var(--border);font-size:13px;font-weight:600}
/* dialogs */
.c-dialog{max-width:min(560px,calc(100% - 2rem))!important;width:100%;padding:28px!important;border-radius:30px!important;border:2px solid var(--border);gap:18px!important;box-shadow:0 30px 60px -24px rgb(0 0 0 / .4);
 max-height:calc(100svh - 2rem);overflow:auto;animation:c-dialog-in calc(520ms*var(--c-k)) var(--c-settle) both}
@keyframes c-dialog-in{0%{transform:scale(.9,.82)}55%{transform:scale(1.025,1.01)}100%{transform:none}}
.c-dialog-title{font:680 24px/1.15 "C Display",ui-sans-serif,system-ui,sans-serif!important;letter-spacing:-.015em;color:var(--foreground)}
.c-dialog-desc{font-size:14px!important;color:var(--muted-foreground)!important;margin:0}
.c-dialog-foot{display:flex;justify-content:flex-end;gap:10px;flex-wrap:wrap;padding-top:4px}
.c-sec{display:grid;gap:10px;padding:16px 0 0;border-top:1.5px solid var(--border)}
.c-sec h3{margin:0;font-size:14px;font-weight:700}
.c-inline{display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.c-inline .c-select{flex:1;min-width:180px}
.c-ticket{position:relative;display:grid;gap:10px;padding:18px 18px 16px;border-radius:20px;border:2px dashed var(--input);background:var(--background);transform-origin:50% -24px}
.c-ticket[data-swing=true]{animation:c-swing calc(760ms*var(--c-k)) var(--c-latex)}
@keyframes c-swing{0%{transform:none}25%{transform:rotate(-4deg)}50%{transform:rotate(3deg)}75%{transform:rotate(-1.2deg)}100%{transform:none}}
.c-ticket code{display:block;font-family:"C Mono",ui-monospace,monospace;font-size:13px;overflow-wrap:anywhere;color:var(--foreground)}
.c-why{display:grid;grid-template-columns:20px 1fr;gap:10px;padding:12px 14px;border-radius:16px;background:var(--muted);border:2px solid var(--border);font-size:14px}
.c-why svg{width:20px;height:20px;color:var(--muted-foreground)}
.c-tension{display:grid;grid-template-columns:72px 1fr;gap:16px;align-items:center}
.c-tension .c-gauge{width:64px;color:var(--destructive)}
.c-skel{border-radius:14px!important;background:var(--muted)!important}
@media (max-width:1023px){
 .c-tools{grid-template-columns:1fr 1fr}.c-search{grid-column:1/-1}
 .c-row{grid-template-columns:minmax(0,1.6fr) minmax(0,1fr) auto;row-gap:8px}
 .c-row-head{display:none}
 .c-row .c-company{display:none}
 .c-roles{grid-template-columns:1fr}
 .c-rail{flex-direction:row;flex-wrap:wrap}.c-rail h2{width:100%}
 .c-tag{flex:1 1 220px}
 .c-me{grid-template-columns:1fr}
}
@media (max-width:640px){
 .c-display{font-size:30px}.c-title{font-size:30px}
 .c-stage{padding:32px 20px 40px}
 .c-board{padding:92px 20px 22px;border-radius:30px}
 .c-float{display:none}
 .c-head{grid-template-columns:1fr auto;padding:12px 20px}
 .c-tube{grid-column:1/-1;grid-row:2;justify-content:stretch}
 .c-seg{flex:1;min-width:0;padding:0 10px}
 .c-account .c-account-txt{display:none}
 .c-main{padding:24px 20px 40px}
 .c-titlebar .c-btn{width:100%}
 .c-tools{grid-template-columns:1fr}
 .c-panel{padding:4px 20px}
 .c-row{grid-template-columns:1fr;gap:8px;padding:16px 0}
 .c-row .c-company{display:block}
 .c-lbl{display:block}
 .c-row-cell{display:grid;grid-template-columns:110px 1fr;align-items:center;gap:8px}
 .c-row .c-btn{width:100%}
 .c-boards{grid-template-columns:1fr}.c-tool.wide .c-tool-list{grid-template-columns:1fr}
 .c-editor,.c-badge-card{padding:20px}
 .c-facts div{grid-template-columns:96px 1fr}
 .c-dialog{padding:20px!important}
 .c-empty{grid-template-columns:1fr}
}
@media (prefers-reduced-motion:reduce){#app *,[data-slot$=content] *,[data-slot$=content]{animation:none!important}}
[data-reduced-motion] #app *,[data-reduced-motion] [data-slot$=content] *,[data-reduced-motion] [data-slot$=content]{animation:none!important}
`;

(() => {
  document.head.insertAdjacentHTML("beforeend", TOKENS);
  const style = document.createElement("style");
  style.id = "c-direction";
  style.textContent = CSS;
  document.head.append(style);
  // ambient balloons pause while the tab is hidden
  document.addEventListener("visibilitychange", () => document.documentElement.classList.toggle("c-hidden", document.hidden));
})();

/* ---------- product data (illustrative; one source for every count) ---------- */
type RoleId = "coord" | "p1" | "p2" | "p3" | "emp" | "adm";
const TOOLS: { id: string; name: string; perms: [string, string][] }[] = [
  { id: "chat", name: "Chat asistido", perms: [["chat", "Usar el chat asistido"]] },
  { id: "contador", name: "Contador de globos", perms: [["contador", "Contar los globos de un diseño"]] },
  { id: "catalogo", name: "Catálogo", perms: [["catalogo", "Ver el catálogo de productos"]] },
  { id: "costos", name: "Calculadora de costos", perms: [["costos", "Calcular costos de un montaje"]] },
  { id: "deco", name: "Decoraciones listas", perms: [["deco", "Explorar decoraciones listas"]] },
  { id: "taller", name: "Taller 3D", perms: [["t.abrir", "Abrir el Taller 3D"], ["t.ia", "Escena con IA"], ["t.planos", "Planos de montaje"], ["t.hoja", "Hoja de montaje"], ["t.exportar", "Exportar a Blender"], ["t.proyectos", "Guardar proyectos propios"], ["t.deco", "Guardar decoraciones propias"]] },
  { id: "interno", name: "Equipo interno", perms: [["i.proyectos", "Ver proyectos de todas las cuentas"], ["i.gasto", "Ver el gasto de IA"], ["i.herramientas", "Herramientas internas"]] },
  { id: "admin", name: "Administración", perms: [["a.cuentas", "Gestionar cuentas"], ["a.roles", "Gestionar roles"], ["a.textos", "Corregir textos en inglés"]] },
];
const P1 = ["chat", "contador", "catalogo"];
const P2 = [...P1, "costos", "deco"];
const P3 = [...P2, "t.abrir", "t.ia", "t.planos", "t.hoja", "t.exportar", "t.proyectos", "t.deco"];
const EMP = [...P3, "i.proyectos", "i.gasto", "i.herramientas"];
const ADM = [...EMP, "a.cuentas", "a.roles", "a.textos"];
const ROLES: Record<RoleId, { name: string; system: boolean; perms: string[]; color: string; first: string }> = {
  coord: { name: "Coordinación de eventos", system: false, perms: [...P2, "t.abrir", "t.hoja"], color: "var(--b-coord)", first: "Chat asistido" },
  p1: { name: "Usuario · Plan 1", system: true, perms: P1, color: "var(--b-p1)", first: "Chat asistido" },
  p2: { name: "Usuario · Plan 2", system: true, perms: P2, color: "var(--b-p2)", first: "Chat asistido" },
  p3: { name: "Usuario · Plan 3", system: true, perms: P3, color: "var(--b-p3)", first: "Chat asistido" },
  emp: { name: "Empleado interno", system: true, perms: EMP, color: "var(--b-emp)", first: "Chat asistido" },
  adm: { name: "Administrador", system: true, perms: ADM, color: "var(--b-adm)", first: "Chat asistido" },
};
type Acct = { id: string; name: string; email: string; company: string; role: RoleId; state: "activa" | "desactivada" | "pendiente"; last: string; work: string; lastAdmin?: boolean };
const ACCOUNTS: Acct[] = [
  { id: "valentina", name: "Valentina Ospina", email: "valentina.ospina@sempertex.com", company: "Sempertex", role: "adm", state: "activa", last: "hace 3 min", work: "", lastAdmin: true },
  { id: "julian", name: "Julián Rojas", email: "julian.rojas@sempertex.com", company: "Sempertex", role: "emp", state: "activa", last: "hoy, 08:41", work: "5 proyectos" },
  { id: "ana", name: "Ana Mejía", email: "ana@decoracionesmejia.co", company: "Decoraciones Mejía", role: "p2", state: "activa", last: "ayer, 17:20", work: "3 proyectos y 1 decoración" },
  { id: "camilo", name: "Camilo Restrepo", email: "camilo@globoarte.com.co", company: "GloboArte", role: "p3", state: "activa", last: "24 oct, 11:05", work: "7 proyectos" },
  { id: "sofia", name: "Sofía Duarte", email: "sofia@salonesduarte.com", company: "Salones Duarte", role: "coord", state: "activa", last: "23 oct, 16:48", work: "2 proyectos" },
  { id: "andres", name: "Andrés Patiño", email: "andres.patino@sempertex.com", company: "Sempertex", role: "emp", state: "activa", last: "25 oct, 09:12", work: "" },
  { id: "laura", name: "Laura Cano", email: "lauracano.eventos@gmail.com", company: "", role: "p1", state: "desactivada", last: "12 oct, 10:30", work: "" },
  { id: "mariana", name: "Mariana Gil", email: "mariana@fiestaviva.co", company: "Fiesta Viva", role: "p2", state: "pendiente", last: "Sin activar", work: "" },
];
const countOf = (r: RoleId) => ACCOUNTS.filter((a) => a.role === r).length;
const STATE_LABEL = { activa: "Activa", desactivada: "Desactivada", pendiente: "Invitación pendiente" } as const;
const INVITE_LINK = "https://demo-decoracion.vercel.app/activar#t=7Qm2kZ9rXa4PcW8e";
const RESET_LINK = "https://demo-decoracion.vercel.app/restablecer#t=Rf3nVb81LqT0sYe2";
const initials = (n: string) => n.split(" ").map((p) => p[0]).slice(0, 2).join("");

/* ---------- balloon drawing ---------- */
function BalloonSvg({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 100 132" className={className} aria-hidden="true">
      <path d="M50 4C77 4 94 27 94 52c0 29-22 52-44 56C28 104 6 81 6 52 6 27 23 4 50 4Z" fill="currentColor" />
      <path d="M43 113h14l-7-8z" fill="currentColor" />
      <ellipse cx="34" cy="30" rx="9" ry="14" transform="rotate(-24 34 30)" fill="#fff" opacity=".42" />
      <path d="M50 113c-6 6 6 10 0 18" stroke="var(--input)" strokeWidth="2.5" fill="none" strokeLinecap="round" />
    </svg>
  );
}
function Mark() {
  return (
    <svg viewBox="0 0 24 30" aria-hidden="true"><path d="M12 1c6 0 10 5 10 11 0 7-5 12-10 13C7 24 2 19 2 12 2 6 6 1 12 1Z" fill="currentColor" /><path d="M10 26h4l-2-2z" fill="currentColor" /></svg>
  );
}
function Avatar({ acct, large, off }: { acct: Pick<Acct, "name" | "role">; large?: boolean; off?: boolean }) {
  return (
    <span className={`c-av${large ? " lg" : ""}`} data-off={off ? "true" : "false"} style={{ color: off ? "var(--b-off)" : ROLES[acct.role].color }} aria-hidden="true">
      <BalloonSvg /><i>{initials(acct.name)}</i>
    </span>
  );
}
/** The sizer ring: a latex balloon that inflates to fill it (ratio 0..1). */
function Gauge({ ratio = 1, mood = "idle" }: { ratio?: number; mood?: "idle" | "busy" | "deflated" | "tight" }) {
  const { spring, reduced, profile } = useMotionProfile();
  const latex = profile === "expressive" ? { type: "spring" as const, stiffness: 300, damping: 11, mass: 0.8 } : spring;
  const s = mood === "deflated" ? 0.62 : 0.42 + 0.58 * Math.max(0, Math.min(1, ratio));
  const sy = mood === "deflated" ? 0.42 : mood === "tight" ? s * 0.9 : s;
  return (
    <div className="c-ring" data-mood={mood} aria-hidden="true">
      <div className="c-ring-in">
        <div className={mood === "idle" ? "c-bob-soft" : ""} style={{ width: 92 }}>
          <motion.div className="c-gauge" initial={reduced ? false : { scaleX: 0.3, scaleY: 0.25 }} animate={{ scaleX: s, scaleY: sy }} transition={reduced ? { duration: 0 } : latex}>
            <BalloonSvg />
          </motion.div>
        </div>
      </div>
    </div>
  );
}
/** Display type that inflates letter by letter; screen readers get the plain heading text. */
function Puff({ text, as: Tag = "h1", className = "c-display" }: { text: string; as?: "h1" | "h2"; className?: string }) {
  let i = 0;
  return (
    <Tag className={className} aria-label={text}>
      {text.split(" ").map((w, wi) => (
        <React.Fragment key={wi}>
          {wi > 0 && " "}
          <span className="c-word" aria-hidden="true">{[...w].map((ch) => <span key={i} className="c-l" style={{ ["--i" as string]: i++ }}>{ch}</span>)}</span>
        </React.Fragment>
      ))}
    </Tag>
  );
}

/* ---------- copy for the access screens (ES / EN: the browser decides) ---------- */
const NOTICE = {
  es: { title: "Aviso de tratamiento de datos personales", body: [
    ["mark", "[RAZÓN SOCIAL DE SEMPERTEX]"], ["", " tratará tus datos personales —nombre, correo, empresa (si la indicas), el rol y el plan que te asignen, y las fechas de invitación, activación y último acceso— para darte acceso a Pictures durante el piloto, administrar tu cuenta y medir el uso de las herramientas, incluido el consumo de inteligencia artificial. Los proyectos y decoraciones que guardes quedan asociados a tu cuenta. Puedes conocer, actualizar, rectificar o pedir la supresión de tus datos, y revocar esta autorización, escribiendo a "],
    ["mark", "[CORREO PARA DERECHOS]"], ["", ". La política de tratamiento de datos está en "], ["mark", "[URL DE LA POLÍTICA]"], ["", ". Al activar tu cuenta declaras que leíste este aviso y autorizas el tratamiento descrito, conforme a la Ley 1581 de 2012."]],
    legal: "Campos entre corchetes: pendientes de revisión legal" },
  en: { title: "Personal data notice", body: [
    ["mark", "[SEMPERTEX LEGAL NAME]"], ["", " will process your personal data —name, email, company (if you provide it), the role and plan assigned to you, and the dates of invitation, activation and last access— to give you access to Pictures during the pilot, manage your account and measure the use of the tools, including artificial-intelligence usage. The projects and decorations you save are linked to your account. You can access, update, correct or request deletion of your data, and withdraw this authorization, by writing to "],
    ["mark", "[RIGHTS CONTACT EMAIL]"], ["", ". The data-processing policy is at "], ["mark", "[POLICY URL]"], ["", ". By activating your account you confirm that you have read this notice and authorize the processing described, under Colombian Law 1581 of 2012."]],
    legal: "Bracketed fields: pending legal review" },
};
function Notice({ lang, version }: { lang: "es" | "en"; version: number }) {
  const n = NOTICE[lang];
  return (
    <section className="c-notice" tabIndex={0} aria-label={`${n.title} · ${lang === "es" ? "versión" : "version"} ${version}`}>
      <span className="c-legal"><AlertCircle size={14} />{n.legal}</span>
      <h3>{n.title} · {lang === "es" ? "versión" : "version"} {version}</h3>
      <p>{n.body.map(([k, t], i) => (k === "mark" ? <mark key={i}>{t}</mark> : <React.Fragment key={i}>{t}</React.Fragment>))}</p>
    </section>
  );
}
function Alert({ tone = "err", title, children }: { tone?: "err" | "ok" | "warn"; title: string; children?: React.ReactNode }) {
  return (
    <div className={`c-alert${tone === "ok" ? " c-alert-ok" : tone === "warn" ? " c-alert-warn" : ""}`} role={tone === "err" ? "alert" : "status"}>
      {tone === "ok" ? <Check /> : <AlertCircle />}
      <div><b>{title}</b>{children && <p>{children}</p>}</div>
    </div>
  );
}
function Field({ id, label, hint, error, ...input }: { id: string; label: string; hint?: React.ReactNode; error?: string } & React.ComponentProps<"input">) {
  return (
    <div className="c-field">
      <label className="c-label" htmlFor={id}>{label}</label>
      <Input id={id} className="c-input" aria-invalid={error ? true : undefined} aria-describedby={hint || error ? `${id}-d` : undefined} {...input} />
      {error ? <p className="c-err" id={`${id}-d`}>{error}</p> : hint ? <p className="c-hint" id={`${id}-d`} aria-live="polite">{hint}</p> : null}
    </div>
  );
}
function Btn({ kind = "pri", size, block, children, ...rest }: { kind?: "pri" | "out" | "ghost" | "danger" | "danger-out"; size?: "sm"; block?: boolean } & React.ComponentProps<typeof Button>) {
  return <Button {...rest} className={`c-btn c-btn-${kind}${size ? " c-btn-sm" : ""}${block ? " c-btn-block" : ""} ${rest.className ?? ""}`}>{children}</Button>;
}
function Spin() {
  return <svg viewBox="0 0 24 24" className="c-spin" aria-hidden="true" style={{ animation: "spin 1s linear infinite" }}><circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" fill="none" strokeDasharray="40 20" /></svg>;
}

/* ---------- access screens: the sizer board ---------- */
function Stage({ wide, mood, ratio, wobble, children }: { wide?: boolean; mood?: "idle" | "busy" | "deflated" | "tight"; ratio?: number; wobble?: boolean; children: React.ReactNode }) {
  return (
    <div className="c-stage">
      <div className="c-float f1 c-bob-soft"><BalloonSvg /></div>
      <div className="c-float f2"><BalloonSvg /></div>
      <div className="c-float f3"><BalloonSvg /></div>
      <div className={`c-column${wide ? " wide" : ""}`}>
        <Gauge mood={mood} ratio={ratio} />
        <section className="c-board" data-wobble={wobble ? "true" : "false"}>
          <span className="c-rivet r1" aria-hidden="true" /><span className="c-rivet r2" aria-hidden="true" />
          <div className="c-brand"><Mark />Pictures</div>
          {children}
        </section>
      </div>
    </div>
  );
}

function Login() {
  const { state } = useMockup();
  const en = state === "ingles";
  const loading = state === "cargando";
  const error = state === "error";
  if (state === "exito") {
    return (
      <Stage mood="idle">
        <div className="c-success">
          <Puff text="Hola, Ana" />
          <p className="c-lede">Te llevamos a la página que pediste antes de entrar: <b>Proyectos</b>. Sin una página pedida, abrimos la primera herramienta de tu rol, <b>Chat asistido</b>.</p>
          <Alert tone="ok" title="Sesión iniciada">Redirigiendo…</Alert>
        </div>
      </Stage>
    );
  }
  const t = en
    ? { h: "Sign in to Pictures", lede: "Use the email your invitation was sent to.", email: "Email", pw: "Password", cta: "Sign in", busy: "Signing in…",
        errT: "We couldn't sign you in", errB: "Check your email and password. After several failed attempts you must wait 15 minutes before trying again.",
        foot: "Forgot your password? Ask your administrator for a reset link. There is no open sign-up: Pictures accounts are by invitation." }
    : { h: "Entra a Pictures", lede: "Usa el correo al que llegó tu invitación.", email: "Correo", pw: "Contraseña", cta: "Entrar", busy: "Entrando…",
        errT: "No pudimos iniciar tu sesión", errB: "Revisa el correo y la contraseña. Después de varios intentos fallidos tendrás que esperar 15 minutos para volver a intentarlo.",
        foot: "¿Olvidaste tu contraseña? Pide a tu administrador un enlace para restablecerla. No hay registro abierto: las cuentas de Pictures son por invitación." };
  return (
    <Stage mood={loading ? "busy" : error ? "tight" : "idle"} wobble={error}>
      <div style={{ display: "grid", gap: 10 }}>
        <Puff text={t.h} />
        <p className="c-lede">{t.lede}</p>
      </div>
      <form className="c-form" onSubmit={(e) => e.preventDefault()} noValidate>
        {error && <Alert title={t.errT}>{t.errB}</Alert>}
        <Field id="login-email" label={t.email} type="email" autoComplete="username" defaultValue="ana@decoracionesmejia.co" disabled={loading} />
        <Field id="login-pw" label={t.pw} type="password" autoComplete="current-password" defaultValue="globos-piloto" disabled={loading} />
        <Btn type="submit" block disabled={loading}>{loading && <Spin />}{loading ? t.busy : t.cta}</Btn>
      </form>
      <p className="c-foot">{t.foot}</p>
    </Stage>
  );
}

function InvalidLink({ en }: { en?: boolean }) {
  return (
    <Stage mood="deflated">
      <div style={{ display: "grid", gap: 10 }}>
        <Puff text={en ? "This link no longer works" : "Este enlace ya no sirve"} />
        <p className="c-lede">{en ? "It may have been used already or it may have expired. Ask your administrator for a new link." : "Puede que ya se haya usado o que haya vencido. Pide a tu administrador un enlace nuevo."}</p>
      </div>
      <Btn kind="out" block>{en ? "Go to sign in" : "Ir a iniciar sesión"}</Btn>
      <p className="c-foot">{en ? "For your security we don't say which of the two happened." : "Por seguridad no indicamos cuál de las dos cosas pasó."}</p>
    </Stage>
  );
}

function PasswordPair({ en, pw, pw2, setPw, setPw2, showErrors, disabled, prefix }: { en: boolean; pw: string; pw2: string; setPw: (v: string) => void; setPw2: (v: string) => void; showErrors: boolean; disabled: boolean; prefix: string }) {
  const short = pw.length < 8;
  const same = pw === pw2;
  const meter = en
    ? `${pw.length} of 8 characters${!short ? " · long enough" : ""}`
    : `${pw.length} de 8 caracteres${!short ? " · suficiente" : ""}`;
  return (
    <>
      <Field id={`${prefix}-pw`} label={en ? "New password" : "Contraseña nueva"} type="password" autoComplete="new-password" value={pw} onChange={(e) => setPw(e.target.value)} disabled={disabled}
        hint={meter} error={showErrors && short ? (en ? "Use at least 8 characters." : "Usa al menos 8 caracteres.") : undefined} />
      <Field id={`${prefix}-pw2`} label={en ? "Repeat the password" : "Repite la contraseña"} type="password" autoComplete="new-password" value={pw2} onChange={(e) => setPw2(e.target.value)} disabled={disabled}
        hint={pw2 && same && !short ? (en ? "Passwords match." : "Las contraseñas coinciden.") : undefined}
        error={showErrors && !same ? (en ? "The passwords don't match." : "Las contraseñas no coinciden.") : undefined} />
    </>
  );
}

function Activate() {
  const { state } = useMockup();
  const en = state === "ingles";
  const error = state === "error";
  const loading = state === "cargando";
  const [pw, setPw] = React.useState(error ? "globo" : "globos2026");
  const [pw2, setPw2] = React.useState(error ? "globos" : "globos2026");
  const [ok, setOk] = React.useState(loading);
  if (state === "enlace") return <InvalidLink />;
  if (state === "exito") {
    return (
      <Stage mood="idle">
        <div className="c-success">
          <Puff text="Cuenta activada" />
          <p className="c-lede">Ya entraste con tu cuenta. Te llevamos a <b>Chat asistido</b>, la primera herramienta de tu rol Usuario · Plan 2.</p>
          <Alert tone="ok" title="Aviso de datos versión 1 aceptado">Guardamos la versión y la fecha (27 oct 2026) en tu cuenta.</Alert>
        </div>
      </Stage>
    );
  }
  const valid = pw.length >= 8 && pw === pw2;
  return (
    <Stage wide mood={loading ? "busy" : "idle"} ratio={pw.length / 8} wobble={error}>
      <div style={{ display: "grid", gap: 10 }}>
        <Puff text={en ? "Activate your account" : "Activa tu cuenta"} />
        <p className="c-lede">{en ? "Choose a password: the balloon fills the ring at 8 characters." : "Elige una contraseña: el globo llena el aro a los 8 caracteres."}</p>
      </div>
      <div className="c-who">
        <Avatar acct={{ name: "Mariana Gil", role: "p2" }} />
        <div><b>Mariana Gil</b><span>mariana@fiestaviva.co · {en ? "invited by" : "invitada por"} Valentina Ospina</span></div>
      </div>
      <form className="c-form" onSubmit={(e) => e.preventDefault()} noValidate>
        {error && <Alert title={en ? "Your account isn't active yet" : "Tu cuenta aún no está activa"}>{en ? "Fix the marked fields and accept the notice." : "Corrige los campos marcados y acepta el aviso."}</Alert>}
        <PasswordPair en={en} pw={pw} pw2={pw2} setPw={setPw} setPw2={setPw2} showErrors={error} disabled={loading} prefix="act" />
        <Notice lang={en ? "en" : "es"} version={1} />
        <label className="c-check">
          <Checkbox className="c-latex" checked={ok} onCheckedChange={(v) => setOk(!!v)} disabled={loading} aria-invalid={error && !ok ? true : undefined} />
          <span>{en ? "I have read the data notice (version 1) and authorize the processing of my data." : "Leí el aviso de datos (versión 1) y autorizo el tratamiento de mis datos."}</span>
        </label>
        {error && !ok && <p className="c-err">{en ? "Accept the notice to activate your account." : "Acepta el aviso para activar tu cuenta."}</p>}
        <Btn type="submit" block disabled={loading || (!error && (!ok || !valid))}>{loading && <Spin />}{loading ? (en ? "Activating…" : "Activando…") : (en ? "Activate account" : "Activar cuenta")}</Btn>
        {!loading && !error && !ok && <p className="c-hint">{en ? "Activation needs the notice accepted." : "Para activar la cuenta debes aceptar el aviso."}</p>}
      </form>
      <p className="c-foot">{en ? "This invitation works once and expires on 3 Nov 2026." : "Esta invitación sirve una vez y vence el 3 nov 2026."}</p>
    </Stage>
  );
}

function Reset() {
  const { state } = useMockup();
  const en = state === "ingles";
  const error = state === "error";
  const loading = state === "cargando";
  const [pw, setPw] = React.useState(error ? "fiesta" : "arco-orgánico");
  const [pw2, setPw2] = React.useState(error ? "fiesta1" : "arco-orgánico");
  if (state === "enlace") return <InvalidLink en={en} />;
  if (state === "exito") {
    return (
      <Stage mood="idle">
        <div className="c-success">
          <Puff text={en ? "Password changed" : "Contraseña cambiada"} />
          <p className="c-lede">{en ? "Sign in with your new password." : "Entra con tu contraseña nueva."}</p>
          <Btn block>{en ? "Sign in" : "Iniciar sesión"}</Btn>
        </div>
      </Stage>
    );
  }
  return (
    <Stage mood={loading ? "busy" : "idle"} ratio={pw.length / 8} wobble={error}>
      <div style={{ display: "grid", gap: 10 }}>
        <Puff text={en ? "New password" : "Nueva contraseña"} />
        <p className="c-lede">{en ? "For" : "Para"} <b>camilo@globoarte.com.co</b>. {en ? "Your administrator generated this link." : "Tu administrador generó este enlace."}</p>
      </div>
      <form className="c-form" onSubmit={(e) => e.preventDefault()} noValidate>
        {error && <Alert title={en ? "We couldn't save it" : "No pudimos guardarla"}>{en ? "Fix the marked fields." : "Corrige los campos marcados."}</Alert>}
        <PasswordPair en={en} pw={pw} pw2={pw2} setPw={setPw} setPw2={setPw2} showErrors={error} disabled={loading} prefix="rst" />
        <Btn type="submit" block disabled={loading}>{loading && <Spin />}{loading ? (en ? "Saving…" : "Guardando…") : (en ? "Save password" : "Guardar contraseña")}</Btn>
      </form>
      <p className="c-foot">{en ? "The link works once for 24 hours. Saving ends your other sessions." : "El enlace sirve una vez durante 24 horas. Al guardar se cierran tus otras sesiones."}</p>
    </Stage>
  );
}

/* ---------- signed-in shell: twisted modelling-balloon navigation + account menu ---------- */
const ADMIN = { name: "Valentina Ospina", role: "adm" as RoleId };
const ANA = { name: "Ana Mejía", role: "p2" as RoleId };

function AccountMenu({ who, gate }: { who: { name: string; role: RoleId }; gate?: boolean }) {
  const { scene, set } = useMockup();
  return (
    <DropdownMenu open={scene === "menu"} onOpenChange={(o) => set("scene", o ? "menu" : "")}>
      <DropdownMenuTrigger className="c-account" aria-label={`Cuenta: ${who.name}, ${ROLES[who.role].name}`}>
        <Avatar acct={who} />
        <span className="c-account-txt"><b>{who.name}</b><small>{ROLES[who.role].name}</small></span>
        <ChevronDown className="c-chev" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={8} className="c-menu">
        <div className="c-menu-who"><b>{who.name}</b><span>{ROLES[who.role].name}</span></div>
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled={gate} onClick={() => set("view", "mi-cuenta")}><UserRound size={18} />{gate ? "Mi cuenta (acepta el aviso primero)" : "Mi cuenta"}</DropdownMenuItem>
        <DropdownMenuItem onClick={() => set("view", "login")}><LogOut size={18} />Cerrar sesión</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function Shell({ who, nav, gate, children }: { who: { name: string; role: RoleId }; nav?: boolean; gate?: boolean; children: React.ReactNode }) {
  const { view, set } = useMockup();
  const items = [{ id: "cuentas", label: "Cuentas" }, { id: "roles", label: "Roles" }];
  return (
    <div className="c-shell">
      <header className="c-head">
        <div className="c-brand"><Mark />Pictures</div>
        {nav ? (
          <nav className="c-tube" aria-label="Administración">
            {items.map((it, i) => (
              <React.Fragment key={it.id}>
                {i > 0 && <span className="c-twist" aria-hidden="true" />}
                <button type="button" className="c-seg" aria-current={view === it.id ? "page" : undefined} onClick={() => set("view", it.id)}>
                  {view === it.id && <span className="c-bulge" aria-hidden="true" />}
                  <span className="c-seg-label">{it.label}</span>
                </button>
              </React.Fragment>
            ))}
          </nav>
        ) : <span />}
        <div className="c-head-end"><AccountMenu who={who} gate={gate} /></div>
      </header>
      {children}
    </div>
  );
}

function NoticeGate() {
  const { state } = useMockup();
  const en = state === "ingles";
  const loading = state === "cargando";
  const error = state === "error";
  const [ok, setOk] = React.useState(loading || error);
  return (
    <Shell who={ANA} gate>
      <Stage wide mood={loading ? "busy" : "idle"} wobble={error}>
        <div style={{ display: "grid", gap: 10 }}>
          <Puff text={en ? "We updated the data notice" : "Actualizamos el aviso de datos"} />
          <p className="c-lede">{en ? "To keep using Pictures, read and accept version 2. You accepted version 1 on 20 Oct 2026." : "Para seguir usando Pictures, lee y acepta la versión 2. Aceptaste la versión 1 el 20 oct 2026."}</p>
        </div>
        {error && <Alert title={en ? "We couldn't save your acceptance" : "No pudimos guardar tu aceptación"}>{en ? "Nothing changed. Try again in a moment." : "No cambió nada. Inténtalo de nuevo en un momento."}</Alert>}
        <Notice lang={en ? "en" : "es"} version={2} />
        <label className="c-check">
          <Checkbox className="c-latex" checked={ok} onCheckedChange={(v) => setOk(!!v)} disabled={loading} />
          <span>{en ? "I have read the data notice (version 2) and authorize the processing of my data." : "Leí el aviso de datos (versión 2) y autorizo el tratamiento de mis datos."}</span>
        </label>
        <div className="c-inline">
          <Btn disabled={loading || !ok}>{loading && <Spin />}{loading ? (en ? "Saving…" : "Guardando…") : (en ? "Accept and continue" : "Aceptar y continuar")}</Btn>
          <Btn kind="ghost"><LogOut />{en ? "Sign out" : "Cerrar sesión"}</Btn>
        </div>
        <p className="c-foot">{en ? "No other page opens until you accept this version." : "Ninguna otra página se abre hasta que aceptes esta versión."}</p>
      </Stage>
    </Shell>
  );
}

function MyAccount() {
  const { state } = useMockup();
  const loading = state === "cargando";
  const error = state === "error";
  const done = state === "exito";
  return (
    <Shell who={ANA}>
      <main className="c-main">
        <div className="c-titlebar"><div><Puff text="Mi cuenta" className="c-title" /><p className="c-small">Tu acceso a Pictures y tu contraseña.</p></div></div>
        <div className="c-me">
          <section className="c-badge-card" aria-label="Tu credencial">
            <span className="c-hole" aria-hidden="true" />
            {loading ? (
              <><Skeleton className="c-skel" style={{ height: 78, width: 64 }} /><Skeleton className="c-skel" style={{ height: 22, width: "70%" }} /><Skeleton className="c-skel" style={{ height: 90 }} /></>
            ) : (
              <>
                <div className="c-person"><Avatar acct={ANA} large /><div><b style={{ fontSize: 19 }}>Ana Mejía</b><span>Usuario · Plan 2</span></div></div>
                <dl className="c-facts">
                  <div><dt>Correo</dt><dd>ana@decoracionesmejia.co</dd></div>
                  <div><dt>Empresa</dt><dd>Decoraciones Mejía</dd></div>
                  <div><dt>Aviso de datos</dt><dd>Versión 1, aceptada el 20 oct 2026</dd></div>
                </dl>
                <div style={{ display: "grid", gap: 8 }}><span className="c-small">Herramientas de tu rol</span>
                  <div className="c-chips">{["Chat asistido", "Contador de globos", "Catálogo", "Calculadora de costos", "Decoraciones listas"].map((t) => <span key={t} className="c-chip">{t}</span>)}</div>
                </div>
              </>
            )}
          </section>
          <section className="c-editor" aria-labelledby="pw-title">
            <h2 className="c-h2" id="pw-title">Cambiar contraseña</h2>
            {done && <Alert tone="ok" title="Contraseña cambiada">Cerramos tus otras sesiones; en este navegador sigues dentro.</Alert>}
            {error && <Alert title="La contraseña actual no es correcta">No cambiamos nada. Escríbela de nuevo.</Alert>}
            <form className="c-form" onSubmit={(e) => e.preventDefault()} noValidate>
              <Field id="me-cur" label="Contraseña actual" type="password" autoComplete="current-password" defaultValue={done ? "" : "globos-piloto"} disabled={loading} error={error ? "No coincide con tu contraseña actual." : undefined} />
              <Field id="me-new" label="Contraseña nueva" type="password" autoComplete="new-password" defaultValue={done ? "" : "arco-de-globos"} disabled={loading} hint="Mínimo 8 caracteres." />
              <Field id="me-new2" label="Repite la contraseña nueva" type="password" autoComplete="new-password" defaultValue={done ? "" : "arco-de-globos"} disabled={loading} />
              <div className="c-inline"><Btn type="submit" disabled={loading}>{loading && <Spin />}{loading ? "Cambiando…" : "Cambiar contraseña"}</Btn></div>
              <p className="c-hint">Al cambiarla cerramos tus sesiones en otros navegadores.</p>
            </form>
          </section>
        </div>
      </main>
    </Shell>
  );
}

/* ---------- administration: accounts ---------- */
function StatePill({ s }: { s: Acct["state"] }) {
  return <span className={`c-pill ${s}`}>{STATE_LABEL[s]}</span>;
}
function Accounts({ onManage, removed }: { onManage: (id: string) => void; removed: string[] }) {
  const { state, set } = useMockup();
  const empty = state === "vacio";
  const [q, setQ] = React.useState(empty ? "carolina" : "");
  const [role, setRole] = React.useState(empty ? "p3" : "");
  const [st, setSt] = React.useState(empty ? "desactivada" : "");
  const rows = ACCOUNTS.filter((a) => !removed.includes(a.id))
    .filter((a) => !q || (a.name + " " + a.email).toLowerCase().includes(q.toLowerCase()))
    .filter((a) => !role || a.role === role).filter((a) => !st || a.state === st);
  const all = ACCOUNTS.filter((a) => !removed.includes(a.id));
  return (
    <main className="c-main">
      <div className="c-titlebar">
        <div><Puff text="Cuentas" className="c-title" />
          <p className="c-small">{all.length} cuentas · {all.filter((a) => a.state === "pendiente").length} invitación pendiente · {all.filter((a) => a.state === "desactivada").length} desactivada</p></div>
        <Btn onClick={() => set("scene", "invitar")}><Plus />Invitar persona</Btn>
      </div>
      <div className="c-tools" role="search">
        <div className="c-search"><Search /><Input className="c-input" aria-label="Buscar por nombre o correo" placeholder="Buscar por nombre o correo" value={q} onChange={(e) => setQ(e.target.value)} /></div>
        <select className="c-select" aria-label="Filtrar por rol" value={role} onChange={(e) => setRole(e.target.value)}>
          <option value="">Todos los roles</option>
          {(Object.keys(ROLES) as RoleId[]).map((r) => <option key={r} value={r}>{ROLES[r].name}</option>)}
        </select>
        <select className="c-select" aria-label="Filtrar por estado" value={st} onChange={(e) => setSt(e.target.value)}>
          <option value="">Todos los estados</option><option value="activa">Activa</option><option value="desactivada">Desactivada</option><option value="pendiente">Invitación pendiente</option>
        </select>
      </div>
      <section className="c-panel c-list" aria-label="Lista de cuentas">
        {state === "error" ? (
          <div className="c-empty"><Gauge mood="deflated" /><div><h2 className="c-h2">No pudimos cargar las cuentas</h2><p className="c-small">Puede ser la conexión. Nada cambió en las cuentas.</p><Btn kind="out" size="sm"><RotateCcw />Reintentar</Btn></div></div>
        ) : state === "cargando" ? (
          <div aria-busy="true" aria-label="Cargando cuentas">{[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="c-row"><div className="c-person"><Skeleton className="c-skel" style={{ width: 38, height: 46 }} /><div style={{ display: "grid", gap: 6 }}><Skeleton className="c-skel" style={{ height: 14, width: 150 }} /><Skeleton className="c-skel" style={{ height: 12, width: 190 }} /></div></div>
              <Skeleton className="c-skel c-company" style={{ height: 14 }} /><Skeleton className="c-skel" style={{ height: 14 }} /><Skeleton className="c-skel" style={{ height: 26, width: 90 }} /><Skeleton className="c-skel" style={{ height: 14 }} /><span /></div>))}</div>
        ) : rows.length === 0 ? (
          <div className="c-empty"><span className="c-gauge" aria-hidden="true"><BalloonSvg /></span><div>
            <h2 className="c-h2">Ninguna cuenta coincide</h2>
            <p className="c-small">Buscaste «{q}» en {role ? ROLES[role as RoleId].name : "todos los roles"} · {st ? STATE_LABEL[st as Acct["state"]] : "todos los estados"}.</p>
            <Btn kind="out" size="sm" onClick={() => { setQ(""); setRole(""); setSt(""); }}>Limpiar filtros</Btn></div></div>
        ) : (
          <div role="list">
            <div className="c-row c-row-head" aria-hidden="true"><span>Persona</span><span className="c-company">Empresa</span><span>Rol</span><span>Estado</span><span>Último acceso</span><span /></div>
            <AnimatePresence initial={false}>
              {rows.map((a, i) => (
                <motion.div key={a.id} role="listitem" className="c-row c-row-in" style={{ ["--i" as string]: i }} exit={{ scale: [1, 1.08, 0.2], opacity: [1, 1, 0], transition: { duration: 0.32 } }}>
                  <div className="c-person"><Avatar acct={a} off={a.state === "desactivada"} /><div><b>{a.name}</b><span>{a.email}</span></div></div>
                  <span className="c-company c-row-cell"><span className="c-lbl">Empresa</span>{a.company || <span className="c-small">Sin empresa</span>}</span>
                  <span className="c-row-cell"><span className="c-lbl">Rol</span>{ROLES[a.role].name}</span>
                  <span className="c-row-cell"><span className="c-lbl">Estado</span><StatePill s={a.state} /></span>
                  <span className="c-row-cell"><span className="c-lbl">Último acceso</span><span className="c-mono">{a.last}</span></span>
                  <Btn kind="out" size="sm" onClick={() => onManage(a.id)} aria-label={`Gestionar la cuenta de ${a.name}`}>Gestionar</Btn>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </section>
    </main>
  );
}

/* ---------- administration: roles ---------- */
function Roles() {
  const { state, set } = useMockup();
  const noCustom = state === "vacio";
  const draft = state === "error";
  const [sel, setSel] = React.useState<RoleId | "nuevo">(draft ? "nuevo" : noCustom ? "p2" : "coord");
  const [perms, setPerms] = React.useState<string[]>(draft ? [] : ROLES.coord.perms);
  const custom = sel === "nuevo" || !ROLES[sel as RoleId].system;
  const shown = sel === "nuevo" || sel === "coord" ? perms : ROLES[sel as RoleId].perms;
  const toggle = (p: string, on: boolean) => setPerms((cur) => (on ? [...cur, p] : cur.filter((x) => x !== p)));
  const systemIds = (Object.keys(ROLES) as RoleId[]).filter((r) => ROLES[r].system);
  if (state === "cargando") {
    return (
      <main className="c-main"><div className="c-titlebar"><div><Puff text="Roles" className="c-title" /><p className="c-small">Cargando roles…</p></div></div>
        <div className="c-roles" aria-busy="true"><div className="c-rail">{[0, 1, 2, 3, 4, 5].map((i) => <Skeleton key={i} className="c-skel" style={{ height: 44 }} />)}</div>
          <div className="c-editor"><Skeleton className="c-skel" style={{ height: 46 }} /><div className="c-boards">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="c-skel" style={{ height: 110 }} />)}</div></div></div></main>
    );
  }
  return (
    <main className="c-main">
      <div className="c-titlebar">
        <div><Puff text="Roles" className="c-title" /><p className="c-small">5 del sistema · {noCustom ? "ningún rol propio" : "1 propio"}. Cada cuenta tiene un rol.</p></div>
        <Btn onClick={() => { setSel("nuevo"); setPerms([]); }}><Plus />Nuevo rol</Btn>
      </div>
      <div className="c-roles">
        <nav className="c-rail" aria-label="Roles">
          <h2>Propios</h2>
          {sel === "nuevo" && <button type="button" className="c-tag" aria-pressed="true"><span className="c-dot" style={{ background: "var(--b-coord)" }} />Rol nuevo<small>sin guardar</small></button>}
          {noCustom ? <p className="c-small" style={{ padding: "4px 6px" }}>Aún no hay roles propios.</p> : (
            <button type="button" className="c-tag" aria-pressed={sel === "coord"} onClick={() => { setSel("coord"); setPerms(ROLES.coord.perms); }}>
              <span className="c-dot" style={{ background: ROLES.coord.color }} />{ROLES.coord.name}<small>{countOf("coord")} cuenta</small></button>
          )}
          <h2>Del sistema</h2>
          {systemIds.map((r) => (
            <button key={r} type="button" className="c-tag" aria-pressed={sel === r} onClick={() => setSel(r)}>
              <span className="c-dot" style={{ background: ROLES[r].color }} />{ROLES[r].name}<small><Lock />{countOf(r)}</small></button>
          ))}
        </nav>
        <section className="c-editor" aria-label="Editor de rol">
          {noCustom && sel !== "nuevo" && (
            <div className="c-empty" style={{ padding: 0 }}><span className="c-gauge" aria-hidden="true"><BalloonSvg /></span><div>
              <h2 className="c-h2">Crea tu primer rol propio</h2><p className="c-small">Elige sus permisos por herramienta. Abajo ves, solo para leer, lo que incluye {ROLES[sel as RoleId].name}.</p></div></div>
          )}
          {custom ? (
            <Field id="role-name" label="Nombre del rol" defaultValue={sel === "nuevo" ? (draft ? "Montaje externo" : "") : ROLES.coord.name} placeholder="Por ejemplo: Montaje externo" />
          ) : (
            <div style={{ display: "grid", gap: 10 }}>
              <h2 className="c-h2">{ROLES[sel as RoleId].name}</h2>
              <div className="c-readonly"><ShieldCheck />Rol del sistema: sus permisos se ven pero no se cambian ni se borra.</div>
            </div>
          )}
          {draft && perms.length === 0 && <Alert title="Elige al menos un permiso">Un rol sin permisos no se puede guardar.</Alert>}
          <div className="c-boards">
            {TOOLS.map((t) => {
              const on = t.perms.filter(([p]) => shown.includes(p)).length;
              return (
                <fieldset key={t.id} className={`c-tool${t.perms.length > 3 ? " wide" : ""}`} style={{ margin: 0 }}>
                  <header><legend style={{ padding: 0 }}><b>{t.name}</b></legend><span className="c-small">{on} de {t.perms.length}</span></header>
                  <div className="c-tool-list">
                    {t.perms.map(([p, label]) => (
                      <label key={p} className="c-check">
                        <Checkbox className="c-latex" checked={shown.includes(p)} disabled={!custom} onCheckedChange={(v) => toggle(p, !!v)} />
                        <span>{label}</span>
                      </label>
                    ))}
                  </div>
                </fieldset>
              );
            })}
          </div>
          {custom && (
            <div className="c-editor-foot">
              <p className="c-small">{sel === "coord" ? "1 cuenta usa este rol: los cambios aplican en su siguiente petición." : "Elige permisos y guarda para usar el rol al invitar."}</p>
              <div className="c-inline">
                {sel === "coord" && <Btn kind="danger-out" onClick={() => set("scene", "rol-borrar")}><Trash2 />Borrar rol</Btn>}
                <Btn>{sel === "nuevo" ? "Crear rol" : "Guardar rol"}</Btn>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

/* ---------- dialogs ---------- */
function RoleSelect({ id, value, onChange }: { id: string; value: string; onChange?: (v: string) => void }) {
  return (
    <select id={id} className="c-select" value={value} onChange={(e) => onChange?.(e.target.value)}>
      <optgroup label="Planes">{(["p1", "p2", "p3"] as RoleId[]).map((r) => <option key={r} value={r}>{ROLES[r].name}</option>)}</optgroup>
      <optgroup label="Personal">{(["emp", "adm"] as RoleId[]).map((r) => <option key={r} value={r}>{ROLES[r].name}</option>)}</optgroup>
      <optgroup label="Propios"><option value="coord">{ROLES.coord.name}</option></optgroup>
    </select>
  );
}
function Modal({ open, title, desc, children, alert }: { open: boolean; title: string; desc?: React.ReactNode; children: React.ReactNode; alert?: boolean }) {
  const { set } = useMockup();
  const close = (o: boolean) => { if (!o) set("scene", ""); };
  if (alert) {
    return (
      <AlertDialog open={open} onOpenChange={close}>
        <AlertDialogContent className="c-dialog">
          <AlertDialogTitle className="c-dialog-title">{title}</AlertDialogTitle>
          {desc && <AlertDialogDescription className="c-dialog-desc">{desc}</AlertDialogDescription>}
          {children}
        </AlertDialogContent>
      </AlertDialog>
    );
  }
  return (
    <Dialog open={open} onOpenChange={close}>
      <DialogContent className="c-dialog" showCloseButton={false}>
        <DialogTitle className="c-dialog-title">{title}</DialogTitle>
        {desc && <DialogDescription className="c-dialog-desc">{desc}</DialogDescription>}
        {children}
      </DialogContent>
    </Dialog>
  );
}
function LinkTicket({ link, note }: { link: string; note: string }) {
  const [copied, setCopied] = React.useState(false);
  return (
    <div className="c-ticket" data-swing={copied ? "true" : "false"}>
      <code>{link}</code>
      <div className="c-inline">
        <CopyButton content={link} copied={copied} onCopiedChange={(c) => setCopied(c)} delay={2400} className="c-btn c-btn-pri c-btn-sm" aria-live="polite">
          {copied ? <Check /> : <Copy />}{copied ? "Copiado" : "Copiar enlace"}
        </CopyButton>
        <span className="c-small">{note}</span>
      </div>
    </div>
  );
}
function Dialogs({ manage, setManage, onRemove }: { manage: string; setManage: (id: string) => void; onRemove: (id: string) => void }) {
  const { scene, set } = useMockup();
  const acct = ACCOUNTS.find((a) => a.id === (scene === "ultimo-admin" ? "valentina" : manage)) ?? ACCOUNTS[2];
  const [roleVal, setRoleVal] = React.useState<string>(acct.role);
  const [off, setOff] = React.useState(acct.state === "desactivada");
  const [reset, setReset] = React.useState(scene === "restablecer-enlace");
  React.useEffect(() => { setRoleVal(acct.role); setOff(acct.state === "desactivada"); setReset(scene === "restablecer-enlace"); }, [acct.id, scene]);
  const del = ACCOUNTS.find((a) => a.id === manage && !a.work && !a.lastAdmin) ?? ACCOUNTS.find((a) => a.id === "laura")!;
  const [typed, setTyped] = React.useState("lauracano.eventos@");
  React.useEffect(() => { setTyped(del.email.slice(0, Math.ceil(del.email.length * 0.66))); }, [del.id]);
  const match = typed === del.email;
  let prefix = 0; while (prefix < typed.length && typed[prefix] === del.email[prefix]) prefix++;
  const { spring, reduced } = useMotionProfile();
  const dup = scene === "invitar-duplicado";
  const pending = acct.state === "pendiente";
  return (
    <>
      <Modal open={scene === "invitar" || dup} title="Invitar persona" desc="Recibirá un enlace de un solo uso para crear su contraseña. Sirve 7 días.">
        <form className="c-form" onSubmit={(e) => { e.preventDefault(); set("scene", "enlace"); }} noValidate>
          <Field id="inv-name" label="Nombre" defaultValue={dup ? "Ana Mejía" : "Mariana Gil"} />
          <Field id="inv-email" label="Correo" type="email" defaultValue={dup ? "ana@decoracionesmejia.co" : "mariana@fiestaviva.co"}
            error={dup ? "Este correo ya tiene una cuenta (Ana Mejía). Búscala en la lista para cambiar su rol o generarle un enlace." : undefined} />
          <Field id="inv-company" label="Empresa (opcional)" defaultValue={dup ? "Decoraciones Mejía" : "Fiesta Viva"} />
          <div className="c-field"><label className="c-label" htmlFor="inv-role">Rol</label><RoleSelect id="inv-role" value="p2" /><p className="c-hint">Usuario · Plan 2: chat asistido, contador, catálogo, costos y decoraciones listas.</p></div>
          <div className="c-dialog-foot"><Btn kind="ghost" type="button" onClick={() => set("scene", "")}>Cancelar</Btn><Btn type="submit"><Link2 />Crear invitación</Btn></div>
        </form>
      </Modal>

      <Modal open={scene === "enlace"} title="Invitación lista para Mariana Gil" desc="Cópiala y envíasela. Solo la verás ahora: si se pierde, genera otra desde su cuenta y esta dejará de servir.">
        <LinkTicket link={INVITE_LINK} note="Vence el 3 nov 2026 · un solo uso" />
        <div className="c-dialog-foot"><Btn onClick={() => set("scene", "")}>Listo</Btn></div>
      </Modal>

      <Modal open={scene === "acciones" || scene === "restablecer-enlace" || scene === "ultimo-admin"} title={acct.name} desc={`${acct.email}${acct.company ? " · " + acct.company : ""}`}>
        <div className="c-person"><Avatar acct={acct} large off={off} /><div><b>{off ? "Cuenta desactivada" : pending ? "Invitación pendiente" : "Cuenta activa"}</b><span>Último acceso: {acct.last}</span></div></div>
        <div className="c-sec"><h3><label htmlFor="acc-role">Rol</label></h3>
          <div className="c-inline"><RoleSelect id="acc-role" value={roleVal} onChange={setRoleVal} /><Btn kind="out" size="sm" disabled={roleVal === acct.role}>Guardar rol</Btn></div>
          <p className="c-hint">El cambio aplica en su siguiente petición, sin cerrar su sesión.</p></div>
        <div className="c-sec"><h3>Acceso</h3>
          {acct.lastAdmin ? (
            <div className="c-why"><ShieldCheck /><span>Es la única cuenta con rol Administrador: no se puede desactivar ni borrar. Da ese rol a otra persona primero.</span></div>
          ) : (
            <div className="c-inline"><Btn kind="out" size="sm" onClick={() => setOff(!off)}>{off ? "Reactivar cuenta" : "Desactivar cuenta"}</Btn><span className="c-small">{off ? "Podrá volver a entrar con su contraseña." : "Su sesión termina en su siguiente petición."}</span></div>
          )}
        </div>
        <div className="c-sec"><h3>{pending ? "Invitación" : "Contraseña"}</h3>
          {reset ? <LinkTicket link={pending ? INVITE_LINK : RESET_LINK} note={pending ? "Vence en 7 días · un solo uso" : "Sirve 24 horas · un solo uso"} /> : (
            <div className="c-inline"><Btn kind="out" size="sm" onClick={() => setReset(true)}><KeyRound />{pending ? "Generar invitación nueva" : "Generar enlace para restablecer"}</Btn></div>
          )}
          <p className="c-hint">Al generar un enlace nuevo, los anteriores del mismo tipo que no se usaron dejan de servir.</p></div>
        <div className="c-sec"><h3>Borrar cuenta</h3>
          {acct.lastAdmin ? <div className="c-why"><Lock /><span>No se puede borrar la última cuenta Administrador.</span></div>
            : acct.work ? <div className="c-why"><Lock /><span>Tiene {acct.work} guardados. Una cuenta con trabajo guardado no se borra: desactívala.</span></div>
              : <div className="c-inline"><Btn kind="danger-out" size="sm" onClick={() => { setManage(acct.id); set("scene", "borrar"); }}><Trash2 />Borrar cuenta…</Btn></div>}
        </div>
        <div className="c-dialog-foot"><Btn onClick={() => set("scene", "")}>Listo</Btn></div>
      </Modal>

      <Modal alert open={scene === "borrar"} title={`Borrar la cuenta de ${del.name}`} desc={`No tiene trabajo guardado. Su gasto de IA se conserva como «Cuenta eliminada», sin datos personales. No se puede deshacer.`}>
        <div className="c-tension">
          <motion.span className="c-gauge" aria-hidden="true" initial={false} animate={{ scale: 0.5 + 0.5 * (prefix / del.email.length), rotate: match ? [0, -4, 4, 0] : 0 }} transition={reduced ? { duration: 0 } : spring}><BalloonSvg /></motion.span>
          <Field id="del-confirm" label={`Escribe ${del.email} para confirmar`} value={typed} onChange={(e) => setTyped(e.target.value)} autoComplete="off" hint={match ? "Coincide." : `${prefix} de ${del.email.length} caracteres coinciden.`} />
        </div>
        <div className="c-dialog-foot"><Btn kind="ghost" onClick={() => set("scene", "")}>Cancelar</Btn>
          <Btn kind="danger" disabled={!match} onClick={() => { onRemove(del.id); set("scene", ""); }}><Trash2 />Borrar cuenta</Btn></div>
      </Modal>

      <Modal open={scene === "rol-borrar"} title="No se puede borrar «Coordinación de eventos»" desc="Un rol que todavía tiene cuentas no se borra.">
        <div className="c-why"><UserRound /><span>1 cuenta lo usa: <b>Sofía Duarte</b>. Cámbiala a otro rol desde Cuentas y vuelve a intentarlo.</span></div>
        <div className="c-dialog-foot"><Btn kind="out" onClick={() => set("scene", "")}>Entendido</Btn></div>
      </Modal>
    </>
  );
}

/* ---------- app ---------- */
const ADMIN_SCENES = ["invitar", "invitar-duplicado", "enlace", "acciones", "restablecer-enlace", "ultimo-admin", "borrar"];
function App() {
  const { view, scene, set } = useMockup();
  const [manage, setManage] = React.useState("ana");
  const [removed, setRemoved] = React.useState<string[]>([]);
  const base = ADMIN_SCENES.includes(scene) && view !== "cuentas" && view !== "roles" ? "cuentas"
    : scene === "rol-borrar" ? "roles"
      : scene === "menu" && ["login", "activar", "restablecer"].includes(view) ? "cuentas" : view;
  const onManage = (id: string) => { setManage(id); set("scene", "acciones"); };
  let screen: React.ReactNode;
  if (base === "login") screen = <Login />;
  else if (base === "activar") screen = <Activate />;
  else if (base === "restablecer") screen = <Reset />;
  else if (base === "aviso") screen = <NoticeGate />;
  else if (base === "mi-cuenta") screen = <MyAccount />;
  else if (base === "roles") screen = <Shell who={ADMIN} nav><Roles /></Shell>;
  else screen = <Shell who={ADMIN} nav><Accounts onManage={onManage} removed={removed} /></Shell>;
  return (
    <>
      {screen}
      <Dialogs manage={scene === "acciones" || scene === "borrar" ? manage : scene === "restablecer-enlace" ? "camilo" : "ana"} setManage={setManage} onRemove={(id) => setRemoved((r) => [...r, id])} />
    </>
  );
}

mountMockup(App, {
  title: "Cuentas y administración · C «Medidor y tubo 260»",
  views: [
    { id: "login", label: "Iniciar sesión" },
    { id: "activar", label: "Activar invitación" },
    { id: "restablecer", label: "Restablecer contraseña" },
    { id: "aviso", label: "Aceptar aviso nuevo" },
    { id: "mi-cuenta", label: "Mi cuenta" },
    { id: "cuentas", label: "Administración · Cuentas" },
    { id: "roles", label: "Administración · Roles" },
  ],
  states: [
    { id: "normal", label: "Normal" },
    { id: "cargando", label: "Cargando" },
    { id: "vacio", label: "Vacío" },
    { id: "error", label: "Error" },
    { id: "enlace", label: "Enlace usado o vencido" },
    { id: "exito", label: "Éxito" },
    { id: "ingles", label: "Navegador en inglés" },
  ],
  scenes: [
    { id: "", label: "Ninguno" },
    { id: "menu", label: "Menú de la cuenta" },
    { id: "invitar", label: "Invitar persona" },
    { id: "invitar-duplicado", label: "Invitar · correo ya registrado" },
    { id: "enlace", label: "Enlace de invitación (una vez)" },
    { id: "acciones", label: "Gestionar cuenta con trabajo" },
    { id: "restablecer-enlace", label: "Enlace para restablecer" },
    { id: "ultimo-admin", label: "Última administradora" },
    { id: "borrar", label: "Borrar cuenta sin trabajo" },
    { id: "rol-borrar", label: "Rol con cuentas" },
  ],
});
