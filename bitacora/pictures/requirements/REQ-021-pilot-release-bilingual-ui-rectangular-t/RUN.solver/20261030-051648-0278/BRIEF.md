# Solucionador 20261030-051648-0278 — pictures REQ-021 (run pictures:REQ-021:r25)

Started 2026-10-30T05:16:48 by the durable engine's maintenance pass.

## Triggers

- `pictures:REQ-021:r25:resolution:4378ebb94f72d6922c89d601ee5db484` — resolution · CG-9: the conflict in src/components/tres-d/Biblioteca.tsx waits for a recorded resolution since 2026-10-30T04:38:35; no retry can settle it
- `pictures:REQ-021:r25:resolution:cacb3537cd9925be000ff500ae8a572c` — resolution · CG-9: the conflict in src/components/tres-d/Taller3D.tsx waits for a recorded resolution since 2026-10-30T04:38:35; no retry can settle it

## Resolution request 4378ebb94f72d6922c89d601ee5db484 (src/components/tres-d/Biblioteca.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/4378ebb94f72d6922c89d601ee5db484.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/4378ebb94f72d6922c89d601ee5db484.diff3`
- blobs: base `fcc3afaf781aab5664a58cd138b30c0ace78cdc7`, ours `7c0e4d1c09ce8d13ad0aab3efa45fc4bf86b8738`, theirs `e8730cad9bc8af6d0356dded08e957cd2de7cb3d` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "650f17a75fd1c08c1c5b8f19b8659dcd166c7a64", "ours": "2bfccbf3fed22a9cd8c37b1516ff0f349c466d90", "theirs": "685fc9c2a8663be3d093787da4262f2431a6c701"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/4378ebb94f72d6922c89d601ee5db484.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
"use client";

import { memo, useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import { ArrowLeft, Box, ClipboardCopy, ExternalLink, Eye, Plus, Replace, Trash2 } from "lucide-react";
import {
  BIBLIOTECA_FABRICA, OCASIONES, TIPOS_ITEM, contenidoDeEscena, copiarItem, escenaDeItem, filtrarBiblioteca, huellaConId, itemDeEscena, nombreGenerico,
  unirBiblioteca, validarItem, type ItemBiblioteca, type ProductosDeItem, type ResumenItem, type TipoItem,
} from "@/lib/globos3d/biblioteca";
import type { Escena, EscenaArmada } from "@/lib/globos3d/escena";
import { aplicarNombreDecoracion, aplicarNombresProducto } from "@/lib/globos3d/biblioteca-textos-ingles";
import { useTextosDecoracion, useTextosProducto } from "./textos-producto-contexto";
import { hexDeCodigo, miniaturaDecoracion, type Miniatura } from "@/lib/globos3d/decoraciones-escena";
import { descripcionParaCliente } from "@/lib/globos3d/descripcion-ficha";
import { urlTienda } from "@/lib/globos3d/utileria-catalogo";
import { nombreOcasion } from "@/lib/taller/taxonomia-celebraciones";
import { REVISADO_TIENDA } from "@/lib/globos3d/productos-tienda";
import { referenciaPorCodigo } from "@/lib/plan/referencia-sempertex";
import { MiniaturaDecoracion } from "./DecoracionesPequenas";
import { ACTIVO, BOTON, INACTIVO } from "./PanelFlor";
import { mostrarArmada } from "./armada-visor";
import { exigirLetraDeRotulos } from "./fuente-rotulos";
import type { EscenaGlobos } from "./escena-globos";
import { armarEnMotor, useMotorBiblioteca, type Armado } from "./biblioteca-cliente";
import { TarjetaReceta } from "./TarjetaReceta";
import { escenografiaEnTexto, type EscenografiaPorRepositorio } from "@/lib/catalogo/lista-por-repositorio";
import { ListaEscenografia, useEscenografiaPorRepositorio } from "./ListaEscenografia";
import { ProcedenciaDeItem } from "./ProcedenciaDeItem";
import { textoCantidadGlobosTaller, textoTaller, type IdiomaTaller } from "./textos/taller-marco";

/**
 * Pestaña **Biblioteca** de /3d: todo lo reutilizable del taller, cada cosa por separado (escenas, estructuras con sus
 * decoraciones, estructuras, decoraciones y utilería), con filtros y una ficha con la vista 3D, la lista exacta de
 * productos (globos con su producto de la tienda, utilería y, aparte, la escenografía) y de dónde viene. Lo de fábrica
 * sale del código (`biblioteca.ts`); lo que guarda el usuario vive en su navegador (biblioteca propia).
 */

// ----------------------------------------------------------------------------------------------------------
// Biblioteca propia (localStorage)
// ----------------------------------------------------------------------------------------------------------

const CLAVE_PROPIA = "taller3d:biblioteca-propia:v1";
const EVENTO_PROPIA = "taller3d:biblioteca-propia";
const TIPO_ESCENA = "escena" as const;
const TIPO_CONJUNTO = "conjunto" as const;
const TIPO_ESTRUCTURA = "estructura" as const;
const TIPO_DECORACION = "decoracion" as const;
const TIPO_UTILERIA = "utileria" as const;
const ERROR_ARMADO = "error" as const;
const SIN_PROPIOS: readonly ItemBiblioteca[] = [];
let lecturaPropia: { crudo: string | null; items: readonly ItemBiblioteca[] } = { crudo: null, items: SIN_PROPIOS };

function leerCrudo(): string | null {
  try { return window.localStorage.getItem(CLAVE_PROPIA); } catch { return null; }
}

/** Lo guardado, validado (lo que no cuadra se descarta). La misma lista mientras no cambie lo guardado. */
function propiosGuardados(): readonly ItemBiblioteca[] {
  const crudo = leerCrudo();
  if (crudo === lecturaPropia.crudo) return lecturaPropia.items;
  let items: ItemBiblioteca[] = [];
  try {
    const datos: unknown = crudo ? JSON.parse(crudo) : [];
    items = Array.isArray(datos) ? datos.map(validarItem).filter((x): x is ItemBiblioteca => x !== null) : [];
  } catch { items = []; }
  lecturaPropia = { crudo, items };
  return items;
}

function escribirPropios(items: readonly ItemBiblioteca[]): boolean {
  try {
    window.localStorage.setItem(CLAVE_PROPIA, JSON.stringify(items));
    window.dispatchEvent(new Event(EVENTO_PROPIA));
    return true;
  } catch { return false; }
}

/** Guarda un item en la biblioteca propia (si ya hay uno con ese id, lo reemplaza). `false` si el navegador no dejó. */
export function guardarPropio(item: ItemBiblioteca): boolean {
  return escribirPropios([...propiosGuardados().filter((i) => i.id !== item.id), { ...item, propio: true }]);
}

function quitarPropio(id: string): boolean {
  return escribirPropios(propiosGuardados().filter((i) => i.id !== id));
}

function suscribirPropios(aviso: () => void) {
  const alCambiar = (e: Event) => { if (!(e instanceof StorageEvent) || e.key === CLAVE_PROPIA) aviso(); };
  window.addEventListener(EVENTO_PROPIA, alCambiar);
  window.addEventListener("storage", alCambiar);
  return () => { window.removeEventListener(EVENTO_PROPIA, alCambiar); window.removeEventListener("storage", alCambiar); };
}

export function useBibliotecaPropia(): readonly ItemBiblioteca[] {
  return useSyncExternalStore(suscribirPropios, propiosGuardados, () => SIN_PROPIOS);
}

// ----------------------------------------------------------------------------------------------------------
// Índice y resúmenes (se calculan de a poco, sin trabar la página)
// ----------------------------------------------------------------------------------------------------------

/**
 * Lo de fábrica más lo propio, con lo que sale de indexar cada escena, sus resúmenes (globos, colores, productos) y
 * sus huellas (para las miniaturas). Todo lo que arma lo hace el motor fuera de la página (`biblioteca-cliente.ts`):
 * aquí no se toca el contenido de nada. La grilla sale enseguida con lo fijo (nombre, tipo, ocasiones, foto) y se
 * completa (sin repetidos, con lo de cada escena) a medida que el motor avanza.
 */
export function useBiblioteca(propios: readonly ItemBiblioteca[]) {
  const motor = useMotorBiblioteca(propios);
  const nombresDecoracion = useTextosDecoracion();
  const base = useMemo(() => [...BIBLIOTECA_FABRICA, ...propios], [propios]);
  // Mientras el motor no ha firmado un item, su firma es única (no se junta con nada todavía).
  const items = useMemo(() => unirBiblioteca(base, motor.indices, (i) => motor.hechos.get(i.id)?.firma ?? `pendiente:${i.id}`).map((item) => aplicarNombreDecoracion(item, nombresDecoracion)), [base, motor.indices, motor.hechos, nombresDecoracion]);
  const { resumenes, huellas } = useMemo(() => {
    const r = new Map<string, ResumenItem>(), h = new Map<string, string>();
    for (const i of items) {
      const hecho = motor.hechos.get(i.id);
      if (hecho) { r.set(i.id, hecho.resumen); h.set(i.id, huellaConId(i.id, hecho.huella)); }
    }
    return { resumenes: r, huellas: h };
  }, [items, motor.hechos]);
  return { items, resumenes, huellas, listos: resumenes.size, indexadas: motor.escenasHechas, escenas: motor.escenas };
}

// ----------------------------------------------------------------------------------------------------------
// Miniaturas 3D (renderizadas una vez en un lienzo oculto y guardadas en la sesión)
// ----------------------------------------------------------------------------------------------------------

const CLAVE_MINI = "taller3d:mini2:";
const ANCHO_MINI = 480, ALTO_MINI = 360;

function miniGuardada(huella: string): string | null {
  try { return window.sessionStorage.getItem(CLAVE_MINI + huella); } catch { return null; }
}

/**
 * Las decoraciones (las de globos) tienen su dibujo SVG; lo demás se renderiza en 3D. Solo se mira el contenido de las
 * decoraciones (piezas chicas): el de una escena de fábrica es perezoso y armarlo aquí trabaría la página.
 */
function miniaturaSvg(item: ItemBiblioteca): Miniatura | null {
  if (item.tipo !== "decoracion") return null;
  const c = item.contenido;
  if (c.tipo !== "pieza" || c.pieza.tipo !== "decoracion") return null;
  try { return miniaturaDecoracion(c.pieza.decoracion); } catch { return null; }
}

const esperarCuadro = () => new Promise<void>((r) => requestAnimationFrame(() => r()));

/**
 * Renderiza en 3D las miniaturas que faltan, de una en una y en el orden en que se ven, con su propio visor en un lienzo
 * oculto (se cierra al terminar). Cada una se guarda en sessionStorage por la huella de su contenido. Lo arma el motor
 * (fuera de la página); aquí solo se dibuja. Sin huella todavía (el motor no llegó a ese item), espera.
 */
export function useMiniaturas3d(orden: readonly ItemBiblioteca[], huellas: ReadonlyMap<string, string>) {
  const lienzoRef = useRef<HTMLCanvasElement>(null);
  const visorRef = useRef<EscenaGlobos | null>(null);
  /** Una miniatura a la vez: el visor oculto es uno solo (la siguiente espera a que termine la anterior). */
  const colaRef = useRef<Promise<void>>(Promise.resolve());
  const [minis, setMinis] = useState<ReadonlyMap<string, string>>(() => new Map());
  const [fallidas, setFallidas] = useState<ReadonlySet<string>>(() => new Set());
  const porHuella = useMemo(() => new Map(orden.flatMap((i) => {
    const huella = huellas.get(i.id);
    return huella && !miniaturaSvg(i) ? [[huella, i] as const] : [];
  })), [orden, huellas]);
  const porHuellaRef = useRef(porHuella);
  useEffect(() => { porHuellaRef.current = porHuella; }, [porHuella]);
  // Por la huella (texto), no por el objeto: la lista se rehace al indexar y el item sería otro objeto igual.
  const pendiente = useMemo(() => [...porHuella.keys()].find((h) => !minis.has(h) && !fallidas.has(h)) ?? null, [porHuella, minis, fallidas]);
  useEffect(() => {
    if (!pendiente) {
      // Sin nada que dibujar: el visor oculto se cierra (no gasta la tarjeta gráfica).
      const t = setTimeout(() => { colaRef.current = colaRef.current.then(() => { visorRef.current?.destruir(); visorRef.current = null; }); }, 1500);
      return () => clearTimeout(t);
    }
    const huella = pendiente;
    let vivo = true;
    const dibujar = async () => {
      const item = porHuellaRef.current.get(huella);
      if (!vivo || !item) return;
      const guardada = miniGuardada(huella);
      if (guardada) { setMinis((m) => new Map(m).set(huella, guardada)); return; }
      const lienzo = lienzoRef.current;
      if (!lienzo) return;
      try {
        if (!visorRef.current) {
          const { crearEscena } = await import("./escena-globos");
          visorRef.current = crearEscena(lienzo);
        }
        if (!vivo) return;
        const hecho = await armarEnMotor(item, false);
        if ("error" in hecho) throw new Error(hecho.error);
        if (!vivo || !visorRef.current) return;
        // Un nombre o un neón se dibuja con la letra cursiva: sin esperarla la miniatura se guarda con la marca roja.
        await exigirLetraDeRotulos(hecho.armada.solidos);
        if (!vivo || !visorRef.current) return;
        mostrarArmada(visorRef.current, hecho.armada);
        await esperarCuadro();
        await esperarCuadro();
        // Justo después de que el visor dibuja (mismo cuadro): el lienzo todavía tiene la imagen.
        const datos = await new Promise<string>((r) => requestAnimationFrame(() => {
          const salida = document.createElement("canvas");
          salida.width = ANCHO_MINI;
          salida.height = ALTO_MINI;
          const pincel = salida.getContext("2d");
          if (!pincel) { r(""); return; }
          pincel.fillStyle = "#efedf2";
          pincel.fillRect(0, 0, ANCHO_MINI, ALTO_MINI);
          // El visor dibuja solo cuando algo cambia: se dibuja aquí mismo para que el lienzo tenga la imagen.
          visorRef.current?.dibujar();
          pincel.drawImage(lienzo, 0, 0, ANCHO_MINI, ALTO_MINI);
          r(salida.toDataURL("image/jpeg", 0.72));
        }));
        if (!datos) throw new Error("sin lienzo 2D");
        try { window.sessionStorage.setItem(CLAVE_MINI + huella, datos); } catch { /* sesión llena: queda en memoria */ }
        setMinis((m) => new Map(m).set(huella, datos));
      } catch (causa) {
        console.error("[biblioteca] miniatura", item.id, causa);
        setFallidas((f) => new Set(f).add(huella));
      }
    };
    const t = setTimeout(() => { colaRef.current = colaRef.current.then(dibujar); }, 30);
    return () => { vivo = false; clearTimeout(t); };
  }, [pendiente]);
  useEffect(() => () => { visorRef.current?.destruir(); visorRef.current = null; }, []);
  return { lienzoRef, minis };
}

// ----------------------------------------------------------------------------------------------------------
// Piezas de la interfaz
// ----------------------------------------------------------------------------------------------------------

export const NOMBRE_TIPO_ITEM = new Map(TIPOS_ITEM.map((t) => [t.id, t.nombre]));
const TARJETA = "rounded-2xl bg-superficie ring-1 ring-borde";
const ETIQUETA = "rounded-full bg-superficie-suave px-2 py-0.5 text-[0.7rem] text-texto-suave ring-1 ring-borde";
/** 44 px de alto y, en el teléfono, letra de 16 px (si no, iOS acerca la página al tocar el campo). */

const nombreColor = (codigo: string) => `${referenciaPorCodigo(codigo)?.nombreCompleto ?? codigo} ${codigo}`;
const nombreProducto = (clave: string) => { const [f, c] = clave.split("|"); return `${f} ${nombreColor(c ?? "")}`; };

export function Chips({ language = "es", colores, max = 8 }: { language?: IdiomaTaller; colores: readonly string[]; max?: number }) {
  return (
    <span className="flex flex-wrap items-center gap-1" aria-label={textoTaller(language, "Colores: ") + (colores.map(nombreColor).join(", "))}>
      {colores.slice(0, max).map((c) => <span key={c} title={nombreColor(c)} className="size-4 rounded-full ring-1 ring-black/15" style={{ background: hexDeCodigo(c) }} />)}
      {colores.length > max && <span className="text-[0.7rem] text-texto-suave">+{colores.length - max}</span>}
    </span>
  );
}

export function Miniatura3d({ language = "es", item, url, className = "" }: { language?: IdiomaTaller; item: ItemBiblioteca; url: string | undefined; className?: string }) {
  const svg = useMemo(() => miniaturaSvg(item), [item]);
  if (svg) return <div className={`grid place-items-center bg-[#efedf2] p-3 ${className}`}><MiniaturaDecoracion miniatura={svg} nombre={item.nombre} className="h-full max-h-full w-full" /></div>;
  if (url) return <div role="img" aria-label={textoTaller(language, "Vista 3D de ") + (item.nombre)} className={`bg-[#efedf2] bg-cover bg-center ${className}`} style={{ backgroundImage: `url(${url})` }} />;
  // Mientras se dibuja la vista 3D, la foto de la idea (url pública de su fuente), si la tiene.
  // eslint-disable-next-line @next/next/no-img-element -- foto externa del CDN de Sempertex, a tamaño de tarjeta
  if (item.fuente?.fotoUrl) return <img src={item.fuente.fotoUrl} alt={`Foto de ${item.nombre}`} loading="lazy" decoding="async" className={`bg-[#efedf2] object-cover ${className}`} />;
  return <div className={`grid place-items-center bg-[#efedf2] text-xs text-texto-suave ${className}`}><Box className="size-6 animate-pulse opacity-50" aria-hidden /><span className="sr-only">{textoTaller(language, "Dibujando…")}</span></div>;
}

export function Fuente({ language = "es", item, corta = false }: { language?: IdiomaTaller; item: ItemBiblioteca; corta?: boolean }) {
  const f = item.fuente;
  if (!f) return null;
  const tipo = f.tipo === "idea-sempertex" ? "Idea de sempertex.com" : f.tipo === "celebra" ? "Revista Celebra" : f.tipo === "referencia-web" ? "Referencia web" : f.tipo === "referencia-dueno" ? "Referencia del dueño" : item.id.startsWith("vista:") ? "De tu escena" : item.propio ? "Tu biblioteca" : "Del taller";
  if (corta) return <span className="truncate text-[0.7rem] text-texto-suave" title={f.titulo}>{tipo}{f.tipo !== textoTaller(language, "propio") ? textoTaller(language, " · ") + (f.titulo) : ""}</span>;
  return (
    <span className="text-sm text-texto">
      <b className="font-semibold">{tipo}</b> · {f.url ? <a href={f.url} target="_blank" rel="noreferrer" className="underline decoration-dotted underline-offset-2 hover:text-acento">{f.titulo} <ExternalLink className="inline size-3" aria-hidden /></a> : f.titulo}
      {f.fotoUrl && <> · <a href={f.fotoUrl} target="_blank" rel="noreferrer" className="underline decoration-dotted underline-offset-2 hover:text-acento">{textoTaller(language, "ver la foto original")}</a></>}
    </span>
  );
}

/** La lista de compra en texto (para copiarla y pegarla en un pedido). */
function listaEnTexto(item: ItemBiblioteca, p: ProductosDeItem, partes: EscenografiaPorRepositorio | null): string {
  const lineas = [`${item.nombre} — productos`, "", "GLOBOS"];
  for (const g of p.globos) lineas.push(`${g.cantidad} × ${g.nombreOficial} — ${g.producto.nombre}${g.producto.estado === "verificado" ? ` — ${g.producto.url}` : " (sin verificar)"}${g.impresos ? ` (${g.impresos} de ellos impresos: ver abajo)` : ""}`);
  for (const [seccion, titulo] of [["impresos", "GLOBOS IMPRESOS"], ["metalizados", "METALIZADOS"]] as const) {
    const de = p.tienda.filter((t) => t.seccion === seccion);
    if (de.length) { lineas.push("", titulo); for (const t of de) lineas.push(`${t.cantidad} × ${t.nombre} (${t.detalle})${t.url ? ` — ${t.url}` : ""}`); }
  }
  if (p.utileria.length) { lineas.push("", "UTILERÍA"); for (const u of p.utileria) lineas.push(`${u.cantidad} × ${u.nombre}${u.variante ? ` (${u.variante})` : ""}${u.url ? ` — ${urlTienda(u.url)}` : ""}`); }
  lineas.push(...escenografiaEnTexto(p.escenografia, partes));
  return lineas.join("\n");
}

export function TablaProductos({ language = "es", item, productos }: { language?: IdiomaTaller; item: ItemBiblioteca; productos: ProductosDeItem }) {
  const [copiado, setCopiado] = useState(false);
  const partes = useEscenografiaPorRepositorio(item, productos);
  const copiar = async () => {
    try { await navigator.clipboard.writeText(listaEnTexto(item, productos, partes)); setCopiado(true); setTimeout(() => setCopiado(false), 2500); } catch { setCopiado(false); }
  };
  const th = "px-2 py-1.5 text-left text-[0.7rem] font-semibold uppercase tracking-wide text-texto-suave";
  const td = "px-2 py-1.5 align-top";
  // En el teléfono cada fila es una ficha: la cantidad a la izquierda y lo demás apilado (sin scroll de lado).
  // Desde 640 px, la tabla de siempre con su propio scroll horizontal si no cabe.
  const tabla = "w-full border-collapse text-sm max-sm:block sm:min-w-[520px]";
  const cabeza = "max-sm:hidden";
  const cuerpo = "max-sm:block";
  const fila = "border-b border-borde/60 max-sm:grid max-sm:grid-cols-[3rem_minmax(0,1fr)] max-sm:py-1";
  const celdaCantidad = `${td} font-mono font-semibold text-texto max-sm:row-span-4`;
  const celda = `${td} min-w-0 break-words max-sm:col-start-2 max-sm:py-0.5`;
  const rotulo = "text-texto-suave sm:hidden";
  return (
    <section className={`${TARJETA} flex flex-col gap-3 p-3`} aria-label={textoTaller(language, "Productos")}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-base font-semibold text-texto">{textoTaller(language, "Productos")}</h3>
        <button type="button" onClick={copiar} className={`${BOTON} ${INACTIVO} inline-flex items-center gap-1.5 px-3 text-xs`}><ClipboardCopy className="size-3.5" aria-hidden />{copiado ? textoTaller(language, "Lista copiada") : textoTaller(language, "Copiar la lista")}</button>
      </div>

      <div>
        <h4 className="text-sm font-semibold text-texto">{textoTaller(language, "Globos ")}<span className="font-normal text-texto-suave">· {productos.totalGlobos} {textoTaller(language, " en total")}</span></h4>
        {productos.globos.length === 0 ? <p className="text-xs text-texto-suave">{textoTaller(language, "No lleva globos.")}</p> : (
          <div className="mt-1 overflow-x-auto overscroll-x-contain">
            <table className={tabla}>
              <thead className={cabeza}><tr className="border-b border-borde"><th className={th}>{textoTaller(language, "Cantidad")}</th><th 
```

## Resolution request cacb3537cd9925be000ff500ae8a572c (src/components/tres-d/Taller3D.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/cacb3537cd9925be000ff500ae8a572c.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/cacb3537cd9925be000ff500ae8a572c.diff3`
- blobs: base `476060cbeff4c30bc0a9393cf0b4709a27498dcd`, ours `8063e2c785601887401da5d9bde3f74f21c6f7d5`, theirs `00a49fb94c211e83626bb1579a0bb14c7b93d35c` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "650f17a75fd1c08c1c5b8f19b8659dcd166c7a64", "ours": "2bfccbf3fed22a9cd8c37b1516ff0f349c466d90", "theirs": "685fc9c2a8663be3d093787da4262f2431a6c701"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/cacb3537cd9925be000ff500ae8a572c.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
"use client";

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  ArrowLeft, Camera, Check, ChevronDown, CircleHelp, House, Layers, LayoutGrid, MoveVertical, Plus, Redo2, RotateCw, Scan, ShoppingCart, SlidersHorizontal, Sparkles, Undo2, X,
} from "lucide-react";
import { PanelControlesPieza } from "./ControlesTactiles";
import { FORMATOS_GLOBO } from "@/lib/globos3d/formatos";
import { referenciaPorCodigo } from "@/lib/plan/referencia-sempertex";
import { papelDeConfeti } from "./armada-visor";
import type { EscenaGlobos, GloboColocadoEnEscena, GloboEnEscena, TuboEnEscena, VistaFija } from "./escena-globos";
import { DIBUJO_VACIO, globoAEscena, materialesEnIngles, R12, tuboAEscena, type DibujoEscena } from "./dibujo-escena";
import { descripcionRender3d, formatoEnIngles } from "@/lib/globos3d/render-ia";
import { GeneradorIA } from "./GeneradorIA";
import { PaletaEscena } from "./PaletaEscena";
import { reemplazarColor } from "@/lib/globos3d/recolorear";
import { armarEscena, escenaEnIngles, idNuevo, SALA_INICIAL, type Escena, type EscenaArmada, type NodoEscena } from "@/lib/globos3d/escena";
import { ESCENAS_PREDEFINIDAS, escenaPredefinida } from "@/lib/globos3d/escenas-presets";
import { nombreParaFoto, nombreQueSigue } from "@/lib/globos3d/nombre-escena";
import type { Encuadre } from "@/lib/globos3d/encuadre-foto";
import { vistaDeFoto } from "./camara-foto";
import type { PiezaArmada } from "@/lib/globos3d/piezas";
import { useEdicionEscena, useHistorialEscena, type PiezaEnVivo } from "./useEdicionEscena";
import { useLienzoDecoraciones, type CopiaElegida } from "./useLienzoDecoraciones";
import { ArrastreDecoracionContexto } from "./arrastre-decoracion";
import { follajeEnIngles } from "@/lib/globos3d/flores-artificiales";
import { plural } from "@/lib/globos3d/texto-cantidad";
import { medirFuera } from "./medicion-visor";
import { MenuContextual, type AccionMenu } from "./MenuContextual";
import { useMenuContextual } from "./useMenuContextual";
import { cargarSolitario, useEditorSolitario } from "./useEditorSolitario";
import type { InfoMenuPieza } from "@/lib/globos3d/editor-solitario";
import type { ItemBiblioteca } from "@/lib/globos3d/biblioteca";
import { TextosProductoProvider } from "./textos-producto-contexto";
import type { NombreProductoIngles } from "@/lib/textos-ingles/aplicar";
import type { SeleccionIA } from "@/lib/globos3d/cuerpo-escena-ia";
import { Ayuda } from "./AyudaTaller";
import { MenuMas } from "./MenuMas";
import { ALTURAS, HojaMovil, type AlturaHoja } from "./HojaMovil";
import { BannerVerAntes } from "./ia/BannerVerAntes";
import { PanelIA } from "./ia/PanelIA";
import { PestanasLaterales, type PestanaLateral } from "./ia/PestanasLaterales";
import { useIATaller } from "./ia/useIATaller";
import { useResaltadoIA } from "./ia/useResaltadoIA";
import { DialogoTaller } from "./DialogoTaller";
import { Inspector } from "./Inspector";
import { PanelPiezas } from "./PanelPiezas";
import { PartesSolitario } from "./PartesSolitario";
import { EditorSala } from "./PanelEscena";
import { DialogoCompra } from "./DialogoCompra";
import { EtiquetasMedidas } from "./EtiquetasMedidas";
import { useMedidasDePieza } from "./useMedidasDePieza";
import { BarraHerramientas, BotonMedidas, EtiquetaElegida, ReglaAlturas, type Herramienta } from "./SobreVisor";
import { SelectorAmbienteVisor } from "./SelectorAmbienteVisor";
import { ExportarEscenaTaller } from "./ExportarEscenaTaller";
import { medidaPrincipal, NOMBRE_TIPO } from "./tipos-pieza";
import { leerGuardada, guardarEscena } from "./guardado-escena";
import { conSalaNueva } from "@/lib/globos3d/salon-techos";
import { claveNueva } from "./guardado-conversacion";
import { useTallerProyectos } from "@/components/proyectos/useTallerProyectos";
import { useInsetTeclado } from "./useInsetTeclado";
import { useEstadoAnadir } from "./useEstadoAnadir";
import type { PiezaParaAnadir } from "./nuevas-taller";
import type { VistaSolitario } from "./ParametrosPieza";
import { BTN, BTN_ICO, BTN_PRI, FLOTANTE, RIEL, RIEL_ON } from "./ui-taller";
import { AvisoRecuperacionWebGL, useRecuperacionWebGL } from "./ciclo-contexto-webgl";
import { capturarMiniaturaBiblioteca as capturarMiniaturaActual } from "./biblioteca/capturar-miniatura";
import { EnlaceGaleriaTaller, useDecoracionEntrada } from "./galeria/useDecoracionEntrada";
import { textoCantidadGlobosTaller, textoTaller, textosTallerMarco } from "./textos/taller-marco";
import { IdiomaTallerEdicion } from "./textos/taller-edicion";
import { textosProyectos } from "@/components/proyectos/textos-proyectos";
import { NombreEscena } from "./NombreEscena";

/**
 * Lo pesado se carga aparte, al abrirlo: el panel «Añadir» (con la Biblioteca: todas las ideas de Sempertex, su índice
 * y sus fichas), las plantillas con miniatura, los productos exactos de la tienda y los parámetros del editor solitario.
 * Importarlos con la página la hacía pesada (y, cuando los lotes armaban al importarse, congelaba /3d ~20 s).
 */
const Cargando = ({ language = "es" }: { language?: "es" | "en" } = {}) => <p className="p-4 text-sm text-taller-suave" role="status">{textoTaller(language, "Cargando…")}</p>;
const PanelAnadir = dynamic(() => import("./PanelAnadir").then((m) => m.PanelAnadir), { ssr: false, loading: () => <Cargando /> });
const FichaDialogo = dynamic(() => import("./Biblioteca").then((m) => m.FichaDialogo), { ssr: false, loading: () => <Cargando /> });
const TarjetasPlantillas = dynamic(() => import("./Biblioteca").then((m) => m.TarjetasPlantillas), { ssr: false, loading: () => <Cargando /> });
const ProductosEscena = dynamic(() => import("./Biblioteca").then((m) => m.ProductosEscena), { ssr: false, loading: () => <Cargando /> });
const AccionesPieza = dynamic(() => import("./biblioteca/AccionesBibliotecaPersonal").then((m) => m.AccionesBibliotecaPersonal), { ssr: false });
const ParametrosPieza = dynamic(() => import("./ParametrosPieza").then((m) => m.ParametrosPieza), { ssr: false, loading: () => <Cargando /> });

/** El mismo corte que `lg:` de Tailwind: desde 1024 px, riel + paneles + inspector; menos, visor a pantalla y hoja. */
const CONSULTA_ANCHO = "(min-width: 1024px)";
function suscribirAncho(aviso: () => void) {
  const consulta = window.matchMedia(CONSULTA_ANCHO);
  consulta.addEventListener("change", aviso);
  return () => consulta.removeEventListener("change", aviso);
}
/** Pantalla ancha (escritorio o tablet acostada). `null` = aún no medida (servidor e hidratación): se pinta un casco neutro. */
function useAnchoMedido(): boolean | null {
  return useSyncExternalStore<boolean | null>(suscribirAncho, () => window.matchMedia(CONSULTA_ANCHO).matches, () => null);
}

type Panel = "anadir" | "piezas" | "plantillas" | "sala";
type PestanaHoja = "anadir" | "piezas" | "pieza" | "ia" | "parametros" | "partes";

const PANELES: ReadonlyArray<{ id: Panel; nombre: string; icono: ReactNode }> = [
  { id: "anadir", nombre: "Añadir", icono: <Plus className="size-5" aria-hidden /> },
  { id: "piezas", nombre: "Piezas", icono: <Layers className="size-5" aria-hidden /> },
  { id: "plantillas", nombre: "Plantillas", icono: <LayoutGrid className="size-5" aria-hidden /> },
  { id: "sala", nombre: "Sala", icono: <House className="size-5" aria-hidden /> },
];

/** Una tecla del taller, como si se pulsara (los botones táctiles usan la misma lógica del teclado). */
function pulsar(key: string, opciones: { shiftKey?: boolean } = {}) {
  window.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...opciones }));
}

/**
 * Una función estable que siempre llama a la última versión de `f`: así los paneles memorizados (y los ocultos) no se
 * vuelven a pintar porque cambió una función.
 */
function useEstable<A extends unknown[], R>(f: (...args: A) => R): (...args: A) => R {
  const ref = useRef(f);
  useLayoutEffect(() => { ref.current = f; });
  return useCallback((...args: A) => ref.current(...args), []);
}

/** Para saber si ya se hidrató (en el servidor, `false`). */
const sinSuscripcion = () => () => {};

function escribiendo(objetivo: EventTarget | null): boolean {
  return objetivo instanceof HTMLElement && (objetivo.isContentEditable || Boolean(objetivo.closest("input, textarea, select, [contenteditable='true'], [role='menu'], dialog")));
}

/**
 * Página /3d: el Taller 3D. Barra superior (escena, deshacer, imagen con IA, lista de compra), riel de paneles (Añadir,
 * Piezas, Plantillas, Sala), el visor a todo lo que queda (herramientas flotantes, etiqueta de la pieza elegida,
 * contador y la IA al pie) e inspector de la pieza elegida. «Editar sola» abre el editor solitario de una pieza con
 * los parámetros completos de su tipo. En teléfono y tablet: visor a pantalla completa y hoja inferior con pestañas.
 */
<<<<<<< ours (src/components/tres-d/Taller3D.tsx)
export function Taller3D({ canViewOtherAccounts = false, language = "es", decoracionEntrada = null }: { canViewOtherAccounts?: boolean; language?: "es" | "en"; decoracionEntrada?: { id: string; escena: Escena | null } | null } = {}) {
  const text = textosTallerMarco(language);
  const projectText = textosProyectos[language];
||||||| base
export function Taller3D({ canViewOtherAccounts = false, language = "es", decoracionEntrada = null }: { canViewOtherAccounts?: boolean; language?: "es" | "en"; decoracionEntrada?: { id: string; escena: Escena | null } | null } = {}) {
=======
export function Taller3D({ canViewOtherAccounts = false, language = "es", decoracionEntrada = null, nombresProducto = {}, nombresDecoracion = {} }: { canViewOtherAccounts?: boolean; language?: "es" | "en"; decoracionEntrada?: { id: string; escena: Escena | null } | null; nombresProducto?: Readonly<Record<string, NombreProductoIngles>>; nombresDecoracion?: Readonly<Record<string, NombreProductoIngles>> } = {}) {
  const text = textosTallerMarco(language);
  const projectText = textosProyectos[language];
>>>>>>> theirs
  const lienzoRef = useRef<HTMLCanvasElement>(null);
  const escenaRef = useRef<EscenaGlobos | null>(null);
  const visorCajaRef = useRef<HTMLElement>(null);
  const [visor, setVisor] = useState<EscenaGlobos | null>(null);
  const listo = visor !== null;
  // A destroyed scene force-loses its WebGL context, so every scene gets a fresh canvas element.
  const [generacionLienzo, setGeneracionLienzo] = useState(0);
  const { error, reportarError, reintentar, prepararContexto } = useRecuperacionWebGL(lienzoRef, escenaRef);

  // Escena (con deshacer y rehacer: Ctrl+Z / Ctrl+Y) y su nombre; se guarda sola en el navegador.
  // La última escena guardada en este navegador (si hay) en vez de la de partida. En el servidor no hay navegador: hasta
  // hidratar (`cargada`) no se pinta nada que dependa de la escena, así lo del servidor y lo del navegador coinciden.
  const [guardadaAlAbrir] = useState(() => (typeof window === "undefined" ? null : leerGuardada()));  // prerender-seguro: tras `typeof window`: en el servidor no se llama
  // La clave nueva lleva la hora: en el servidor (prerender) Next no admite `Date.now()`, y allí no se usa (no hay conversación que cargar).
  const [claveInicial] = useState(() => guardadaAlAbrir?.clave ?? (typeof window === "undefined" ? "servidor" : claveNueva()));  // prerender-seguro: tras `typeof window`: `claveNueva` solo corre en el navegador
  const historialEscena = useHistorialEscena(() => guardadaAlAbrir?.escena ?? { sala: structuredClone(SALA_INICIAL), nodos: [] }, claveInicial);
  const escenaEdit = historialEscena.escena;
  const { cambiar: setEscenaEdit } = historialEscena;
  const [nombreEscena, setNombreEscena] = useState(() => guardadaAlAbrir?.nombre ?? projectText.nuevo);
  const setEscenaProyecto = useCallback((escena: Escena, key?: string) => setEscenaEdit(escena, { clave: key ?? claveNueva() }), [setEscenaEdit]);
  const proyectoUi = useTallerProyectos({ nombre: nombreEscena, escena: escenaEdit, language, setNombre: setNombreEscena, setEscena: setEscenaProyecto });
  const anchoMedido = useAnchoMedido();
  const esAncho = anchoMedido === true;
  const sinMedir = anchoMedido === null;
  const cargada = useSyncExternalStore(sinSuscripcion, () => true, () => false);
  // Piezas ya armadas por su JSON: mover una pieza no rehace el arco orgánico (medio segundo).
  const [cacheEscena] = useState(() => new Map<string, PiezaArmada>());
  // Editor solitario: lo que se ve y se edita es la estructura aislada con su propio deshacer; «Listo» la devuelve.
  const solitario = useEditorSolitario({ escena: escenaEdit, cambiarEscena: setEscenaEdit, cache: cacheEscena, visorRef: escenaRef });
  const escenaVista = solitario.escena;
  const cambiarVista = solitario.activo ? solitario.cambiar : setEscenaEdit;
  const deshacerVista = solitario.activo ? solitario.deshacer : historialEscena.deshacer;
  const rehacerVista = solitario.activo ? solitario.rehacer : historialEscena.rehacer;
  const puedeDeshacerVista = solitario.activo ? solitario.puedeDeshacer : historialEscena.puedeDeshacer;
  const puedeRehacerVista = solitario.activo ? solitario.puedeRehacer : historialEscena.puedeRehacer;
  // La IA (pestaña «IA» del panel derecho): cada turno es UN paso nombrado del historial global; Ctrl+Z y «Deshacer turno» van juntos.
  const claveEscena = historialEscena.clave ?? claveInicial;
  // El nombre de la escena sigue a lo que la IA arma, si era el de una plantilla (nombre-escena.ts); el que escribió la persona no se toca.
  const alAplicarIA = useCallback((nueva: Escena) => { if (!solitario.activo) setNombreEscena((actual) => nombreQueSigue(actual, nueva)); }, [solitario.activo]);
  const nombreFoto = useMemo(() => nombreParaFoto(nombreEscena, escenaVista), [nombreEscena, escenaVista]);
  const { ia, rotuloDeshacer } = useIATaller({ language, escena: escenaVista, cambiar: cambiarVista, ambito: solitario.activo ? `pieza:${solitario.solitario?.raizId ?? ""}` : "escena", clave: claveEscena, cache: cacheEscena, cargada, alAplicar: alAplicarIA, verDesdeLaFoto: (encuadre) => { vistaFotoPendiente.current = encuadre; } });
  /** Una pieza recién creada desde «Añadir → Nuevas» y abierta en el editor: «Cancelar» la quita. */
  const nuevaRef = useRef<string | null>(null);
  const [pestanaLado, setPestanaLado] = useState<PestanaLateral>("pieza");
  const [vistaSolitario, setVistaSolitario] = useState<VistaSolitario>({ verAnclas: false, todosLosGlobos: false });

  const [seleccionElegida, setSeleccion] = useState<string | null>(null);
  const seleccion = seleccionElegida && escenaVista.nodos.some((n) => n.id === seleccionElegida) ? seleccionElegida : null;
  const [enVivo, setEnVivo] = useState<PiezaEnVivo | null>(null);
  const [copiaTocada, setCopiaTocada] = useState<CopiaElegida | null>(null);
  const copiaElegida = copiaTocada && copiaTocada.id === seleccion ? copiaTocada : null;
  const [avisoLienzo, setAvisoLienzo] = useState<string | null>(null);
  useDecoracionEntrada(decoracionEntrada, language, proyectoUi.requestDestination, setAvisoLienzo);
  const [vueltaEncuadre, setVueltaEncuadre] = useState(0);
  const encuadradoRef = useRef<number | null>(null);
  /** El encuadre de la foto que se acaba de modelar: cuando la escena nueva se dibuja, la cámara pasa a ver desde donde estaba la de la foto. */
  const vistaFotoPendiente = useRef<Encuadre | null>(null);
  const [armadas] = useState(() => new WeakMap<Escena, EscenaArmada>());
  const [dibujos] = useState(() => new WeakMap<EscenaArmada, DibujoEscena>());
  const [menu, setMenu] = useState<{ id: string; x: number; y: number; tactil: boolean } | null>(null);
  const [infoMenu, setInfoMenu] = useState<{ id: string; info: InfoMenuPieza } | null>(null);
  const [avisoQuitar, setAvisoQuitar] = useState<string | null>(null);
  const [confirmarEliminar, setConfirmarEliminar] = useState<{ id: string; decoraciones: number } | null>(null);
  /** Piezas ocultas en el visor (siguen en la escena y en la lista de compra). */
  const [ocultos, setOcultos] = useState<ReadonlySet<string>>(() => new Set());
  // Interfaz: panel abierto, pestaña de «Añadir», herramienta del visor, vista fija, diálogos.
  const insetTeclado = useInsetTeclado(!esAncho);
  const [panel, setPanelElegido] = useState<Panel | null>("piezas");
  /** Los paneles que ya se abrieron alguna vez (quedan montados). */
  const [panelesVistos, setPanelesVistos] = useState<ReadonlySet<Panel>>(() => new Set<Panel>(["piezas"]));
  const setPanel = useCallback((p: Panel | null | ((actual: Panel | null) => Panel | null)) => {
    setPanelElegido((actual) => {
      const nuevo = typeof p === "function" ? p(actual) : p;
      if (nuevo) setPanelesVistos((v) => (v.has(nuevo) ? v : new Set(v).add(nuevo)));
      return nuevo;
    });
  }, []);
  const anadir = useEstadoAnadir();
  const [herramienta, setHerramienta] = useState<Herramienta>("mover");
  const [vistaFija, setVistaFija] = useState<VistaFija | null>("3d");
  const [dialogo, setDialogo] = useState<"lista" | "imagen" | "ayuda" | null>(null);
  const [ficha, setFicha] = useState<ItemBiblioteca | null>(null);
  const [pedirGuardar, setPedirGuardar] = useState(0);
  const [renombrando, setRenombrando] = useState(false);
  const [menuMas, setMenuMas] = useState(false);
  const [colgarEnSolitario, setColgarEnSolitario] = useState(false);
  // Teléfono y tablet: la hoja inferior.
  const [hoja, setHoja] = useState<AlturaHoja>("media");
  const [pestanaHoja, setPestanaHoja] = useState<PestanaHoja>("piezas");
  const [hojasVistas, setHojasVistas] = useState<ReadonlySet<PestanaHoja>>(() => new Set<PestanaHoja>());
  const [alturaMovil, setAlturaMovil] = useState(false);

  // El visor se crea una vez (three.js se carga solo en el navegador).
  useEffect(() => {
    if (sinMedir) return; // sin lienzo hasta medir el ancho
    let vivo = true;
    let observador: ResizeObserver | null = null;
    let quitarOyentesContexto: (() => void) | null = null;
    void import("./escena-globos").then(({ crearEscena }) => {
      const lienzo = lienzoRef.current;
      if (!vivo || !lienzo) return;
      try {
        const escena = crearEscena(lienzo);
        escenaRef.current = escena;
        quitarOyentesContexto = prepararContexto(lienzo, escena);
        observador = new ResizeObserver(() => escena.redimensionar());
        observador.observe(lienzo);
        setVisor(escena);
      } catch (causa) {
        reportarError("Tu navegador no pudo abrir el visor 3D (WebGL). Prueba con Chrome o Edge actualizados.");
        console.error("[3d]", causa);
      }
    });
    return () => {
      vivo = false;
      observador?.disconnect();
      quitarOyentesContexto?.();
      escenaRef.current?.destruir();
      if (escenaRef.current) setGeneracionLienzo((g) => g + 1);
      escenaRef.current = null;
      setVisor(null);
      encuadradoRef.current = null;
      vistaFotoPendiente.current = null;
    };
  }, [sinMedir, prepararContexto, reportarError]);

  // Guardar solo (medio segundo después del último cambio).
  useEffect(() => {
    if (!cargada) return;
    const t = setTimeout(() => { guardarEscena({ nombre: nombreEscena, escena: escenaEdit, clave: claveEscena }); }, 500);
    return () => clearTimeout(t);
  }, [cargada, escenaEdit, nombreEscena, claveEscena]);
  const armadaEscena = useMemo(() => {
    if (!cargada) return null;
    const hecha = armadas.get(escenaVista);
    if (hecha) return hecha;
    const nueva = medirFuera("armarEscena", () => armarEscena(escenaVista, cacheEscena));
    armadas.set(escenaVista, nueva);
    return nueva;
  }, [cargada, escenaVista, cacheEscena, armadas]);

  // «Ver antes» (IA): el visor dibuja la escena sin lo del turno; los paneles y la edición siguen con la real (y se bloquea editar).
  const armadaAntes = useMemo(() => (ia.escenaAntes ? armarEscena(ia.escenaAntes, cacheEscena) : null), [ia.escenaAntes, ca
```

## CG-9

Workflow `None` (None); state: `null`

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/CG-9.history.jsonl` (none yet)

## CG-9

Workflow `None` (None); state: `null`

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/CG-9.history.jsonl` (none yet)

## Run status

Run workflow `bt:pictures:REQ-021:r25@2`: PENDING; summary status running. Full status: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.solver/20261030-051648-0278/status.json`.

- T10.2: PENDING {"task_id": "T10.2", "state": "running", "attempt": "pictures-REQ-021-r25-T10.2-a2-601931f0"}

## Composition gates

Composed: `{"CG-3": "C1", "CG-5": "C2", "CG-6": "C3", "CG-7": "C4", "CG-8": "C5"}`; rejected: `{"CG-9": "git_text_conflict"}`. A composition that fails is tried again on later turns of the run loop (`COMPOSE_TURNS`) before the gate counts as rejected; the owner's `retry-task` of the gate task composes it again.

Last gate and line events (telemetry):
- subplan_line_conflict: {}
- subplan_line_conflict: {}
- subplan_line_conflict: {}
- subplan_line_conflict: {}
- gate_compose_failed: {"gate": "CG-7", "turn": 1, "reason": "DBOSMaxStepRetriesExceeded: DBOS Error 7: Step bt.compose has exceeded its maximum of 3 retries"}
- gate_compose_failed: {"gate": "CG-7", "turn": 2, "reason": "DBOSMaxStepRetriesExceeded: DBOS Error 7: Step bt.compose has exceeded its maximum of 3 retries"}
- gate_compose_failed: {"gate": "CG-7", "turn": 3, "reason": "DBOSMaxStepRetriesExceeded: DBOS Error 7: Step bt.compose has exceeded its maximum of 3 retries"}
- gate_composed: {"gate": "CG-7", "state": "rejected", "reason": "COMPOSE_FAILED 3 turns: DBOSMaxStepRetriesExceeded: DBOS Error 7: Step bt.compose has exceeded its maximum of 3 retries"}
- gate_recompose: {"gate": "CG-7", "previous": "COMPOSE_FAILED 3 turns: DBOSMaxStepRetriesExceeded: DBOS Error 7: Step bt.compose has exceeded its maximum of 3 retries"}
- gate_composed: {"gate": "CG-7", "state": "candidate", "candidate_id": "C4", "reason": ""}
- gate_composed: {"gate": "CG-8", "state": "candidate", "candidate_id": "C5", "reason": ""}
- gate_composed: {"gate": "CG-9", "state": "rejected", "candidate_id": "C6", "reason": "git_text_conflict"}

Known case (agents/solver.md): gate CG-9 is rejected. Fix the origin of its reason above (the composer, a merge rule, the environment or the plan), integrate the fix, then `uv run --project ~/dev/metodologia bt-durable retry-task pictures REQ-021 T99`: it reopens the ended run and composes CG-9 again.

## Files

- requirement: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t` (SPEC.md, PLAN.md, PLAN.json, SPEC.es.md)
- the frozen plan this run executes: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/plan-revisions/PLAN.r25.json`
- project decisions: `/home/david/bitacora/pictures/DECISIONS.md`
- metodologia decisions: `/home/david/bitacora/metodologia/DECISIONS.md`
- day log: `/home/david/bitacora/pictures/2026-10/W5/2026-10-28.md`
- day log: `/home/david/bitacora/pictures/2026-10/W5/2026-10-29.md`
- day log: `/home/david/bitacora/metodologia/2026-10/W5/2026-10-29.md`
- day log: `/home/david/bitacora/metodologia/2026-10/W5/2026-10-30.md`
- diagnoses: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.diagnoses`; healing: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.durable-healing.json`; activity: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/.planning/activity.jsonl`; telemetry and attempts: `/home/david/bitacora/.state/durable`

## Commands

- run status: `uv run --project ~/dev/metodologia bt-durable status pictures REQ-021`
- engine journal: `journalctl --user -u bt-durable.service --since -3h --no-pager -o cat`
- answer a decision: `uv run --project ~/dev/metodologia bt-durable answer pictures REQ-021 <task> <request>@k<round> <action> --note "..." --by solver`
- the run's Planner: `python3 /home/david/dev/metodologia/skill/scripts/bt_agent_terminal.py tell-planner pictures REQ-021 "<change request>"`
- integrate a metodologia fix: `python3 ~/dev/metodologia/skill/scripts/bt_integrate.py --branch solver/20261030-051648-0278 --worktree /home/david/.local/share/bitacora-solver/pictures/20261030-051648-0278/wt --title "<what> (D-NNN)" --session 20261030-051648-0278 --trailer "<your attribution line>"` (`--dry-run` first; `--help` for the steps)

## Your session

- session folder (REPORT.md, result.json, NOTES.md, inbox.jsonl): `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.solver/20261030-051648-0278`
- working folder (your worktree goes in `/home/david/.local/share/bitacora-solver/pictures/20261030-051648-0278/wt`): `/home/david/.local/share/bitacora-solver/pictures/20261030-051648-0278`
- trigger keys for result.json `handled`: pictures:REQ-021:r25:resolution:4378ebb94f72d6922c89d601ee5db484, pictures:REQ-021:r25:resolution:cacb3537cd9925be000ff500ae8a572c
- keep NOTES.md current (what you found, what you changed, what is next): you may be restarted on another account and must be able to continue from your files.
