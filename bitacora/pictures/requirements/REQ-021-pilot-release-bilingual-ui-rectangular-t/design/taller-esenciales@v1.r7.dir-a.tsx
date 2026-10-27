// taller-esenciales@v1 · r7 · direction A — «Hoja de despiece» (production cut sheet).
// Operational/editorial: the Taller's furniture, Backing and GLB export typeset as one dense working sheet.
// A typographic index is the navigation, the measurements are the headline, a tape-yellow marker is the only accent.
import * as React from "react";
import "@fontsource-variable/bricolage-grotesque/wdth.css";
import "@fontsource-variable/instrument-sans/wdth.css";
import "@fontsource-variable/jetbrains-mono";
import { Undo2, Plus, Minus, Download, ArrowRight, TriangleAlert, Check, RotateCw, ImageDown, Search, CircleHelp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { mountMockup, useMockup } from "@kit/mockup";
import { useMotionProfile } from "@kit/motion";

// ───────────────────────────── tokens, layout and motion grammar ─────────────────────────────
const css = `
:root,[data-theme="light"]{
 --hd-paper:#e9ebec;--hd-sheet:#f7f8f8;--hd-sheet-2:#dde1e4;--hd-ink:#15181b;--hd-soft:#474e55;--hd-hair:#c3c8cc;--hd-edge:#737a81;
 --hd-tape:#f2c12e;--hd-on-tape:#15181b;--hd-tape-edge:#15181b;--hd-warn:#7a4f00;--hd-warn-bg:#fbefc8;--hd-bad:#a8231a;--hd-bad-bg:#f8e1de;--hd-ok:#25633a;
 --background:var(--hd-paper);--foreground:var(--hd-ink);--card:var(--hd-sheet);--card-foreground:var(--hd-ink);--popover:var(--hd-sheet);--popover-foreground:var(--hd-ink);
 --primary:var(--hd-tape);--primary-foreground:var(--hd-on-tape);--secondary:var(--hd-sheet-2);--secondary-foreground:var(--hd-ink);--muted:var(--hd-sheet-2);--muted-foreground:var(--hd-soft);
 --accent:var(--hd-sheet-2);--accent-foreground:var(--hd-ink);--border:var(--hd-hair);--input:var(--hd-edge);--ring:var(--hd-ink);--destructive:var(--hd-bad);--overlay:rgb(21 24 27/.5);
 --radius:2px;color-scheme:light}
.dark,[data-theme="dark"]{
 --hd-paper:#141618;--hd-sheet:#1b1e21;--hd-sheet-2:#262a2e;--hd-ink:#eef0f1;--hd-soft:#adb4ba;--hd-hair:#3a4045;--hd-edge:#7a838b;
 --hd-tape:#f5cc3d;--hd-on-tape:#15181b;--hd-tape-edge:#f5cc3d;--hd-warn:#f3cf75;--hd-warn-bg:#2f2814;--hd-bad:#ff9b8f;--hd-bad-bg:#3a1d1a;--hd-ok:#8fd3a2;
 --background:var(--hd-paper);--foreground:var(--hd-ink);--card:var(--hd-sheet);--card-foreground:var(--hd-ink);--popover:var(--hd-sheet);--popover-foreground:var(--hd-ink);
 --primary:var(--hd-tape);--primary-foreground:var(--hd-on-tape);--secondary:var(--hd-sheet-2);--secondary-foreground:var(--hd-ink);--muted:var(--hd-sheet-2);--muted-foreground:var(--hd-soft);
 --accent:var(--hd-sheet-2);--accent-foreground:var(--hd-ink);--border:var(--hd-hair);--input:var(--hd-edge);--ring:var(--hd-ink);--destructive:var(--hd-bad);--overlay:rgb(0 0 0/.62);
 color-scheme:dark}
/* motion grammar: precise registration, expo-out travel, stepped plotting, no overshoot; profile scales time */
:root{--hd-k:1;--hd-cut:cubic-bezier(.16,1,.3,1);--hd-sweep:cubic-bezier(.65,0,.35,1)}
[data-motion="natural"]{--hd-k:.62}[data-motion="subtle"]{--hd-k:.36}
body{background:var(--hd-paper)}
.hd{--disp:"Bricolage Grotesque Variable",system-ui,sans-serif;--text:"Instrument Sans Variable",system-ui,sans-serif;--mono:"JetBrains Mono Variable",ui-monospace,monospace;
 min-height:calc(100svh - var(--mockup-bar-h,0px));background:var(--hd-paper);color:var(--hd-ink);font:400 14px/1.45 var(--text);font-stretch:100%}
.hd *{box-sizing:border-box}
.hd-wrap{max-width:1440px;margin:0 auto;padding:20px 24px 40px}
.hd :focus-visible{outline:2px solid var(--hd-ink);outline-offset:2px;box-shadow:0 0 0 5px var(--hd-tape);transition:outline-offset calc(140ms*var(--hd-k)) var(--hd-cut)}
.hd .mono{font-family:var(--mono);font-variant-numeric:tabular-nums;font-size:12.5px}
.hd .soft{color:var(--hd-soft)}
/* masthead */
.hd-mast{display:grid;grid-template-columns:auto 1fr auto;align-items:center;gap:8px 20px;padding-bottom:10px;position:relative}
.hd-brand{display:flex;align-items:baseline;gap:10px;font:700 15px/1 var(--text)}
.hd-brand b{font:800 22px/1 var(--disp);font-stretch:75%;letter-spacing:-.01em}
.hd-scene{font-size:13px;color:var(--hd-soft);min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hd-scene strong{color:var(--hd-ink);font-weight:600}
.hd-tools{display:flex;align-items:center;gap:10px}
.hd-lang{display:flex;align-items:center;gap:6px;font-size:13px;color:var(--hd-soft)}
.hd select{font:500 13px/1 var(--text);color:var(--hd-ink);background:var(--hd-sheet);border:1px solid var(--hd-edge);border-radius:2px;padding:7px 28px 7px 9px;min-height:34px}
.hd-rule{height:2px;background:var(--hd-ink);transform-origin:0 50%;animation:hd-rule calc(640ms*var(--hd-k)) var(--hd-cut) both}
@keyframes hd-rule{from{transform:scaleX(0)}to{transform:scaleX(1)}}
/* buttons (shadcn Button restyled) */
.hd .hd-btn{height:auto;min-height:36px;border-radius:2px;padding:7px 12px;font:600 13.5px/1.2 var(--text);gap:8px;transition:transform calc(90ms*var(--hd-k)) var(--hd-cut),background-color calc(160ms*var(--hd-k)) linear}
.hd .hd-btn:active:not(:disabled){transform:translateY(1px) scale(.985)}
.hd .hd-btn--tape{background:var(--hd-tape);color:var(--hd-on-tape);border:1.5px solid var(--hd-tape-edge)}
.hd .hd-btn--tape:hover:not(:disabled){background:color-mix(in srgb,var(--hd-tape) 82%,#fff)}
.hd .hd-btn--line{background:transparent;color:var(--hd-ink);border:1px solid var(--hd-edge)}
.hd .hd-btn--line:hover:not(:disabled){background:var(--hd-sheet-2)}
.hd .hd-btn--bare{background:transparent;color:var(--hd-ink);border:1px solid transparent;text-decoration:underline;text-underline-offset:3px;padding-inline:4px}
.hd .hd-btn:disabled{opacity:1;color:var(--hd-soft);background:var(--hd-sheet-2);border-color:var(--hd-hair);cursor:not-allowed}
.hd-status{font:500 12.5px/1.2 var(--mono);display:inline-flex;align-items:center;gap:6px;color:var(--hd-soft)}
/* typographic index = navigation */
.hd-indexbar{display:flex;align-items:flex-end;gap:18px;margin:18px 0 22px;overflow-x:auto;overflow-y:hidden;scrollbar-width:none;padding:4px 2px 6px}
.hd-group{display:flex;flex-direction:column;gap:4px;flex:none}
.hd-group > span{font:500 12px/1 var(--text);color:var(--hd-soft);padding-left:2px}
.hd .hd-index{position:relative;display:flex;gap:6px;background:transparent;padding:0;height:auto;border-radius:0;width:auto}
.hd .hd-tab{position:relative;z-index:1;flex:none;height:auto;border:0;border-radius:2px;padding:2px 8px 0;background:transparent;box-shadow:none;
 font:800 46px/1 var(--disp);font-stretch:75%;letter-spacing:-.02em;color:var(--hd-soft);overflow:hidden;transition:color calc(160ms*var(--hd-k)) linear}
.hd .hd-tab:hover{color:var(--hd-ink)}
.hd .hd-tab[data-active],.hd .hd-tab[aria-selected="true"]{color:var(--hd-on-tape);background-color:var(--hd-tape);animation:hd-ink-in calc(420ms*var(--hd-k)) step-end both}
@keyframes hd-ink-in{from{color:var(--hd-soft);background-color:transparent}to{color:var(--hd-on-tape);background-color:var(--hd-tape)}}
.hd .hd-tab > .hd-word{display:inline-block;animation:hd-rise calc(560ms*var(--hd-k)) var(--hd-cut) both;animation-delay:calc(var(--i,0)*55ms*var(--hd-k))}
@keyframes hd-rise{from{transform:translateY(62%)}to{transform:none}}
.hd-marker{position:absolute;z-index:0;left:0;top:0;height:100%;background:var(--hd-tape);border-radius:2px;pointer-events:none}
.hd-sep{width:1px;align-self:stretch;background:var(--hd-hair);flex:none;margin-top:16px}
/* the sheet: asymmetric three columns */
.hd-sheet{display:grid;grid-template-columns:minmax(340px,410px) minmax(0,1fr) 248px;gap:28px;align-items:start}
.hd-sheet.wide{grid-template-columns:minmax(0,1fr) 248px}
.hd-work{min-width:0}
.hd-h2{font:700 24px/1.15 var(--text);letter-spacing:-.01em;margin:0}
.hd-lede{margin:6px 0 0;color:var(--hd-soft);max-width:46ch}
.hd-headrow{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.hd-sec{margin-top:22px}
.hd-sec > h3{font:600 13px/1.2 var(--text);margin:0 0 4px;padding-bottom:6px;border-bottom:1.5px solid var(--hd-ink);display:flex;justify-content:space-between;gap:12px}
.hd-sec > h3 .mono{font-weight:500;color:var(--hd-soft)}
/* rows with a left tick that registers on hover */
.hd-rows{list-style:none;margin:0;padding:0}
.hd-row{position:relative;display:grid;grid-template-columns:44px minmax(0,1fr) auto;align-items:center;gap:12px;padding:9px 0 9px 2px;border-bottom:1px solid var(--hd-hair);
 animation:hd-reg calc(420ms*var(--hd-k)) var(--hd-cut) both;animation-delay:calc(var(--i,0)*32ms*var(--hd-k) + 80ms*var(--hd-k))}
@keyframes hd-reg{from{transform:translateX(-14px)}to{transform:none}}
.hd-row::before{content:"";position:absolute;left:-14px;top:50%;width:8px;height:2px;background:var(--hd-ink);transform:scaleX(0);transform-origin:0 50%;transition:transform calc(160ms*var(--hd-k)) var(--hd-cut)}
.hd-row:hover::before,.hd-row:focus-within::before{transform:scaleX(1)}
.hd-row .name{font-weight:600}
.hd-row .meta{display:block;font:500 12px/1.35 var(--mono);color:var(--hd-soft);margin-top:2px}
.hd-row .note{display:block;font-size:12.5px;color:var(--hd-soft);margin-top:2px}
.hd-glyph{width:44px;height:30px;color:var(--hd-ink)}
.hd-count{font:500 12px/1 var(--mono);color:var(--hd-soft)}
/* the measurement headline */
.hd-figure{margin:14px 0 4px;display:flex;flex-direction:column;gap:2px}
.hd-was{font:500 12.5px/1.2 var(--mono);color:var(--hd-soft);position:relative;align-self:flex-start;padding:0 2px}
.hd-was s{text-decoration:none;position:relative}
.hd-was s::after{content:"";position:absolute;left:-2px;right:-2px;top:52%;height:1.5px;background:var(--hd-ink);transform-origin:0 50%;animation:hd-strike calc(360ms*var(--hd-k)) var(--hd-sweep) both;animation-delay:calc(260ms*var(--hd-k))}
@keyframes hd-strike{from{transform:scaleX(0)}to{transform:scaleX(1)}}
.hd-num{font:800 clamp(46px,7.4vw,88px)/.9 var(--disp);font-stretch:75%;letter-spacing:-.035em;display:flex;align-items:baseline;flex-wrap:wrap;gap:0 .08em;font-variant-numeric:tabular-nums}
.hd-num .x{font-size:.42em;font-weight:500;color:var(--hd-soft);padding:0 .1em}
.hd-num .u{font:500 15px/1 var(--text);color:var(--hd-soft);margin-left:.4em}
.hd-dbox{display:inline-flex;overflow:hidden;padding-bottom:.04em}
.hd-d{display:inline-block;animation:hd-roll calc(460ms*var(--hd-k)) var(--hd-cut) both;animation-delay:calc(var(--i,0)*38ms*var(--hd-k))}
@keyframes hd-roll{from{transform:translateY(-92%)}to{transform:none}}
/* fields */
.hd-fields{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:16px}
.hd-field{display:flex;flex-direction:column;gap:5px;min-width:0}
.hd-field label,.hd-field .lab{font:600 12.5px/1.2 var(--text)}
.hd-field .hint{font:500 11.5px/1.2 var(--mono);color:var(--hd-soft)}
.hd .hd-input{height:38px;border-radius:2px;border:1px solid var(--hd-edge);background:var(--hd-sheet);color:var(--hd-ink);font:600 15px/1 var(--mono);padding:0 10px;font-variant-numeric:tabular-nums}
.hd .hd-input[aria-invalid="true"]{border-color:var(--hd-bad);border-width:2px}
.hd-stepper{display:flex;align-items:center;gap:8px}
.hd-stepper output{font:800 34px/1 var(--disp);font-stretch:75%;min-width:2ch;text-align:right;font-variant-numeric:tabular-nums}
.hd .hd-ico{width:38px;min-width:38px;height:38px;padding:0;border-radius:2px;border:1px solid var(--hd-edge);background:var(--hd-sheet);color:var(--hd-ink)}
.hd .hd-ico:hover:not(:disabled){background:var(--hd-sheet-2)}
.hd-chairs{display:grid;grid-template-columns:auto minmax(0,1fr) minmax(0,1fr);gap:12px;align-items:end;margin-top:12px}
/* warnings and alerts (state changes) */
.hd-warn{margin-top:16px;padding:12px 14px;background:var(--hd-warn-bg);color:var(--hd-ink);border:1px solid var(--hd-warn);border-top:3px solid var(--hd-warn);position:relative;
 animation:hd-drop calc(380ms*var(--hd-k)) var(--hd-cut) both}
@keyframes hd-drop{from{transform:translateY(-8px);clip-path:inset(0 0 100% 0)}to{transform:none;clip-path:inset(0 0 0 0)}}
.hd-warn h4{margin:0 0 4px;font:700 14px/1.3 var(--text);display:flex;gap:8px;align-items:center;color:var(--hd-warn)}
.hd-warn p{margin:0 0 10px}
.hd-warn .acts{display:flex;flex-wrap:wrap;gap:8px}
.hd .hd-alert{border-radius:2px;border:1px solid var(--hd-bad);border-left:4px solid var(--hd-bad);background:var(--hd-bad-bg);color:var(--hd-ink);padding:12px 14px;animation:hd-drop calc(380ms*var(--hd-k)) var(--hd-cut) both}
.hd .hd-alert [data-slot="alert-title"]{color:var(--hd-bad);font-weight:700}
.hd .hd-alert [data-slot="alert-description"]{color:var(--hd-ink)}
.hd-banner{display:flex;align-items:center;gap:12px;flex-wrap:wrap;justify-content:space-between;margin:12px 0 0;padding:10px 14px;border:1px solid var(--hd-bad);border-left:4px solid var(--hd-bad);background:var(--hd-bad-bg);animation:hd-drop calc(380ms*var(--hd-k)) var(--hd-cut) both}
.hd-banner p{margin:0}
.hd-banner strong{color:var(--hd-bad)}
/* change log */
.hd-log{list-style:none;margin:0;padding:0;font:500 12.5px/1.3 var(--mono)}
.hd-log li{display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-bottom:1px solid var(--hd-hair)}
.hd-log li:last-child{font-weight:700}
.hd-log .t{color:var(--hd-soft)}
/* plan drawing */
.hd-plan{background:var(--hd-sheet);border:1px solid var(--hd-edge);padding:12px 14px 14px;position:relative;min-width:0}
.hd-plan header{display:flex;justify-content:space-between;align-items:baseline;gap:12px;font:600 13px/1.2 var(--text);margin-bottom:6px}
.hd-plan header .mono{font-weight:500;color:var(--hd-soft)}
.hd-plan svg{display:block;width:100%;height:auto}
.hd-plan .cap{font:500 12px/1.3 var(--text);color:var(--hd-soft);margin:6px 0 0}
.hd-svg-ink{stroke:var(--hd-ink);fill:none}
.hd-svg-txt{fill:var(--hd-ink);font:600 15px var(--mono)}
.hd-svg-soft{fill:var(--hd-soft);font:500 14px var(--mono)}
.hd-table-top{fill:var(--hd-tape);stroke:var(--hd-ink);stroke-width:2.5}
.hd-chair{fill:var(--hd-sheet);stroke:var(--hd-ink);stroke-width:2;transform-box:fill-box;transform-origin:50% 50%;animation:hd-plot calc(300ms*var(--hd-k)) var(--hd-cut) both;animation-delay:calc(var(--i,0)*30ms*var(--hd-k) + 160ms*var(--hd-k))}
@keyframes hd-plot{from{transform:scale(.3);opacity:0}to{transform:none;opacity:1}}
.hd-dim{stroke:var(--hd-ink);stroke-width:1.5;stroke-dasharray:900;animation:hd-draw calc(700ms*var(--hd-k)) var(--hd-sweep) both;animation-delay:calc(120ms*var(--hd-k))}
@keyframes hd-draw{from{stroke-dashoffset:900}to{stroke-dashoffset:0}}
.hd-scan{stroke:var(--hd-soft);stroke-width:1;stroke-dasharray:4 6;animation:hd-scan 9s linear infinite}
@keyframes hd-scan{from{transform:translateX(0)}to{transform:translateX(900px)}}
[data-offscreen] .hd-scan,.hd-paused .hd-scan{animation-play-state:paused}
.hd-balloon{stroke:var(--hd-ink);stroke-width:1.2}
/* live margin */
.hd-margin{border-top:1.5px solid var(--hd-ink);padding-top:8px;position:sticky;top:calc(var(--mockup-bar-h,0px) + 12px)}
.hd-margin h3{font:600 13px/1.2 var(--text);margin:0 0 4px;display:flex;justify-content:space-between}
.hd-mrow{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;padding:7px 0;border-bottom:1px solid var(--hd-hair);font-size:13px}
.hd-mrow b{font:700 15px/1.2 var(--mono);font-variant-numeric:tabular-nums}
.hd-mrow .meta{display:block;font:500 11.5px/1.3 var(--mono);color:var(--hd-soft)}
.hd-mnote{font-size:12.5px;color:var(--hd-soft);margin:10px 0 0}
.hd-bump{animation:hd-bump calc(320ms*var(--hd-k)) var(--hd-cut) both}
@keyframes hd-bump{from{transform:translateY(-6px)}to{transform:none}}
/* shopping list table */
.hd-table{width:100%;border-collapse:collapse;font-size:13.5px}
.hd-table caption{text-align:left;font:600 13px/1.2 var(--text);padding:16px 0 6px;border-bottom:1.5px solid var(--hd-ink)}
.hd-table th{font:600 12px/1.2 var(--text);color:var(--hd-soft);text-align:left;padding:8px 8px 6px 0;border-bottom:1px solid var(--hd-hair)}
.hd-table td{padding:9px 8px 9px 0;border-bottom:1px solid var(--hd-hair);vertical-align:baseline}
.hd-table td.dim{font:500 12.5px/1.3 var(--mono);color:var(--hd-ink)}
.hd-table .q{text-align:right;font:700 15px/1 var(--mono);font-variant-numeric:tabular-nums;padding-right:0}
.hd-table th.q{font:600 12px/1.2 var(--text)}
.hd-table tbody tr{animation:hd-reg calc(420ms*var(--hd-k)) var(--hd-cut) both;animation-delay:calc(var(--i,0)*30ms*var(--hd-k))}
.hd-swatch{display:inline-block;width:12px;height:12px;border-radius:50%;border:1px solid var(--hd-ink);margin-right:8px;vertical-align:-1px}
/* export plotter */
.hd-plotbar{display:grid;grid-template-columns:repeat(12,1fr);gap:3px;margin:12px 0 6px;height:12px}
.hd-plotbar i{background:var(--hd-sheet-2);border:1px solid var(--hd-edge)}
.hd-plotbar i.on{background:var(--hd-ink);animation:hd-cell calc(120ms*var(--hd-k)) steps(2,end) both;animation-delay:calc(var(--i,0)*70ms*var(--hd-k))}
@keyframes hd-cell{from{opacity:.2}to{opacity:1}}
.hd-steps{list-style:none;margin:8px 0 0;padding:0;font:500 12.5px/1.3 var(--mono)}
.hd-steps li{display:flex;gap:8px;align-items:center;padding:5px 0}
.hd-steps li.done{color:var(--hd-ink)}.hd-steps li.now{font-weight:700}.hd-steps li.next{color:var(--hd-soft)}
.hd-file{display:inline-flex;align-items:center;gap:10px;margin-top:12px;padding:10px 14px;border:1.5px solid var(--hd-ink);background:var(--hd-sheet);font:600 13px/1.2 var(--mono);
 animation:hd-stamp calc(420ms*var(--hd-k)) var(--hd-cut) both}
@keyframes hd-stamp{from{transform:scale(1.06) rotate(-1.2deg)}to{transform:none}}
.hd-manifest{list-style:none;margin:0;padding:0}
.hd-manifest li{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:10px;padding:7px 0;border-bottom:1px solid var(--hd-hair);font-size:13.5px}
.hd-manifest .mono{color:var(--hd-ink)}
.hd-empty{padding:16px 0 4px}
.hd-empty p{margin:6px 0 12px;color:var(--hd-soft);max-width:44ch}
.hd-search{position:relative;margin-top:14px}
.hd-search svg{position:absolute;left:10px;top:50%;transform:translateY(-50%);color:var(--hd-soft);pointer-events:none}
.hd-search .hd-input{padding-left:34px;font:500 14px/1 var(--text);width:100%}
.hd-groups{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:10px;font-size:12.5px;color:var(--hd-soft)}
.hd-skel{display:grid;gap:10px;margin-top:16px}
.hd .hd-skel [data-slot="skeleton"]{background:var(--hd-sheet-2);border-radius:2px}
/* dialog */
.hd-dialog{border-radius:2px!important;border:1.5px solid var(--hd-ink)!important;background:var(--hd-sheet)!important;color:var(--hd-ink)!important;padding:20px 22px!important;max-width:min(520px,calc(100vw - 32px))!important}
.hd-dialog ol{margin:8px 0 0;padding-left:20px;display:grid;gap:8px;font-size:14px}
.hd-dialog .mono{font-size:12.5px}
/* reflow: tablet and phone */
@media (max-width:1099px){
 .hd-sheet{grid-template-columns:minmax(320px,380px) minmax(0,1fr)}
 .hd-sheet.wide{grid-template-columns:minmax(0,1fr)}
 .hd-margin{grid-column:2;position:static}
 .hd-sheet.wide .hd-margin{grid-column:auto}
 .hd .hd-tab{font-size:38px}
}
@media (max-width:767px){
 .hd-wrap{padding:16px 20px 32px}
 .hd-mast{grid-template-columns:1fr auto}
 .hd-scene{grid-column:1/-1;grid-row:2;white-space:normal}
 .hd-sheet,.hd-sheet.wide{grid-template-columns:minmax(0,1fr);gap:22px}
 .hd-plan{order:-1}
 .hd-margin{grid-column:auto}
 .hd .hd-tab{font-size:28px;padding:2px 6px 0}
 .hd-indexbar{gap:12px;margin:14px -20px 16px;padding:4px 20px 6px}
 .hd-fields{grid-template-columns:repeat(2,minmax(0,1fr))}
 .hd-chairs{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}
 .hd-chairs .hd-field:first-child{grid-column:1/-1}
 .hd-lang span{display:none}
 .hd-table .hide-sm{display:none}
}
/* reduced motion / Quieto: final state, immediate feedback */
[data-reduced-motion] .hd *,[data-reduced-motion] .hd *::before,[data-reduced-motion] .hd *::after{animation:none!important;transition:none!important}
@media (prefers-reduced-motion:reduce){.hd *,.hd *::before,.hd *::after{animation:none!important;transition:none!important}}
`;
if (typeof document !== "undefined" && !document.getElementById("hd-style")) {
  const s = document.createElement("style");
  s.id = "hd-style";
  s.textContent = css;
  document.head.append(s);
}

// ───────────────────────────── copy (ES / EN) and mock data ─────────────────────────────
type Lang = "es" | "en";
let LANG: Lang = "es";          // survives the mockup's remount on view/state changes
let PREV_TAB = "";              // where the tape marker slides from
const LangCtx = React.createContext<{ lang: Lang; setLang: (l: Lang) => void }>({ lang: "es", setLang: () => {} });
function useT() {
  const { lang } = React.useContext(LangCtx);
  return (es: string, en: string) => (lang === "en" ? en : es);
}
const cmToM = (cm: number, lang: Lang) => (cm / 100).toFixed(2).replace(".", lang === "es" ? "," : ".");

type TableType = { id: string; es: string; en: string; w: number; d: number; h: number; chairs: number; shape: "round" | "square" | "rect" | "oval" | "cocktail" | "half" | "serp" | "u" };
const TABLE_TYPES: TableType[] = [
  { id: "redonda", es: "Mesa redonda", en: "Round table", w: 150, d: 150, h: 75, chairs: 8, shape: "round" },
  { id: "cuadrada", es: "Mesa cuadrada", en: "Square table", w: 90, d: 90, h: 75, chairs: 4, shape: "square" },
  { id: "rectangular", es: "Mesa rectangular", en: "Rectangular table", w: 240, d: 90, h: 75, chairs: 8, shape: "rect" },
  { id: "ovalada", es: "Mesa ovalada", en: "Oval table", w: 240, d: 120, h: 75, chairs: 10, shape: "oval" },
  { id: "coctel", es: "Mesa cóctel", en: "Cocktail table", w: 60, d: 60, h: 110, chairs: 0, shape: "cocktail" },
  { id: "media_luna", es: "Mesa media luna", en: "Half-moon table", w: 180, d: 90, h: 75, chairs: 4, shape: "half" },
  { id: "serpentina", es: "Mesa serpentina", en: "Serpentine table", w: 240, d: 60, h: 75, chairs: 4, shape: "serp" },
  { id: "u", es: "Banquete en U", en: "U-shaped banquet", w: 600, d: 500, h: 75, chairs: 24, shape: "u" },
];

type Prop = { id: string; es: string; en: string; size: string; from: "fondos" | "decorado"; descEs: string; descEn: string };
const BACKING: Prop[] = [
  { id: "panel_redondo", es: "Panel redondo", en: "Round panel", size: "Ø 150 cm", from: "fondos", descEs: "Panel circular con aro dorado", descEn: "Circular panel with a gold rim" },
  { id: "media_luna", es: "Media luna", en: "Half moon", size: "180 cm", from: "fondos", descEs: "Panel azul marino, va detrás del redondo", descEn: "Navy panel, sits behind the round one" },
  { id: "arcos_chiara", es: "Arcos chiara", en: "Chiara arches", size: "3 arcos", from: "fondos", descEs: "Tres arcos de medio punto escalonados", descEn: "Three stepped round arches" },
  { id: "pedestales", es: "Pedestales", en: "Pedestals", size: "3 alturas", from: "decorado", descEs: "Tres cilindros para la torta y los dulces", descEn: "Three cylinders for cake and sweets" },
  { id: "aro_metalico", es: "Aro metálico", en: "Metal hoop", size: "150 × 34 × 175 cm", from: "decorado", descEs: "Aro dorado con pie", descEn: "Gold hoop on a stand" },
  { id: "aro_hexagonal", es: "Marco hexagonal metálico", en: "Hexagonal metal frame", size: "140 × 34 × 175 cm", from: "decorado", descEs: "Marco dorado con pie", descEn: "Gold frame on a stand" },
  { id: "arco_metalico", es: "Arco metálico", en: "Metal arch", size: "120 × 34 × 230 cm", from: "decorado", descEs: "Arco de medio punto con patines", descEn: "Round arch on skids" },
];
const IN_SCENE = new Set(["panel_redondo", "pedestales", "arco_metalico"]);
const BALLOONS = [
  { es: "R12 Rosa pastel", en: "R12 Pastel pink", hex: "#f2b6c6", n: 96 },
  { es: "R12 Dorado cromo", en: "R12 Chrome gold", hex: "#c9a14a", n: 48 },
  { es: "R5 Blanco", en: "R5 White", hex: "#f6f4ef", n: 42 },
];
const CHAIR_TYPES = [
  { id: "tiffany", es: "Silla Tiffany", en: "Tiffany chair", size: "45 × 45 × 90 cm" },
  { id: "crossback", es: "Silla crossback", en: "Crossback chair", size: "46 × 50 × 92 cm" },
  { id: "ghost", es: "Silla ghost", en: "Ghost chair", size: "47 × 52 × 90 cm" },
];

type Disp = "alrededor" | "dos_lados" | "cabeceras";
const capacityOf = (L: number, D: number, disp: Disp) => {
  const side = Math.floor(L / 60);
  return disp === "alrededor" ? 2 * side + (D >= 60 ? 2 : 0) : disp === "dos_lados" ? 2 * side : 2;
};
type Table = { L: number; D: number; H: number; want: number; chair: string; disp: Disp };
type Change = { es: string; en: string; before: Table };

// ───────────────────────────── small drawings (one stroke weight) ─────────────────────────────
function Glyph({ shape }: { shape: string }) {
  const p = { className: "hd-svg-ink", strokeWidth: 1.6 } as const;
  const shapes: Record<string, React.ReactNode> = {
    round: <circle cx="22" cy="15" r="10" {...p} />, square: <rect x="14" y="7" width="16" height="16" {...p} />,
    rect: <rect x="4" y="9" width="36" height="12" {...p} />, oval: <rect x="5" y="8" width="34" height="14" rx="7" {...p} />,
    cocktail: <><circle cx="22" cy="15" r="6" {...p} /><circle cx="22" cy="15" r="1.5" {...p} /></>,
    half: <path d="M8 21 A14 14 0 0 1 36 21 Z" {...p} />, serp: <path d="M6 22 Q22 2 38 22 L32 22 Q22 10 12 22 Z" {...p} />,
    u: <path d="M6 6 V24 H38 V6 H32 V18 H12 V6 Z" {...p} />,
    panel_redondo: <circle cx="22" cy="15" r="11" {...p} />, media_luna: <path d="M9 24 A13 13 0 0 1 35 24" {...p} />,
    arcos_chiara: <><path d="M6 26 V14 A5 5 0 0 1 16 14 V26" {...p} /><path d="M17 26 V10 A5 5 0 0 1 27 10 V26" {...p} /><path d="M28 26 V16 A5 5 0 0 1 38 16 V26" {...p} /></>,
    pedestales: <><rect x="8" y="12" width="8" height="14" {...p} /><rect x="18" y="6" width="8" height="20" {...p} /><rect x="28" y="16" width="8" height="10" {...p} /></>,
    aro_metalico: <><circle cx="22" cy="13" r="9" {...p} /><path d="M22 22 V27 M16 27 H28" {...p} /></>,
    aro_hexagonal: <><path d="M17 5 H27 L32 13 L27 21 H17 L12 13 Z" {...p} /><path d="M22 21 V27 M16 27 H28" {...p} /></>,
    arco_metalico: <path d="M12 27 V14 A10 10 0 0 1 32 14 V27" {...p} />,
  };
  return <svg className="hd-glyph" viewBox="0 0 44 30" aria-hidden>{shapes[shape]}</svg>;
}

/** Top view (planta) and front view (alzado) of the scene; the selected table is the only tape-yellow shape. */
function Drawing({ table, empty, loading }: { table: Table | null; empty?: boolean; loading?: boolean }) {
  const t = useT();
  const { lang } = React.useContext(LangCtx);
  const ref = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) el.removeAttribute("data-offscreen"); else el.setAttribute("data-offscreen", ""); });
    io.observe(el);
    const vis = () => el.classList.toggle("hd-paused", document.hidden);
    document.addEventListener("visibilitychange", vis);
    return () => { io.disconnect(); document.removeEventListener("visibilitychange", vis); };
  }, []);
  if (loading) {
    return <section className="hd-plan" aria-label={t("Plano de la escena", "Scene drawing")} aria-busy="true">
      <header><span>{t("Planta · vista superior", "Plan · top view")}</span></header>
      <div className="hd-skel"><Skeleton className="h-[230px] w-full" /><Skeleton className="h-[90px] w-full" /></div>
    </section>;
  }
  const cx = 450, cy = 330;
  const chairs: { x: number; y: number }[] = [];
  if (table) {
    const placed = Math.min(table.want, capacityOf(table.L, table.D, table.disp));
    // long sides fill first, then the heads (the same order capacityOf counts)
    const sideCount = table.disp === "cabeceras" ? 0 : Math.min(placed, 2 * Math.floor(table.L / 60));
    const top = Math.ceil(sideCount / 2), bottom = Math.floor(sideCount / 2);
    for (let i = 0; i < top; i++) chairs.push({ x: cx - table.L / 2 + (table.L / top) * (i + 0.5), y: cy - table.D / 2 - 32 });
    for (let i = 0; i < bottom; i++) chairs.push({ x: cx - table.L / 2 + (table.L / bottom) * (i + 0.5), y: cy + table.D / 2 + 32 });
    const rest = placed - sideCount;
    if (rest > 0) chairs.push({ x: cx - table.L / 2 - 32, y: cy });
    if (rest > 1) chairs.push({ x: cx + table.L / 2 + 32, y: cy });
  }
  const arch = Array.from({ length: 15 }, (_, i) => {
    const a = Math.PI - (Math.PI * i) / 14;
    return { x: 230 + Math.cos(a) * 66, y: 128 - Math.sin(a) * 66, c: BALLOONS[i % 3].hex };
  });
  return (
    <section ref={ref} className="hd-plan" aria-label={t("Plano de la escena", "Scene drawing")}>
      <header><span>{t("Planta · vista superior", "Plan · top view")}</span><span className="mono">{t("salón 9,00 × 6,00 m", "room 9.00 × 6.00 m")}</span></header>
      <svg viewBox="0 0 900 600" role="img" aria-label={table ? t(`Mesa rectangular de ${table.L} × ${table.D} cm con ${chairs.length} sillas, frente al Backing`, `Rectangular table ${table.L} × ${table.D} cm with ${chairs.length} chairs, facing the Backing`) : t("Salón vacío", "Empty room")}>
        <rect x="6" y="6" width="888" height="588" className="hd-svg-ink" strokeWidth="2" />
        {!empty && <>
          <rect x="350" y="40" width="200" height="10" className="hd-svg-ink" strokeWidth="2" />
          <text x="450" y="76" textAnchor="middle" className="hd-svg-soft">{t("panel redondo", "round panel")}</text>
          <rect x="166" y="40" width="128" height="12" className="hd-svg-ink" strokeWidth="2" />
          <text x="230" y="76" textAnchor="middle" className="hd-svg-soft">{t("arco metálico", "metal arch")}</text>
          {[0, 1, 2].map((i) => <circle key={i} cx={640 + i * 48} cy="52" r={14 + i * 3} className="hd-svg-ink" strokeWidth="2" />)}
          <text x="688" y="96" textAnchor="middle" className="hd-svg-soft">{t("pedestales", "pedestals")}</text>
        </>}
        {table && <>
          <line className="hd-dim" x1={cx - table.L / 2} y1={cy + table.D / 2 + 84} x2={cx + table.L / 2} y2={cy + table.D / 2 + 84} />
          <line className="hd-dim" x1={cx - table.L / 2} y1={cy + table.D / 2 + 74} x2={cx - table.L / 2} y2={cy + table.D / 2 + 94} />
          <line className="hd-dim" x1={cx + table.L / 2} y1={cy + table.D / 2 + 74} x2={cx + table.L / 2} y2={cy + table.D / 2 + 94} />
          <text x={cx} y={cy + table.D / 2 + 112} textAnchor="middle" className="hd-svg-txt">{cmToM(table.L, lang)} m</text>
          <line className="hd-dim" x1={cx + table.L / 2 + 84} y1={cy - table.D / 2} x2={cx + table.L / 2 + 84} y2={cy + table.D / 2} />
          <text x={cx + table.L / 2 + 96} y={cy + 5} className="hd-svg-txt">{cmToM(table.D, lang)} m</text>
          <rect className="hd-table-top" x={cx - table.L / 2} y={cy - table.D / 2} width={table.L} height={table.D} />
          {chairs.map((c, i) => <rect key={i} className="hd-chair" style={{ ["--i" as string]: i }} x={c.x - 20} y={c.y - 20} width="40" height="40" rx="3" />)}
        </>}
        {empty && <text x="450" y="300" textAnchor="middle" className="hd-svg-soft">{t("Salón vacío: añade una mesa o una pieza de Backing", "Empty room: add a table or a Backing piece")}</text>}
        <line className="hd-scan" x1="0" y1="8" x2="0" y2="592" />
        <path d="M30 560 H130 M30 552 V568 M130 552 V568" className="hd-svg-ink" strokeWidth="1.5" />
        <text x="140" y="565" className="hd-svg-soft">1 m</text>
      </svg>
      {!empty && <>
        <header style={{ marginTop: 10 }}><span>{t("Alzado · frente", "Elevation · front")}</span><span className="mono">{t("colores base", "base colours")}</span></header>
        <svg viewBox="0 0 900 260" role="img" aria-label={t("Alzado: arco con guirnalda, panel redondo, mesa y pedestales", "Elevation: arch with garland, round panel, table and pedestals")}>
          <line x1="10" y1="250" x2="890" y2="250" className="hd-svg-ink" strokeWidth="2" />
          <path d="M170 250 V130 A60 60 0 0 1 290 130 V250" className="hd-svg-ink" strokeWidth="2.5" />
          {arch.map((b, i) => <circle key={i} className="hd-balloon hd-chair" style={{ ["--i" as string]: i, fill: b.c }} cx={b.x} cy={b.y} r="11" />)}
          <circle cx="450" cy="175" r="75" className="hd-svg-ink" strokeWidth="2.5" />
          {table && <rect x={450 - table.L / 2} y={250 - table.H} width={table.L} height={table.H} className="hd-table-top" />}
          {[0, 1, 2].map((i) => <rect key={i} x={640 + i * 48} y={250 - [90, 70, 50][i]} width="40" height={[90, 70, 50][i]} className="hd-svg-ink" strokeWidth="2" />)}
        </svg>
      </>}
      <p className="cap">{t("El GLB lleva estas posiciones y medidas en metros.", "The GLB carries these positions and sizes in metres.")}</p>
    </section>
  );
}

// ───────────────────────────── navigation: the typographic index ─────────────────────────────
const TABS = [
  { id: "mesas", es: "Mesas", en: "Tables", group: 0 },
  { id: "backing", es: "Backing", en: "Backing", group: 0 },
  { id: "lista", es: "Lista de compra", en: "Shopping list", group: 1 },
  { id: "exportar", es: "Exportar", en: "Export", group: 1 },
];
const tabOf = (view: string) => (view === "inspector" ? "mesas" : view);

function Index() {
  const { view, set, reduced } = useMockup();
  const t = useT();
  const active = tabOf(view);
  const listRef = React.useRef<HTMLDivElement>(null);
  const markRef = React.useRef<HTMLSpanElement>(null);
  React.useLayoutEffect(() => {
    const host = listRef.current, mark = markRef.current;
    if (!host || !mark) return;
    const cur = host.querySelector<HTMLElement>(`[data-tab="${active}"]`);
    const prev = PREV_TAB && PREV_TAB !== active ? host.querySelector<HTMLElement>(`[data-tab="${PREV_TAB}"]`) : null;
    PREV_TAB = active;
    if (!cur) return;
    const base = host.getBoundingClientRect();
    const c = cur.getBoundingClientRect();
    mark.style.width = `${c.width}px`;
    mark.style.transform = `translateX(${c.left - base.left}px)`;
    if (reduced) return;
    const k = parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--hd-k")) || 1;
    const from = prev ? prev.getBoundingClientRect() : { left: c.left, width: 0 };
    // the tape marker travels from the previous entry (or swipes in from the left edge of this one on first load)
    mark.animate(
      [{ transform: `translateX(${from.left - base.left}px)`, width: `${from.width}px` }, { transform: `translateX(${c.left - base.left}px)`, width: `${c.width}px` }],
      { duration: 400 * k, easing: "cubic-bezier(.65,0,.35,1)", fill: "both" },
    );
  }, [active, reduced]);
  return (
    <Tabs value={active} onValueChange={(v) => set("view", String(v))}>
      <nav className="hd-indexbar" aria-label={t("Secciones del taller", "Workshop sections")}>
        <TabsList ref={listRef} className="hd-index" aria-label={t("Fondos y muebles, lista y exportación", "Backdrops and furniture, list and export")}>
          <span ref={markRef} className="hd-marker" aria-hidden />
          {TABS.map((tab, i) => (
            <React.Fragment key={tab.id}>
              {i === 2 && <span className="hd-sep" aria-hidden />}
              <TabsTrigger value={tab.id} data-tab={tab.id} className="hd-tab">
                <span className="hd-word" style={{ ["--i" as string]: i }}>{t(tab.es, tab.en)}</span>
              </TabsTrigger>
            </React.Fragment>
          ))}
        </TabsList>
      </nav>
    </Tabs>
  );
}

// ───────────────────────────── shared pieces ─────────────────────────────
function Digits({ value }: { value: number }) {
  return <span className="hd-dbox">{String(value).split("").map((d, i) => <span key={`${i}-${d}`} className="hd-d" style={{ ["--i" as string]: i }}>{d}</span>)}</span>;
}

function Masthead() {
  const { state, set } = useMockup();
  const t = useT();
  const { lang, setLang } = React.useContext(LangCtx);
  const status = state === "exportando" ? t("Preparando GLB…", "Preparing GLB…") : state === "exportado" ? t("GLB descargado · 2,4 MB", "GLB downloaded · 2.4 MB") : state === "error" ? t("El GLB falló", "GLB failed") : "";
  return (
    <>
      <header className="hd-mast">
        <div className="hd-brand"><b>Pictures</b><span>Taller 3D</span></div>
        <p className="hd-scene" style={{ margin: 0 }}><strong>Boda Restrepo-Ortiz</strong> · {t("Salón Cedro, 120 invitados", "Cedro hall, 120 guests")}</p>
        <div className="hd-tools">
          {status && <span className="hd-status" role="status">{state === "exportado" ? <Check size={14} aria-hidden /> : state === "error" ? <TriangleAlert size={14} aria-hidden /> : null}{status}</span>}
          <label className="hd-lang"><span>{t("Idioma", "Language")}</span>
            <select aria-label={t("Idioma", "Language")} value={lang} onChange={(e) => setLang(e.target.value as Lang)}>
              <option value="es">Español</option><option value="en">English</option>
            </select>
          </label>
          <Button className="hd-btn hd-btn--line" onClick={() => set("view", "exportar")} disabled={state === "exportando"}>
            <Download size={16} aria-hidden />{t("Exportar", "Export")}
          </Button>
        </div>
      </header>
      <div className="hd-rule" aria-hidden />
      {state === "error" && (
        <div className="hd-banner" role="alert">
          <p><strong>{t("No se pudo preparar el GLB.", "The GLB could not be prepared.")}</strong> {t("La escena no cambió; puedes reintentarlo.", "The scene did not change; you can try again.")}</p>
          <Button className="hd-btn hd-btn--line" onClick={() => set("state", "exportando")}><RotateCw size={15} aria-hidden />{t("Reintentar", "Try again")}</Button>
        </div>
      )}
    </>
  );
}

function Margin({ table, empty, loading }: { table: Table | null; empty?: boolean; loading?: boolean }) {
  const t = useT();
  const { set } = useMockup();
  if (loading) return <aside className="hd-margin" aria-busy="true" aria-label={t("Lista de compra en vivo", "Live shopping list")}><h3>{t("Lista de compra", "Shopping list")}</h3><div className="hd-skel">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-7 w-full" />)}</div></aside>;
  const placed = table ? Math.min(table.want, capacityOf(table.L, table.D, table.disp)) : 0;
  const chair = CHAIR_TYPES.find((c) => c.id === table?.chair) ?? CHAIR_TYPES[0];
  return (
    <aside className="hd-margin" aria-label={t("Lista de compra en vivo", "Live shopping list")}>
      <h3><span>{t("Lista de compra", "Shopping list")}</span><span className="mono soft">{t("en vivo", "live")}</span></h3>
      {empty ? <p className="hd-mnote">{t("Vacía. Cada mesa, silla y pieza que pongas aparece aquí con su medida.", "Empty. Every table, chair and piece you place appears here with its size.")}</p> : <>
        {table && <div className="hd-mrow hd-bump" key={`t${table.L}${table.D}`}><span>{t("Mesa rectangular", "Rectangular table")}<span className="meta">{table.L} × {table.D} × {table.H} cm</span></span><b>1</b></div>}
        {table && <div className="hd-mrow hd-bump" key={`c${placed}`}><span>{t(chair.es, chair.en)}<span className="meta">{chair.size}</span></span><b>{placed}</b></div>}
        {BACKING.filter((p) => IN_SCENE.has(p.id)).map((p) => <div className="hd-mrow" key={p.id}><span>{t(p.es, p.en)}<span className="meta">{p.size}</span></span><b>1</b></div>)}
        <div className="hd-mrow"><span>{t("Globos", "Balloons")}<span className="meta">{t("3 colores", "3 colours")}</span></span><b>186</b></div>
        <p className="hd-mnote">{t("Cantidades y medidas, sin precios de alquiler.", "Quantities and sizes, without rental prices.")}</p>
        <Button className="hd-btn hd-btn--bare" onClick={() => set("view", "lista")}>{t("Ver la lista completa", "Open the full list")}<ArrowRight size={15} aria-hidden /></Button>
      </>}
    </aside>
  );
}

function WorkSkeleton({ rows = 6 }: { rows?: number }) {
  return <div className="hd-skel" aria-busy="true">{Array.from({ length: rows }, (_, i) => <Skeleton key={i} className="h-11 w-full" />)}</div>;
}

// ───────────────────────────── views ─────────────────────────────
function MesasView() {
  const { state, set } = useMockup();
  const t = useT();
  const loading = state === "cargando";
  return (
    <div className="hd-work">
      <h2 className="hd-h2">{t("Mesas", "Tables")}</h2>
      <p className="hd-lede">{t("Toca un tipo: entra a su medida de partida y se abre su inspector para cambiar medidas y sillas.", "Tap a type: it enters at its starting size and opens its inspector to change sizes and chairs.")}</p>
      {loading ? <WorkSkeleton rows={8} /> : (
        <section className="hd-sec" aria-label={t("Tipos de mesa", "Table types")}>
          <h3><span>{t("Tipos de mesa", "Table types")}</span><span className="mono">{t("medida de partida", "starting size")}</span></h3>
          <ul className="hd-rows">
            {TABLE_TYPES.map((tt, i) => (
              <li key={tt.id} className="hd-row" style={{ ["--i" as string]: i }} data-type={tt.id}>
                <Glyph shape={tt.shape} />
                <span><span className="name">{t(tt.es, tt.en)}</span>
                  <span className="meta">{tt.shape === "round" || tt.shape === "cocktail" ? `Ø ${tt.w}` : `${tt.w} × ${tt.d}`} × {tt.h} cm · {tt.chairs ? t(`${tt.chairs} sillas`, `${tt.chairs} chairs`) : t("sin sillas", "no chairs")}</span></span>
                <Button className="hd-btn hd-btn--line" aria-label={t(`Añadir ${tt.es.toLowerCase()}`, `Add ${tt.en.toLowerCase()}`)} onClick={() => set("view", "inspector")}><Plus size={15} aria-hidden />{t("Añadir", "Add")}</Button>
              </li>
            ))}
          </ul>
          <p className="hd-mnote">{t("Las mesas fijas Imperial siguen en Mobiliario, como antes.", "Fixed Imperial tables stay in Furniture, as before.")}</p>
        </section>
      )}
      {state === "error" && <p className="hd-mnote">{t("El error de exportación no afecta a las mesas: puedes seguir editando.", "The export error does not affect tables: you can keep editing.")}</p>}
    </div>
  );
}

const START_LISTO: Table = { L: 300, D: 100, H: 75, want: 12, chair: "tiffany", disp: "alrededor" };
const START_AVISO: Table = { L: 240, D: 90, H: 75, want: 12, chair: "tiffany", disp: "alrededor" };
const HISTORY_LISTO: Change[] = [
  { es: "Mesa rectangular añadida", en: "Rectangular table added", before: { ...START_LISTO, L: 0 } },
  { es: "Largo 240 → 300 cm", en: "Length 240 → 300 cm", before: { L: 240, D: 90, H: 75, want: 8, chair: "tiffany", disp: "alrededor" } },
  { es: "Ancho 90 → 100 cm", en: "Width 90 → 100 cm", before: { L: 300, D: 90, H: 75, want: 8, chair: "tiffany", disp: "alrededor" } },
  { es: "Sillas 8 → 12", en: "Chairs 8 → 12", before: { L: 300, D: 100, H: 75, want: 8, chair: "tiffany", disp: "alrededor" } },
];
const HISTORY_AVISO: Change[] = [...HISTORY_LISTO, { es: "Largo 300 → 240 cm", en: "Length 300 → 240 cm", before: { ...START_LISTO } }];

function InspectorView({ table, setTable, history, setHistory }: { table: Table | null; setTable: (t: Table | null) => void; history: Change[]; setHistory: (h: Change[]) => void }) {
  const { state, set } = useMockup();
  const t = useT();
  if (state === "cargando") return <div className="hd-work"><h2 className="hd-h2">{t("Mesa rectangular", "Rectangular table")}</h2><WorkSkeleton rows={5} /></div>;
  if (!table) {
    return (
      <div className="hd-work">
        <h2 className="hd-h2">{t("Inspector de mesa", "Table inspector")}</h2>
        <div className="hd-empty">
          <p>{t("No hay ninguna mesa elegida. Añade una desde su tipo: la rectangular entra a 240 × 90 × 75 cm con 8 sillas.", "No table is selected. Add one from its type: the rectangular one enters at 240 × 90 × 75 cm with 8 chairs.")}</p>
          <Button className="hd-btn hd-btn--tape" onClick={() => set("view", "mesas")}><ArrowRight size={15} aria-hidden />{t("Elegir un tipo de mesa", "Choose a table type")}</Button>
        </div>
      </div>
    );
  }
  const cap = capacityOf(table.L, table.D, table.disp);
  const placed = Math.min(table.want, cap);
  const over = table.want - placed;
  const last = history[history.length - 1];
  const prev = last?.before && last.before.L ? last.before : null;
  const change = (patch: Partial<Table>, es: string, en: string) => {
    setHistory([...history, { es, en, before: table }]);
    setTable({ ...table, ...patch });
  };
  const undo = () => {
    if (!history.length) return;
    const h = history[history.length - 1];
    setHistory(history.slice(0, -1));
    setTable(h.before.L ? h.before : null);
  };
  const limits = { L: [100, 600], D: [40, 150], H: [40, 110] } as const;
  const field = (key: "L" | "D" | "H", es: string, en: string) => {
    const [min, max] = limits[key];
    return (
      <div className="hd-field">
        <label htmlFor={`f-${key}`}>{t(es, en)}</label>
        <Input id={`f-${key}`} className="hd-input" type="number" inputMode="numeric" min={min} max={max} step={5} defaultValue={table[key]} key={`${key}${table[key]}`}
          onBlur={(e) => { const v = Math.max(min, Math.min(max, Number(e.currentTarget.value) || table[key])); if (v !== table[key]) change({ [key]: v } as Partial<Table>, `${es} ${table[key]} → ${v} cm`, `${en} ${table[key]} → ${v} cm`); }}
          onKeyDown={(e) => { if (e.key === "Enter") (e.currentTarget as HTMLInputElement).blur(); }} />
        <span className="hint">{min}–{max} cm</span>
      </div>
    );
  };
  return (
    <div className="hd-work">
      <div className="hd-headrow"><h2 className="hd-h2">{t("Mesa rectangular", "Rectangular table")}</h2><span className="mono soft">{t("seleccionada", "selected")}</span></div>
      <div className="hd-figure" aria-live="polite">
        {prev && <span className="hd-was">{t("antes", "was")} <s>{prev.L} × {prev.D} × {prev.H}</s></span>}
        <span className="hd-num" aria-label={`${table.L} × ${table.D} × ${table.H} cm`}>
          <Digits value={table.L} /><span className="x">×</span><Digits value={table.D} /><span className="x">×</span><Digits value={table.H} /><span className="u">cm</span>
        </span>
      </div>
      <div className="hd-fields">
        {field("L", "Largo", "Length")}
        {field("D", "Ancho de la mesa", "Table width")}
        {field("H", "Alto de la tapa", "Top height")}
      </div>
      <div className="hd-chairs">
        <div className="hd-field">
          <span className="lab" id="sillas-lab">{t("Sillas", "Chairs")} <span className="soft">({t(`caben ${cap}`, `${cap} fit`)})</span></span>
          <div className="hd-stepper" role="group" aria-labelledby="sillas-lab">
            <Button className="hd-ico" aria-label={t("Una silla menos", "One chair fewer")} disabled={table.want <= 0} onClick={() => change({ want: table.want - 1 }, `Sillas ${table.want} → ${table.want - 1}`, `Chairs ${table.want} → ${table.want - 1}`)}><Minus size={16} aria-hidden /></Button>
            <output aria-live="polite" key={table.want} className="hd-bump">{table.want}</output>
            <Button className="hd-ico" aria-label={t("Una silla más", "One chair more")} disabled={table.want >= cap} onClick={() => change({ want: table.want + 1 }, `Sillas ${table.want} → ${table.want + 1}`, `Chairs ${table.want} → ${table.want + 1}`)}><Plus size={16} aria-hidden /></Button>
          </div>
        </div>
        <div className="hd-field">
          <label htmlFor="f-silla">{t("Tipo de silla", "Chair type")}</label>
          <select id="f-silla" value={table.chair} onChange={(e) => change({ chair: e.target.value }, `Silla → ${e.target.value}`, `Chair → ${e.target.value}`)}>
            {CHAIR_TYPES.map((c) => <option key={c.id} value={c.id}>{t(c.es, c.en)}</option>)}
          </select>
        </div>
        <div className="hd-field">
          <label htmlFor="f-disp">{t("Disposición", "Layout")}</label>
          <select id="f-disp" value={table.disp} onChange={(e) => change({ disp: e.target.value as Disp }, `Disposición → ${e.target.value}`, `Layout → ${e.target.value}`)}>
            <option value="alrededor">{t("Alrededor", "All around")}</option>
            <option value="dos_lados">{t("Dos lados (los largos)", "Two long sides")}</option>
            <option value="cabeceras">{t("Solo cabeceras", "Heads only")}</option>
          </select>
        </div>
      </div>
      {over > 0 && (
        <div className="hd-warn" role="status">
          <h4><TriangleAlert size={16} aria-hidden />{t(`${over} sillas no caben`, `${over} chairs do not fit`)}</h4>
          <p>{t(`Pediste ${table.want}; alrededor de ${table.L} × ${table.D} cm caben ${cap}. Se colocan ${placed} y la lista cuenta ${placed}.`, `You asked for ${table.want}; ${cap} fit around ${table.L} × ${table.D} cm. ${placed} are placed and the list counts ${placed}.`)}</p>
          <div className="acts">
            <Button className="hd-btn hd-btn--tape" onClick={() => change({ want: cap }, `Sillas ${table.want} → ${cap}`, `Chairs ${table.want} → ${cap}`)}>{t(`Dejar ${cap} sillas`, `Keep ${cap} chairs`)}</Button>
            <Button className="hd-btn hd-btn--line" onClick={() => change({ L: 300, D: Math.max(table.D, 100) }, `Largo ${table.L} → 300 cm`, `Length ${table.L} → 300 cm`)}>{t("Alargar a 300 cm", "Lengthen to 300 cm")}</Button>
          </div>
        </div>
      )}
      <section className="hd-sec" aria-label={t("Cambios de esta mesa", "Changes to this table")}>
        <h3><span>{t("Cambios", "Changes")}</span><span className="mono">{history.length}</span></h3>
        <ol className="hd-log">
          {history.slice(-4).map((h, i) => <li key={`${history.length}-${i}`}><span>{t(h.es, h.en)}</span><span className="t">{["12:04", "12:05", "12:05", "12:06", "12:07"][i] ?? "12:08"}</span></li>)}
        </ol>
        <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap" }}>
          <Button className="hd-btn hd-btn--line" onClick={undo} disabled={!history.length}><Undo2 size={15} aria-hidden />{t("Deshacer", "Undo")}{last ? <span className="soft">· {t(last.es, last.en)}</span> : null}</Button>
        </div>
      </section>
    </div>
  );
}

function BackingView() {
  const { state } = useMockup();
  const t = useT();
  const [q, setQ] = React.useState(state === "vacio" ? "columpio" : "");
  const [added, setAdded] = React.useState<Record<string, number>>({ panel_redondo: 1, pedestales: 1, arco_metalico: 1 });
  const norm = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const shown = BACKING.filter((p) => !q || norm(`${p.es} ${p.en} ${p.descEs}`).includes(norm(q)));
  return (
    <div className="hd-work">
      <div className="hd-headrow"><h2 className="hd-h2">Backing</h2><span className="mono soft">{t("7 piezas", "7 pieces")}</span></div>
      <p className="hd-lede">{t("Fondos y estructuras para montar globos detrás de la mesa. Cada pieza vive solo aquí; las de siempre se encuentran por su nombre de siempre.", "Backdrops and frames to build balloons behind the table. Each piece lives only here; old names still find them.")}</p>
      <div className="hd-search">
        <Search size={16} aria-hidden />
        <Input className="hd-input" aria-label={t("Buscar en Fondos y muebles", "Search backdrops and furniture")} placeholder={t("Buscar: aro, pedestal, media luna…", "Search: hoop, pedestal, half moon…")} value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {state === "cargando" ? <WorkSkeleton rows={7} /> : shown.length === 0 ? (
        <div className="hd-empty">
          <p>{t(`Nada en Backing se llama «${q}». Prueba con «aro», «arco», «panel» o «pedestal»; la búsqueda por foto también encuentra estas piezas.`, `Nothing in Backing is called “${q}”. Try “hoop”, “arch”, “panel” or “pedestal”; photo search also finds these pieces.`)}</p>
          <Button className="hd-btn hd-btn--line" onClick={() => setQ("")}>{t("Ver las 7 piezas", "Show all 7 pieces")}</Button>
        </div>
      ) : (
        <section className="hd-sec" aria-label={t("Piezas de Backing", "Backing pieces")}>
          <h3><span>{t("Fondos y muebles › Backing", "Backdrops and furniture › Backing")}</span><span className="mono">{shown.length}/7</span></h3>
          <ul className="hd-rows">
            {shown.map((p, i) => (
              <li key={p.id} className="hd-row" style={{ ["--i" as string]: i }} data-id={p.id}>
                <Glyph shape={p.id} />
                <span><span className="name">{t(p.es, p.en)}</span>
                  <span className="meta">{p.size}{added[p.id] ? ` · ${t("en la escena", "in scene")}: ${added[p.id]}` : ""}</span>
                  <span className="note">{t(p.descEs, p.descEn)} · {p.from === "fondos" ? t("antes en Fondos y tapetes", "formerly in Backdrops and mats") : t("antes en Decorado de pie", "formerly in Standing decor")}</span></span>
                <Button className="hd-btn hd-btn--line" aria-label={t(`Añadir ${p.es}`, `Add ${p.en}`)} onClick={() => setAdded({ ...added, [p.id]: (added[p.id] ?? 0) + 1 })}><Plus size={15} aria-hidden />{t("Añadir", "Add")}</Button>
              </li>
            ))}
          </ul>
          <div className="hd-groups" aria-label={t("Otros grupos", "Other groups")}>
            <span>{t("Fondos y tapetes · 5", "Backdrops and mats · 5")}</span><span>{t("Sillas y asientos · 7", "Chairs and seating · 7")}</span><span>{t("Mesas · 8 tipos", "Tables · 8 types")}</span><span>{t("Decorado de pie · 6", "Standing decor · 6")}</span>
          </div>
        </section>
      )}
    </div>
  );
}

function ListaView({ table }: { table: Table | null }) {
  const { state, set } = useMockup();
  const t = useT();
  if (state === "cargando") return <div className="hd-work"><h2 className="hd-h2">{t("Lista de compra", "Shopping list")}</h2><WorkSkeleton rows={8} /></div>;
  if (!table && state === "vacio") {
    return <div className="hd-work"><h2 className="hd-h2">{t("Lista de compra", "Shopping list")}</h2>
      <div className="hd-empty"><p>{t("La lista está vacía. Añade una mesa o una pieza de Backing y aparecerá aquí con su cantidad y medida.", "The list is empty. Add a table or a Backing piece and it appears here with its quantity and size.")}</p>
        <Button className="hd-btn hd-btn--tape" onClick={() => set("view", "mesas")}><Plus size={15} aria-hidden />{t("Añadir una mesa", "Add a table")}</Button></div></div>;
  }
  const tb = table ?? START_LISTO;
  const placed = Math.min(tb.want, capacityOf(tb.L, tb.D, tb.disp));
  const chair = CHAIR_TYPES.find((c) => c.id === tb.chair) ?? CHAIR_TYPES[0];
  let i = 0;
  return (
    <div className="hd-work">
      <div className="hd-headrow"><h2 className="hd-h2">{t("Lista de compra", "Shopping list")}</h2><span className="mono soft">{t("Boda Restrepo-Ortiz", "Restrepo-Ortiz wedding")}</span></div>
      <p className="hd-lede">{t("Cantidades y medidas de lo que está en la escena. El mobiliario va sin precios de alquiler: pídelo a tu proveedor con estas medidas.", "Quantities and sizes of what is in the scene. Furniture has no rental prices: order it from your supplier with these sizes.")}</p>
      <table className="hd-table">
        <caption>{t("Mobiliario", "Furniture")}</caption>
        <thead><tr><th>{t("Pieza", "Piece")}</th><th>{t("Medidas", "Size")}</th><th className="q">{t("Cantidad", "Qty")}</th></tr></thead>
        <tbody>
          <tr style={{ ["--i" as string]: i++ }}><td>{t("Mesa rectangular", "Rectangular table")}</td><td className="dim">{tb.L} × {tb.D} × {tb.H} cm</td><td className="q">1</td></tr>
          <tr style={{ ["--i" as string]: i++ }}><td>{t(chair.es, chair.en)}{tb.want > placed && <span className="soft"> · {t(`${tb.want - placed} pedidas no caben`, `${tb.want - placed} requested do not fit`)}</span>}</td><td className="dim">{chair.size}</td><td className="q">{placed}</td></tr>
        </tbody>
      </table>
      <table className="hd-table">
        <caption>Backing</caption>
        <thead><tr><th>{t("Pieza", "Piece")}</th><th>{t("Medidas", "Size")}</th><th className="q">{t("Cantidad", "Qty")}</th></tr></thead>
        <tbody>{BACKING.filter((p) => IN_SCENE.has(p.id)).map((p) => <tr key={p.id} style={{ ["--i" as string]: i++ }}><td>{t(p.es, p.en)}</td><td className="dim">{p.size}</td><td className="q">1</td></tr>)}</tbody>
      </table>
      <table className="hd-table">
        <caption>{t("Globos · guirnalda del arco", "Balloons · arch garland")}</caption>
        <thead><tr><th>{t("Color", "Colour")}</th><th className="hide-sm">{t("Uso", "Use")}</th><th className="q">{t("Cantidad", "Qty")}</th></tr></thead>
        <tbody>{BALLOONS.map((b) => <tr key={b.hex} style={{ ["--i" as string]: i++ }}><td><span className="hd-swatch" style={{ background: b.hex }} aria-hidden />{t(b.es, b.en)}</td><td className="hide-sm soft">{t("guirnalda orgánica", "organic garland")}</td><td className="q">{b.n}</td></tr>)}</tbody>
      </table>
      <p className="hd-mnote">{t(`Total: ${1 + placed + 3} piezas de mobiliario y Backing · 186 globos.`, `Total: ${1 + placed + 3} furniture and Backing pieces · 186 balloons.`)}</p>
    </div>
  );
}

function ExportView({ table }: { table: Table | null }) {
  const { state, set } = useMockup();
  const t = useT();
  const { lang } = React.useContext(LangCtx);
  const empty = state === "vacio";
  const tb = table ?? START_LISTO;
  const placed = Math.min(tb.want, capacityOf(tb.L, tb.D, tb.disp));
  if (state === "cargando") return <div className="hd-work"><h2 className="hd-h2">{t("Exportar escena", "Export scene")}</h2><WorkSkeleton rows={6} /></div>;
  const steps = [t("Recorrer la escena", "Walk the scene"), t("Medir en metros", "Measure in metres"), t("Colores base por material", "Base colour per material"), t("Empaquetar GLB", "Pack GLB")];
  const stepNow = 2;
  return (
    <div className="hd-work">
      <h2 className="hd-h2">{t("Exportar escena", "Export scene")}</h2>
      <p className="hd-lede">{t("El modelo GLB se abre en Blender con la misma disposición, medidas en metros y colores base. Exportar no cambia la escena.", "The GLB model opens in Blender with the same layout, sizes in metres and base colours. Exporting does not change the scene.")}</p>
      {empty ? (
        <div className="hd-empty"><p>{t("Nada que exportar: la escena está vacía. Añade una mesa o una pieza de Backing.", "Nothing to export: the scene is empty. Add a table or a Backing piece.")}</p>
          <Button className="hd-btn hd-btn--tape" disabled><Download size={16} aria-hidden />{t("Descargar modelo GLB", "Download GLB model")}</Button></div>
      ) : <>
        <section className="hd-sec" aria-label={t("Contenido del GLB", "GLB contents")}>
          <h3><span>{t("Lo que lleva el archivo", "What the file carries")}</span><span className="mono">{t("metros · Y arriba", "metres · Y up")}</span></h3>
          <ul className="hd-manifest">
            <li><span>{t("Mesa rectangular", "Rectangular table")}</span><span className="mono">{cmToM(tb.L, lang)} × {cmToM(tb.D, lang)} × {cmToM(tb.H, lang)} m</span></li>
            <li><span>{t(`${placed} sillas Tiffany`, `${placed} Tiffany chairs`)}</span><span className="mono">0{lang === "es" ? "," : "."}45 × 0{lang === "es" ? "," : "."}45 × 0{lang === "es" ? "," : "."}90 m</span></li>
            <li><span>{t("Panel redondo · Arco metálico · Pedestales", "Round panel · Metal arch · Pedestals")}</span><span className="mono">3</span></li>
            <li><span>{t("Guirnalda: 186 globos, 3 colores base", "Garland: 186 balloons, 3 base colours")}</span><span className="mono">186</span></li>
          </ul>
          <p className="hd-mnote">{t("No viajan las luces del estudio ni el brillo del metalizado: Blender recibe el color base de cada material.", "Studio lights and foil shine do not travel: Blender receives each material's base colour.")}</p>
        </section>
        {state === "exportando" && (
          <section className="hd-sec" aria-label={t("Preparando el GLB", "Preparing the GLB")} aria-busy="true">
            <h3><span>{t("Preparando GLB…", "Preparing GLB…")}</span><span className="mono">{stepNow + 1}/4</span></h3>
            <div className="hd-plotbar" role="progressbar" aria-valuemin={0} aria-valuemax={12} aria-valuenow={7} aria-label={t("Progreso del GLB", "GLB progress")}>
              {Array.from({ length: 12 }, (_, i) => <i key={i} className={i < 7 ? "on" : ""} style={{ ["--i" as string]: i }} />)}
            </div>
            <ol className="hd-steps">{steps.map((s, i) => <li key={s} className={i < stepNow ? "done" : i === stepNow ? "now" : "next"}>{i < stepNow ? <Check size={14} aria-hidden /> : <span aria-hidden>{i === stepNow ? "▸" : "·"}</span>}{s}</li>)}</ol>
          </section>
        )}
        {state === "exportado" && (
          <section className="hd-sec" aria-label={t("GLB descargado", "GLB downloaded")}>
            <h3><span>{t("Descargado", "Downloaded")}</span><span className="mono">12:09</span></h3>
            <div className="hd-file" role="status"><Check size={16} aria-hidden />boda-restrepo-ortiz.glb · 2,4 MB</div>
            <p className="hd-mnote">{t("Ábrelo en Blender con Archivo › Importar › glTF 2.0. La mesa debe medir 3,00 × 1,00 × 0,75 m.", "Open it in Blender with File › Import › glTF 2.0. The table should measure 3.00 × 1.00 × 0.75 m.")}</p>
          </section>
        )}
        {state === "error" && (
          <Alert className="hd-alert" style={{ marginTop: 18 }}>
            <TriangleAlert aria-hidden />
            <AlertTitle>{t("No se pudo preparar el GLB", "The GLB could not be prepared")}</AlertTitle>
            <AlertDescription>{t("El material «Dorado cromo» de la guirnalda no se pudo leer. La escena no cambió y no se descargó ningún archivo a medias.", "The garland's “Chrome gold” material could not be read. The scene did not change and no partial file was downloaded.")}</AlertDescription>
          </Alert>
        )}
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 18 }}>
          {state === "error"
            ? <Button className="hd-btn hd-btn--tape" onClick={() => set("state", "exportando")}><RotateCw size={16} aria-hidden />{t("Reintentar", "Try again")}</Button>
            : <Button className="hd-btn hd-btn--tape" disabled={state === "exportando"} onClick={() => set("state", "exportando")}><Download size={16} aria-hidden />{state === "exportando" ? t("Preparando GLB…", "Preparing GLB…") : state === "exportado" ? t("Descargar otra vez", "Download again") : t("Descargar modelo GLB", "Download GLB model")}</Button>}
          <Button className="hd-btn hd-btn--line" onClick={() => set("scene", "blender")}><CircleHelp size={16} aria-hidden />{t("Cómo abrirlo en Blender", "How to open it in Blender")}</Button>
          <Button className="hd-btn hd-btn--line"><ImageDown size={16} aria-hidden />{t("Descargar PNG · 3000 px", "Download PNG · 3000 px")}</Button>
        </div>
      </>}
    </div>
  );
}

function BlenderDialog() {
  const { scene, set } = useMockup();
  const t = useT();
  return (
    <Dialog open={scene === "blender"} onOpenChange={(o) => { if (!o) set("scene", ""); }}>
      <DialogContent className="hd-dialog" showCloseButton={false}>
        <DialogTitle style={{ font: "700 20px/1.2 var(--text)" }}>{t("Abrir el GLB en Blender", "Open the GLB in Blender")}</DialogTitle>
        <DialogDescription style={{ color: "var(--hd-soft)" }}>{t("Blender 4.2 LTS o posterior. No hace falta ningún complemento.", "Blender 4.2 LTS or later. No add-on is needed.")}</DialogDescription>
        <ol>
          <li>{t("Archivo › Importar › glTF 2.0 (.glb/.gltf).", "File › Import › glTF 2.0 (.glb/.gltf).")}</li>
          <li>{t("Elige ", "Choose ")}<span className="mono">boda-restrepo-ortiz.glb</span>.</li>
          <li>{t("Las medidas llegan en metros: la mesa mide 3,00 × 1,00 × 0,75 m.", "Sizes arrive in metres: the table measures 3.00 × 1.00 × 0.75 m.")}</li>
          <li>{t("Los colores son los colores base; luces y reflejos no se exportan.", "Colours are base colours; lights and reflections are not exported.")}</li>
        </ol>
        <DialogFooter style={{ marginTop: 12 }}>
          <Button className="hd-btn hd-btn--tape" onClick={() => set("scene", "")}>{t("Entendido", "Got it")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// ───────────────────────────── the screen ─────────────────────────────
function App() {
  const { view, state } = useMockup();
  const [lang, setLangState] = React.useState<Lang>(LANG);
  const setLang = (l: Lang) => { LANG = l; setLangState(l); document.documentElement.lang = l; };
  const empty = state === "vacio";
  const loading = state === "cargando";
  const [table, setTable] = React.useState<Table | null>(empty ? null : state === "aviso" ? START_AVISO : START_LISTO);
  const [history, setHistory] = React.useState<Change[]>(empty ? [] : state === "aviso" ? HISTORY_AVISO : HISTORY_LISTO);
  const wide = view === "lista";
  const work =
    view === "mesas" ? <MesasView /> :
    view === "inspector" ? <InspectorView table={table} setTable={setTable} history={history} setHistory={setHistory} /> :
    view === "backing" ? <BackingView /> :
    view === "lista" ? <ListaView table={table} /> : <ExportView table={table} />;
  return (
    <LangCtx.Provider value={{ lang, setLang }}>
      <div className="hd" lang={lang}>
        <div className="hd-wrap">
          <Masthead />
          <Index />
          <div className={`hd-sheet${wide ? " wide" : ""}`} data-view={view}>
            {work}
            {!wide && <Drawing table={view === "backing" && empty ? null : table} empty={empty && view !== "mesas"} loading={loading} />}
            <Margin table={table} empty={empty} loading={loading} />
          </div>
        </div>
        <BlenderDialog />
      </div>
    </LangCtx.Provider>
  );
}

mountMockup(App, {
  title: "Taller esenciales · A · Hoja de despiece",
  views: [
    { id: "mesas", label: "Mesas · tipos" },
    { id: "inspector", label: "Mesa rectangular · inspector" },
    { id: "backing", label: "Backing" },
    { id: "lista", label: "Lista de compra" },
    { id: "exportar", label: "Exportar GLB" },
  ],
  states: [
    { id: "listo", label: "Con datos" },
    { id: "cargando", label: "Cargando" },
    { id: "vacio", label: "Vacío / sin resultados" },
    { id: "aviso", label: "Aviso de capacidad" },
    { id: "exportando", label: "Preparando GLB" },
    { id: "exportado", label: "GLB descargado" },
    { id: "error", label: "Error de exportación" },
  ],
  scenes: [{ id: "", label: "Ninguno" }, { id: "blender", label: "Abrir en Blender" }],
});
