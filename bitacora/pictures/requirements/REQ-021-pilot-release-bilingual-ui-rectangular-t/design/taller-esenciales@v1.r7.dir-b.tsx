// Mockup · taller-esenciales@v1 · r7 direction B «Cámara de salón».
// Kinetic/spatial: the Taller is a camera over the event venue. A room map (plano de sala) is the navigation; choosing a
// zone dollies the camera across a tilted dance floor with a standing Backing wall, and the working sheet follows with
// an elastic lag. Real shadcn/Base UI controls, Animate UI CountingNumber, Motion springs; mock data from the repo.
import "@fontsource-variable/bricolage-grotesque/standard.css";
import "@fontsource-variable/manrope";
import * as React from "react";
import { motion } from "motion/react";
import { ArrowLeft, Check, CircleAlert, Download, Info, Minus, Plus, RotateCcw, Search, Undo2 } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Empty, EmptyContent, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableFooter, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { CountingNumber } from "@animate-ui/react/primitives/texts/counting-number";
import { mountMockup, useMockup } from "@kit/mockup";
import { useMotionProfile } from "@kit/motion";

const CSS = String.raw`
:root:root{--background:#e4eee8;--foreground:#10261f;--card:#fbfdfb;--card-foreground:#10261f;--popover:#fbfdfb;--popover-foreground:#10261f;
 --primary:#ad3d06;--primary-foreground:#ffffff;--primary-hover:#923204;--primary-soft:#fbe4d6;--secondary:#d3e2da;--secondary-foreground:#10261f;
 --muted:#d3e2da;--muted-foreground:#38554b;--accent:#c9dccf;--accent-foreground:#10261f;--destructive:#b0202d;--destructive-foreground:#fff;
 --border:#a3bdb0;--input:#557367;--ring:#ad3d06;--success:#1d6436;--success-soft:#dcefe1;--warning:#7f4f05;--warning-soft:#f8ead0;
 --info:#1d5a6e;--info-soft:#d8ebef;--overlay:rgb(16 38 31 / .5);--radius:.9rem;
 --floor:#cfe1d6;--floor-line:#b2cbbe;--wall:#f3efe6;--wall-edge:#7d9a8e;--stage:#d9e8df;--ink-soft:#38554b;--mantel:#f7f6f2;--silla:#d6b25a;--silla-edge:#5b4a1c;
 --display:'Bricolage Grotesque Variable',ui-sans-serif,system-ui,sans-serif;--text:'Manrope Variable',ui-sans-serif,system-ui,sans-serif;--k:1}
html.dark:root,:root:root[data-theme="dark"]{--background:#0a1915;--foreground:#e3f1ea;--card:#11241e;--card-foreground:#e3f1ea;--popover:#15302a;--popover-foreground:#e3f1ea;
 --primary:#ff9b5e;--primary-foreground:#1d0b02;--primary-hover:#ffb282;--primary-soft:#3b2416;--secondary:#1a332b;--secondary-foreground:#e3f1ea;
 --muted:#1a332b;--muted-foreground:#a6c4b8;--accent:#20403560;--accent-foreground:#e3f1ea;--destructive:#ff9191;--destructive-foreground:#1d0505;
 --border:#2f5045;--input:#86a99b;--ring:#ff9b5e;--success:#8fd6a3;--success-soft:#173426;--warning:#f2c26b;--warning-soft:#33290f;
 --info:#8fd0e0;--info-soft:#13303a;--overlay:rgb(2 8 6 / .72);
 --floor:#12302a;--floor-line:#1f463b;--wall:#1b3a31;--wall-edge:#5f8577;--stage:#0d231d;--ink-soft:#a6c4b8;--silla-edge:#2a2208}
[data-motion="natural"]{--k:.6}[data-motion="subtle"]{--k:.32}
body{background:var(--background);color:var(--foreground);font-family:var(--text)}
.taller{min-height:calc(100svh - var(--mockup-bar-h,0px));display:flex;flex-direction:column}
.cabecera{display:flex;align-items:center;gap:16px;flex-wrap:wrap;padding:14px 24px;border-bottom:1px solid var(--border)}
.marca{display:flex;align-items:center;gap:10px;font:700 16px/1 var(--text)}
.marca svg{width:22px;height:28px}
.ruta{color:var(--ink-soft);font-size:14px}
.idioma{margin-left:auto;display:inline-flex;border:1px solid var(--input);border-radius:999px;padding:3px;gap:2px}
.idioma button{font:700 13px/1 var(--text);padding:8px 12px;border-radius:999px;color:var(--foreground);background:transparent;transition:background calc(var(--k)*180ms),transform 120ms}
.idioma button[aria-pressed="true"]{background:var(--foreground);color:var(--background)}
.idioma button:active{transform:scale(.94)}
.obra{flex:1;display:grid;grid-template-columns:minmax(0,1fr) 420px;grid-template-areas:"stage ficha";gap:24px;padding:24px}
.escenario{grid-area:stage;position:sticky;top:calc(var(--mockup-bar-h,0px) + 16px);height:calc(100svh - var(--mockup-bar-h,0px) - 110px);min-height:560px;
 border-radius:32px;background:var(--stage);overflow:hidden;border:1px solid var(--border);isolation:isolate}
.camara{position:absolute;inset:0;transform-origin:50% 55%;will-change:transform}
.plano{position:absolute;left:8%;right:8%;top:30%;height:62%;transform:perspective(1500px) rotateX(54deg);transform-style:preserve-3d;transform-origin:50% 100%}
.baldosas{position:absolute;inset:0;display:grid;grid-template-columns:repeat(12,1fr);grid-template-rows:repeat(8,1fr);border-radius:18px;overflow:hidden;background:var(--floor-line);gap:2px;padding:2px}
.baldosa{background:var(--floor);border-radius:3px;animation:ola calc(var(--k)*900ms) cubic-bezier(.2,1.35,.3,1) both;animation-delay:calc(var(--i)*var(--k)*28ms)}
@keyframes ola{from{transform:translateZ(-30px) scale(.82);opacity:.15}}
.pared{position:absolute;left:0;right:0;bottom:100%;height:42%;transform-origin:50% 100%;transform:rotateX(-90deg);background:var(--wall);border:2px solid var(--wall-edge);border-bottom:0;border-radius:16px 16px 0 0}
.pared svg{position:absolute;inset:6% 2% 0;width:96%;height:94%}
.prop{transition:opacity calc(var(--k)*200ms),transform calc(var(--k)*420ms) cubic-bezier(.2,1.35,.3,1);transform-box:fill-box;transform-origin:50% 100%}
.prop[data-dim]{opacity:.35}
.prop[data-hl]{transform:translateY(-4%) scale(1.06)}
.prop[data-nuevo]{animation:cuelga calc(var(--k)*1100ms) cubic-bezier(.2,1.5,.3,1) both}
@keyframes cuelga{0%{transform:translateY(-60%) rotate(-6deg);opacity:0}60%{transform:translateY(4%) rotate(2deg);opacity:1}}
.pieza-piso{position:absolute;transform-style:preserve-3d}
.mesa-tapa{position:absolute;inset:0;background:var(--mantel);border:2px solid #4e5b55;box-shadow:0 0 0 2px var(--floor),6px 10px 0 rgb(16 38 31 / .22)}
.mesa-tapa[data-sel]{border-color:var(--primary);box-shadow:0 0 0 4px var(--primary-soft),6px 10px 0 rgb(16 38 31 / .22)}
.silla{position:absolute;width:3.6%;height:5.4%;margin:-1.8% 0 0 -1.8%;border-radius:30%;background:var(--silla);border:2px solid var(--silla-edge)}
.caja-lista{position:absolute;left:5%;top:84%;width:9%;height:10%;background:#c79a52;border:2px solid #5b4a1c;border-radius:6px;box-shadow:5px 8px 0 rgb(16 38 31 / .25)}
.globos{position:absolute;inset:0;pointer-events:none}
.globo{position:absolute;width:var(--s);height:calc(var(--s)*1.15);border-radius:50% 50% 47% 47%;background:var(--c);
 box-shadow:inset calc(var(--s)*-.16) calc(var(--s)*-.2) 0 rgb(0 0 0 / .14),inset calc(var(--s)*.12) calc(var(--s)*.12) 0 rgb(255 255 255 / .35);
 animation:flota calc(3.6s + var(--d)*1s) ease-in-out infinite alternate;animation-delay:calc(var(--d)*-1.3s)}
.globo::after{content:"";position:absolute;left:50%;top:100%;width:8px;height:7px;margin-left:-4px;background:inherit;clip-path:polygon(50% 0,100% 100%,0 100%)}
.globo::before{content:"";position:absolute;left:50%;top:calc(100% + 6px);width:1.5px;height:calc(var(--s)*1.1);background:var(--wall-edge);transform-origin:top;animation:cuerda 2.8s ease-in-out infinite alternate}
@keyframes flota{to{transform:translate(calc(var(--d)*6px),-14px) rotate(calc(var(--d)*4deg))}}
@keyframes cuerda{from{transform:rotate(-6deg)}to{transform:rotate(6deg)}}
.cotas{position:absolute;inset:0;pointer-events:none}
.cota{position:absolute;font:700 13px/1 var(--text);font-variant-numeric:tabular-nums;background:var(--card);color:var(--foreground);border:1px solid var(--input);padding:7px 10px;border-radius:999px;white-space:nowrap}
.fantasma{position:absolute;width:30px;height:30px;border-radius:9px;border:2px dashed var(--destructive);background:color-mix(in oklab,var(--destructive) 12%,transparent);animation:escapa calc(var(--k)*2.6s) ease-in-out infinite alternate}
@keyframes escapa{from{transform:translateY(0) rotate(-8deg)}to{transform:translateY(-16px) rotate(8deg)}}
.caja-glb{position:absolute;left:7%;right:7%;top:16%;bottom:12%;border:2px dashed var(--foreground);border-radius:20px;animation:encuadre calc(var(--k)*900ms) cubic-bezier(.2,1.35,.3,1) both}
.caja-glb[data-error]{border-color:var(--destructive);animation:ladea calc(var(--k)*700ms) cubic-bezier(.2,1.5,.3,1) both}
@keyframes encuadre{from{transform:scale(1.12);opacity:0}}
@keyframes ladea{0%{transform:rotate(0)}40%{transform:rotate(-2.4deg)}70%{transform:rotate(1.2deg)}100%{transform:rotate(-.6deg)}}
.sello{position:absolute;right:9%;top:19%;display:grid;place-items:center;width:104px;height:104px;border-radius:50%;background:var(--success);color:var(--background);font:800 15px/1.1 var(--display);text-align:center;animation:sella calc(var(--k)*700ms) cubic-bezier(.2,1.6,.3,1) both}
@keyframes sella{from{transform:scale(1.8) rotate(-20deg);opacity:0}}
.plano-sala{grid-area:stage;align-self:end;justify-self:start;margin:0 0 20px 20px;z-index:2;width:300px;background:var(--card);border:1px solid var(--input);border-radius:24px;padding:14px;box-shadow:0 18px 40px -18px rgb(16 38 31 / .45)}
.plano-sala h2{font:700 13px/1.2 var(--text);color:var(--ink-soft);margin:2px 4px 10px}
.sala{position:relative;display:grid;grid-template-columns:1fr 1fr;grid-template-rows:auto 1fr auto;gap:8px;border:2px solid var(--foreground);border-radius:18px;padding:8px;min-height:176px}
.estacion{position:relative;display:flex;align-items:center;justify-content:center;gap:6px;min-height:44px;padding:8px 12px;border-radius:12px;border:1.5px solid var(--input);background:var(--background);
 font:700 14px/1.15 var(--text);color:var(--foreground);transition:transform calc(var(--k)*240ms) cubic-bezier(.2,1.5,.3,1),background 160ms,border-color 160ms}
.estacion:hover{transform:translateY(-3px)}
.estacion:active{transform:translateY(1px) scale(.96)}
.estacion[aria-current="page"]{background:var(--foreground);color:var(--background);border-color:var(--foreground)}
.estacion small{font-weight:600;font-size:12px;opacity:.9}
.est-backing{grid-column:1/3}.est-mesas{grid-column:1/3;min-height:64px}
.viajero{position:absolute;left:0;top:0;width:16px;height:19px;border-radius:50% 50% 46% 46%;background:var(--primary);border:2px solid var(--card);pointer-events:none;z-index:3}
.ficha{grid-area:ficha;align-self:start;background:var(--card);border:1px solid var(--border);border-radius:28px;padding:28px 24px;position:relative}
.ficha::before{content:"";position:absolute;left:32px;top:-9px;width:16px;height:16px;background:var(--primary);clip-path:polygon(50% 0,100% 100%,0 100%);transform:rotate(180deg)}
.titulo{font-family:var(--display);font-size:clamp(32px,3.2vw,46px);line-height:1.02;font-weight:800;font-stretch:100%;letter-spacing:-.025em;margin:0;min-height:2.04em;text-wrap:balance;display:flex;align-items:flex-end}
.titulo span{display:inline-block;animation:infla calc(var(--k)*1000ms) cubic-bezier(.2,1.4,.3,1) both}
@keyframes infla{from{font-stretch:75%;font-weight:300;letter-spacing:.02em}}
.lede{font-size:15px;line-height:1.5;color:var(--ink-soft);margin:10px 0 20px}
.tipos{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
.tipo{position:relative;display:flex;flex-direction:column;align-items:flex-start;gap:6px;text-align:left;padding:14px;border-radius:20px;border:1.5px solid var(--input);background:var(--background);color:var(--foreground);
 transition:transform calc(var(--k)*260ms) cubic-bezier(.2,1.5,.3,1),box-shadow 200ms;cursor:pointer}
.tipo:hover{transform:translateY(-4px) rotate(-.6deg);box-shadow:0 12px 0 -4px var(--border)}
.tipo:active{transform:scale(.96)}
.tipo svg.sil{width:100%;height:58px;color:var(--foreground)}
.tipo strong{font:700 15px/1.2 var(--text)}
.tipo .med{font-size:13px;color:var(--ink-soft);font-variant-numeric:tabular-nums}
.tipo .badge-n{position:absolute;right:10px;top:10px}
.nota{display:flex;gap:10px;align-items:flex-start;font-size:14px;line-height:1.45;color:var(--ink-soft);border-top:1px solid var(--border);margin-top:20px;padding-top:16px}
.nota svg{flex:none;margin-top:2px}
.campos{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.campo label{display:block;font:700 13px/1.2 var(--text);margin-bottom:6px}
.campo .unidad{position:relative}
.campo .unidad span{position:absolute;right:12px;top:50%;transform:translateY(-50%);font-size:13px;color:var(--ink-soft);pointer-events:none}
.campo input{font-variant-numeric:tabular-nums;padding-right:34px;height:44px;font-size:16px;border-color:var(--input)}
.campo .ayuda{font-size:12px;color:var(--ink-soft);margin-top:6px}
.campo .mal{font-size:13px;color:var(--destructive);margin-top:6px;font-weight:600}
.bloque{margin-top:22px}
.bloque h2{font:800 18px/1.2 var(--display);margin:0 0 10px}
.sillas{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.pasos{display:inline-flex;align-items:center;border:1.5px solid var(--input);border-radius:999px;padding:3px}
.pasos button{width:40px;height:40px;border-radius:999px;display:grid;place-items:center;color:var(--foreground);transition:transform 120ms,background 160ms}
.pasos button:hover{background:var(--muted)}.pasos button:active{transform:scale(.88)}
.pasos button:disabled{opacity:.45}
.pasos output{min-width:44px;text-align:center;font:800 22px/1 var(--display);font-variant-numeric:tabular-nums}
.nativo{height:44px;border:1.5px solid var(--input);border-radius:12px;background:var(--card);color:var(--foreground);font:600 15px var(--text);padding:0 12px}
.cupo{display:flex;align-items:center;gap:8px;margin-top:12px;font-size:14px;font-variant-numeric:tabular-nums}
.cupo .punto{width:10px;height:10px;border-radius:50%;background:var(--success)}
.cupo[data-lleno] .punto{background:var(--warning)}
.acciones{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
.deshacer{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-top:22px;padding:12px 14px;border-radius:16px;background:var(--muted);font-size:14px}
.grupos{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 16px;padding:0;list-style:none}
.grupos li{font-size:13px;font-weight:600;padding:6px 10px;border-radius:999px;border:1px solid var(--border);color:var(--ink-soft)}
.grupos li[aria-current="true"]{background:var(--foreground);color:var(--background);border-color:var(--foreground)}
.buscar{position:relative;margin-bottom:16px}
.buscar svg{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--ink-soft)}
.buscar input{padding-left:42px;height:44px;font-size:15px;border-color:var(--input)}
.piezas{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px}
.pieza{display:flex;flex-direction:column;gap:6px;padding:14px;border-radius:20px;border:1.5px solid var(--input);background:var(--background);transition:transform calc(var(--k)*260ms) cubic-bezier(.2,1.5,.3,1)}
.pieza:hover,.pieza:focus-within{transform:translateY(-3px)}
.pieza svg{width:100%;height:70px}
.pieza strong{font:700 15px/1.2 var(--text)}
.pieza .med,.pieza .antes{font-size:12.5px;color:var(--ink-soft)}
.pieza button{margin-top:6px}
.tabla td,.tabla th{padding:12px 8px}
.tabla th{font:600 13px/1.2 var(--text);color:var(--ink-soft)}
.num{text-align:right;font-variant-numeric:tabular-nums}
.archivo{border:1.5px solid var(--input);border-radius:20px;padding:18px;background:var(--background)}
.archivo code{font:700 14px/1.3 var(--text);word-break:break-all}
.archivo ul{margin:12px 0 0;padding:0;list-style:none;display:grid;gap:8px;font-size:14px}
.archivo li{display:flex;gap:8px;align-items:flex-start}
.archivo li svg{flex:none;margin-top:2px}
.progreso{margin-top:18px}
.vacio-izq,.vacio-izq *{text-align:left!important;align-items:flex-start!important;justify-items:start!important}
.vacio-izq{padding:20px!important;border:1.5px dashed var(--input);border-radius:20px}
.ficha [data-slot="button"]{border-radius:999px;font-weight:700;min-height:40px;padding-inline:16px;transition:transform 120ms cubic-bezier(.2,1.5,.3,1),background 160ms,box-shadow 160ms}
.ficha [data-slot="button"]:active{transform:translateY(1px) scale(.95)}
.ficha [data-slot="button"][data-variant="default"],.ficha [data-slot="button"]:not([data-variant]){box-shadow:inset 0 -3px 0 rgb(0 0 0 / .18),inset 0 2px 0 rgb(255 255 255 / .22)}
.ficha [data-slot="button"][data-variant="outline"]{border:1.5px solid var(--input);background:var(--card)}
:focus-visible{outline:3px solid var(--ring)!important;outline-offset:3px;transition:outline-offset 160ms cubic-bezier(.2,1.5,.3,1)}
.escenario[data-pausa] *,html[data-oculto] .escenario *{animation-play-state:paused!important}
html[data-reduced-motion] .taller *,html[data-reduced-motion] .taller *::before,html[data-reduced-motion] .taller *::after{animation:none!important;transition:none!important}
@media (prefers-reduced-motion:reduce){.taller *,.taller *::before,.taller *::after{animation:none!important;transition:none!important}}
@media (max-width:1023px){
 .obra{grid-template-columns:minmax(0,1fr);grid-template-areas:"stage" "mapa" "ficha";padding:20px}
 .escenario{position:relative;top:0;height:400px;min-height:0}
 .plano-sala{grid-area:mapa;align-self:stretch;justify-self:stretch;margin:0;width:auto;box-shadow:none}
 .sala{grid-template-columns:repeat(4,1fr);grid-template-rows:auto auto;min-height:0}
 .est-backing{grid-column:1/3}.est-mesas{grid-column:3/5;min-height:44px}
}
@media (max-width:767px){
 .cabecera{padding:12px 20px}.ruta{flex-basis:100%;order:3}
 .obra{padding:16px 20px 24px;gap:16px}
 .escenario{height:280px;border-radius:24px}
 .sala{grid-template-columns:1fr 1fr}.est-backing,.est-mesas{grid-column:auto}
 .ficha{padding:24px 20px;border-radius:24px}
 .campos{grid-template-columns:1fr 1fr}
 .cota{font-size:12px;padding:6px 8px}
 .sello{width:84px;height:84px;font-size:13px}
}
`;

type Lang = "es" | "en";
type View = "mesas" | "inspector" | "backing" | "lista" | "exportar";
const LangCtx = React.createContext<{ lang: Lang; t: (es: string, en: string) => string }>({ lang: "es", t: (es) => es });
const useT = () => React.useContext(LangCtx);

// Mesa types, defaults and limits as in src/lib/globos3d/mobiliario-conjunto-tipos.ts (PARTIDA_MESA, LIMITES_MESA).
const TYPES = [
  { id: "redonda", es: "Mesa redonda", en: "Round table", w: 150, d: 150, h: 75, lim: [60, 300], dLim: null, fromW: true },
  { id: "cuadrada", es: "Mesa cuadrada", en: "Square table", w: 90, d: 90, h: 75, lim: [60, 250], dLim: null, fromW: true },
  { id: "rectangular", es: "Mesa rectangular", en: "Rectangular table", w: 240, d: 90, h: 75, lim: [100, 600], dLim: [40, 150], fromW: false },
  { id: "ovalada", es: "Mesa ovalada", en: "Oval table", w: 240, d: 120, h: 75, lim: [100, 500], dLim: [60, 250], fromW: false },
  { id: "coctel", es: "Mesa cóctel", en: "Cocktail table", w: 60, d: 60, h: 110, lim: [40, 100], dLim: null, fromW: true },
  { id: "media_luna", es: "Mesa media luna", en: "Half-moon table", w: 180, d: 90, h: 75, lim: [100, 400], dLim: null, fromW: true },
  { id: "serpentina", es: "Mesa serpentina", en: "Serpentine table", w: 240, d: 60, h: 75, lim: [120, 600], dLim: [40, 100], fromW: false },
  { id: "u", es: "Banquete en U", en: "U-shaped banquet", w: 600, d: 500, h: 75, lim: [250, 800], dLim: [200, 800], fromW: false },
] as const;
type TypeId = (typeof TYPES)[number]["id"];

// The seven Backing props with their real names, tints and former visual groups (fondos-escenografia.ts, mobiliario-catalogo.ts).
const PROPS = [
  { id: "panel_redondo", es: "Panel redondo", en: "Round panel", med: "Ø 150 cm", antes: ["Fondos y tapetes", "Backdrops and rugs"] },
  { id: "media_luna", es: "Media luna", en: "Half moon", med: "Ø 180 cm", antes: ["Fondos y tapetes", "Backdrops and rugs"] },
  { id: "arcos_chiara", es: "Arcos chiara", en: "Chiara arches", med: "120 · 105 · 80 cm", antes: ["Fondos y tapetes", "Backdrops and rugs"] },
  { id: "pedestales", es: "Pedestales", en: "Pedestals", med: "70 · 85 · 100 cm", antes: ["Decorado de pie", "Standing decor"] },
  { id: "aro_metalico", es: "Aro metálico", en: "Metal hoop", med: "Ø 200 cm", antes: ["Decorado de pie", "Standing decor"] },
  { id: "aro_hexagonal", es: "Marco hexagonal metálico", en: "Hexagonal metal frame", med: "200 cm", antes: ["Decorado de pie", "Standing decor"] },
  { id: "arco_metalico", es: "Arco metálico", en: "Metal arch", med: "240 × 220 cm", antes: ["Decorado de pie", "Standing decor"] },
] as const;
type PropId = (typeof PROPS)[number]["id"];

const DISPOS = [
  { id: "alrededor", es: "Alrededor", en: "All around" }, { id: "dos_lados", es: "Dos lados largos", en: "Both long sides" },
  { id: "cabeceras", es: "Cabeceras", en: "Ends only" }, { id: "un_lado", es: "Un lado", en: "One side" }, { id: "frente", es: "Frente al escenario", en: "Facing the stage" },
] as const;
type Dispo = (typeof DISPOS)[number]["id"];

// Survives the remount the mockup shell does on every view/state change, so edits and the camera's origin carry over.
const memo = { lang: "es" as Lang, lastView: "" as View | "", tipo: "rectangular" as TypeId, w: 240, d: 90, h: 75, sillas: 10, dispo: "alrededor" as Dispo };

const SEAT = 60; // cm of table edge per chair
function capacity(w: number, d: number, dispo: Dispo) {
  const long = Math.floor(w / SEAT), ends = Math.max(1, Math.floor(d / SEAT));
  return { alrededor: long * 2 + ends * 2, dos_lados: long * 2, cabeceras: ends * 2, un_lado: long, frente: long }[dispo];
}
function seatSpots(w: number, d: number, dispo: Dispo, n: number) {
  const long = Math.floor(w / SEAT), ends = Math.max(1, Math.floor(d / SEAT));
  const spots: { x: number; y: number }[] = [];
  const side = (y: number) => { for (let i = 0; i < long; i++) spots.push({ x: -w / 2 + (w / long) * (i + 0.5), y }); };
  const end = (x: number) => { for (let i = 0; i < ends; i++) spots.push({ x, y: -d / 2 + (d / ends) * (i + 0.5) }); };
  if (dispo === "alrededor" || dispo === "dos_lados" || dispo === "un_lado" || dispo === "frente") side(d / 2 + 34);
  if (dispo === "alrededor" || dispo === "dos_lados") side(-d / 2 - 34);
  if (dispo === "alrededor" || dispo === "cabeceras") { end(-w / 2 - 34); end(w / 2 + 34); }
  return spots.slice(0, n);
}

// Camera stops (stage-relative). The salon floor is 1200 × 800 cm.
const CAMERA: Record<View | "llegada", { x: string; y: string; scale: number; rotate: number }> = {
  llegada: { x: "0%", y: "-14%", scale: 0.62, rotate: 5 },
  mesas: { x: "0%", y: "2%", scale: 1.08, rotate: 0 },
  inspector: { x: "0%", y: "-4%", scale: 1.75, rotate: -1.5 },
  backing: { x: "0%", y: "30%", scale: 1.3, rotate: 1 },
  lista: { x: "30%", y: "-26%", scale: 1.7, rotate: -2 },
  exportar: { x: "0%", y: "2%", scale: 0.86, rotate: 0 },
};
const SPRINGS = {
  expressive: { type: "spring" as const, stiffness: 82, damping: 10.5, mass: 1.1 },
  natural: { type: "spring" as const, stiffness: 150, damping: 21 },
  subtle: { type: "spring" as const, stiffness: 320, damping: 42 },
};
const ORDER: View[] = ["backing", "mesas", "inspector", "lista", "exportar"];

function Balloon({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 22 28" className={className} aria-hidden="true">
      <path d="M11 1C5.5 1 2 5.3 2 10.2 2 15.8 6.6 20 11 20s9-4.2 9-9.8C20 5.3 16.5 1 11 1Z" fill="var(--primary)" />
      <path d="M9 20.5h4L11 23Z" fill="var(--primary)" />
      <path d="M11 23c-1.5 1.4 1.5 2.4 0 4" stroke="var(--foreground)" strokeWidth="1.2" fill="none" />
      <ellipse cx="7.5" cy="7" rx="2" ry="3" fill="#fff" opacity=".45" />
    </svg>
  );
}

function Silhouette({ id }: { id: TypeId }) {
  const s = { fill: "var(--mantel)", stroke: "currentColor", strokeWidth: 2.5 };
  const chair = (x: number, y: number) => <rect key={`${x}-${y}`} x={x - 5} y={y - 5} width="10" height="10" rx="3" fill="var(--silla)" stroke="var(--silla-edge)" strokeWidth="1.5" />;
  const around = (cx: number, cy: number, r: number, n: number) => Array.from({ length: n }, (_, i) => chair(cx + r * Math.cos((i / n) * Math.PI * 2), cy + r * Math.sin((i / n) * Math.PI * 2)));
  const shape = {
    redonda: <><circle cx="80" cy="29" r="17" {...s} />{around(80, 29, 25, 8)}</>,
    cuadrada: <><rect x="64" y="13" width="32" height="32" rx="2" {...s} />{[chair(80, 5), chair(80, 53), chair(56, 29), chair(104, 29)]}</>,
    rectangular: <><rect x="34" y="18" width="92" height="22" rx="2" {...s} />{[46, 69, 92, 114].flatMap((x) => [chair(x, 9), chair(x, 49)])}{[chair(25, 29), chair(135, 29)]}</>,
    ovalada: <><ellipse cx="80" cy="29" rx="44" ry="16" {...s} />{[52, 80, 108].flatMap((x) => [chair(x, 6), chair(x, 52)])}</>,
    coctel: <><circle cx="80" cy="29" r="12" {...s} /><circle cx="80" cy="29" r="3" fill="currentColor" /></>,
    media_luna: <><path d="M44 18h72a36 36 0 0 1-72 0Z" {...s} />{[chair(56, 44), chair(80, 52), chair(104, 44)]}</>,
    serpentina: <><path d="M30 34c20-24 40-24 50 0s30 24 50 0" fill="none" stroke="currentColor" strokeWidth="14" strokeLinecap="round" /><path d="M30 34c20-24 40-24 50 0s30 24 50 0" fill="none" stroke="var(--mantel)" strokeWidth="9" strokeLinecap="round" /></>,
    u: <><path d="M40 8h20v30h40V8h20v42H40Z" {...s} />{[chair(32, 20), chair(32, 38), chair(128, 20), chair(128, 38)]}</>,
  }[id];
  return <svg viewBox="0 0 160 58" className="sil" aria-hidden="true">{shape}</svg>;
}

// Front elevations in each prop's real colours; x/y in a 1200 × 300 cm wall.
function PropArt({ id, x = 0, scale = 1 }: { id: PropId; x?: number; scale?: number }) {
  const g = (children: React.ReactNode) => <g transform={`translate(${x} 0) scale(${scale})`}>{children}</g>;
  switch (id) {
    case "panel_redondo": return g(<><circle cx="75" cy="190" r="75" fill="#f3e7cf" stroke="#d8b25a" strokeWidth="6" /><rect x="70" y="262" width="10" height="38" fill="#8a7240" /></>);
    case "media_luna": return g(<path d="M0 300a90 90 0 0 1 180 0Z" fill="#1c2f5e" />);
    case "arcos_chiara": return g(<><path d="M0 300V150a60 60 0 0 1 120 0v150Z" fill="#3d8fd6" /><path d="M27 300V163a52 52 0 0 1 105 0v137Z" fill="#f2dcc4" /><path d="M55 300V175a40 40 0 0 1 80 0v125Z" fill="#d6336c" /></>);
    case "pedestales": return g(<><rect x="0" y="230" width="55" height="70" rx="4" fill="#1f3366" /><rect x="60" y="215" width="50" height="85" rx="4" fill="#f4f1ea" stroke="#9aa59f" strokeWidth="2" /><rect x="115" y="200" width="45" height="100" rx="4" fill="#c9a14a" /></>);
    case "aro_metalico": return g(<><circle cx="100" cy="190" r="96" fill="none" stroke="#b9b4a6" strokeWidth="7" /><rect x="70" y="292" width="60" height="8" fill="#7d786c" /></>);
    case "aro_hexagonal": return g(<><path d="M100 92l86 50v98l-86 50-86-50v-98Z" fill="none" stroke="#c9a14a" strokeWidth="7" /><rect x="70" y="292" width="60" height="8" fill="#7d786c" /></>);
    case "arco_metalico": return g(<path d="M10 300V190a110 110 0 0 1 220 0v110" fill="none" stroke="#b9b4a6" strokeWidth="8" />);
  }
}

// What the mock scene holds: the selected table plus two round tables (8 chairs) and three Backing props on the wall.
const WALL: { id: PropId; x: number; scale: number }[] = [
  { id: "media_luna", x: 360, scale: 1 }, { id: "panel_redondo", x: 375, scale: 1 }, { id: "arcos_chiara", x: 640, scale: 1 }, { id: "pedestales", x: 820, scale: 1 },
];

function Stage({ view, state, hl, props }: { view: View; state: string; hl: PropId | null; props: PropId[] }) {
  const { reduced, profile } = useMotionProfile();
  const empty = state === "vacio" && view !== "backing";
  const t = TYPES.find((x) => x.id === memo.tipo)!;
  const want = state === "capacidad" ? 12 : state === "asistente" ? 12 : memo.sillas;
  const w = state === "asistente" ? 300 : memo.w, d = state === "asistente" ? 100 : memo.d;
  const cap = capacity(w, d, memo.dispo);
  const placed = Math.min(want, cap);
  const seats = seatSpots(w, d, memo.dispo, placed);
  const from = CAMERA[(memo.lastView || "llegada") as View | "llegada"];
  const ref = React.useRef<HTMLElement>(null);
  React.useEffect(() => {
    const el = ref.current;
    if (!el || !("IntersectionObserver" in window)) return;
    const io = new IntersectionObserver(([e]) => el.toggleAttribute("data-pausa", !e.isIntersecting));
    io.observe(el);
    return () => io.disconnect();
  }, []);
  const pct = (cm: number, of: number) => `${(cm / of) * 100}%`;
  const rect = { cx: 600, cy: 420 };
  const showRect = !empty && (memo.tipo === "rectangular" || view === "inspector" || state === "asistente");
  const round = (cx: number, cy: number, key: string) => (
    <div key={key} className="pieza-piso" style={{ left: pct(cx - 75, 1200), top: pct(cy - 75, 800), width: pct(150, 1200), height: pct(150, 800) }}>
      <div className="mesa-tapa" style={{ borderRadius: "50%" }} />
      {Array.from({ length: 8 }, (_, i) => {
        const a = (i / 8) * Math.PI * 2;
        return <span key={i} className="silla" style={{ left: `${50 + 66 * Math.cos(a)}%`, top: `${50 + 66 * Math.sin(a)}%`, width: "24%", height: "24%", margin: "-12% 0 0 -12%" }} />;
      })}
    </div>
  );
  const tiles = React.useMemo(() => Array.from({ length: 96 }, (_, i) => <span key={i} className="baldosa" style={{ "--i": (i % 12) + Math.floor(i / 12) } as React.CSSProperties} />), []);
  return (
    <section ref={ref} className="escenario" aria-label="Vista 3D del salón (ilustración)">
      <motion.div className="camara" initial={reduced ? false : from} animate={CAMERA[view]} transition={reduced ? { duration: 0 } : SPRINGS[profile]}>
        <div className="plano">
          <div className="baldosas" aria-hidden="true">{tiles}</div>
          <div className="pared" aria-hidden="true">
            <svg viewBox="0 0 1200 300" preserveAspectRatio="xMidYMax meet">
              {(empty ? [] : WALL).map((p) => (
                <g key={p.id} className="prop" data-hl={hl === p.id || undefined} data-dim={hl && hl !== p.id ? "" : undefined}><PropArt id={p.id} x={p.x} scale={p.scale} /></g>
              ))}
              {props.map((id, i) => (
                <g key={id} className="prop" data-nuevo="" data-hl={hl === id || undefined}><PropArt id={id} x={60 + i * 250} scale={0.9} /></g>
              ))}
              {hl && !WALL.some((p) => p.id === hl) && !props.includes(hl) && (
                <g className="prop" data-nuevo="" data-hl=""><PropArt id={hl} x={60} scale={0.9} /></g>
              )}
            </svg>
          </div>
          {!empty && round(250, 520, "r1")}
          {!empty && round(950, 520, "r2")}
          {showRect && (
            <div className="pieza-piso" style={{ left: pct(rect.cx - w / 2, 1200), top: pct(rect.cy - d / 2, 800), width: pct(w, 1200), height: pct(d, 800) }}>
              <motion.div className="mesa-tapa" data-sel={view === "inspector" || undefined} style={{ borderRadius: 6 }}
                initial={reduced || state !== "exito" ? false : { y: -60, opacity: 0, scale: 1.2 }} animate={{ y: 0, opacity: 1, scale: 1 }} transition={SPRINGS[profile]} />
              {seats.map((s, i) => (
                <motion.span key={`${i}-${seats.length}`} className="silla" style={{ left: `${50 + (s.x / w) * 100}%`, top: `${50 + (s.y / d) * 100}%`, width: `${(44 / w) * 100}%`, height: `${(44 / d) * 100}%`, margin: `-${(22 / d) * 100}% 0 0 -${(22 / w) * 100}%` }}
                  initial={reduced ? false : { scale: 0.3, opacity: 0, y: -18 }} animate={{ scale: 1, opacity: 1, y: 0 }} transition={{ ...SPRINGS[profile], delay: 0.25 + i * 0.045 }} />
              ))}
            </div>
          )}
          {!empty && <div className="caja-lista" aria-hidden="true" />}
        </div>
        <div className="globos" aria-hidden="true">
          {[["14%", "8%", 44, "#e46a1e", 0], ["19%", "4%", 36, "#f3efe6", 1], ["23%", "10%", 40, "#2f8a6a", 2], ["76%", "6%", 42, "#c9a14a", 1], ["81%", "10%", 36, "#e46a1e", 2], ["72%", "11%", 32, "#2f8a6a", 0]].map(([l, tp, s, c, dd], i) => (
            <span key={i} className="globo" style={{ left: l as string, top: tp as string, "--s": `${s}px`, "--c": c, "--d": dd } as React.CSSProperties} />
          ))}
        </div>
      </motion.div>
      <div className="cotas">
        {view === "inspector" && !empty && state !== "cargando" && (
          <>
            <span className="cota" style={{ left: "50%", bottom: "16%", transform: "translateX(-50%)" }}>{w} cm</span>
            <span className="cota" style={{ right: "8%", top: "46%" }}>{d} cm</span>
            <span className="cota" style={{ left: "6%", top: "10%" }}>{t.id === "rectangular" ? `${placed} / ${want}` : ""} {placed === 1 ? "silla" : "sillas"}</span>
            {want > placed && Array.from({ length: want - placed }, (_, i) => <span key={i} className="fantasma" style={{ left: `${44 + i * 8}%`, top: "18%", animationDelay: `${i * -0.7}s` }} aria-hidden="true" />)}
          </>
        )}
        {view === "exportar" && !empty && (
          <>
            <div className="caja-glb" data-error={state === "error" || undefined} aria-hidden="true" />
            <span className="cota" style={{ left: "50%", top: "calc(16% - 16px)", transform: "translateX(-50%)" }}>12,00 m</span>
            <span className="cota" style={{ left: "calc(7% - 8px)", top: "50%" }}>8,00 m</span>
            {state === "exito" && <span className="sello">GLB<br />listo</span>}
          </>
        )}
      </div>
    </section>
  );
}

function RoomMap({ view, go }: { view: View; go: (v: View) => void }) {
  const { t } = useT();
  const { reduced, profile } = useMotionProfile();
  const box = React.useRef<HTMLDivElement>(null);
  const refs = React.useRef<Partial<Record<View, HTMLButtonElement | null>>>({});
  const [pos, setPos] = React.useState<Record<string, { x: number; y: number }> | null>(null);
  React.useLayoutEffect(() => {
    const measure = () => {
      const out: Record<string, { x: number; y: number }> = {};
      for (const v of ["mesas", "backing", "lista", "exportar"] as View[]) {
        const b = refs.current[v];
        if (b) out[v] = { x: b.offsetLeft + b.offsetWidth / 2 - 8, y: b.offsetTop - 10 };
      }
      out.inspector = out.mesas;
      setPos(out);
    };
    measure();
    const ro = new ResizeObserver(measure);
    if (box.current) ro.observe(box.current);
    return () => ro.disconnect();
  }, []);
  const st = (v: View, cls: string, label: string, sub: string) => (
    <button ref={(el) => { refs.current[v] = el; }} type="button" className={`estacion ${cls}`} aria-current={view === v || (v === "mesas" && view === "inspector") ? "page" : undefined} onClick={() => go(v)}>
      <span>{label}{sub && <><br /><small>{sub}</small></>}</span>
    </button>
  );
  const prev = (memo.lastView || view) as View;
  return (
    <nav className="plano-sala" aria-label={t("Plano de sala", "Room map")}>
      <h2>{t("Plano de sala · toca una zona", "Room map · pick a zone")}</h2>
      <div ref={box} className="sala">
        {st("backing", "est-backing", "Backing", t("pared del fondo", "back wall"))}
        {st("mesas", "est-mesas", t("Mesas", "Tables"), view === "inspector" ? t("Mesa rectangular · M-03", "Rectangular table · M-03") : t("pista", "floor"))}
        {st("lista", "est-lista", t("Lista", "List"), "")}
        {st("exportar", "est-exportar", t("Exportar", "Export"), "")}
        {pos && pos[view] && (
          <motion.span className="viajero" aria-hidden="true" initial={reduced ? false : pos[prev] ?? pos[view]} animate={pos[view]}
            transition={reduced ? { duration: 0 } : { ...SPRINGS[profile], delay: 0.05 }} />
        )}
      </div>
    </nav>
  );
}

function Title({ children }: { children: string }) {
  return <h1 className="titulo"><span key={children}>{children}</span></h1>;
}

function Notice({ tone, title, children, action }: { tone: "ok" | "error" | "info" | "warn"; title: string; children?: React.ReactNode; action?: React.ReactNode }) {
  const Icon = tone === "ok" ? Check : tone === "info" ? Info : CircleAlert;
  const color = { ok: "var(--success)", error: "var(--destructive)", info: "var(--info)", warn: "var(--warning)" }[tone];
  const soft = { ok: "var(--success-soft)", error: "var(--destructive-soft, var(--muted))", info: "var(--info-soft)", warn: "var(--warning-soft)" }[tone];
  return (
    <Alert variant={tone === "error" ? "destructive" : "default"} className="mb-5" style={{ borderColor: color, background: soft, padding: "14px 16px" }}>
      <Icon style={{ color }} />
      <AlertTitle style={{ color: tone === "error" ? color : "var(--foreground)" }}>{title}</AlertTitle>
      {(children || action) && (
        <AlertDescription style={{ color: "var(--foreground)" }}>
          {children}
          {action && <div className="mt-3 flex flex-wrap gap-2">{action}</div>}
        </AlertDescription>
      )}
    </Alert>
  );
}

function SkeletonGrid({ n, h = 132 }: { n: number; h?: number }) {
  return <div className="tipos" aria-busy="true">{Array.from({ length: n }, (_, i) => <Skeleton key={i} style={{ height: h, borderRadius: 20 }} />)}</div>;
}

function MesasView({ state, go }: { state: string; go: (v: View) => void }) {
  const { t, lang } = useT();
  const mp = useMotionProfile();
  const add = (id: TypeId) => {
    const tp = TYPES.find((x) => x.id === id)!;
    Object.assign(memo, { tipo: id, w: tp.w, d: tp.d, h: tp.h, sillas: id === "coctel" ? 0 : capacity(tp.w, tp.d, "alrededor") });
    go("inspector");
  };
  return (
    <>
      <Title>{t("Mesas", "Tables")}</Title>
      <p className="lede">{t("Toca un tipo: entra a la pista con su medida inicial y se abre el inspector.", "Pick a type: it lands on the floor at its starting size and the inspector opens.")}</p>
      {state === "error" && <Notice tone="error" title={t("No pudimos añadir la mesa rectangular", "We couldn't add the rectangular table")} action={<Button size="sm"><RotateCcw /> {t("Reintentar", "Try again")}</Button>}>{t("La escena no cambió.", "The scene didn't change.")}</Notice>}
      {state === "exito" && <Notice tone="ok" title={t("Mesa rectangular añadida · 240 × 90 × 75 cm", "Rectangular table added · 240 × 90 × 75 cm")} action={<><Button size="sm" onClick={() => go("inspector")}>{t("Abrir inspector", "Open inspector")}</Button><Button size="sm" variant="outline"><Undo2 /> {t("Deshacer", "Undo")}</Button></>}>{t("Está seleccionada en la pista con 10 sillas alrededor.", "It is selected on the floor with 10 chairs around it.")}</Notice>}
      {state === "vacio" && <Notice tone="info" title={t("La escena aún no tiene mesas", "The scene has no tables yet")}>{t("Empieza por un tipo; podrás cambiar medidas y sillas después.", "Start with a type; you can change size and chairs afterwards.")}</Notice>}
      {state === "asistente" && <Notice tone="info" title={t("El asistente añadió 2 mesas rectangulares", "The assistant added 2 rectangular tables")}>{t("Con 240 × 90 × 75 cm y 10 sillas cada una: lo mismo que obtienes tocando la tarjeta.", "At 240 × 90 × 75 cm with 10 chairs each — the same as tapping the card.")}</Notice>}
      {state === "cargando" ? <SkeletonGrid n={8} /> : (
        <div className="tipos">
          {TYPES.map((tp, i) => (
            <motion.button key={tp.id} type="button" className="tipo" onClick={() => add(tp.id)} aria-label={`${t("Añadir", "Add")} ${lang === "en" ? tp.en.toLowerCase() : tp.es.toLowerCase()}`}
              {...stagger(i, mp)}>
              {tp.id === "rectangular" && <Badge className="badge-n" style={{ background: "var(--primary)", color: "var(--primary-foreground)" }}>{t("Nueva", "New")}</Badge>}
              <Silhouette id={tp.id} />
              <strong>{lang === "en" ? tp.en : tp.es}</strong>
              <span className="med">{tp.fromW && tp.id !== "media_luna" ? `Ø/${tp.w} × ${tp.h} cm` : `${tp.w} × ${tp.d} × ${tp.h} cm`}</span>
            </motion.button>
          ))}
        </div>
      )}
      <p className="nota"><Info size={16} /> {t("Las piezas fijas Imperial (mesa imperial con 10 sillas, 360 × 198 cm) siguen en Fondos y muebles › Mesas.", "Fixed Imperial pieces (imperial table with 10 chairs, 360 × 198 cm) stay in Backdrops & furniture › Tables.")}</p>
    </>
  );
}

function stagger(i: number, { reduced, profile }: { reduced: boolean; profile: keyof typeof SPRINGS }) {
  return reduced ? { initial: false as const } : {
    initial: { opacity: 0, y: 26, rotate: i % 2 ? 2.5 : -2.5 },
    animate: { opacity: 1, y: 0, rotate: 0 },
    transition: { ...SPRINGS[profile], delay: 0.18 + i * 0.05 },
  };
}

function Field({ id, label, value, unit, onChange, lim, invalid, help }: { id: string; label: string; value: number; unit: string; onChange: (n: number) => void; lim: readonly [number, number]; invalid?: string; help?: string }) {
  return (
    <div className="campo">
      <label htmlFor={id}>{label}</label>
      <div className="unidad">
        <Input id={id} type="number" inputMode="numeric" min={lim[0]} max={lim[1]} value={value} aria-invalid={invalid ? true : undefined} aria-describedby={`${id}-a`}
          onChange={(e) => onChange(Number(e.target.value))} />
        <span>{unit}</span>
      </div>
      {invalid ? <p id={`${id}-a`} className="mal">{invalid}</p> : <p id={`${id}-a`} className="ayuda">{help ?? `${lim[0]}–${lim[1]} ${unit}`}</p>}
    </div>
  );
}

function InspectorView({ state, go, onChange }: { state: string; go: (v: View) => void; onChange: () => void }) {
  const { t, lang } = useT();
  const tp = TYPES.find((x) => x.id === memo.tipo)!;
  const ai = state === "asistente";
  const [w, setW] = React.useState(ai ? 300 : memo.w);
  const [d, setD] = React.useState(ai ? 100 : memo.d);
  const [h, setH] = React.useState(memo.h);
  const [want, setWant] = React.useState(state === "capacidad" || ai ? 12 : memo.sillas);
  const [dispo, setDispo] = React.useState<Dispo>(memo.dispo);
  const [last, setLast] = React.useState(ai ? t("asistente: largo 240 → 300 cm, sillas 10 → 12", "assistant: length 240 → 300 cm, chairs 10 → 12") : t("sillas 8 → 10", "chairs 8 → 10"));
  const cap = capacity(w, tp.fromW ? w : d, dispo);
  const placed = Math.min(want, cap);
  const sync = (patch: Partial<typeof memo>, label: string) => { Object.assign(memo, patch); setLast(label); onChange(); };
  if (state === "cargando") return (<><Title>{lang === "en" ? tp.en : tp.es}</Title><div className="campos" aria-busy="true">{[0, 1, 2].map((i) => <Skeleton key={i} style={{ height: 70, borderRadius: 12 }} />)}</div><Skeleton style={{ height: 120, borderRadius: 16, marginTop: 22 }} /></>);
  if (state === "vacio") return (
    <>
      <Title>{t("Inspector", "Inspector")}</Title>
      <Empty className="vacio-izq mt-4">
        <EmptyHeader><EmptyTitle>{t("Ninguna mesa seleccionada", "No table selected")}</EmptyTitle>
          <EmptyDescription>{t("Añade una mesa desde su tarjeta o tócala en la pista para editar medidas y sillas.", "Add a table from its card or tap it on the floor to edit size and chairs.")}</EmptyDescription></EmptyHeader>
        <EmptyContent><Button onClick={() => go("mesas")}>{t("Elegir un tipo de mesa", "Choose a table type")}</Button></EmptyContent>
      </Empty>
    </>
  );
  const badLength = state === "error" ? t("El largo va de 100 a 600 cm. La mesa sigue en 240 cm.", "Length goes from 100 to 600 cm. The table stays at 240 cm.") : undefined;
  return (
    <>
      <Button variant="ghost" size="sm" className="-ml-2 mb-2" onClick={() => go("mesas")}><ArrowLeft /> {t("Mesas", "Tables")}</Button>
      <Title>{lang === "en" ? tp.en : tp.es}</Title>
      <p className="lede">{t("M-03 · seleccionada en la pista. Los cambios se ven en la escena y en la lista al instante.", "M-03 · selected on the floor. Changes show in the scene and the list right away.")}</p>
      {ai && <Notice tone="info" title={t("El asistente cambió esta mesa", "The assistant changed this table")}>{t("Largo 300 cm, fondo 100 cm y 12 sillas: los mismos valores que verías editando aquí.", "Length 300 cm, depth 100 cm and 12 chairs — the same values you'd get editing here.")}</Notice>}
      {state === "exito" && <Notice tone="ok" title={t("Cambios aplicados a la escena", "Changes applied to the scene")} />}
      <div className="campos">
        <Field id="largo" label={tp.fromW ? t("Diámetro / ancho", "Diameter / width") : t("Largo", "Length")} unit="cm" value={state === "error" ? 650 : w} lim={tp.lim} invalid={badLength}
          onChange={(n) => { setW(n); sync({ w: n }, `${t("largo", "length")} ${w} → ${n} cm`); }} />
        {!tp.fromW && tp.dLim && <Field id="fondo" label={t("Fondo", "Depth")} unit="cm" value={d} lim={tp.dLim} onChange={(n) => { setD(n); sync({ d: n }, `${t("fondo", "depth")} ${d} → ${n} cm`); }} />}
        <Field id="alto" label={t("Alto", "Height")} unit="cm" value={h} lim={[40, 110]} onChange={(n) => { setH(n); sync({ h: n }, `${t("alto", "height")} ${h} → ${n} cm`); }} />
      </div>
      {tp.id !== "coctel" && (
        <div className="bloque">
          <h2>{t("Sillas", "Chairs")}</h2>
          <div className="sillas">
            <div className="pasos" role="group" aria-label={t("Número de sillas", "Number of chairs")}>
              <button type="button" aria-label={t("Una silla menos", "One chair fewer")} disabled={want <= 0} onClick={() => { setWant(want - 1); sync({ sillas: want - 1 }, `${t("sillas", "chairs")} ${want} → ${want - 1}`); }}><Minus size={18} /></button>
              <output aria-live="polite">{want}</output>
              <button type="button" aria-label={t("Una silla más", "One chair more")} disabled={want >= 40} onClick={() => { setWant(want + 1); sync({ sillas: want + 1 }, `${t("sillas", "chairs")} ${want} → ${want + 1}`); }}><Plus size={18} /></button>
            </div>
            <label className="sr-only" htmlFor="dispo">{t("Disposición", "Arrangement")}</label>
            <select id="dispo" className="nativo" value={dispo} onChange={(e) => { const v = e.target.value as Dispo; setDispo(v); sync({ dispo: v }, `${t("disposición", "arrangement")} → ${v}`); }}>
              {DISPOS.map((o) => <option key={o.id} value={o.id}>{lang === "en" ? o.en : o.es}</option>)}
            </select>
          </div>
          <p className="cupo" data-lleno={want > cap || undefined}><span className="punto" aria-hidden="true" />
            {t(`Caben ${cap} con esta disposición · ${placed} colocadas`, `${cap} fit with this arrangement · ${placed} placed`)}</p>
          {want > cap && (
            <div className="mt-4">
              <Notice tone="warn" title={t(`Pediste ${want} sillas; caben ${cap}`, `You asked for ${want} chairs; ${cap} fit`)}
                action={<><Button size="sm" onClick={() => { setWant(cap); sync({ sillas: cap }, `${t("sillas", "chairs")} ${want} → ${cap}`); }}>{t(`Dejar ${cap} sillas`, `Keep ${cap} chairs`)}</Button>
                  <Button size="sm" variant="outline" onClick={() => { const nw = Math.min(tp.lim[1], w + SEAT); setW(nw); sync({ w: nw }, `${t("largo", "length")} ${w} → ${nw} cm`); }}>{t("Alargar 60 cm", "Lengthen 60 cm")}</Button></>}>
                {t(`Colocamos ${placed} alrededor de ${w} × ${d} cm y la lista cuenta ${placed}. Alarga la mesa o cambia la disposición.`, `We placed ${placed} around ${w} × ${d} cm and the list counts ${placed}. Lengthen the table or change the arrangement.`)}
              </Notice>
            </div>
          )}
        </div>
      )}
      <div className="deshacer">
        <span>{t("Último cambio", "Last change")}: <strong>{last}</strong></span>
        <Button size="sm" variant="outline"><Undo2 /> {t("Deshacer", "Undo")}</Button>
      </div>
      <div className="acciones"><Button variant="outline" onClick={() => go("lista")}>{t("Ver en la lista de compras", "See it in the shopping list")}</Button></div>
    </>
  );
}

function BackingView({ state, setHl, added, onAdd }: { state: string; setHl: (p: PropId | null) => void; added: PropId[]; onAdd: (p: PropId) => void }) {
  const { t, lang } = useT();
  const mp = useMotionProfile();
  const [q, setQ] = React.useState(state === "vacio" ? "columna espejo" : state === "asistente" ? "hexagonal" : "");
  const norm = (s: string) => s.normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();
  const list = PROPS.filter((p) => !q || [p.es, p.en, p.id.replace(/_/g, " ")].some((s) => norm(s).includes(norm(q))));
  return (
    <>
      <Title>Backing</Title>
      <p className="lede">{t("Las siete piezas de fondo de fiesta, juntas y una sola vez. Toca «Añadir» y cuelgan en la pared del fondo.", "The seven party backdrop pieces, together and listed once. Tap Add and they hang on the back wall.")}</p>
      <ul className="grupos" aria-label={t("Grupos de Fondos y muebles", "Backdrops & furniture groups")}>
        {[["Backing", "Backing"], ["Fondos y tapetes", "Backdrops and rugs"], ["Sillas y asientos", "Chairs and seating"], ["Mesas", "Tables"], ["Decorado de pie", "Standing decor"]].map(([es, en], i) => (
          <li key={es} aria-current={i === 0 ? "true" : undefined}>{lang === "en" ? en : es}</li>
        ))}
      </ul>
      <div className="buscar">
        <Search size={18} aria-hidden="true" />
        <label className="sr-only" htmlFor="buscar">{t("Buscar en Fondos y muebles", "Search backdrops & furniture")}</label>
        <Input id="buscar" type="search" placeholder={t("Buscar: aro, arco, panel…", "Search: hoop, arch, panel…")} value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      {state === "error" && <Notice tone="error" title={t("No pudimos añadir Arcos chiara", "We couldn't add Chiara arches")} action={<Button size="sm"><RotateCcw /> {t("Reintentar", "Try again")}</Button>}>{t("La escena no cambió.", "The scene didn't change.")}</Notice>}
      {state === "exito" && <Notice tone="ok" title={t("Arcos chiara cuelga en la pared del fondo", "Chiara arches now hang on the back wall")} action={<Button size="sm" variant="outline"><Undo2 /> {t("Deshacer", "Undo")}</Button>} />}
      {state === "asistente" && <Notice tone="info" title={t("El asistente reconoció un aro hexagonal en tu foto", "The assistant spotted a hexagonal hoop in your photo")}>{t("Es el Marco hexagonal metálico, la misma pieza de siempre, ahora dentro de Backing.", "It's the Hexagonal metal frame — the same piece as before, now inside Backing.")}</Notice>}
      {state === "cargando" ? <SkeletonGrid n={7} h={168} /> : list.length === 0 ? (
        <Empty className="vacio-izq">
          <EmptyHeader><EmptyTitle>{t(`Nada se llama «${q}»`, `Nothing is called “${q}”`)}</EmptyTitle>
            <EmptyDescription>{t("Prueba con «aro», «arco», «panel» o «pedestal». Los nombres de antes también sirven.", "Try “hoop”, “arch”, “panel” or “pedestal”. The old names still work.")}</EmptyDescription></EmptyHeader>
          <EmptyContent><Button variant="outline" onClick={() => setQ("")}>{t("Limpiar búsqueda", "Clear search")}</Button></EmptyContent>
        </Empty>
      ) : (
        <div className="piezas">
          {list.map((p, i) => (
            <motion.div key={p.id} className="pieza" onMouseEnter={() => setHl(p.id)} onMouseLeave={() => setHl(null)} onFocus={() => setHl(p.id)} onBlur={() => setHl(null)} {...stagger(i, mp)}>
              <svg viewBox="-10 80 280 230" preserveAspectRatio="xMidYMax meet" aria-hidden="true"><PropArt id={p.id} /></svg>
              <strong>{lang === "en" ? p.en : p.es}</strong>
              <span className="med">{p.med}</span>
              <span className="antes">{t("Antes en", "Was in")} {lang === "en" ? p.antes[1] : p.antes[0]}</span>
              <Button size="sm" variant={added.includes(p.id) || (state === "exito" && p.id === "arcos_chiara") ? "outline" : "default"} onClick={() => onAdd(p.id)}>
                {added.includes(p.id) || (state === "exito" && p.id === "arcos_chiara") ? <><Check /> {t("Añadido", "Added")}</> : <><Plus /> {t("Añadir", "Add")}</>}
              </Button>
            </motion.div>
          ))}
        </div>
      )}
    </>
  );
}

function Count({ n }: { n: number }) {
  const { reduced } = useMotionProfile();
  return reduced ? <>{n}</> : <CountingNumber number={n} fromNumber={0} transition={{ stiffness: 90, damping: 18 }} />;
}

function ListaView({ state, go }: { state: string; go: (v: View) => void }) {
  const { t, lang } = useT();
  const tp = TYPES.find((x) => x.id === memo.tipo)!;
  const ai = state === "asistente";
  const w = ai ? 300 : memo.w, d = ai ? 100 : memo.d;
  const want = state === "capacidad" || ai ? 12 : memo.sillas;
  const placed = Math.min(want, capacity(w, tp.fromW ? w : d, memo.dispo));
  if (state === "cargando") return (<><Title>{t("Lista de compras", "Shopping list")}</Title><div aria-busy="true" className="grid gap-3">{[0, 1, 2, 3, 4, 5].map((i) => <Skeleton key={i} style={{ height: 40, borderRadius: 10 }} />)}</div></>);
  if (state === "vacio") return (
    <>
      <Title>{t("Lista de compras", "Shopping list")}</Title>
      <Empty className="vacio-izq mt-4">
        <EmptyHeader><EmptyTitle>{t("La lista está vacía", "The list is empty")}</EmptyTitle>
          <EmptyDescription>{t("Se llena sola con lo que pongas en la escena: mesas, sillas colocadas y piezas de Backing.", "It fills itself with what you put in the scene: tables, placed chairs and Backing pieces.")}</EmptyDescription></EmptyHeader>
        <EmptyContent><Button onClick={() => go("mesas")}>{t("Añadir una mesa", "Add a table")}</Button></EmptyContent>
      </Empty>
    </>
  );
  const rows: { name: string; med: string; n: number; note?: string; ai?: boolean }[] = [
    { name: lang === "en" ? tp.en : tp.es, med: tp.fromW ? `Ø ${w} × ${memo.h} cm` : `${w} × ${d} × ${memo.h} cm`, n: 1, ai },
    { name: t("Mesa redonda", "Round table"), med: "Ø 150 × 75 cm", n: 2 },
    { name: t("Silla tiffany dorada", "Gold tiffany chair"), med: "40 × 42 × 92 cm", n: placed + 16, note: want > placed ? t(`${want - placed} pedidas sin lugar no se cuentan`, `${want - placed} requested without room aren't counted`) : undefined, ai },
    { name: t("Panel redondo", "Round panel"), med: "Ø 150 cm", n: 1 },
    { name: t("Arcos chiara", "Chiara arches"), med: "120 · 105 · 80 cm", n: 1 },
    { name: t("Pedestales", "Pedestals"), med: "70 · 85 · 100 cm", n: 1 },
  ];
  return (
    <>
      <Title>{t("Lista de compras", "Shopping list")}</Title>
      <p className="lede">{t("Cantidades y medidas de lo que hay en la escena. Sin precios de alquiler.", "Quantities and sizes of what's in the scene. No rental prices.")}</p>
      {state === "error" && <Notice tone="error" title={t("No pudimos actualizar la lista", "We couldn't update the list")} action={<Button size="sm"><RotateCcw /> {t("Reintentar", "Try again")}</Button>}>{t("Lo que ves corresponde a la escena de las 18:42.", "What you see matches the scene at 18:42.")}</Notice>}
      {state === "exito" && <Notice tone="ok" title={t("Lista al día con la escena", "List up to date with the scene")} />}
      <Table className="tabla">
        <TableHeader><TableRow><TableHead>{t("Pieza", "Item")}</TableHead><TableHead>{t("Medidas", "Size")}</TableHead><TableHead className="num">{t("Cant.", "Qty")}</TableHead></TableRow></TableHeader>
        <TableBody>
          {rows.map((r) => (
            <TableRow key={r.name}>
              <TableCell><strong className="font-semibold">{r.name}</strong>{r.ai && <Badge variant="outline" className="ml-2">{t("asistente", "assistant")}</Badge>}{r.note && <div className="text-[13px] font-semibold" style={{ color: "var(--warning)" }}>{r.note}</div>}</TableCell>
              <TableCell className="whitespace-normal" style={{ color: "var(--ink-soft)" }}>{r.med}</TableCell>
              <TableCell className="num font-bold"><Count n={r.n} /></TableCell>
            </TableRow>
          ))}
        </TableBody>
        <TableFooter><TableRow><TableCell colSpan={2}>{t("Piezas en la escena", "Pieces in the scene")}</TableCell><TableCell className="num font-bold"><Count n={rows.reduce((a, r) => a + r.n, 0)} /></TableCell></TableRow></TableFooter>
      </Table>
      <div className="acciones"><Button variant="outline">{t("Copiar lista", "Copy list")}</Button><Button variant="outline" onClick={() => go("inspector")}>{t("Editar la mesa", "Edit the table")}</Button></div>
    </>
  );
}

function ExportView({ state, openInfo }: { state: string; openInfo: () => void }) {
  const { t } = useT();
  const loading = state === "cargando";
  if (state === "vacio") return (
    <>
      <Title>{t("Exportar a Blender", "Export to Blender")}</Title>
      <Empty className="vacio-izq mt-4">
        <EmptyHeader><EmptyTitle>{t("No hay nada que exportar", "There's nothing to export")}</EmptyTitle>
          <EmptyDescription>{t("La escena está vacía. Añade mesas o piezas y vuelve aquí.", "The scene is empty. Add tables or pieces and come back.")}</EmptyDescription></EmptyHeader>
        <EmptyContent><Button disabled><Download /> {t("Descargar GLB", "Download GLB")}</Button></EmptyContent>
      </Empty>
    </>
  );
  return (
    <>
      <Title>{t("Exportar a Blender", "Export to Blender")}</Title>
      <p className="lede">{t("Un GLB con la escena tal como está: posiciones, medidas en metros y colores base. Se arma en tu navegador.", "A GLB of the scene as it is: positions, sizes in metres and base colours. Built in your browser.")}</p>
      {state === "error" && <Notice tone="error" title={t("No pudimos generar el GLB", "We couldn't build the GLB")} action={<Button size="sm"><RotateCcw /> {t("Reintentar exportación", "Retry export")}</Button>}>{t("Tu escena no cambió. Si vuelve a fallar, recarga el Taller y exporta de nuevo.", "Your scene didn't change. If it fails again, reload the Taller and export again.")}</Notice>}
      {state === "exito" && <Notice tone="ok" title={t("GLB descargado · 2,4 MB", "GLB downloaded · 2.4 MB")}>{t("En Blender: Archivo › Importar › glTF 2.0 (.glb/.gltf).", "In Blender: File › Import › glTF 2.0 (.glb/.gltf).")}</Notice>}
      <div className="archivo">
        <code>salon-jardin-cumple-sofia.glb</code>
        <ul>
          <li><Check size={16} style={{ color: "var(--success)" }} />{t("3 mesas · 26 sillas colocadas · 3 piezas de Backing", "3 tables · 26 placed chairs · 3 Backing pieces")}</li>
          <li><Check size={16} style={{ color: "var(--success)" }} />{t("1 unidad = 1 metro; sala de 12,00 × 8,00 m", "1 unit = 1 metre; room 12.00 × 8.00 m")}</li>
          <li><Check size={16} style={{ color: "var(--success)" }} />{t("Color base de cada material", "Base colour of every material")}</li>
          <li><Info size={16} style={{ color: "var(--info)" }} />{t("No lleva luces ni el entorno del Taller", "Doesn't include lights or the Taller environment")}</li>
        </ul>
      </div>
      {loading && (
        <div className="progreso" aria-live="polite">
          <Progress value={64} aria-label={t("Preparando el GLB", "Preparing the GLB")} />
          <p className="mt-2 text-sm" style={{ color: "var(--ink-soft)" }}>{t("Preparando el GLB… 64 %. No se envía nada a internet.", "Preparing the GLB… 64%. Nothing is sent to the internet.")}</p>
        </div>
      )}
      <div className="acciones">
        <Button disabled={loading}><Download /> {loading ? t("Preparando…", "Preparing…") : state === "exito" ? t("Descargar otra vez", "Download again") : t("Descargar GLB", "Download GLB")}</Button>
        <Button variant="outline" onClick={openInfo}>{t("Qué lleva el archivo", "What's in the file")}</Button>
      </div>
    </>
  );
}

function GlbDialog({ open, close }: { open: boolean; close: () => void }) {
  const { t } = useT();
  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) close(); }}>
      <DialogContent className="sm:max-w-[460px]" style={{ borderRadius: 24, padding: 24 }}>
        <DialogHeader>
          <DialogTitle style={{ fontFamily: "var(--display)", fontSize: 26, fontWeight: 800 }}>{t("Qué lleva el GLB", "What's in the GLB")}</DialogTitle>
          <DialogDescription>{t("El archivo copia la escena; el Taller no cambia al exportar.", "The file copies the scene; the Taller doesn't change when exporting.")}</DialogDescription>
        </DialogHeader>
        <ul className="grid gap-2 text-sm">
          <li>• {t("Posición, giro y escala reales de cada pieza visible.", "Real position, rotation and scale of every visible piece.")}</li>
          <li>• {t("Medidas en metros: una mesa de 240 cm mide 2,40 en Blender.", "Sizes in metres: a 240 cm table measures 2.40 in Blender.")}</li>
          <li>• {t("Color base de cada material, en el mismo espacio de color.", "Base colour of every material, in the same colour space.")}</li>
          <li>• {t("Sin luces, sin cielo HDRI y sin piezas ocultas.", "No lights, no HDRI sky and no hidden pieces.")}</li>
        </ul>
        <DialogFooter><Button onClick={close}>{t("Entendido", "Got it")}</Button></DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function App() {
  const m = useMockup();
  const { reduced, profile } = useMotionProfile();
  const view = (m.view || "mesas") as View;
  const [lang, setLang] = React.useState<Lang>(memo.lang);
  const [hl, setHl] = React.useState<PropId | null>(null);
  const [added, setAdded] = React.useState<PropId[]>([]);
  const [, bump] = React.useReducer((x: number) => x + 1, 0);
  React.useEffect(() => () => { memo.lastView = view; }, [view]);
  React.useEffect(() => {
    const on = () => document.documentElement.toggleAttribute("data-oculto", document.hidden);
    document.addEventListener("visibilitychange", on);
    return () => document.removeEventListener("visibilitychange", on);
  }, []);
  const t = React.useCallback((es: string, en: string) => (lang === "en" ? en : es), [lang]);
  const go = (v: View) => { memo.lastView = view; m.set("view", v); };
  const prevIdx = ORDER.indexOf((memo.lastView || view) as View), idx = ORDER.indexOf(view);
  const dir = memo.lastView ? Math.sign(idx - prevIdx) || 1 : 1;
  return (
    <LangCtx.Provider value={{ lang, t }}>
      <style>{CSS}</style>
      <div className="taller" lang={lang}>
        <header className="cabecera">
          <span className="marca"><Balloon /> Pictures</span>
          <span className="ruta">{t("Taller 3D · Fondos y muebles · Salón jardín, cumpleaños de Sofía", "3D Taller · Backdrops & furniture · Garden hall, Sofía's birthday")}</span>
          <div className="idioma" role="group" aria-label={t("Idioma", "Language")}>
            {(["es", "en"] as Lang[]).map((l) => (
              <button key={l} type="button" aria-pressed={lang === l} onClick={() => { memo.lang = l; setLang(l); }}>{l.toUpperCase()}</button>
            ))}
          </div>
        </header>
        <div className="obra">
          <Stage view={view} state={m.state} hl={hl} props={added} />
          <RoomMap view={view} go={go} />
          <motion.aside className="ficha" aria-label={t("Ficha de trabajo", "Work sheet")}
            initial={reduced ? false : { opacity: 0, x: 70 * dir, rotate: 2.5 * dir }} animate={{ opacity: 1, x: 0, rotate: 0 }}
            transition={reduced ? { duration: 0 } : { ...SPRINGS[profile], delay: 0.12 }}>
            {view === "mesas" && <MesasView state={m.state} go={go} />}
            {view === "inspector" && <InspectorView state={m.state} go={go} onChange={bump} />}
            {view === "backing" && <BackingView state={m.state} setHl={setHl} added={added} onAdd={(p) => setAdded((a) => (a.includes(p) ? a : [...a, p].slice(-3)))} />}
            {view === "lista" && <ListaView state={m.state} go={go} />}
            {view === "exportar" && <ExportView state={m.state} openInfo={() => m.set("scene", "glb")} />}
          </motion.aside>
        </div>
        <GlbDialog open={m.scene === "glb"} close={() => m.set("scene", "")} />
      </div>
    </LangCtx.Provider>
  );
}

mountMockup(App, {
  title: "Taller esenciales · B · Cámara de salón",
  motion: "expressive",
  views: [
    { id: "mesas", label: "Mesas (tarjetas por tipo)" }, { id: "inspector", label: "Inspector de mesa" }, { id: "backing", label: "Backing" },
    { id: "lista", label: "Lista de compras" }, { id: "exportar", label: "Exportar GLB" },
  ],
  states: [
    { id: "normal", label: "Normal" }, { id: "cargando", label: "Cargando" }, { id: "vacio", label: "Vacío" }, { id: "error", label: "Error" },
    { id: "exito", label: "Éxito" }, { id: "capacidad", label: "Capacidad excedida" }, { id: "asistente", label: "Cambio del asistente" },
  ],
  scenes: [{ id: "", label: "Ninguno" }, { id: "glb", label: "Qué lleva el GLB" }],
});
