// Shared mock data and building blocks for the four Taller 3D proposals (2026-11-17).
// Everything here is MOCK: one classic arch of real Sempertex products (R-12 in 970 Reflex Dorado, 080 Fashion Negro,
// 005 Fashion Blanco; every colour exists in R-12 in contracts/domain/v1/sempertex/tabla-color.json). The viewer picture is a
// Cycles render of that arch (pictures-infra/boceto-lab-2/estructuras-3d), the catalogue cards use real renders and the
// Sempertex reference photos already shipped in public/. Counts are illustrative and add up (28 quartets x 4 = 112).
import * as React from "react";
import { motion } from "motion/react";
import {
  Box, Camera, ChevronDown, ChevronRight, CircleHelp, Download, Eye, EyeOff, Hand, House, Layers, MousePointer2,
  MoveVertical, Plus, Redo2, RotateCw, Ruler, Scan, Search, ShoppingCart, Sparkles, Undo2,
} from "lucide-react";
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@bitacora/ui/components/ui/breadcrumb";
import { Button } from "@bitacora/ui/components/ui/button";
import { Input } from "@bitacora/ui/components/ui/input";
import { Slider } from "@bitacora/ui/components/ui/slider";
import { Skeleton } from "@bitacora/ui/components/ui/skeleton";
import { useMockup } from "@kit/mockup";
import fotoVisor from "./img/visor-arco-clasico.jpg";
import imgArcoClasico from "./img/arco-clasico.jpg";
import imgArcoOrganico from "./img/arco-organico.jpg";
import imgSemiColOrg from "./img/semiarco-columna-organico.jpg";
import imgSemiColCla from "./img/semiarco-columna-clasico.jpg";
import imgSemiOrg from "./img/semiarco-organico.jpg";
import imgRueda from "./img/rueda.jpg";
import imgIdeaAro from "./img/idea-aro-blanco-dorado-nude.jpg";
import imgIdeaGuirnalda from "./img/idea-guirnalda-salvia-flores.jpg";
import imgIdeaNavidad from "./img/idea-aro-navideno-salvia.jpg";
import imgIdeaSemiarco from "./img/idea-semiarco-reflex.jpg";

// ---------------------------------------------------------------------------------------------------------------- data

export type Codigo = "970" | "080" | "005";
/** Real Sempertex references (code, full name, balloon colour from tabla-color.json). */
export const COLORES: Record<Codigo, { nombre: string; hex: string; acabado: string }> = {
  "970": { nombre: "Reflex Dorado", hex: "#a08344", acabado: "cromado" },
  "080": { nombre: "Fashion Negro", hex: "#1b1b1b", acabado: "mate" },
  "005": { nombre: "Fashion Blanco", hex: "#ffffff", acabado: "mate" },
};
export const ESCENA = { nombre: "Arco clásico dorado", sala: "6 × 5 × 3,2 m", piezas: 1, globos: 112 };
export const PIEZA = { nombre: "Arco clásico", tipo: "Arco · clásico de cuartetos", ancho: "2,6 m", alto: "2,45 m", formato: "R-12", inflado: "25 cm", cuartetos: 28, globos: 112, patron: "Espiral" };
export const LISTA: ReadonlyArray<{ cantidad: number; formato: string; codigo: Codigo }> = [
  { cantidad: 48, formato: "R-12", codigo: "970" },
  { cantidad: 32, formato: "R-12", codigo: "080" },
  { cantidad: 32, formato: "R-12", codigo: "005" },
];
/** Quartet 14 (the crown of the arch) and its four balloons. */
export const CUARTETO = { nombre: "Cuarteto 14", posicion: "corona del arco", globos: ["970", "080", "970", "005"] as Codigo[] };
export const GLOBO_ELEGIDO = 2; // 1-based: balloon 2 of quartet 14

export const FORMAS: ReadonlyArray<{ id: string; nombre: string; detalle: string; img: string }> = [
  { id: "arco-clasico", nombre: "Arco clásico", detalle: "Cuartetos en espiral", img: imgArcoClasico },
  { id: "arco-organico", nombre: "Arco orgánico", detalle: "Globos de varios tamaños", img: imgArcoOrganico },
  { id: "semiarco-columna-org", nombre: "Semiarco y columna", detalle: "Orgánico", img: imgSemiColOrg },
  { id: "semiarco-columna-cla", nombre: "Semiarco y columna", detalle: "Clásico", img: imgSemiColCla },
  { id: "semiarco-org", nombre: "Semiarco", detalle: "Orgánico", img: imgSemiOrg },
  { id: "rueda", nombre: "Aro con base", detalle: "Orgánico", img: imgRueda },
];
export const IDEAS: ReadonlyArray<{ nombre: string; img: string }> = [
  { nombre: "Aro blanco, dorado y nude", img: imgIdeaAro },
  { nombre: "Guirnalda verde salvia con flores", img: imgIdeaGuirnalda },
  { nombre: "Aro navideño verde salvia", img: imgIdeaNavidad },
  { nombre: "Semiarco orgánico con reflex", img: imgIdeaSemiarco },
];
export const SECCIONES_ANADIR = ["Estructuras", "Decoraciones", "Utilería", "Ideas"] as const;

export type Estado = "escena" | "pieza" | "modulo" | "forma" | "vacia";
export const ESTADOS = [
  { id: "escena", label: "Escena, nada elegido" },
  { id: "pieza", label: "Estructura elegida" },
  { id: "modulo", label: "Módulo › globo elegido" },
  { id: "forma", label: "Crear forma guiada" },
  { id: "vacia", label: "Escena vacía" },
];
export const VISTAS = [
  { id: "escritorio", label: "Escritorio 1440" },
  { id: "tablet", label: "Tablet 820 (vertical)" },
];
export function useEstado(): { estado: Estado; tablet: boolean } {
  const { view, state } = useMockup();
  return { estado: (state || "escena") as Estado, tablet: view === "tablet" };
}

// ------------------------------------------------------------------------------------------------------------ frames

/** Desktop 1440 x 900 or tablet 820 x 1180, drawn at real size; the page scrolls when the window is smaller. */
export function Marco({ tablet, nota, children }: { tablet: boolean; nota: string; children: React.ReactNode }) {
  const w = tablet ? 820 : 1440;
  const h = tablet ? 1180 : 900;
  return (
    <div className="min-h-[calc(100svh-var(--mockup-bar-h))] overflow-auto bg-muted px-6 py-6">
      <p className="mx-auto mb-3 text-xs text-muted-foreground" style={{ width: w }}>{nota} · {w} × {h} px · datos de ejemplo</p>
      <div className="relative mx-auto overflow-hidden rounded-md border border-border bg-card text-foreground shadow-sm" style={{ width: w, height: h }} data-marco>
        {children}
      </div>
    </div>
  );
}

const PESTANAS_APP = ["Chat", "Contador", "Calculadora", "Taller 3D", "Boceto"];
/** The app's real tool tabs (PestanasTaller) — the left block of the single 48 px row on desktop, its own row on tablet. */
export function PestanasApp({ tablet }: { tablet: boolean }) {
  return (
    <nav aria-label="Herramientas" className={`flex h-12 shrink-0 border-b border-border bg-card ${tablet ? "w-full" : "w-[24rem] border-r"}`}>
      {PESTANAS_APP.map((p) => (
        <a key={p} href="#" aria-current={p === "Taller 3D" ? "page" : undefined} onClick={(e) => e.preventDefault()}
          className={`flex flex-1 items-center justify-center border-t-[3px] px-1 text-[13px] font-semibold ${p === "Taller 3D" ? "border-t-foreground text-foreground" : "border-t-transparent text-muted-foreground hover:text-foreground"}`}>
          {p}
        </a>
      ))}
    </nav>
  );
}
export function Avatar() {
  return <span aria-label="Tu cuenta" className="grid size-8 shrink-0 place-items-center rounded-full bg-secondary text-xs font-semibold text-foreground">DT</span>;
}

// ------------------------------------------------------------------------------------------------------------ pieces

export function Muestra({ codigo, size = 18, elegida = false }: { codigo: Codigo; size?: number; elegida?: boolean }) {
  const c = COLORES[codigo];
  const brillo = codigo === "970" ? "radial-gradient(circle at 32% 30%, #f6e3a6 0, #c9a24f 32%, #7a5b22 100%)" : codigo === "080" ? "radial-gradient(circle at 32% 30%, #6b6b6b 0, #1b1b1b 45%, #000 100%)" : "radial-gradient(circle at 32% 30%, #fff 0, #f4f2ef 55%, #d9d4cd 100%)";
  return (
    <span aria-hidden className={`inline-block shrink-0 rounded-full ${elegida ? "ring-2 ring-foreground ring-offset-2 ring-offset-card" : "ring-1 ring-black/15"}`}
      style={{ width: size, height: size, background: brillo }} title={`${codigo} ${c.nombre}`} />
  );
}
export function NombreColor({ codigo, formato }: { codigo: Codigo; formato?: string }) {
  return (
    <span className="inline-flex min-w-0 items-center gap-2">
      <Muestra codigo={codigo} />
      <span className="truncate">{formato ? `${formato} · ` : ""}{COLORES[codigo].nombre}</span>
      <span className="font-mono text-xs text-muted-foreground">{codigo}</span>
    </span>
  );
}

/** Lines of the shopping list, numbers right-aligned in tabular figures. */
export function FilasLista({ compacta = false }: { compacta?: boolean }) {
  return (
    <ul className="flex flex-col">
      {LISTA.map((l) => (
        <li key={l.codigo} className={`flex items-center gap-3 border-b border-border last:border-b-0 ${compacta ? "py-1.5 text-[13px]" : "py-2 text-sm"}`}>
          <span className="min-w-0 flex-1"><NombreColor codigo={l.codigo} formato={l.formato} /></span>
          <span className="font-mono tabular-nums">{l.cantidad}</span>
        </li>
      ))}
      <li className={`flex items-center justify-between pt-2 font-medium ${compacta ? "text-[13px]" : "text-sm"}`}><span>Total</span><span className="font-mono tabular-nums">{ESCENA.globos} globos</span></li>
    </ul>
  );
}

/** Structure > module > balloon, the hierarchy the engine adds; each crumb selects that level. */
export function Migas({ estado, compacta = false }: { estado: Estado; compacta?: boolean }) {
  const niveles = estado === "modulo" ? ["Escena", PIEZA.nombre, CUARTETO.nombre, `Globo ${GLOBO_ELEGIDO}`] : estado === "pieza" ? ["Escena", PIEZA.nombre] : ["Escena"];
  return (
    <Breadcrumb aria-label="Nivel de selección">
      <BreadcrumbList className={compacta ? "text-[13px]" : "text-sm"}>
        {niveles.map((n, i) => (
          <React.Fragment key={n}>
            {i > 0 && <BreadcrumbSeparator />}
            <BreadcrumbItem>
              {i === niveles.length - 1 ? <BreadcrumbPage className="font-medium">{n}</BreadcrumbPage> : <BreadcrumbLink href="#" onClick={(e) => e.preventDefault()}>{n}</BreadcrumbLink>}
            </BreadcrumbItem>
          </React.Fragment>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  );
}

// ------------------------------------------------------------------------------------------------------------ viewer

/**
 * The 3D viewer. The picture is "cover"-sized inside a size container, so overlays placed in % of the picture stay on the
 * balloons at any frame size. Selection is drawn as in the engine: a thin box for a structure, a ring for a module and a
 * dot for the chosen balloon. «forma» shows the ghost sketch of the guided flow over an empty room.
 */
export function Visor({ estado, children, etiqueta = true }: { estado: Estado; children?: React.ReactNode; etiqueta?: boolean }) {
  const vacia = estado === "vacia" || estado === "forma";
  return (
    <div className="relative h-full w-full overflow-hidden bg-[#efe6da]" style={{ containerType: "size" }} role="img"
      aria-label={vacia ? "Visor 3D: sala vacía" : "Visor 3D: arco clásico de globos dorados, negros y blancos"}>
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2" style={{ width: "max(100cqw, 133.4cqh)", aspectRatio: "1100 / 825" }}>
        {vacia ? <SalaVacia /> : <img src={fotoVisor} alt="" className="absolute inset-0 h-full w-full select-none" draggable={false} />}
        {estado === "pieza" && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.18 }}
            className="absolute rounded-sm border border-dashed border-foreground/70" style={{ left: "20.5%", top: "12.5%", width: "59%", height: "77%" }}>
            {etiqueta && <span className="absolute -top-7 left-0 whitespace-nowrap rounded bg-foreground px-2 py-0.5 text-xs font-medium text-background">{PIEZA.nombre} · {PIEZA.ancho} × {PIEZA.alto}</span>}
          </motion.div>
        )}
        {estado === "modulo" && (
          <>
            <div className="absolute bg-black/25" style={{ inset: 0, maskImage: "radial-gradient(ellipse 7% 8% at 52.5% 20%, transparent 98%, #000 100%)", WebkitMaskImage: "radial-gradient(ellipse 7% 8% at 52.5% 20%, transparent 98%, #000 100%)" }} />
            <motion.div initial={{ scale: 1.15, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: "spring", stiffness: 380, damping: 30 }}
              className="absolute rounded-full border-2 border-white shadow-[0_0_0_1px_rgba(0,0,0,.35)]" style={{ left: "45.5%", top: "12%", width: "14%", height: "16%" }} />
            <span className="absolute size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-foreground" style={{ left: "55%", top: "17.5%" }} aria-hidden />
            {etiqueta && <span className="absolute whitespace-nowrap rounded bg-foreground px-2 py-0.5 text-xs font-medium text-background" style={{ left: "45.5%", top: "5.5%" }}>{CUARTETO.nombre} · globo {GLOBO_ELEGIDO}</span>}
          </>
        )}
        {estado === "forma" && <BocetoFantasma />}
      </div>
      {children}
    </div>
  );
}

function SalaVacia() {
  return (
    <div className="absolute inset-0" style={{ background: "linear-gradient(180deg,#f3ebe0 0%,#eee4d6 76%,#e3d7c6 76.3%,#ddd0bd 100%)" }}>
      <div className="absolute inset-x-0" style={{ top: "76%", height: 1, background: "rgba(0,0,0,.08)" }} />
      <svg className="absolute inset-0 h-full w-full" viewBox="0 0 1100 825" aria-hidden>
        {Array.from({ length: 12 }, (_, i) => <line key={i} x1={i * 100} y1={630} x2={550 + (i * 100 - 550) * 1.9} y2={825} stroke="rgba(0,0,0,.06)" />)}
      </svg>
    </div>
  );
}

/** Ghost sketch of a classic arch 2,6 x 2,45 m with its measure lines (guided shape flow, step 2). */
function BocetoFantasma() {
  const q = Array.from({ length: 28 }, (_, i) => i);
  // half-ellipse-ish arch from (300,630) up to (550,160) down to (800,630) in picture coordinates
  const punto = (t: number) => {
    const a = Math.PI * (1 - t);
    return { x: 550 + 250 * Math.cos(a), y: 630 - 470 * Math.pow(Math.sin(a), 0.55) };
  };
  return (
    <motion.svg className="absolute inset-0 h-full w-full" viewBox="0 0 1100 825" aria-hidden initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
      {q.map((i) => {
        const p = punto(i / 27);
        return <circle key={i} cx={p.x} cy={p.y} r={21} fill="rgba(28,20,37,.06)" stroke="rgba(28,20,37,.55)" strokeDasharray="4 4" strokeWidth={1.5} />;
      })}
      <g stroke="rgba(28,20,37,.7)" strokeWidth={1.2} fill="none">
        <line x1={279} y1={690} x2={821} y2={690} /><line x1={279} y1={680} x2={279} y2={700} /><line x1={821} y1={680} x2={821} y2={700} />
        <line x1={870} y1={139} x2={870} y2={651} /><line x1={860} y1={139} x2={880} y2={139} /><line x1={860} y1={651} x2={880} y2={651} />
      </g>
      <g fontFamily="var(--ui-font-sans)" fontSize={20} fill="#1c1425" fontWeight={600}>
        <rect x={505} y={676} width={90} height={28} rx={6} fill="#fff" /><text x={550} y={697} textAnchor="middle">2,6 m</text>
        <rect x={880} y={381} width={90} height={28} rx={6} fill="#fff" /><text x={925} y={402} textAnchor="middle">2,45 m</text>
      </g>
    </motion.svg>
  );
}

/** Floating viewer tools: the current four drag tools, the fixed views, measures, realistic mode and frame-all. */
export function HerramientasVisor({ vertical = false, compacta = false }: { vertical?: boolean; compacta?: boolean }) {
  const [h, setH] = React.useState("mover");
  const [v, setV] = React.useState("3D");
  const herramientas = [
    { id: "mover", label: "Elegir y mover", icon: <MousePointer2 /> },
    { id: "girar", label: "Girar", icon: <RotateCw /> },
    { id: "altura", label: "Subir o bajar", icon: <MoveVertical /> },
    { id: "camara", label: "Mover la vista", icon: <Hand /> },
  ];
  return (
    <div role="toolbar" aria-label="Herramientas del visor" className={`pointer-events-auto flex items-center gap-0.5 rounded-lg border border-border bg-card p-1 shadow-sm ${vertical ? "flex-col" : ""}`}>
      {herramientas.map((t) => (
        <Button key={t.id} size="icon" variant={h === t.id ? "secondary" : "ghost"} aria-pressed={h === t.id} aria-label={t.label} title={t.label} onClick={() => setH(t.id)}
          className={h === t.id ? "bg-foreground text-background hover:bg-foreground/90" : ""}>{t.icon}</Button>
      ))}
      <span aria-hidden className={vertical ? "my-1 h-px w-5 bg-border" : "mx-1 h-5 w-px bg-border"} />
      {!compacta && ["Frente", "Arriba", "3D"].map((x) => (
        <Button key={x} size="sm" variant={v === x ? "secondary" : "ghost"} aria-pressed={v === x} onClick={() => setV(x)} className="px-2 text-xs">{x}</Button>
      ))}
      {!compacta && <span aria-hidden className={vertical ? "my-1 h-px w-5 bg-border" : "mx-1 h-5 w-px bg-border"} />}
      <Button size="icon" variant="ghost" aria-label="Mostrar medidas" title="Mostrar medidas"><Ruler /></Button>
      <Button size="icon" variant="ghost" aria-label="Modo realista" title="Modo realista"><Sparkles /></Button>
      <Button size="icon" variant="ghost" aria-label="Encuadrar todo" title="Encuadrar todo"><Scan /></Button>
    </div>
  );
}

export function ContadorVisor() {
  return <span className="rounded-md border border-border bg-card px-2.5 py-1 text-xs text-muted-foreground shadow-sm"><b className="font-mono font-medium text-foreground">1</b> pieza · <b className="font-mono font-medium text-foreground">112</b> globos</span>;
}

// ------------------------------------------------------------------------------------------------------- panels: add

/** Catalogue cards of the current «Añadir» panel, with the real renders and Sempertex reference photos. */
export function TarjetasCatalogo({ columnas = 2, ideas = false, tam = "md" }: { columnas?: number; ideas?: boolean; tam?: "sm" | "md" }) {
  const items = ideas ? IDEAS.map((i) => ({ id: i.nombre, nombre: i.nombre, detalle: "Idea de sempertex.com", img: i.img })) : FORMAS.slice(0, 4);
  return (
    <ul className="grid gap-2" style={{ gridTemplateColumns: `repeat(${columnas}, minmax(0, 1fr))` }}>
      {items.map((f) => (
        <li key={f.id + f.detalle}>
          <button type="button" className="group flex w-full flex-col gap-1.5 rounded-lg border border-border bg-card p-1.5 text-left hover:border-foreground/40 focus-visible:outline-2 focus-visible:outline-ring">
            <span className={`block w-full overflow-hidden rounded-md bg-muted ${tam === "sm" ? "h-16" : "h-[84px]"}`}><img src={f.img} alt="" className="h-full w-full object-cover transition-transform duration-200 group-hover:scale-[1.03]" /></span>
            <span className="px-0.5 text-[13px] font-medium leading-tight">{f.nombre}</span>
            <span className="px-0.5 text-xs leading-tight text-muted-foreground">{f.detalle}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}

export function BuscarCatalogo({ placeholder = "Buscar: columna, flor, dorado…" }: { placeholder?: string }) {
  return (
    <div className="relative">
      <Search aria-hidden className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
      <Input aria-label="Buscar en el catálogo" placeholder={placeholder} className="h-9 pl-8" />
    </div>
  );
}

/** Rest of «Añadir» kept as entry points: new adjustable pieces, loose balloons, your library, search by photo, filters. */
export function OrigenesAnadir() {
  const filas = ["Nuevas · ajustables", "Globos sueltos", "De tu biblioteca", "Buscar por foto", "Celebración y temática"];
  return (
    <ul className="flex flex-col">
      {filas.map((f) => (
        <li key={f}><button type="button" className="flex h-9 w-full items-center justify-between rounded-md px-2 text-left text-[13px] hover:bg-muted">{f}<ChevronRight aria-hidden className="size-4 text-muted-foreground" /></button></li>
      ))}
    </ul>
  );
}

// ----------------------------------------------------------------------------------------------- panels: properties

export function Campo({ label, children, valor }: { label: string; children?: React.ReactNode; valor?: string }) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline justify-between text-[13px]"><span className="text-muted-foreground">{label}</span>{valor && <span className="font-mono tabular-nums">{valor}</span>}</div>
      {children}
    </div>
  );
}
export function Seccion({ titulo, children, accion }: { titulo: string; children: React.ReactNode; accion?: React.ReactNode }) {
  return (
    <section className="flex flex-col gap-3 border-b border-border px-4 py-4 last:border-b-0">
      <div className="flex items-center justify-between"><h3 className="text-[13px] font-semibold">{titulo}</h3>{accion}</div>
      {children}
    </section>
  );
}
function Segmentos({ opciones, valor }: { opciones: string[]; valor: string }) {
  const [v, setV] = React.useState(valor);
  return (
    <div role="radiogroup" className="grid gap-1 rounded-lg bg-muted p-[3px]" style={{ gridTemplateColumns: `repeat(${opciones.length}, minmax(0,1fr))` }}>
      {opciones.map((o) => (
        <button key={o} type="button" role="radio" aria-checked={v === o} onClick={() => setV(o)}
          className={`h-7 rounded-md text-xs font-medium ${v === o ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>{o}</button>
      ))}
    </div>
  );
}
function ColoresEnOrden() {
  return (
    <div className="flex flex-col gap-1.5">
      {(["970", "080", "970", "005"] as Codigo[]).map((c, i) => (
        <button key={i} type="button" className="flex h-9 items-center gap-2 rounded-md border border-border px-2 text-left text-[13px] hover:bg-muted">
          <span className="w-4 font-mono text-xs text-muted-foreground">{i + 1}</span><NombreColor codigo={c} /><ChevronDown aria-hidden className="ml-auto size-4 text-muted-foreground" />
        </button>
      ))}
    </div>
  );
}

/** The structure's properties: what the Inspector and «Editar sola» split today, in one place. */
export function PropiedadesPieza({ denso = false }: { denso?: boolean }) {
  return (
    <>
      <Seccion titulo="Medidas">
        <Campo label="Ancho" valor={PIEZA.ancho}><Slider defaultValue={[52]} aria-label="Ancho" /></Campo>
        <Campo label="Alto" valor={PIEZA.alto}><Slider defaultValue={[49]} aria-label="Alto" /></Campo>
      </Seccion>
      <Seccion titulo="Globos y patrón">
        <div className="grid grid-cols-2 gap-2">
          <Campo label="Formato"><Segmentos opciones={["R-9", "R-12"]} valor="R-12" /></Campo>
          <Campo label="Inflado" valor={PIEZA.inflado} />
        </div>
        <Campo label="Patrón"><Segmentos opciones={["Espiral", "Franjas", "Liso"]} valor="Espiral" /></Campo>
        {!denso && <Campo label="Colores en orden"><ColoresEnOrden /></Campo>}
      </Seccion>
      <Seccion titulo="Lugar">
        <Campo label="Dónde va"><Segmentos opciones={["Piso", "Pared", "Techo", "Suelta"]} valor="Piso" /></Campo>
        <p className="text-xs text-muted-foreground">En el piso · arrástrala en el visor o usa las flechas.</p>
      </Seccion>
      {!denso && (
        <Seccion titulo="Decoraciones colgadas" accion={<Button size="sm" variant="ghost"><Plus />Colgar una</Button>}>
          <p className="text-[13px] text-muted-foreground">Nada colgado todavía.</p>
        </Seccion>
      )}
    </>
  );
}

/** The new module level: the quartet, its four balloons and the scope of a colour change. */
export function PropiedadesModulo({ compacta = false }: { compacta?: boolean }) {
  return (
    <>
      <Seccion titulo={`${CUARTETO.nombre} · ${CUARTETO.posicion}`}>
        <div className="flex items-center gap-3">
          <div className="grid grid-cols-2 gap-1 rounded-lg bg-muted p-2">
            {CUARTETO.globos.map((c, i) => <Muestra key={i} codigo={c} size={compacta ? 22 : 26} elegida={i + 1 === GLOBO_ELEGIDO} />)}
          </div>
          <p className="text-xs leading-snug text-muted-foreground">4 globos R-12. Toca uno en el visor o aquí para cambiar solo ese.</p>
        </div>
      </Seccion>
      <Seccion titulo={`Globo ${GLOBO_ELEGIDO}`}>
        <div className="flex items-center justify-between text-[13px]"><NombreColor codigo="080" formato="R-12" /><span className="text-xs text-muted-foreground">25 cm</span></div>
        <div className="flex flex-wrap gap-2" role="radiogroup" aria-label="Color del globo">
          {(["970", "080", "005"] as Codigo[]).map((c) => (
            <button key={c} type="button" role="radio" aria-checked={c === "080"} aria-label={`${c} ${COLORES[c].nombre}`} className="rounded-full p-0.5"><Muestra codigo={c} size={28} elegida={c === "080"} /></button>
          ))}
          <Button size="sm" variant="outline" className="h-8">Otro color…</Button>
        </div>
      </Seccion>
      <Seccion titulo="Aplicar el cambio a">
        <Segmentos opciones={["Este globo", "Este cuarteto", "Cada 2", "Todos"]} valor="Este globo" />
        <p className="text-xs text-muted-foreground">«Todos» cambia el globo 2 en los 28 cuartetos.</p>
      </Seccion>
    </>
  );
}

/** Guided shape flow: pick → ghost → measures → create. `paso` 1 lists the shapes, 2 shows the measures. */
export function FormaGuiada({ paso = 2, columnas = 2 }: { paso?: 1 | 2; columnas?: number }) {
  return (
    <div className="flex flex-col">
      <ol className="flex gap-1 px-4 pt-4 text-xs" aria-label="Pasos">
        {["Forma", "Medidas", "Globos"].map((p, i) => (
          <li key={p} className={`flex flex-1 flex-col gap-1 ${i + 1 <= paso ? "text-foreground" : "text-muted-foreground"}`}>
            <span className={`h-1 rounded-full ${i + 1 <= paso ? "bg-foreground" : "bg-muted"}`} /><span>{i + 1}. {p}</span>
          </li>
        ))}
      </ol>
      {paso === 1 ? (
        <div className="p-4"><TarjetasCatalogo columnas={columnas} /></div>
      ) : (
        <>
          <div className="flex items-center gap-3 px-4 pt-4">
            <img src={imgArcoClasico} alt="" className="size-12 rounded-md object-cover" />
            <div className="min-w-0 flex-1"><p className="text-sm font-medium">Arco clásico</p><p className="text-xs text-muted-foreground">Cuartetos en espiral</p></div>
            <Button size="sm" variant="ghost">Cambiar</Button>
          </div>
          <Seccion titulo="Medidas">
            <Campo label="Ancho entre patas" valor="2,6 m"><Slider defaultValue={[52]} aria-label="Ancho entre patas" /></Campo>
            <Campo label="Alto" valor="2,45 m"><Slider defaultValue={[49]} aria-label="Alto" /></Campo>
            <p className="text-xs text-muted-foreground">El boceto del visor sigue a las medidas; nada se arma hasta «Crear».</p>
          </Seccion>
          <Seccion titulo="Globos">
            <Campo label="Formato"><Segmentos opciones={["R-9", "R-12"]} valor="R-12" /></Campo>
            <div className="flex items-center justify-between text-[13px]"><span className="text-muted-foreground">Resultado</span><span><b className="font-mono font-medium">28</b> cuartetos · <b className="font-mono font-medium">112</b> globos</span></div>
          </Seccion>
        </>
      )}
    </div>
  );
}

/** The AI request box (scope chip + prompt), as in ComposicionIA. */
export function PedirIA({ alcance = "Escena entera", compacta = false }: { alcance?: string; compacta?: boolean }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center gap-2 text-xs text-muted-foreground"><Sparkles aria-hidden className="size-3.5" />La IA cambiará: <span className="rounded-md border border-border px-1.5 py-0.5 text-foreground">{alcance}</span></div>
      <div className="flex items-end gap-2 rounded-lg border border-border bg-card p-2">
        <textarea rows={compacta ? 1 : 2} aria-label="Qué quieres cambiar en la escena" placeholder="Pídele un cambio… «copia esta columna al otro lado»" className="min-h-0 flex-1 resize-none bg-transparent text-[13px] outline-none placeholder:text-muted-foreground" />
        <Button size="icon" variant="ghost" aria-label="Adjuntar una foto de la decoración"><Camera /></Button>
        <Button size="sm" variant="outline">Enviar</Button>
      </div>
    </div>
  );
}

export function EscenaVacia({ onAnadir }: { onAnadir?: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 px-6 py-8 text-center">
      <Box aria-hidden className="size-6 text-muted-foreground" />
      <p className="max-w-64 text-sm">La sala está vacía: añade una pieza o crea una forma guiada.</p>
      <div className="flex gap-2"><Button size="sm" onClick={onAnadir}><Plus />Crear forma</Button><Button size="sm" variant="outline">Ver ideas</Button></div>
    </div>
  );
}

export function CargandoLista() {
  return <div className="flex flex-col gap-2 p-4"><Skeleton className="h-4 w-2/3" /><Skeleton className="h-4 w-1/2" /><Skeleton className="h-4 w-3/5" /></div>;
}

// --------------------------------------------------------------------------------------------- scene-level controls

export function NombreEscena({ compacta = false }: { compacta?: boolean }) {
  return (
    <button type="button" className="flex min-w-0 items-center gap-1 rounded-md px-1.5 py-1 hover:bg-muted" aria-haspopup="menu" aria-label={`Escena: ${ESCENA.nombre}. Opciones de la escena`}>
      <span className={`truncate font-semibold ${compacta ? "text-[13px]" : "text-sm"}`}>{ESCENA.nombre}</span><ChevronDown aria-hidden className="size-4 text-muted-foreground" />
    </button>
  );
}
export function EstadoGuardado() {
  return <span className="whitespace-nowrap text-xs text-muted-foreground">Guardado hace 1 min</span>;
}
export function DeshacerRehacer() {
  return (
    <div className="flex gap-0.5">
      <Button size="icon" variant="ghost" aria-label="Deshacer (Ctrl+Z)" title="Deshacer (Ctrl+Z)"><Undo2 /></Button>
      <Button size="icon" variant="ghost" aria-label="Rehacer (Ctrl+Y)" title="Rehacer (Ctrl+Y)"><Redo2 /></Button>
    </div>
  );
}
export function BotonFoto({ solo = false }: { solo?: boolean }) {
  return <Button variant="outline" size={solo ? "icon" : "default"} aria-label="Foto realista" title="Foto realista"><Camera />{!solo && "Foto realista"}</Button>;
}
export function BotonExportar() {
  return <Button variant="ghost" size="icon" aria-label="Exportar: PNG 3000 px o modelo GLB" title="Exportar (PNG 3000 px · GLB)"><Download /></Button>;
}
export function BotonLista({ primaria = true, corto = false }: { primaria?: boolean; corto?: boolean }) {
  return (
    <Button variant={primaria ? "default" : "outline"} aria-label={`Lista de compra: ${ESCENA.globos} globos`}>
      <ShoppingCart />{!corto && <span>Lista de compra ·</span>}<span className="font-mono">{ESCENA.globos}</span>
    </Button>
  );
}
export function BotonAyuda() {
  return <Button variant="ghost" size="icon" aria-label="Ayuda y atajos de teclado" title="Ayuda y atajos"><CircleHelp /></Button>;
}

/** A row of the scene outline (structure, module or balloon) with show/hide. */
export function FilaArbol({ nivel, nombre, detalle, elegida = false, abierta, oculta = false, icono }: { nivel: number; nombre: string; detalle?: string; elegida?: boolean; abierta?: boolean; oculta?: boolean; icono?: React.ReactNode }) {
  return (
    <li>
      <div className={`group flex h-8 items-center gap-1.5 rounded-md pr-1 text-[13px] ${elegida ? "bg-secondary font-medium text-foreground" : "text-foreground/85 hover:bg-muted"}`} style={{ paddingLeft: 6 + nivel * 14 }}>
        <span className="grid size-4 place-items-center text-muted-foreground">{abierta === undefined ? null : abierta ? <ChevronDown className="size-3.5" aria-hidden /> : <ChevronRight className="size-3.5" aria-hidden />}</span>
        {icono}
        <button type="button" className="min-w-0 flex-1 truncate text-left" aria-current={elegida || undefined}>{nombre}</button>
        {detalle && <span className="font-mono text-xs text-muted-foreground tabular-nums">{detalle}</span>}
        <button type="button" aria-label={oculta ? `Mostrar ${nombre}` : `Ocultar ${nombre}`} className="grid size-6 place-items-center rounded text-muted-foreground opacity-0 hover:bg-card group-hover:opacity-100 focus-visible:opacity-100">
          {oculta ? <EyeOff className="size-3.5" aria-hidden /> : <Eye className="size-3.5" aria-hidden />}
        </button>
      </div>
    </li>
  );
}

/** Scene > structure > modules > balloons, opened down to the current selection. */
export function ArbolEscena({ estado }: { estado: Estado }) {
  if (estado === "vacia" || estado === "forma") {
    return <ul className="flex flex-col"><FilaArbol nivel={0} nombre="Sala" detalle="6 × 5 m" icono={<House className="size-3.5 text-muted-foreground" aria-hidden />} /></ul>;
  }
  const abierto = estado === "modulo";
  return (
    <ul className="flex flex-col" aria-label="Piezas de la escena">
      <FilaArbol nivel={0} nombre="Sala" detalle="6 × 5 m" icono={<House className="size-3.5 text-muted-foreground" aria-hidden />} />
      <FilaArbol nivel={0} nombre={PIEZA.nombre} detalle="112" abierta={abierto || estado === "pieza"} elegida={estado === "pieza"} icono={<Layers className="size-3.5 text-muted-foreground" aria-hidden />} />
      {(abierto || estado === "pieza") && (
        <>
          <FilaArbol nivel={1} nombre="Cuartetos 1–13" detalle="52" abierta={false} />
          <FilaArbol nivel={1} nombre={CUARTETO.nombre} detalle="4" abierta={abierto} elegida={false} />
          {abierto && CUARTETO.globos.map((c, i) => (
            <FilaArbol key={i} nivel={2} nombre={`Globo ${i + 1} · ${COLORES[c].nombre}`} elegida={i + 1 === GLOBO_ELEGIDO} icono={<Muestra codigo={c} size={12} />} />
          ))}
          <FilaArbol nivel={1} nombre="Cuartetos 15–28" detalle="56" abierta={false} />
        </>
      )}
    </ul>
  );
}
