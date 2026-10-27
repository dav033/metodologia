// cuentas-admin@v1 · r9 · direction A — «Hoja de llamado»: the access desk set like an event-production call sheet.
// Three asymmetric tracks (headline column, dense register, margin notes tied to each row), bottle-green ink on
// newsprint, Instrument Serif display against condensed Bricolage Grotesque, precise typesetting motion.
// Exploration only: not the canonical contract. Mock data is illustrative.
import * as React from "react";
import { motion } from "motion/react";
import { Check, ChevronDown, Copy, Loader2, LogOut, Plus, Search, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuGroup, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { mountMockup, useMockup } from "@kit/mockup";
import { useMotionProfile } from "@kit/motion";
import serifRoman from "@fontsource/instrument-serif/files/instrument-serif-latin-400-normal.woff2";
import serifItalic from "@fontsource/instrument-serif/files/instrument-serif-latin-400-italic.woff2";
import sansVar from "@fontsource-variable/bricolage-grotesque/files/bricolage-grotesque-latin-standard-normal.woff2";
import monoVar from "@fontsource-variable/jetbrains-mono/files/jetbrains-mono-latin-wght-normal.woff2";

const FONTS = `
@font-face{font-family:"Llamado Display";src:url(${serifRoman}) format("woff2");font-style:normal;font-weight:400;font-display:block}
@font-face{font-family:"Llamado Display";src:url(${serifItalic}) format("woff2");font-style:italic;font-weight:400;font-display:block}
@font-face{font-family:"Llamado Sans";src:url(${sansVar}) format("woff2");font-weight:200 800;font-stretch:75% 100%;font-display:block}
@font-face{font-family:"Llamado Mono";src:url(${monoVar}) format("woff2");font-weight:100 800;font-display:block}`;

const CSS = `
html:root,html[data-theme="light"]{
  --background:#eef0ea;--foreground:#13201b;--card:#f9faf6;--card-foreground:#13201b;--popover:#f9faf6;--popover-foreground:#13201b;
  --primary:#0d5a43;--primary-foreground:#ffffff;--secondary:#e1e6df;--secondary-foreground:#13201b;
  --muted:#e1e6df;--muted-foreground:#46534c;--accent:#d5e6db;--accent-foreground:#13201b;
  --destructive:#a32116;--destructive-foreground:#ffffff;--border:#b6bfb8;--input:#66736c;--ring:#0d5a43;
  --hl-sel:#d5e6db;--hl-note:#a32116;--hl-amber:#7a4b00;--hl-rule:#13201b;--hl-overlay:rgb(19 32 27 / .5);
  --hl-disabled-bg:#dfe3dc;--hl-disabled-fg:#46534c;
}
html.dark,html[data-theme="dark"]{
  --background:#0f1412;--foreground:#e7ece8;--card:#161d1a;--card-foreground:#e7ece8;--popover:#161d1a;--popover-foreground:#e7ece8;
  --primary:#8fd3b4;--primary-foreground:#072319;--secondary:#1e2723;--secondary-foreground:#e7ece8;
  --muted:#1e2723;--muted-foreground:#a7b3ac;--accent:#1d362b;--accent-foreground:#e7ece8;
  --destructive:#ff9d88;--destructive-foreground:#2a0702;--border:#33413a;--input:#7d8c84;--ring:#8fd3b4;
  --hl-sel:#1d362b;--hl-note:#ff9d88;--hl-amber:#f0b765;--hl-rule:#e7ece8;--hl-overlay:rgb(0 0 0 / .62);
  --hl-disabled-bg:#1e2723;--hl-disabled-fg:#a7b3ac;
}
html{--k:1;--set:cubic-bezier(.16,1,.3,1);--cut:cubic-bezier(.7,0,.3,1)}
html[data-motion="natural"]{--k:.6}html[data-motion="subtle"]{--k:.35}
.hl,.hl-dlg,.hl-menu{font-family:"Llamado Sans",ui-sans-serif,system-ui,sans-serif;font-stretch:96%;font-variant-numeric:tabular-nums}
.hl{min-height:calc(100svh - var(--mockup-bar-h,0px));background:var(--background);color:var(--foreground);font-size:14px;line-height:1.45}
.hl *{box-sizing:border-box}
.hl-serif{font-family:"Llamado Display",Georgia,serif;font-weight:400;font-stretch:100%}
.hl-mono{font-family:"Llamado Mono",ui-monospace,monospace;font-size:12px;font-stretch:100%}
.hl-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}

/* dateline: brand, running section index, colour control strip, account menu */
.hl-date{display:flex;align-items:center;gap:12px 24px;flex-wrap:wrap;padding:12px 40px}
.hl-brand{font-size:26px;line-height:1;font-style:italic;margin-right:8px}
.hl-index ul{display:flex;gap:4px;list-style:none;margin:0;padding:0}
.hl-index button{position:relative;display:inline-flex;align-items:baseline;gap:8px;min-height:40px;padding:10px 14px;border:0;background:transparent;
  color:var(--foreground);font:600 14px/1.2 "Llamado Sans",sans-serif;cursor:pointer;transition:background-color calc(var(--k)*180ms) var(--set),color calc(var(--k)*180ms) var(--set)}
.hl-index button::after{content:"";position:absolute;left:14px;right:14px;bottom:8px;height:2px;background:currentColor;transform:scaleX(0);transform-origin:left;
  transition:transform calc(var(--k)*220ms) var(--set)}
.hl-index button:hover::after{transform:scaleX(1)}
.hl-index button[aria-current="page"]{background:var(--foreground);color:var(--background)}
.hl-index button[aria-current="page"]::after{transform:scaleX(0)}
.hl-index .hl-mono{font-weight:500}
.hl-gate{font-size:14px;color:var(--muted-foreground)}
.hl-strip{display:flex;gap:2px;margin-left:auto}
.hl-strip i{display:block;width:10px;height:18px;animation:hl-swatch calc(var(--k)*420ms) var(--set) both;animation-delay:calc(var(--i)*30ms*var(--k))}
.hl-acct{display:inline-flex;align-items:center;gap:10px;min-height:44px;padding:8px 14px;background:transparent;border:1px solid var(--input);color:var(--foreground);
  font:500 14px/1.2 "Llamado Sans",sans-serif;cursor:pointer;transition:background-color calc(var(--k)*160ms) var(--set),transform 120ms var(--set)}
.hl-acct:hover{background:var(--muted)}.hl-acct:active{transform:translateY(1px)}
.hl-acct small{color:var(--muted-foreground);font-size:13px}
.hl-rule{height:1px;background:var(--hl-rule);transform-origin:left;animation:hl-draw calc(var(--k)*620ms) var(--cut) both}
.hl-rule.double{height:4px;background:transparent;border-top:1px solid var(--hl-rule);border-bottom:1px solid var(--hl-rule)}
.hl-stick{height:3px;background:var(--primary);transform-origin:left;animation:hl-draw calc(var(--k)*520ms) var(--cut) both}

/* working sheet: headline column + register (with margin notes inside the register) */
.hl-sheet{display:grid;grid-template-columns:300px minmax(0,1fr);gap:48px;padding:36px 40px 72px;animation:hl-shift calc(var(--k)*560ms) var(--set) both}
.hl-lead{position:sticky;top:calc(var(--mockup-bar-h,0px) + 20px);align-self:start;display:grid;gap:20px}
.hl-headwrap{transform-origin:left top}
.hl-head{margin:0;font-size:96px;line-height:.86;letter-spacing:-.025em;animation:hl-set calc(var(--k)*680ms) var(--set) both}
.hl-head em{font-style:italic}
.hl-deck{margin:0;font-size:22px;line-height:1.22;max-width:30ch}
.hl-roll{display:inline-flex;overflow:hidden;vertical-align:bottom;line-height:1.1}
.hl-roll-in{display:inline-block;animation:hl-roll calc(var(--k)*460ms) var(--set) both}
.hl-filters{display:grid;gap:14px}
.hl-field{display:grid;gap:6px}
.hl-field>label,.hl-label{font-size:13px;font-weight:600;color:var(--foreground)}
.hl-help{font-size:13px;color:var(--muted-foreground);margin:0}
.hl-err{font-size:13px;color:var(--hl-note);margin:0;font-weight:600}
.hl-search{position:relative}.hl-search svg{position:absolute;left:12px;top:50%;width:16px;height:16px;transform:translateY(-50%);color:var(--muted-foreground);pointer-events:none}
.hl-search input{padding-left:36px}
.hl [data-slot="input"],.hl-dlg [data-slot="input"],.hl-select{height:44px;border-radius:2px;border:1px solid var(--input);background:var(--card);color:var(--foreground);
  font:400 15px/1.2 "Llamado Sans",sans-serif;padding:0 12px;box-shadow:none;transition:border-color calc(var(--k)*160ms) var(--set),outline-offset 160ms var(--set)}
.hl [data-slot="input"]:hover,.hl-select:hover,.hl-dlg [data-slot="input"]:hover{border-color:var(--foreground)}
.hl [data-slot="input"][aria-invalid="true"],.hl-dlg [data-slot="input"][aria-invalid="true"]{border-color:var(--hl-note)}
.hl-select{width:100%;appearance:auto}
.hl-row2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
:where(.hl,.hl-dlg,.hl-menu) :focus-visible{outline-offset:2px!important;transition:outline-offset 160ms var(--set)}

/* buttons: the real shadcn Button, restyled as square printer's slugs */
.hl .hl-btn,.hl-dlg .hl-btn{height:44px;padding:0 18px;border-radius:2px;font:600 14px/1 "Llamado Sans",sans-serif;font-stretch:96%;gap:8px;
  transition:background-color calc(var(--k)*160ms) var(--set),transform 120ms var(--set),box-shadow 120ms var(--set)}
.hl .hl-btn.primary,.hl-dlg .hl-btn.primary{background:var(--primary);color:var(--primary-foreground);border:1px solid var(--primary)}
.hl .hl-btn.primary:hover,.hl-dlg .hl-btn.primary:hover{background:color-mix(in oklab,var(--primary),var(--foreground) 18%)}
.hl .hl-btn.line,.hl-dlg .hl-btn.line{background:transparent;color:var(--foreground);border:1px solid var(--input)}
.hl .hl-btn.line:hover,.hl-dlg .hl-btn.line:hover{background:var(--muted)}
.hl .hl-btn.danger,.hl-dlg .hl-btn.danger{background:var(--destructive);color:var(--destructive-foreground);border:1px solid var(--destructive)}
.hl .hl-btn.danger:hover,.hl-dlg .hl-btn.danger:hover{background:color-mix(in oklab,var(--destructive),var(--foreground) 16%)}
.hl .hl-btn:active,.hl-dlg .hl-btn:active{transform:translateY(1px);box-shadow:inset 0 2px 0 rgb(0 0 0 / .18)}
.hl .hl-btn:disabled,.hl-dlg .hl-btn:disabled{opacity:1;background:var(--hl-disabled-bg);color:var(--hl-disabled-fg);border-color:var(--input)}
.hl-textbtn{display:flex;width:100%;align-items:center;gap:8px;min-height:40px;padding:8px 10px;border:0;background:transparent;color:var(--foreground);text-align:left;
  font:500 14px/1.3 "Llamado Sans",sans-serif;cursor:pointer;transition:background-color calc(var(--k)*140ms) var(--set)}
.hl-textbtn:hover{background:var(--muted)}.hl-textbtn.danger{color:var(--hl-note)}
.hl-textbtn:disabled{cursor:not-allowed;color:var(--muted-foreground);text-decoration:line-through}

/* register */
.hl-reg{width:100%;border-collapse:collapse;font-stretch:84%}
.hl-reg caption{text-align:left}
.hl-reg th{padding:12px;text-align:left;font-size:13px;font-weight:500;color:var(--muted-foreground);border-bottom:1px solid var(--hl-rule);white-space:nowrap}
.hl-reg td{padding:14px 12px;vertical-align:top;border-bottom:1px solid var(--border)}
.hl-reg tbody tr{position:relative;animation:hl-row calc(var(--k)*520ms) var(--set) both;animation-delay:calc(var(--r)*32ms*var(--k) + 160ms*var(--k))}
.hl-reg tbody tr:hover td:not(.hl-m){background:color-mix(in oklab,var(--hl-sel),transparent 45%)}
.hl-reg tbody tr td{transition:background-color calc(var(--k)*160ms) var(--set)}
.hl-reg tr[data-sel] td{background:var(--hl-sel)}
.hl-reg .hl-m,.hl-reg th.hl-mh{position:relative;width:236px;padding-left:24px}
.hl-reg .hl-m::before,.hl-reg th.hl-mh::before{content:"";position:absolute;left:0;top:0;bottom:-1px;width:1px;background:var(--hl-rule)}
.hl-pick{display:block;border:0;background:transparent;padding:0;text-align:left;color:var(--foreground);cursor:pointer;font:600 16px/1.25 "Llamado Sans",sans-serif;font-stretch:84%}
.hl-pick:hover{text-decoration:underline;text-underline-offset:4px}
.hl-sub{display:block;color:var(--muted-foreground);font-size:13px;margin-top:2px}
.hl-state{display:inline-flex;align-items:center;gap:8px;white-space:nowrap}
.hl-state.invitada{color:var(--hl-amber)}.hl-state.desactivada{color:var(--muted-foreground)}
.hl-note{position:relative;display:block;padding-left:22px;font-family:"Llamado Display",Georgia,serif;font-style:italic;font-size:17px;line-height:1.2;font-stretch:100%;
  color:var(--muted-foreground);animation:hl-note calc(var(--k)*420ms) var(--set) both;animation-delay:calc(var(--r)*32ms*var(--k) + 520ms*var(--k))}
.hl-note.refuse{color:var(--hl-note)}
.hl-leader{position:absolute;left:-24px;top:.62em;width:38px;height:1px;background:currentColor;transform-origin:left;
  animation:hl-draw calc(var(--k)*380ms) var(--cut) both;animation-delay:inherit}
.hl-slip{display:grid;gap:10px;margin-top:12px;padding:16px;background:var(--card);border:1px solid var(--hl-rule);font-stretch:96%}
.hl-slip h3{margin:0;font-size:13px;font-weight:600}
.hl-slip .hl-textbtn{margin:0 -10px;width:calc(100% + 20px)}
.hl-status{font-size:13px;font-weight:600;color:var(--primary)}
.hl-empty,.hl-fail{display:grid;gap:12px;justify-items:start;padding:28px 0}
.hl-empty h2,.hl-fail h2{margin:0;font-size:34px;line-height:1.05}
.hl-skel{display:grid;gap:18px;padding-top:12px}
.hl-skel [data-slot="skeleton"]{border-radius:2px;background:var(--muted)}

/* split: working column + margin column of notes (Mi cuenta, roles editor) */
.hl-split{display:grid;grid-template-columns:minmax(0,1fr) 236px;gap:0 36px;align-items:start}
.hl-margin{position:relative;display:grid;gap:22px;padding:4px 0 4px 24px;align-content:start}
.hl-margin::before{content:"";position:absolute;left:0;top:0;bottom:0;width:1px;background:var(--hl-rule);transform-origin:top;animation:hl-drop calc(var(--k)*560ms) var(--cut) both}
.hl-margin .hl-note{animation-delay:calc(var(--r,0)*60ms*var(--k) + 300ms*var(--k))}
.hl-facts{display:grid;grid-template-columns:150px minmax(0,1fr);margin:0}
.hl-facts dt,.hl-facts dd{margin:0;padding:12px 0;border-bottom:1px solid var(--border)}
.hl-facts dt{color:var(--muted-foreground);font-size:13px;padding-top:14px}
.hl-facts dd{font-weight:600;font-stretch:88%}
.hl-sec{margin:36px 0 14px;font-size:34px;line-height:1}
.hl-form{display:grid;gap:18px;max-width:440px}

/* roles */
.hl-rindex{list-style:none;margin:0;padding:0;display:grid}
.hl-rindex button{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 12px;width:100%;padding:12px;border:0;border-bottom:1px solid var(--border);background:transparent;
  color:var(--foreground);text-align:left;cursor:pointer;font:600 15px/1.25 "Llamado Sans",sans-serif;font-stretch:88%;transition:background-color calc(var(--k)*160ms) var(--set)}
.hl-rindex button:hover{background:color-mix(in oklab,var(--hl-sel),transparent 45%)}
.hl-rindex button[aria-pressed="true"]{background:var(--hl-sel)}
.hl-rindex small{grid-column:1/-1;font-weight:400;color:var(--muted-foreground);font-size:13px}
.hl-rindex .hl-mono{align-self:center;color:var(--muted-foreground)}
.hl-perms{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:26px 32px;margin-top:8px}
.hl-perms fieldset{margin:0;padding:0;border:0;min-width:0;animation:hl-row calc(var(--k)*480ms) var(--set) both;animation-delay:calc(var(--r)*40ms*var(--k) + 120ms*var(--k))}
.hl-perms legend{padding:0 0 8px;font-family:"Llamado Display",Georgia,serif;font-size:24px;line-height:1.1;font-stretch:100%}
.hl-check{display:flex;align-items:flex-start;gap:12px;padding:10px 0;border-top:1px solid var(--border);font-size:14px;line-height:1.35;cursor:pointer}
.hl-check [data-slot="checkbox"]{margin-top:1px;width:20px;height:20px;border-radius:2px;border-color:var(--input);background:var(--card)}
.hl-check [data-slot="checkbox"][data-checked]{background:var(--primary);border-color:var(--primary);color:var(--primary-foreground)}
.hl-ro{display:flex;align-items:flex-start;gap:12px;padding:10px 0;border-top:1px solid var(--border);font-size:14px}
.hl-ro.off{color:var(--muted-foreground)}
.hl-ro svg{flex:none;margin-top:2px}
.hl-actions{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}

/* public sheets: nameplate + columns */
.hl-plate{margin:0;padding:28px 40px 6px;font-size:168px;line-height:.8;letter-spacing:-.035em;font-style:italic;animation:hl-set calc(var(--k)*760ms) var(--set) both}
.hl-plate-wrap{position:relative}
.hl-reg-mark{position:absolute;width:18px;height:18px;color:var(--muted-foreground)}
.hl-pubdate{display:flex;align-items:center;gap:12px 24px;flex-wrap:wrap;padding:12px 40px;font-size:14px}
.hl-pubdate .hl-field{display:flex;align-items:center;gap:10px;margin-left:auto}
.hl-pubdate .hl-select{width:auto;height:40px}
.hl-cols{display:grid;grid-template-columns:400px minmax(0,1fr);grid-template-areas:"form art" "acc art";gap:0 64px;padding:36px 40px 72px;align-items:start;
  animation:hl-shift calc(var(--k)*560ms) var(--set) both}
.hl-cols>.f{grid-area:form;display:grid;gap:18px}
.hl-cols>.a{grid-area:art;position:relative;padding-left:36px}
.hl-cols>.a::before{content:"";position:absolute;left:0;top:0;bottom:0;width:1px;background:var(--hl-rule);transform-origin:top;animation:hl-drop calc(var(--k)*620ms) var(--cut) both}
.hl-cols>.c{grid-area:acc;display:grid;gap:18px;margin-top:22px}
.hl-title{margin:0;font-size:52px;line-height:.95;letter-spacing:-.015em;animation:hl-set calc(var(--k)*620ms) var(--set) both;animation-delay:calc(var(--k)*120ms)}
.hl-lede{margin:0;font-size:16px;color:var(--muted-foreground);max-width:40ch}
.hl-article{font-family:"Llamado Display",Georgia,serif;font-stretch:100%;font-size:21px;line-height:1.42;max-width:62ch;margin:0}
.hl-article h2{font-size:30px;line-height:1.05;margin:0 0 8px;font-weight:400}
.hl-meta{display:block;margin:0 0 18px;font-family:"Llamado Sans",sans-serif;font-size:13px;color:var(--muted-foreground)}
.hl-ph{color:var(--hl-note);text-decoration:underline dotted;text-underline-offset:4px}
.hl-columns{columns:2 260px;column-gap:36px;font-size:15px}
.hl-columns p{margin:0 0 14px;break-inside:avoid}
.hl-accept{display:flex;align-items:flex-start;gap:12px;font-size:15px;line-height:1.4;cursor:pointer}
.hl-accept [data-slot="checkbox"]{margin-top:2px;width:22px;height:22px;border-radius:2px;border-color:var(--input);background:var(--card)}
.hl-accept [data-slot="checkbox"][data-checked]{background:var(--primary);border-color:var(--primary);color:var(--primary-foreground)}
.hl-alert{position:relative;display:grid;gap:6px;padding:14px 16px 14px 20px;background:var(--card);border:1px solid var(--hl-note);animation:hl-row calc(var(--k)*420ms) var(--set) both}
.hl-alert strong{color:var(--hl-note)}
.hl-ok{display:grid;gap:6px;padding:14px 16px 14px 20px;background:var(--card);border:1px solid var(--primary);animation:hl-row calc(var(--k)*420ms) var(--set) both}
.hl-foot{margin:0;font-size:14px;color:var(--muted-foreground)}
.hl-invited{display:grid;grid-template-columns:110px minmax(0,1fr);margin:0;font-size:15px}
.hl-invited dt,.hl-invited dd{margin:0;padding:10px 0;border-bottom:1px solid var(--border)}
.hl-invited dt{color:var(--muted-foreground);font-size:13px;padding-top:12px}
.hl-invited dd{font-weight:600}

/* dialogs & menu (portalled outside .hl) */
[data-slot="dialog-overlay"],[data-slot="alert-dialog-overlay"]{background:var(--hl-overlay)!important;backdrop-filter:none!important}
.hl-dlg{border-radius:2px!important;box-shadow:0 18px 50px rgb(0 0 0 / .28)!important;color:var(--foreground)}
.hl-dlg .hl-dlg-in{display:grid;gap:18px;animation:hl-slip calc(var(--k)*460ms) var(--set) both}
.hl-dlg .hl-dlg-title{font-family:"Llamado Display",Georgia,serif;font-size:34px;line-height:1;font-weight:400;letter-spacing:-.01em;color:var(--foreground)}
.hl-dlg .hl-dlg-desc{font-size:15px;line-height:1.45;color:var(--muted-foreground);text-wrap:pretty}
.hl-dlg .hl-dlg-foot{display:flex;flex-wrap:wrap;justify-content:flex-end;gap:12px;padding-top:8px}
.hl-dlg .hl-rule{animation-delay:calc(var(--k)*80ms)}
.hl-link{display:flex;gap:8px;align-items:stretch}
.hl-link input{flex:1;min-width:0;font-family:"Llamado Mono",ui-monospace,monospace!important;font-size:13px!important}
.hl-stamp{display:inline-flex;align-items:center;gap:6px}
.hl-stamp path{stroke-dasharray:24;stroke-dashoffset:0;animation:hl-ink calc(var(--k)*360ms) var(--set) both}
.hl-menu{border-radius:2px!important;min-width:260px!important;padding:6px!important;box-shadow:0 14px 36px rgb(0 0 0 / .22)!important}
.hl-menu [data-slot="dropdown-menu-item"]{min-height:40px;border-radius:2px;padding:8px 10px;font-size:14px}
.hl-menu [data-slot="dropdown-menu-label"]{padding:10px;color:var(--foreground);font-size:14px}
.hl-menu [data-slot="dropdown-menu-label"] span{display:block;color:var(--muted-foreground);font-weight:400;font-size:13px}

@keyframes hl-draw{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes hl-drop{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes hl-set{from{clip-path:inset(0 100% 0 0);transform:translateX(-.08em)}to{clip-path:inset(0 0 0 0);transform:none}}
@keyframes hl-shift{from{transform:translateX(18px)}to{transform:none}}
@keyframes hl-row{from{transform:translateX(-12px)}to{transform:none}}
@keyframes hl-note{from{transform:translateX(10px)}to{transform:none}}
@keyframes hl-roll{from{transform:translateY(100%)}to{transform:none}}
@keyframes hl-swatch{from{transform:scaleY(.15)}to{transform:none}}
@keyframes hl-slip{from{transform:translateY(16px)}to{transform:none}}
@keyframes hl-ink{from{stroke-dashoffset:24}to{stroke-dashoffset:0}}
@keyframes hl-condense{from{transform:none}to{transform:scale(.62)}}
@supports (animation-timeline: scroll()){
  @media (min-width:1200px){.hl-headwrap{animation:hl-condense linear both;animation-timeline:scroll(root);animation-range:0 280px}}
}

/* tablet: the headline column becomes a band above the register */
@media (max-width:1199px){
  .hl-sheet{grid-template-columns:minmax(0,1fr);gap:32px;padding:28px 32px 64px}
  .hl-lead{position:static;grid-template-columns:minmax(0,1fr) minmax(0,1fr);align-items:end;gap:20px 32px}
  .hl-head{font-size:80px}
  .hl-reg .hl-m,.hl-reg th.hl-mh{width:200px}
  .hl-split{grid-template-columns:minmax(0,1fr) 200px;gap:0 28px}
  .hl-date{padding:12px 32px}.hl-pubdate{padding:12px 32px}
  .hl-plate{font-size:128px;padding:24px 32px 6px}
  .hl-cols{grid-template-columns:340px minmax(0,1fr);gap:0 40px;padding:32px 32px 64px}
}
/* phone: everything in one column; margin notes drop under their row */
@media (max-width:767px){
  .hl-date{padding:12px 20px;gap:8px 12px}.hl-strip{display:none}
  .hl-acct{margin-left:auto}
  .hl-index{order:3;width:100%}.hl-index ul{flex-wrap:wrap}
  .hl-sheet{padding:24px 20px 56px;gap:28px}
  .hl-lead{grid-template-columns:minmax(0,1fr)}
  .hl-head{font-size:60px}.hl-deck{font-size:19px}
  .hl-reg,.hl-reg tbody,.hl-reg tr,.hl-reg td{display:block;width:100%}
  .hl-reg thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
  .hl-reg tr{border-bottom:1px solid var(--hl-rule)}
  .hl-reg td{border:0;padding:12px}
  .hl-reg td[data-label]:not(.hl-first){display:grid;grid-template-columns:120px minmax(0,1fr);gap:12px;padding-top:4px;padding-bottom:4px}
  .hl-reg td[data-label]:not(.hl-first)::before{content:attr(data-label);color:var(--muted-foreground);font-size:13px}
  .hl-reg .hl-m{width:100%;padding:12px}
  .hl-reg .hl-m::before{left:12px;right:12px;top:0;bottom:auto;width:auto;height:1px}
  .hl-reg .hl-m:empty{display:none}
  .hl-note{padding-left:0;padding-top:10px}.hl-leader{display:none}
  .hl-split{grid-template-columns:minmax(0,1fr);gap:24px}
  .hl-margin{padding:20px 0 0}.hl-margin::before{left:0;right:0;top:0;bottom:auto;width:auto;height:1px;transform-origin:left}
  .hl-facts{grid-template-columns:110px minmax(0,1fr)}
  .hl-perms{grid-template-columns:minmax(0,1fr)}
  .hl-pubdate{padding:12px 20px}.hl-pubdate .hl-field{margin-left:0}
  .hl-plate{font-size:76px;padding:20px 20px 4px}
  .hl-cols{grid-template-columns:minmax(0,1fr);grid-template-areas:"form" "art" "acc";padding:24px 20px 56px}
  .hl-cols>.a{padding-left:0;padding-top:24px;margin-top:28px}
  .hl-cols>.a::before{left:0;right:0;top:0;bottom:auto;width:auto;height:1px;transform-origin:left}
  .hl-title{font-size:42px}
  .hl-article{font-size:19px}
  .hl-row2{grid-template-columns:minmax(0,1fr)}
  .hl-reg-mark{display:none}
}
/* reduced motion / Quieto: final layout at once, feedback still immediate */
html[data-reduced-motion] .hl *,html[data-reduced-motion] .hl,html[data-reduced-motion] .hl-dlg *,html[data-reduced-motion] .hl-menu *{
  animation:none!important;transition-duration:0s!important}
@media (prefers-reduced-motion:reduce){.hl *,.hl,.hl-dlg *,.hl-menu *{animation:none!important;transition-duration:0s!important}}
`;

// ── mock data (illustrative; one source for every count on screen) ─────────────────────────────────────────────
type Estado = "activa" | "invitada" | "desactivada";
type Cuenta = { id: string; nombre: string; correo: string; empresa?: string; rol: string; estado: Estado; acceso: string;
  trabajo?: string; nota?: { texto: string; rechazo?: boolean } };
type Rol = { id: string; nombre: string; sistema: boolean; permisos: string[]; resumen: string };

const GRUPOS: { herramienta: string; permisos: { id: string; label: string }[] }[] = [
  { herramienta: "Chat asistido", permisos: [{ id: "chat.usar", label: "Usar el chat asistido" }] },
  { herramienta: "Contador de globos", permisos: [{ id: "contador.usar", label: "Usar el contador de globos" }] },
  { herramienta: "Catálogo y decoraciones", permisos: [{ id: "catalogo.ver", label: "Ver el catálogo" }, { id: "decoraciones.explorar", label: "Explorar decoraciones listas" }] },
  { herramienta: "Calculadora de costos", permisos: [{ id: "costos.usar", label: "Usar la calculadora de costos" }] },
  { herramienta: "Taller 3D", permisos: [{ id: "taller.usar", label: "Usar el Taller 3D: IA de escena, planos, hoja de montaje, exportar y proyectos propios" }] },
  { herramienta: "Proyectos y gasto", permisos: [{ id: "proyectos.ver_todos", label: "Ver los proyectos de todas las cuentas" }, { id: "gasto.ver", label: "Ver el gasto de IA" }] },
  { herramienta: "Herramientas internas", permisos: [{ id: "internas.usar", label: "Usar las herramientas internas" }] },
  { herramienta: "Administración", permisos: [{ id: "cuentas.administrar", label: "Administrar cuentas" }, { id: "roles.administrar", label: "Administrar roles" }, { id: "textos.corregir", label: "Corregir textos en inglés" }] },
];
const P1 = ["chat.usar", "contador.usar", "catalogo.ver"];
const P2 = [...P1, "costos.usar", "decoraciones.explorar"];
const P3 = [...P2, "taller.usar"];
const EMP = [...P3, "proyectos.ver_todos", "gasto.ver", "internas.usar"];
const ADM = [...EMP, "cuentas.administrar", "roles.administrar", "textos.corregir"];
const ROLES: Rol[] = [
  { id: "plan1", nombre: "Usuario · Plan 1", sistema: true, permisos: P1, resumen: "Chat, contador y catálogo" },
  { id: "plan2", nombre: "Usuario · Plan 2", sistema: true, permisos: P2, resumen: "Plan 1 + costos y decoraciones" },
  { id: "plan3", nombre: "Usuario · Plan 3", sistema: true, permisos: P3, resumen: "Plan 2 + Taller 3D" },
  { id: "empleado", nombre: "Empleado interno", sistema: true, permisos: EMP, resumen: "Plan 3 + proyectos de todos, gasto e internas" },
  { id: "admin", nombre: "Administrador", sistema: true, permisos: ADM, resumen: "Todo, con cuentas, roles y textos" },
  { id: "montaje", nombre: "Montaje externo", sistema: false, permisos: ["chat.usar", "contador.usar", "catalogo.ver", "taller.usar"], resumen: "Creado aquí el 14 oct" },
  { id: "ventas", nombre: "Ventas · cotizaciones", sistema: false, permisos: ["chat.usar", "catalogo.ver", "costos.usar"], resumen: "Creado aquí el 21 oct" },
];
const rolNombre = (id: string) => ROLES.find((r) => r.id === id)?.nombre ?? id;

const CUENTAS: Cuenta[] = [
  { id: "lr", nombre: "Lucía Ramírez", correo: "lucia.ramirez@sempertex.com", empresa: "Sempertex", rol: "admin", estado: "activa", acceso: "hoy 09:12",
    nota: { texto: "Único administrador: no se puede desactivar ni borrar.", rechazo: true } },
  { id: "mo", nombre: "Mariana Ortiz", correo: "mariana@eventosaurora.co", empresa: "Eventos Aurora", rol: "plan2", estado: "activa", acceso: "ayer 18:40" },
  { id: "cr", nombre: "Camila Restrepo", correo: "camila@decoracionesluz.co", empresa: "Decoraciones Luz", rol: "plan3", estado: "activa", acceso: "hoy 08:05",
    trabajo: "7 proyectos y 2 decoraciones", nota: { texto: "7 proyectos y 2 decoraciones guardados: solo se puede desactivar.", rechazo: true } },
  { id: "jc", nombre: "Julián Cárdenas", correo: "julian@fiestasjc.com", empresa: "Fiestas JC", rol: "plan3", estado: "invitada", acceso: "—",
    nota: { texto: "Invitación abierta hasta el 2 nov." } },
  { id: "th", nombre: "Tomás Herrera", correo: "tomas.herrera@sempertex.com", empresa: "Sempertex", rol: "empleado", estado: "activa", acceso: "24 oct 16:02" },
  { id: "dc", nombre: "Daniela Cruz", correo: "daniela@momentosdc.com", empresa: "Momentos DC", rol: "montaje", estado: "activa", acceso: "25 oct 11:30" },
  { id: "am", nombre: "Andrés Mejía", correo: "andres@globosandes.co", empresa: "Globos Andes", rol: "plan1", estado: "activa", acceso: "20 oct 10:47" },
  { id: "vr", nombre: "Valentina Rojas", correo: "valen@celebrarte.co", empresa: "Celebrarte", rol: "plan2", estado: "invitada", acceso: "—",
    nota: { texto: "Invitación vencida el 24 oct: genera un enlace nuevo.", rechazo: true } },
  { id: "pg", nombre: "Paola Gómez", correo: "paola.gomez@sempertex.com", empresa: "Sempertex", rol: "empleado", estado: "desactivada", acceso: "12 oct 15:20",
    trabajo: "4 proyectos", nota: { texto: "4 proyectos guardados: no se puede borrar." } },
  { id: "sp", nombre: "Sergio Patiño", correo: "sergio.patino@gmail.com", rol: "plan1", estado: "activa", acceso: "3 oct 09:58" },
  { id: "fa", nombre: "Felipe Arango", correo: "felipe@arangoeventos.co", empresa: "Arango Eventos", rol: "plan2", estado: "desactivada", acceso: "30 sep 17:14" },
  { id: "nv", nombre: "Natalia Vélez", correo: "natalia.velez@sempertex.com", empresa: "Sempertex", rol: "empleado", estado: "invitada", acceso: "—",
    nota: { texto: "Invitación abierta hasta el 31 oct." } },
];
const cuentasDe = (rol: string) => CUENTAS.filter((c) => c.rol === rol);
const ESTADO_LABEL: Record<Estado, string> = { activa: "Activa", invitada: "Invitada", desactivada: "Desactivada" };
const ADMIN = CUENTAS[0];
const AVISO = {
  es: { titulo: "Aviso de tratamiento de datos personales", parts: ["", "[RAZÓN SOCIAL DE SEMPERTEX]", " tratará tus datos personales —nombre, correo, empresa (si la indicas), el rol y el plan que te asignen, y las fechas de invitación, activación y último acceso— para darte acceso a Pictures durante el piloto, administrar tu cuenta y medir el uso de las herramientas, incluido el consumo de inteligencia artificial. Los proyectos y decoraciones que guardes quedan asociados a tu cuenta. Puedes conocer, actualizar, rectificar o pedir la supresión de tus datos, y revocar esta autorización, escribiendo a ", "[CORREO PARA DERECHOS]", ". La política de tratamiento de datos está en ", "[URL DE LA POLÍTICA]", ". Al activar tu cuenta declaras que leíste este aviso y autorizas el tratamiento descrito, conforme a la Ley 1581 de 2012."], idioma: "Español" },
  en: { titulo: "Personal data notice", parts: ["", "[SEMPERTEX LEGAL NAME]", " will process your personal data —name, email, company (if you provide it), the role and plan assigned to you, and the dates of invitation, activation and last access— to give you access to Pictures during the pilot, manage your account and measure the use of the tools, including artificial-intelligence usage. The projects and decorations you save are linked to your account. You can access, update, correct or request deletion of your data, and withdraw this authorization, by writing to ", "[RIGHTS CONTACT EMAIL]", ". The data-processing policy is at ", "[POLICY URL]", ". By activating your account you confirm that you have read this notice and authorize the processing described, under Colombian Law 1581 of 2012."], idioma: "English" },
};
const SWATCHES = ["#c8102e", "#e35205", "#f6be00", "#0a8f3c", "#0057b8", "#d0006f", "#7d55c7", "#a7a8aa", "#b08d57", "#1d1d1b"];

// ── small pieces ──────────────────────────────────────────────────────────────────────────────────────────────
function Roll({ value }: { value: number | string }) {
  return <span className="hl-roll"><span key={String(value)} className="hl-roll-in">{value}</span></span>;
}
function StateMark({ estado }: { estado: Estado }) {
  return (
    <span className={`hl-state ${estado}`}>
      <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden="true">
        {estado === "activa" && <rect x="1" y="1" width="8" height="8" fill="currentColor" />}
        {estado === "invitada" && <rect x="1.5" y="1.5" width="7" height="7" fill="none" stroke="currentColor" strokeWidth="1.5" />}
        {estado === "desactivada" && <path d="M1 5h8" stroke="currentColor" strokeWidth="2" />}
      </svg>
      {ESTADO_LABEL[estado]}
    </span>
  );
}
function Note({ children, refuse, r = 0 }: { children: React.ReactNode; refuse?: boolean; r?: number }) {
  return (
    <span className={`hl-note${refuse ? " refuse" : ""}`} style={{ ["--r" as string]: r }}>
      <span className="hl-leader" aria-hidden="true" />{children}
    </span>
  );
}
function RegMark({ style }: { style: React.CSSProperties }) {
  return (
    <svg className="hl-reg-mark" style={style} viewBox="0 0 18 18" aria-hidden="true">
      <circle cx="9" cy="9" r="5" fill="none" stroke="currentColor" /><path d="M9 0v18M0 9h18" stroke="currentColor" />
    </svg>
  );
}
function Strip() {
  return <span className="hl-strip" aria-hidden="true">{SWATCHES.map((c, i) => <i key={c} style={{ background: c, ["--i" as string]: i }} />)}</span>;
}
function Btn({ kind = "primary", className = "", ...p }: React.ComponentProps<typeof Button> & { kind?: "primary" | "line" | "danger" }) {
  return <Button {...p} className={`hl-btn ${kind} ${className}`} />;
}
function Field({ id, label, help, error, ...p }: React.ComponentProps<"input"> & { id: string; label: string; help?: string; error?: string }) {
  const desc = error ? `${id}-err` : help ? `${id}-help` : undefined;
  return (
    <div className="hl-field">
      <label htmlFor={id}>{label}</label>
      <Input id={id} aria-invalid={error ? true : undefined} aria-describedby={desc} {...p} />
      {error ? <p className="hl-err" id={`${id}-err`}>{error}</p> : help ? <p className="hl-help" id={`${id}-help`}>{help}</p> : null}
    </div>
  );
}

// ── signed-in dateline with the running section index and the account menu ──────────────────────────────────
function AccountMenu({ gate }: { gate?: boolean }) {
  const m = useMockup();
  const [open, setOpen] = React.useState(false);
  return (
    <DropdownMenu open={open || m.scene === "menu"} onOpenChange={(o) => { setOpen(o); if (!o && m.scene === "menu") m.set("scene", ""); }}>
      <DropdownMenuTrigger render={<button type="button" className="hl-acct" aria-label={`Cuenta de ${ADMIN.nombre}, ${rolNombre(ADMIN.rol)}`} />}>
        <UserRound size={16} aria-hidden="true" />
        <span>{ADMIN.nombre} <small>· {rolNombre(ADMIN.rol)}</small></span>
        <ChevronDown size={16} aria-hidden="true" />
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={6} className="hl-menu">
        <DropdownMenuGroup>
          <DropdownMenuLabel><strong>{ADMIN.nombre}</strong><span>{rolNombre(ADMIN.rol)} · {ADMIN.correo}</span></DropdownMenuLabel>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled={gate} onClick={() => m.set("view", "mi-cuenta")}><UserRound aria-hidden="true" />{gate ? "Mi cuenta (acepta el aviso primero)" : "Mi cuenta"}</DropdownMenuItem>
        <DropdownMenuItem onClick={() => m.set("view", "login")}><LogOut aria-hidden="true" />Cerrar sesión</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
function Dateline({ gate }: { gate?: boolean }) {
  const m = useMockup();
  const items = [{ id: "cuentas", label: "Cuentas", n: CUENTAS.length }, { id: "roles", label: "Roles", n: ROLES.length }, { id: "mi-cuenta", label: "Mi cuenta" }];
  return (
    <>
      <header className="hl-date">
        <span className="hl-brand hl-serif">Pictures</span>
        {gate ? <span className="hl-gate">Antes de seguir, acepta el aviso de datos actualizado.</span> : (
          <nav className="hl-index" aria-label="Administración">
            <ul>
              {items.map((it) => (
                <li key={it.id}>
                  <button type="button" aria-current={m.view === it.id ? "page" : undefined} onClick={() => m.set("view", it.id)}>
                    {it.label}{it.n !== undefined && <span className="hl-mono">{it.n}</span>}
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        )}
        <Strip />
        <AccountMenu gate={gate} />
      </header>
      <div className="hl-stick" aria-hidden="true" />
    </>
  );
}

// ── Administración · Cuentas ─────────────────────────────────────────────────────────────────────────────────
function Slip({ c, saved }: { c: Cuenta; saved: boolean }) {
  const m = useMockup();
  const { reduced, profile } = useMotionProfile();
  const dur = { expressive: 0.46, natural: 0.28, subtle: 0.16 }[profile];
  const lastAdmin = c.rol === "admin" && cuentasDe("admin").length === 1;
  return (
    <motion.div id={`slip-${c.id}`} className="hl-slip" role="group" aria-label={`Acciones para ${c.nombre}`}
      initial={reduced ? false : { clipPath: "inset(0 0 100% 0)", y: -6 }} animate={{ clipPath: "inset(0 0 0% 0)", y: 0 }}
      transition={{ duration: dur, ease: [0.16, 1, 0.3, 1] }}>
      <h3>Acciones · {c.nombre}</h3>
      <div className="hl-field">
        <label htmlFor="slip-rol">Rol</label>
        <select id="slip-rol" className="hl-select" defaultValue={saved ? "plan3" : c.rol} disabled={lastAdmin} aria-describedby={lastAdmin ? "slip-last" : undefined}>
          {ROLES.map((r) => <option key={r.id} value={r.id}>{r.nombre}</option>)}
        </select>
      </div>
      {saved ? <p className="hl-status" role="status">Rol cambiado a Usuario · Plan 3. Aplica en su próxima acción.</p>
        : !lastAdmin && <Btn kind="line">Guardar rol</Btn>}
      <div>
        <button type="button" className="hl-textbtn" onClick={() => m.set("scene", c.estado === "invitada" ? "invitar-enlace" : "restablecer-enlace")}>
          {c.estado === "invitada" ? "Generar enlace de invitación nuevo" : "Generar enlace para restablecer"}
        </button>
        {c.estado === "desactivada"
          ? <button type="button" className="hl-textbtn">Reactivar cuenta</button>
          : <button type="button" className="hl-textbtn" disabled={lastAdmin} aria-describedby={lastAdmin ? "slip-last" : undefined} onClick={() => m.set("scene", "desactivar")}>Desactivar cuenta</button>}
        <button type="button" className="hl-textbtn danger" disabled={lastAdmin} aria-describedby={lastAdmin ? "slip-last" : undefined}
          onClick={() => m.set("scene", c.trabajo ? "borrar-rechazado" : "borrar")}>Borrar cuenta…</button>
      </div>
      {lastAdmin && <p className="hl-help" id="slip-last">Siempre debe quedar un administrador activo.</p>}
    </motion.div>
  );
}

function Cuentas() {
  const m = useMockup();
  const [q, setQ] = React.useState(m.state === "vacio" ? "zuleta" : "");
  const [rol, setRol] = React.useState("");
  const [est, setEst] = React.useState("");
  const [sel, setSel] = React.useState("mo");
  const loading = m.state === "cargando";
  const failed = m.state === "error";
  const saved = m.state === "exito";
  const rows = CUENTAS.filter((c) => (!q || `${c.nombre} ${c.correo}`.toLowerCase().includes(q.toLowerCase())) && (!rol || c.rol === rol) && (!est || c.estado === est));
  const n = (e: Estado) => CUENTAS.filter((c) => c.estado === e).length;
  const filtered = q || rol || est;
  return (
    <div className="hl-sheet">
      <aside className="hl-lead" aria-label="Resumen y filtros">
        <div className="hl-headwrap"><h1 className="hl-head hl-serif">Cuentas</h1></div>
        {loading ? <div className="hl-skel" aria-hidden="true"><Skeleton className="h-6 w-56" /><Skeleton className="h-6 w-44" /></div> : (
          <p className="hl-deck hl-serif" aria-live="polite">
            {filtered ? <><Roll value={rows.length} /> de {CUENTAS.length} cuentas coinciden con el filtro.</>
              : <><Roll value={CUENTAS.length} /> cuentas: <Roll value={n("activa")} /> activas, <Roll value={n("invitada")} /> invitaciones abiertas y <Roll value={n("desactivada")} /> desactivadas.</>}
          </p>
        )}
        <div><Btn onClick={() => m.set("scene", "invitar")}><Plus size={16} aria-hidden="true" />Invitar persona</Btn></div>
        <div className="hl-rule" aria-hidden="true" />
        <div className="hl-filters" role="search" aria-label="Filtrar cuentas">
          <div className="hl-field">
            <label htmlFor="q">Buscar por nombre o correo</label>
            <div className="hl-search"><Search aria-hidden="true" /><Input id="q" value={q} onChange={(e) => setQ(e.target.value)} placeholder="p. ej. Ortiz o @sempertex.com" /></div>
          </div>
          <div className="hl-row2">
            <div className="hl-field"><label htmlFor="f-rol">Rol</label>
              <select id="f-rol" className="hl-select" value={rol} onChange={(e) => setRol(e.target.value)}>
                <option value="">Todos</option>{ROLES.map((r) => <option key={r.id} value={r.id}>{r.nombre}</option>)}
              </select></div>
            <div className="hl-field"><label htmlFor="f-est">Estado</label>
              <select id="f-est" className="hl-select" value={est} onChange={(e) => setEst(e.target.value)}>
                <option value="">Todos</option><option value="activa">Activa</option><option value="invitada">Invitada</option><option value="desactivada">Desactivada</option>
              </select></div>
          </div>
        </div>
      </aside>
      <section aria-label="Registro de cuentas">
        {failed ? (
          <div className="hl-fail" role="alert">
            <h2 className="hl-serif">No se pudo cargar la lista de cuentas.</h2>
            <p className="hl-help">Revisa la conexión y vuelve a intentarlo. No cambió nada.</p>
            <Btn kind="line">Volver a intentar</Btn>
          </div>
        ) : (
          <table className="hl-reg" aria-busy={loading || undefined}>
            <caption className="hl-sr">Cuentas con nombre, empresa, rol, estado, último acceso y notas</caption>
            <thead><tr><th scope="col">Persona</th><th scope="col">Empresa</th><th scope="col">Rol</th><th scope="col">Estado</th><th scope="col">Último acceso</th><th scope="col" className="hl-mh">Notas y acciones</th></tr></thead>
            <tbody>
              {loading ? Array.from({ length: 7 }, (_, i) => (
                <tr key={i} style={{ ["--r" as string]: i }} aria-hidden="true">
                  <td className="hl-first"><Skeleton className="h-4 w-36" /><Skeleton className="mt-2 h-3 w-44" /></td>
                  <td data-label="Empresa"><Skeleton className="h-4 w-20" /></td><td data-label="Rol"><Skeleton className="h-4 w-24" /></td>
                  <td data-label="Estado"><Skeleton className="h-4 w-16" /></td><td data-label="Último acceso"><Skeleton className="h-4 w-16" /></td><td className="hl-m" />
                </tr>
              )) : rows.length === 0 ? (
                <tr style={{ ["--r" as string]: 0 }}><td colSpan={6} className="hl-first">
                  <div className="hl-empty">
                    <h2 className="hl-serif">Ninguna cuenta coincide con «{q}».</h2>
                    <p className="hl-help">Busca por otra parte del nombre o del correo, o invita a esa persona si aún no tiene cuenta.</p>
                    <div className="hl-actions" style={{ marginTop: 0 }}>
                      <Btn kind="line" onClick={() => { setQ(""); setRol(""); setEst(""); }}>Quitar filtros</Btn>
                      <Btn onClick={() => m.set("scene", "invitar")}><Plus size={16} aria-hidden="true" />Invitar persona</Btn>
                    </div>
                  </div>
                </td></tr>
              ) : rows.map((c, i) => {
                const on = sel === c.id;
                const nota = saved && c.id === "mo" ? undefined : c.nota;
                return (
                  <tr key={c.id} data-sel={on || undefined} style={{ ["--r" as string]: i }}>
                    <td className="hl-first">
                      <button type="button" className="hl-pick" aria-expanded={on} aria-controls={on ? `slip-${c.id}` : undefined} onClick={() => setSel(on ? "" : c.id)}>{c.nombre}</button>
                      <span className="hl-sub hl-mono">{c.correo}</span>
                    </td>
                    <td data-label="Empresa">{c.empresa ?? <span className="hl-sub" style={{ marginTop: 0 }}>Sin empresa</span>}</td>
                    <td data-label="Rol">{rolNombre(saved && c.id === "mo" ? "plan3" : c.rol)}</td>
                    <td data-label="Estado"><StateMark estado={c.estado} /></td>
                    <td data-label="Último acceso" className="hl-mono">{c.acceso}</td>
                    <td className="hl-m">
                      {nota && <Note refuse={nota.rechazo} r={i}>{nota.texto}</Note>}
                      {on && <Slip c={c} saved={saved && c.id === "mo"} />}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}

// ── Administración · Roles ───────────────────────────────────────────────────────────────────────────────────
function Roles() {
  const m = useMockup();
  const loading = m.state === "cargando";
  const empty = m.state === "vacio";
  const roles = empty ? ROLES.filter((r) => r.sistema) : ROLES;
  const [sel, setSel] = React.useState(m.state === "error" ? "ventas" : empty ? "plan2" : "montaje");
  const rol = roles.find((r) => r.id === sel) ?? roles[0];
  const [perms, setPerms] = React.useState<string[]>(m.state === "error" ? [] : rol.permisos);
  React.useEffect(() => { if (m.state !== "error") setPerms(rol.permisos); }, [rol.id]);
  const n = cuentasDe(rol.id).length;
  const sinPermisos = m.state === "error";
  return (
    <div className="hl-sheet">
      <aside className="hl-lead" aria-label="Índice de roles">
        <div className="hl-headwrap"><h1 className="hl-head hl-serif">Roles</h1></div>
        <p className="hl-deck hl-serif"><Roll value={5} /> roles del sistema y <Roll value={roles.length - 5} /> {roles.length - 5 === 1 ? "creado" : "creados"} aquí, para <Roll value={CUENTAS.length} /> cuentas.</p>
        <div><Btn><Plus size={16} aria-hidden="true" />Crear rol</Btn></div>
        <div className="hl-rule" aria-hidden="true" />
        {loading ? <div className="hl-skel" aria-hidden="true">{[0, 1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-9 w-full" />)}</div> : (
          <ul className="hl-rindex" aria-label="Roles">
            {roles.map((r) => (
              <li key={r.id}>
                <button type="button" aria-pressed={r.id === rol.id} onClick={() => setSel(r.id)}>
                  <span>{r.nombre}</span><span className="hl-mono">{cuentasDe(r.id).length} {cuentasDe(r.id).length === 1 ? "cuenta" : "cuentas"}</span>
                  <small>{r.sistema ? "Rol del sistema · " : ""}{r.resumen}</small>
                </button>
              </li>
            ))}
            {empty && <li><p className="hl-help" style={{ padding: "14px 12px" }}>Aún no hay roles creados aquí. Crea uno cuando un grupo necesite una combinación de permisos distinta a los planes.</p></li>}
          </ul>
        )}
      </aside>
      <section aria-label={`Rol ${rol.nombre}`}>
        {loading ? <div className="hl-skel" aria-busy="true"><Skeleton className="h-10 w-72" /><Skeleton className="h-40 w-full" /><Skeleton className="h-40 w-full" /></div> : (
          <div className="hl-split">
            <div>
              {rol.sistema ? (
                <h2 className="hl-sec hl-serif" style={{ marginTop: 0 }}>{rol.nombre}</h2>
              ) : (
                <div className="hl-form" style={{ maxWidth: 520 }}>
                  <Field id="rol-nombre" label="Nombre del rol" defaultValue={rol.nombre} />
                </div>
              )}
              <p className="hl-help" style={{ margin: "10px 0 18px" }} id="perm-help">
                {rol.sistema ? "Permisos de este rol del sistema, de solo lectura." : "Marca lo que este rol puede usar, agrupado por herramienta."}
              </p>
              {sinPermisos && <div className="hl-alert" role="alert" id="perm-err"><strong>Elige al menos un permiso.</strong><span>Un rol sin permisos no deja entrar a ninguna herramienta, así que no se puede guardar.</span></div>}
              <div className="hl-perms">
                {GRUPOS.map((g, gi) => (
                  <fieldset key={g.herramienta} style={{ ["--r" as string]: gi }} aria-describedby={sinPermisos ? "perm-err" : "perm-help"}>
                    <legend>{g.herramienta}</legend>
                    {g.permisos.map((p) => rol.sistema ? (
                      <div key={p.id} className={`hl-ro${rol.permisos.includes(p.id) ? "" : " off"}`}>
                        <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">{rol.permisos.includes(p.id)
                          ? <path d="M2 8.5l4 4 8-9" fill="none" stroke="currentColor" strokeWidth="2" />
                          : <path d="M3 8h10" stroke="currentColor" strokeWidth="1.5" />}</svg>
                        <span>{p.label}<span className="hl-sr">{rol.permisos.includes(p.id) ? " (incluido)" : " (no incluido)"}</span></span>
                      </div>
                    ) : (
                      <label key={p.id} className="hl-check">
                        <Checkbox checked={perms.includes(p.id)} onCheckedChange={(v) => setPerms((cur) => v ? [...cur, p.id] : cur.filter((x) => x !== p.id))} aria-invalid={sinPermisos || undefined} />
                        <span>{p.label}</span>
                      </label>
                    ))}
                  </fieldset>
                ))}
              </div>
              {!rol.sistema && (
                <div className="hl-actions">
                  <Btn>Guardar rol</Btn>
                  <Btn kind="line" onClick={() => m.set("scene", n > 0 ? "rol-borrar" : "")}>Borrar rol…</Btn>
                </div>
              )}
            </div>
            <aside className="hl-margin" aria-label="Notas">
              {m.state === "exito" && !rol.sistema && <span className="hl-status" role="status">Rol guardado. Aplica a {n} {n === 1 ? "cuenta" : "cuentas"} en su próxima acción.</span>}
              {rol.sistema ? <Note r={0}>Rol del sistema: se consulta, no se edita ni se borra.</Note>
                : <Note r={0}>Los cambios aplican a cada cuenta en su próxima acción.</Note>}
              {n > 0 ? <Note refuse={!rol.sistema} r={1}>{n} {n === 1 ? "cuenta usa" : "cuentas usan"} este rol{!rol.sistema ? ": no se puede borrar mientras tenga cuentas." : "."}</Note>
                : <Note r={1}>Ninguna cuenta usa este rol: se puede borrar.</Note>}
              {sinPermisos && <Note refuse r={2}>Código ROL_SIN_PERMISOS.</Note>}
            </aside>
          </div>
        )}
      </section>
    </div>
  );
}

// ── Mi cuenta ────────────────────────────────────────────────────────────────────────────────────────────────
function MiCuenta() {
  const m = useMockup();
  const busy = m.state === "cargando";
  return (
    <div className="hl-sheet">
      <aside className="hl-lead">
        <div className="hl-headwrap"><h1 className="hl-head hl-serif">Mi <em>cuenta</em></h1></div>
        <p className="hl-deck hl-serif">{ADMIN.nombre}, {rolNombre(ADMIN.rol)}. Entraste {ADMIN.acceso}.</p>
      </aside>
      <section aria-label="Datos y contraseña" className="hl-split">
        <div>
          <dl className="hl-facts">
            <dt>Nombre</dt><dd>{ADMIN.nombre}</dd>
            <dt>Correo</dt><dd className="hl-mono" style={{ fontSize: 13 }}>{ADMIN.correo}</dd>
            <dt>Empresa</dt><dd>{ADMIN.empresa}</dd>
            <dt>Rol</dt><dd>{rolNombre(ADMIN.rol)}</dd>
            <dt>Aviso de datos</dt><dd>Versión 1, aceptada el 3 oct 2026</dd>
          </dl>
          <h2 className="hl-sec hl-serif">Cambiar contraseña</h2>
          <form className="hl-form" onSubmit={(e) => e.preventDefault()}>
            {m.state === "exito" && <div className="hl-ok" role="status"><strong>Contraseña cambiada.</strong><span>Cerramos tus otras sesiones; esta sigue abierta.</span></div>}
            <Field id="pw-actual" type="password" label="Contraseña actual" defaultValue="globos-lila-26" readOnly={busy}
              error={m.state === "error" ? "La contraseña actual no es correcta." : undefined} />
            <Field id="pw-nueva" type="password" label="Contraseña nueva" defaultValue="arco-orgánico-9" help="Mínimo 8 caracteres." readOnly={busy} />
            <Field id="pw-repite" type="password" label="Repite la contraseña nueva" defaultValue="arco-orgánico-9" readOnly={busy} />
            <div><Btn type="submit" disabled={busy}>{busy && <Loader2 className="animate-spin" aria-hidden="true" />}{busy ? "Cambiando…" : "Cambiar contraseña"}</Btn></div>
          </form>
        </div>
        <aside className="hl-margin" aria-label="Notas">
          <Note r={0}>Nombre, correo y rol los cambia un administrador.</Note>
          <Note r={1}>Al cambiar la contraseña se cierran tus otras sesiones; esta sigue abierta.</Note>
        </aside>
      </section>
    </div>
  );
}

// ── public sheets: sign-in, activation, reset; and the notice gate ───────────────────────────────────────────
function Nameplate({ lang, setLang, showLang }: { lang: "es" | "en"; setLang: (l: "es" | "en") => void; showLang?: boolean }) {
  return (
    <header>
      <div className="hl-plate-wrap">
        <RegMark style={{ right: 40, top: 22 }} />
        <p className="hl-plate hl-serif" aria-label="Pictures">Pictures</p>
      </div>
      <div className="hl-rule double" aria-hidden="true" />
      <div className="hl-pubdate">
        <span>Planeación de decoraciones con globos · Sempertex · piloto 2026</span>
        <Strip />
        {showLang && (
          <div className="hl-field">
            <label htmlFor="hl-lang">Idioma del aviso</label>
            <select id="hl-lang" className="hl-select" value={lang} onChange={(e) => setLang(e.target.value as "es" | "en")}>
              <option value="es">Español</option><option value="en">English</option>
            </select>
          </div>
        )}
      </div>
      <div className="hl-stick" aria-hidden="true" />
    </header>
  );
}
function Notice({ lang, version = 1 }: { lang: "es" | "en"; version?: number }) {
  const a = AVISO[lang];
  return (
    <article className="hl-article" lang={lang} aria-labelledby="aviso-t">
      <h2 id="aviso-t">{a.titulo}</h2>
      <span className="hl-meta">{lang === "es" ? `Versión ${version} · ${a.idioma}, el idioma de tu navegador` : `Version ${version} · ${a.idioma}, your browser language`}</span>
      <p style={{ margin: 0 }}>{a.parts.map((t, i) => i % 2 ? <span key={i} className="hl-ph" title="Pendiente de revisión legal">{t}</span> : <React.Fragment key={i}>{t}</React.Fragment>)}</p>
      <span className="hl-meta" style={{ marginTop: 16 }}>{lang === "es" ? "Los campos entre corchetes están pendientes de la revisión legal de Sempertex." : "Bracketed fields are pending Sempertex legal review."}</span>
    </article>
  );
}
const LINK_INVALID = (
  <div className="hl-alert" role="alert">
    <strong>Este enlace ya no sirve.</strong>
    <span>Pide a la persona que administra tu acceso un enlace nuevo; cada enlace sirve una sola vez y vence.</span>
  </div>
);

function Login() {
  const m = useMockup();
  const [lang, setLang] = React.useState<"es" | "en">("es");
  const busy = m.state === "cargando";
  const err = m.state === "error";
  return (
    <>
      <Nameplate lang={lang} setLang={setLang} />
      <main className="hl-cols">
        <form className="f" onSubmit={(e) => e.preventDefault()} aria-labelledby="login-t">
          <h1 id="login-t" className="hl-title hl-serif">Entrar</h1>
          <p className="hl-lede">Con el correo al que te llegó la invitación.</p>
          {err && <div className="hl-alert" role="alert"><strong>No pudimos iniciar sesión con ese correo y esa contraseña.</strong><span>Revisa los dos datos. Después de varios intentos fallidos hay que esperar quince minutos para volver a intentarlo.</span></div>}
          {m.state === "exito" && <div className="hl-ok" role="status"><strong>Sesión iniciada.</strong><span>Abriendo «Administración · Cuentas», la página que pediste.</span></div>}
          <Field id="login-correo" type="email" label="Correo" defaultValue="lucia.ramirez@sempertex.com" autoComplete="email" readOnly={busy} error={err ? " " : undefined} aria-describedby={err ? undefined : undefined} />
          <Field id="login-pw" type="password" label="Contraseña" defaultValue="globos-lila-26" autoComplete="current-password" readOnly={busy} />
        </form>
        <div className="c">
          <div><Btn type="submit" disabled={busy} style={{ width: "100%" }}>{busy && <Loader2 className="animate-spin" aria-hidden="true" />}{busy ? "Entrando…" : "Entrar"}</Btn></div>
          <p className="hl-foot">¿Olvidaste la contraseña? Pide a tu administrador un enlace para restablecerla.</p>
        </div>
        <section className="a" aria-labelledby="como-t">
          <h2 id="como-t" className="hl-sec hl-serif" style={{ marginTop: 0 }}>Cómo funciona el acceso</h2>
          <div className="hl-columns">
            <p><strong>Solo por invitación.</strong> Una persona que administra Pictures crea tu cuenta y te comparte un enlace para activarla. No hay registro abierto.</p>
            <p><strong>Lo que ves depende de tu rol.</strong> Al entrar vuelves a la página que pediste, o a la primera herramienta que tu rol permite; si no tiene ninguna, a Mi cuenta.</p>
            <p><strong>Si fallas varias veces.</strong> El mismo aviso aparece sin importar la causa, y tras varios intentos fallidos hay que esperar quince minutos.</p>
            <p><strong>Tus datos.</strong> Al activar la cuenta aceptas el aviso de tratamiento de datos; lo puedes revisar en Mi cuenta.</p>
          </div>
        </section>
      </main>
    </>
  );
}

function Activar() {
  const m = useMockup();
  const [lang, setLang] = React.useState<"es" | "en">("es");
  const [ok, setOk] = React.useState(m.state === "cargando" || m.state === "exito");
  const busy = m.state === "cargando";
  if (m.state === "enlace-invalido") return (<><Nameplate lang={lang} setLang={setLang} /><main className="hl-cols"><div className="f"><h1 className="hl-title hl-serif">Activa tu cuenta</h1>{LINK_INVALID}</div></main></>);
  return (
    <>
      <Nameplate lang={lang} setLang={setLang} showLang />
      <main className="hl-cols">
        <form className="f" id="act-form" onSubmit={(e) => e.preventDefault()} aria-labelledby="act-t">
          <h1 id="act-t" className="hl-title hl-serif">Activa tu <em>cuenta</em></h1>
          <dl className="hl-invited">
            <dt>Invitación para</dt><dd>Mariana Ortiz</dd>
            <dt>Correo</dt><dd className="hl-mono" style={{ fontSize: 13 }}>mariana@eventosaurora.co</dd>
          </dl>
          {m.state === "exito" && <div className="hl-ok" role="status"><strong>Cuenta activada.</strong><span>Abriendo el Chat asistido, la primera herramienta de tu rol.</span></div>}
          <Field id="act-pw" type="password" label="Elige una contraseña" defaultValue="globo-dorado" help="Mínimo 8 caracteres." readOnly={busy}
            error={m.state === "error" ? undefined : undefined} />
          <Field id="act-pw2" type="password" label="Repítela" defaultValue={m.state === "error" ? "globo-dorad" : "globo-dorado"} readOnly={busy}
            error={m.state === "error" ? "Las dos contraseñas no coinciden." : undefined} />
        </form>
        <section className="a" aria-label="Aviso de datos"><Notice lang={lang} /></section>
        <div className="c">
          <label className="hl-accept">
            <Checkbox checked={ok} onCheckedChange={(v) => setOk(!!v)} aria-describedby="act-need" />
            <span>{lang === "es" ? "Leí el aviso de tratamiento de datos (versión 1) y lo acepto." : "I have read the personal data notice (version 1) and accept it."}</span>
          </label>
          <div><Btn type="submit" form="act-form" disabled={!ok || busy} style={{ width: "100%" }}>{busy && <Loader2 className="animate-spin" aria-hidden="true" />}{busy ? "Activando…" : "Activar cuenta"}</Btn></div>
          <p className="hl-foot" id="act-need">{ok ? "Al activar entras de una vez." : "Para activar la cuenta tienes que aceptar el aviso."}</p>
        </div>
      </main>
    </>
  );
}

function Restablecer() {
  const m = useMockup();
  const [lang, setLang] = React.useState<"es" | "en">("es");
  const busy = m.state === "cargando";
  if (m.state === "enlace-invalido") return (<><Nameplate lang={lang} setLang={setLang} /><main className="hl-cols"><div className="f"><h1 className="hl-title hl-serif">Nueva contraseña</h1>{LINK_INVALID}</div></main></>);
  return (
    <>
      <Nameplate lang={lang} setLang={setLang} />
      <main className="hl-cols">
        <form className="f" id="rst-form" onSubmit={(e) => e.preventDefault()} aria-labelledby="rst-t">
          <h1 id="rst-t" className="hl-title hl-serif">Nueva contraseña</h1>
          <p className="hl-lede">Para Andrés Mejía · <span className="hl-mono">andres@globosandes.co</span></p>
          {m.state === "exito" ? <div className="hl-ok" role="status"><strong>Contraseña guardada.</strong><span>Ya puedes entrar con ella.</span></div> : <>
            <Field id="rst-pw" type="password" label="Contraseña nueva" defaultValue={m.state === "error" ? "globo" : "guirnalda-2026"} readOnly={busy}
              error={m.state === "error" ? "Usa al menos 8 caracteres." : undefined} help="Mínimo 8 caracteres." />
            <Field id="rst-pw2" type="password" label="Repítela" defaultValue={m.state === "error" ? "globo" : "guirnalda-2026"} readOnly={busy} />
          </>}
        </form>
        <div className="c">
          {m.state === "exito" ? <div><Btn onClick={() => m.set("view", "login")}>Ir a iniciar sesión</Btn></div>
            : <div><Btn type="submit" form="rst-form" disabled={busy} style={{ width: "100%" }}>{busy && <Loader2 className="animate-spin" aria-hidden="true" />}{busy ? "Guardando…" : "Guardar contraseña"}</Btn></div>}
        </div>
        <section className="a" aria-label="Sobre este enlace">
          <div className="hl-columns" style={{ columns: 1, maxWidth: "52ch" }}>
            <p><strong>Un enlace, una vez.</strong> Te lo generó una persona que administra Pictures. Sirve una sola vez y vence 24 horas después de creado.</p>
            <p><strong>Si pidieron otro enlace,</strong> este deja de servir: usa siempre el más reciente.</p>
          </div>
        </section>
      </main>
    </>
  );
}

function AvisoNuevo() {
  const m = useMockup();
  const [lang, setLang] = React.useState<"es" | "en">("es");
  const [ok, setOk] = React.useState(m.state === "cargando" || m.state === "exito");
  const busy = m.state === "cargando";
  return (
    <>
      <Dateline gate />
      <main className="hl-cols">
        <div className="f">
          <h1 className="hl-title hl-serif">El aviso de datos <em>cambió</em></h1>
          <p className="hl-lede">Aceptaste la versión 1 el 3 oct 2026. Para seguir usando Pictures, lee y acepta la versión 2.</p>
          <div className="hl-field" style={{ maxWidth: 220 }}>
            <label htmlFor="hl-lang">Idioma del aviso</label>
            <select id="hl-lang" className="hl-select" value={lang} onChange={(e) => setLang(e.target.value as "es" | "en")}><option value="es">Español</option><option value="en">English</option></select>
          </div>
        </div>
        <section className="a" aria-label="Aviso de datos"><Notice lang={lang} version={2} /></section>
        <div className="c">
          {m.state === "error" && <div className="hl-alert" role="alert"><strong>No se pudo guardar tu aceptación.</strong><span>Vuelve a intentarlo; hasta entonces las demás páginas siguen cerradas.</span></div>}
          {m.state === "exito" && <div className="hl-ok" role="status"><strong>Aceptaste la versión 2 el 27 oct 2026.</strong><span>Volviendo a la página que abriste.</span></div>}
          <label className="hl-accept">
            <Checkbox checked={ok} onCheckedChange={(v) => setOk(!!v)} />
            <span>Leí la versión 2 del aviso y la acepto.</span>
          </label>
          <div className="hl-actions" style={{ marginTop: 0 }}>
            <Btn disabled={!ok || busy}>{busy && <Loader2 className="animate-spin" aria-hidden="true" />}{busy ? "Guardando…" : "Aceptar y continuar"}</Btn>
            <Btn kind="line" onClick={() => m.set("view", "login")}>Cerrar sesión</Btn>
          </div>
        </div>
      </main>
    </>
  );
}

// ── dialogs ──────────────────────────────────────────────────────────────────────────────────────────────────
function CopyLink({ url }: { url: string }) {
  const [done, setDone] = React.useState(false);
  return (
    <div className="hl-field">
      <label htmlFor="link">Enlace (se muestra una sola vez)</label>
      <div className="hl-link">
        <Input id="link" readOnly value={url} onFocus={(e) => e.currentTarget.select()} />
        <Btn kind={done ? "line" : "primary"} onClick={() => setDone(true)} aria-live="polite">
          {done ? <span className="hl-stamp"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="M2 8.5l4 4 8-9" fill="none" stroke="currentColor" strokeWidth="2" /></svg>Copiado</span>
            : <><Copy size={16} aria-hidden="true" />Copiar enlace</>}
        </Btn>
      </div>
    </div>
  );
}
function Dlg({ id, title, desc, children, wide }: { id: string; title: string; desc?: React.ReactNode; children?: React.ReactNode; wide?: boolean }) {
  const m = useMockup();
  return (
    <Dialog open={m.scene === id} onOpenChange={(o) => { if (!o) m.set("scene", ""); }}>
      <DialogContent showCloseButton={false} className={`hl-dlg rounded-[2px] bg-card p-7 ring-1 ring-foreground ${wide ? "sm:max-w-[560px]" : "sm:max-w-[500px]"}`}>
        <div className="hl-dlg-in">
          <div className="hl-rule double" aria-hidden="true" />
          <DialogTitle className="hl-dlg-title">{title}</DialogTitle>
          {desc && <DialogDescription className="hl-dlg-desc">{desc}</DialogDescription>}
          {children}
        </div>
      </DialogContent>
    </Dialog>
  );
}
function Confirm({ id, title, desc, children, action }: { id: string; title: string; desc: React.ReactNode; children?: React.ReactNode; action?: React.ReactNode }) {
  const m = useMockup();
  return (
    <AlertDialog open={m.scene === id} onOpenChange={(o) => { if (!o) m.set("scene", ""); }}>
      <AlertDialogContent className="hl-dlg rounded-[2px] bg-card p-7 ring-1 ring-foreground data-[size=default]:max-w-[calc(100%-2rem)] data-[size=default]:sm:max-w-[500px]">
        <div className="hl-dlg-in">
          <div className="hl-rule double" aria-hidden="true" />
          <AlertDialogTitle className="hl-dlg-title">{title}</AlertDialogTitle>
          <AlertDialogDescription className="hl-dlg-desc">{desc}</AlertDialogDescription>
          {children}
          <div className="hl-dlg-foot">
            <AlertDialogCancel className="hl-btn line">{action ? "Cancelar" : "Entendido"}</AlertDialogCancel>
            {action}
          </div>
        </div>
      </AlertDialogContent>
    </AlertDialog>
  );
}
function InviteForm({ duplicate }: { duplicate?: boolean }) {
  const m = useMockup();
  return (
    <form className="hl-form" style={{ maxWidth: "none" }} onSubmit={(e) => { e.preventDefault(); m.set("scene", "invitar-enlace"); }}>
      <Field id="inv-nombre" label="Nombre" defaultValue={duplicate ? "Valentina Rojas" : "Esteban Ruiz"} />
      <Field id="inv-correo" type="email" label="Correo" defaultValue={duplicate ? "valen@celebrarte.co" : "esteban@globosfiesta.co"}
        error={duplicate ? "Este correo ya tiene una cuenta (Valentina Rojas, invitada). Para enviarle otro enlace, búscala en Cuentas y usa «Generar enlace de invitación nuevo»." : undefined} />
      <div className="hl-row2">
        <Field id="inv-empresa" label="Empresa (opcional)" defaultValue={duplicate ? "Celebrarte" : "Globos Fiesta"} />
        <div className="hl-field"><label htmlFor="inv-rol">Rol</label>
          <select id="inv-rol" className="hl-select" defaultValue="plan2">
            <optgroup label="Usuarios externos">{ROLES.slice(0, 3).map((r) => <option key={r.id} value={r.id}>{r.nombre}</option>)}</optgroup>
            <optgroup label="Personal">{ROLES.slice(3, 5).map((r) => <option key={r.id} value={r.id}>{r.nombre}</option>)}</optgroup>
            <optgroup label="Creados aquí">{ROLES.slice(5).map((r) => <option key={r.id} value={r.id}>{r.nombre}</option>)}</optgroup>
          </select></div>
      </div>
      <div className="hl-dlg-foot">
        <Btn kind="line" type="button" onClick={() => m.set("scene", "")}>Cancelar</Btn>
        <Btn type="submit">Crear invitación</Btn>
      </div>
    </form>
  );
}
function Dialogs() {
  const m = useMockup();
  const close = () => m.set("scene", "");
  return (
    <>
      <Dlg id="invitar" title="Invitar persona" desc="Crea la cuenta y un enlace de un solo uso para que la persona elija su contraseña." wide><InviteForm /></Dlg>
      <Dlg id="invitar-duplicado" title="Invitar persona" desc="Crea la cuenta y un enlace de un solo uso para que la persona elija su contraseña." wide><InviteForm duplicate /></Dlg>
      <Dlg id="invitar-enlace" title="Invitación creada" wide
        desc={<>Esteban Ruiz · Usuario · Plan 2. Compártele este enlace: sirve una vez y vence el 3 nov 2026. Si generas otro, este deja de servir.</>}>
        <CopyLink url="https://demo-decoracion.vercel.app/activar/inv_7QkR2mVd9xLp4sTa" />
        <p className="hl-help">Después de cerrar no lo volverás a ver; si se pierde, genera uno nuevo desde la cuenta.</p>
        <div className="hl-dlg-foot"><Btn onClick={close}>Listo</Btn></div>
      </Dlg>
      <Dlg id="restablecer-enlace" title="Enlace para restablecer" wide
        desc={<>Para Mariana Ortiz. Sirve una vez y vence en 24 horas. Los enlaces de restablecimiento anteriores de esta cuenta ya no sirven.</>}>
        <CopyLink url="https://demo-decoracion.vercel.app/restablecer/rst_Hc83PzWq1bNe6uYo" />
        <p className="hl-help">Después de cerrar no lo volverás a ver.</p>
        <div className="hl-dlg-foot"><Btn onClick={close}>Listo</Btn></div>
      </Dlg>
      <Confirm id="desactivar" title="¿Desactivar a Mariana Ortiz?"
        desc="No podrá entrar y su sesión abierta termina en su próxima acción. Su trabajo y sus datos se conservan; puedes reactivarla cuando quieras."
        action={<Btn kind="danger" onClick={close}>Desactivar cuenta</Btn>} />
      <Confirm id="borrar" title="Borrar la cuenta de Mariana Ortiz"
        desc="No tiene proyectos ni decoraciones guardados. Se borran su nombre, correo y empresa; su gasto de IA se conserva como «Cuenta eliminada». No se puede deshacer."
        action={<Btn kind="danger" disabled>Borrar cuenta</Btn>}>
        <Field id="borrar-correo" label="Escribe mariana@eventosaurora.co para confirmar" defaultValue="mariana@eventos" help="El botón se activa cuando el correo coincide." />
      </Confirm>
      <Confirm id="borrar-rechazado" title="Camila Restrepo no se puede borrar"
        desc="Tiene 7 proyectos y 2 decoraciones guardados. Una cuenta con trabajo guardado solo se desactiva, para no perder ese trabajo."
        action={<Btn kind="danger" onClick={() => m.set("scene", "desactivar")}>Desactivar en su lugar</Btn>} />
      <Confirm id="rol-borrar" title="«Montaje externo» no se puede borrar"
        desc="Daniela Cruz tiene este rol. Cámbiale el rol en Cuentas y vuelve a intentarlo." />
    </>
  );
}

// ── shell ────────────────────────────────────────────────────────────────────────────────────────────────────
function App() {
  const m = useMockup();
  const signedIn = ["cuentas", "roles", "mi-cuenta"].includes(m.view);
  return (
    <div className="hl" data-view={m.view}>
      <style>{FONTS + CSS}</style>
      {signedIn && <Dateline />}
      {m.view === "cuentas" && <main><Cuentas /></main>}
      {m.view === "roles" && <main><Roles /></main>}
      {m.view === "mi-cuenta" && <main><MiCuenta /></main>}
      {m.view === "login" && <Login />}
      {m.view === "activar" && <Activar />}
      {m.view === "restablecer" && <Restablecer />}
      {m.view === "aviso" && <AvisoNuevo />}
      <Dialogs />
    </div>
  );
}

mountMockup(App, {
  title: "Cuentas y administración · r9 dir. A «Hoja de llamado»",
  views: [
    { id: "cuentas", label: "Administración · Cuentas" }, { id: "roles", label: "Administración · Roles" }, { id: "mi-cuenta", label: "Mi cuenta" },
    { id: "login", label: "Iniciar sesión" }, { id: "activar", label: "Activar invitación" }, { id: "restablecer", label: "Restablecer contraseña" },
    { id: "aviso", label: "Aviso nuevo (bloqueo)" },
  ],
  states: [
    { id: "normal", label: "Normal" }, { id: "cargando", label: "Cargando / enviando" }, { id: "vacio", label: "Vacío" }, { id: "error", label: "Error" },
    { id: "enlace-invalido", label: "Enlace no válido" }, { id: "exito", label: "Éxito" },
  ],
  scenes: [
    { id: "", label: "Ninguno" }, { id: "menu", label: "Menú de cuenta" }, { id: "invitar", label: "Invitar persona" },
    { id: "invitar-duplicado", label: "Invitar · correo ya registrado" }, { id: "invitar-enlace", label: "Invitación creada · enlace" },
    { id: "restablecer-enlace", label: "Enlace para restablecer" }, { id: "desactivar", label: "Desactivar cuenta" },
    { id: "borrar", label: "Borrar cuenta sin trabajo" }, { id: "borrar-rechazado", label: "Borrar rechazado · con trabajo" },
    { id: "rol-borrar", label: "Borrar rol con cuentas" },
  ],
  motion: "expressive",
});
