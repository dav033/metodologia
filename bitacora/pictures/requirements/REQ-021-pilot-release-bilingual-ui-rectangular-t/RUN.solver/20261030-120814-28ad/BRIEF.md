# Solucionador 20261030-120814-28ad — pictures REQ-021 (run pictures:REQ-021:r27)

Started 2026-10-30T12:08:14 by the durable engine's maintenance pass.

## Triggers

- `pictures:REQ-021:r27:resolution:000cc420754a9d752462160c5452618a` — resolution · T2.55: the conflict in src/app/3d/Taller3DConPermisoPersonal.tsx waits for a recorded resolution since 2026-10-29T23:09:03; no retry can settle it
- `pictures:REQ-021:r27:resolution:312b5f3cde0689853fe078d348f08bb0` — resolution · T2.55: the conflict in scripts/test/test-harness-taller-esenciales.ts waits for a recorded resolution since 2026-10-29T23:09:03; no retry can settle it
- `pictures:REQ-021:r27:resolution:67302a71b7947706bdbcbc0d72dbc129` — resolution · T2.55: the conflict in src/app/3d/page.tsx waits for a recorded resolution since 2026-10-29T23:09:03; no retry can settle it
- `pictures:REQ-021:r27:resolution:6df4cea9605036b2ac01269b320741b1` — resolution · T2.55: the conflict in src/components/ui/shell/CabeceraApp.tsx waits for a recorded resolution since 2026-10-30T11:40:00; no retry can settle it
- `pictures:REQ-021:r27:resolution:7e0709f8ac37f2164efc6081f259c5df` — resolution · T2.55: the conflict in src/app/page.tsx waits for a recorded resolution since 2026-10-30T11:40:00; no retry can settle it
- `pictures:REQ-021:r27:resolution:8042b963196a321dcee14a10cf512e87` — resolution · T2.55: the conflict in scripts/test/test-integracion-decoraciones-personales.ts waits for a recorded resolution since 2026-10-29T23:09:03; no retry can settle it
- `pictures:REQ-021:r27:resolution:87f60eeb77d9f299cfb7dd9902dd315c` — resolution · T2.55: the conflict in .evidence/REQ-021/CG-2.integration.json waits for a recorded resolution since 2026-10-29T23:09:03; no retry can settle it
- `pictures:REQ-021:r27:resolution:8f4d1b7928b20f9f71fe0b9e76ef136b` — resolution · T2.55: the conflict in src/components/guiado/VistaGuiada.tsx waits for a recorded resolution since 2026-10-30T11:40:00; no retry can settle it
- `pictures:REQ-021:r27:resolution:9d3f9d9ac1350969fd6a4fe71204cd1c` — resolution · T2.55: the conflict in src/app/login/page.tsx waits for a recorded resolution since 2026-10-30T11:40:00; no retry can settle it
- `pictures:REQ-021:r27:resolution:ba2580bb7203f67c81c4eadf632e2b62` — resolution · T2.55: the conflict in src/lib/cuentas/cuenta-actual.ts waits for a recorded resolution since 2026-10-30T11:40:00; no retry can settle it
- `pictures:REQ-021:r27:resolution:dd4cc8117603023fa4561e12cdbe7254` — resolution · T2.55: the conflict in scripts/test/test-integracion-proyectos.ts waits for a recorded resolution since 2026-10-29T23:09:03; no retry can settle it
- `pictures:REQ-021:r27:resolution:deec9ffa25d6d1798fe3f9da9ac100df` — resolution · T2.55: the conflict in src/app/asistente/page.tsx waits for a recorded resolution since 2026-10-30T11:40:00; no retry can settle it
- `pictures:REQ-021:r27:resolution:585d3876c7dcbf3c967460530ce058d6` — resolution · T2.55: the conflict in src/app/page.tsx waits for a recorded resolution since 2026-10-30T11:59:34; no retry can settle it
- `pictures:REQ-021:r27:resolution:6d4aa822010fb3ca2b27ee9dbbdc64e0` — resolution · T2.55: the conflict in src/components/ui/shell/CabeceraApp.tsx waits for a recorded resolution since 2026-10-30T11:59:34; no retry can settle it
- `pictures:REQ-021:r27:resolution:88054d9772b8651d2e5deb8410a8f05a` — resolution · T2.55: the conflict in src/app/asistente/page.tsx waits for a recorded resolution since 2026-10-30T11:59:34; no retry can settle it
- `pictures:REQ-021:r27:resolution:f97d80d9d2fc59d46ef6cd1c461f869c` — resolution · T2.55: the conflict in src/app/login/page.tsx waits for a recorded resolution since 2026-10-30T11:59:34; no retry can settle it
- `pictures:REQ-021:r27:resolution:fbddea742dcfc000eb541a6dcedd0981` — resolution · T2.55: the conflict in src/lib/cuentas/cuenta-actual.ts waits for a recorded resolution since 2026-10-30T11:59:34; no retry can settle it
- `pictures:REQ-021:r27:T2.55:T2.55:d2@k1` — decision · T2.55: the diagnosis failed: la respuesta no trae JSON

## Resolution request 000cc420754a9d752462160c5452618a (src/app/3d/Taller3DConPermisoPersonal.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/000cc420754a9d752462160c5452618a.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/000cc420754a9d752462160c5452618a.diff3`
- blobs: base `-`, ours `2dc417dc682f5f4447da540e8e62b69787bfef88`, theirs `ad3d4fac228b66281d2f66847336901336d782a8` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "217e5e5053d0497c4867ff21dae3c33e3fd8170a", "ours": "56f02a46dc6f0d169f587f41889681745874023c", "theirs": "c09fc4edda7a6699dec6af4bc7ea9e7786588193"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/000cc420754a9d752462160c5452618a.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
<<<<<<< ours (src/app/3d/Taller3DConPermisoPersonal.tsx)
import { Taller3D } from "@/components/tres-d/Taller3D";
import { getAccountLanguage, getCurrentAccount } from "@/lib/cuentas/cuenta-actual";

export async function Taller3DConPermisoPersonal() {
  const [account, language] = await Promise.all([getCurrentAccount(), getAccountLanguage()]);
  const canViewOtherAccounts = account?.roles.some((role) => role === "empleado_interno" || role === "administrador") ?? false;
  return <Taller3D canViewOtherAccounts={canViewOtherAccounts} language={language} />;
}
||||||| base
=======
import { Taller3D } from "@/components/tres-d/Taller3D";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { SESSION_COOKIE } from "@/lib/auth/session";
import { getCurrentAccount } from "@/lib/cuentas/cuenta-actual";
import { resolverSesion } from "@/lib/cuentas/sesion";
import { getRequestLanguage } from "@/lib/idioma/servidor";
import { puedeExplorarDecoraciones } from "@/lib/globos3d/permisos-galeria-decoraciones";

export async function Taller3DConPermisoPersonal({ decoracionId = null }: { decoracionId?: string | null }) {
  const [account, language, session] = await Promise.all([
    getCurrentAccount(),
    getRequestLanguage(),
    (async () => {
      const token = (await cookies()).get(SESSION_COOKIE)?.value;
      return token && /^[A-Za-z0-9_-]{43}$/.test(token) ? resolverSesion(token) : null;
    })(),
  ]);
  if (decoracionId && (!session || !puedeExplorarDecoraciones(session.permissions))) redirect("/sin-acceso?herramienta=decoraciones");
  const canViewOtherAccounts = account?.roles.some((role) => role === "empleado_interno" || role === "administrador") ?? false;
  let decoracion: { id: string; escena: import("@/lib/globos3d/escena").Escena | null } | null = null;
  if (decoracionId) {
    const { escenaDeDecoracion } = await import("@/lib/globos3d/galeria-decoraciones");
    decoracion = { id: decoracionId, escena: escenaDeDecoracion(decoracionId) };
  }
  return <Taller3D canViewOtherAccounts={canViewOtherAccounts} language={language} decoracionEntrada={decoracion} />;
}
>>>>>>> theirs

```

## Resolution request 312b5f3cde0689853fe078d348f08bb0 (scripts/test/test-harness-taller-esenciales.ts)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/312b5f3cde0689853fe078d348f08bb0.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/312b5f3cde0689853fe078d348f08bb0.diff3`
- blobs: base `-`, ours `7677641aad5717a1023fdac4701ccecdcb5a0e6d`, theirs `7a0d262156fbd757a72d2676ca5f4b262676e19f` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "217e5e5053d0497c4867ff21dae3c33e3fd8170a", "ours": "56f02a46dc6f0d169f587f41889681745874023c", "theirs": "c09fc4edda7a6699dec6af4bc7ea9e7786588193"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/312b5f3cde0689853fe078d348f08bb0.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
<<<<<<< ours (scripts/test/test-harness-taller-esenciales.ts)
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { verificarHashArchivo, PINNED_SHA256 } from "../taller/preparar-blender";
import { construirEvidencia, resolverBlender, tiposElemento } from "./lib/harness-taller";

async function main(): Promise<void> {
const root = await mkdtemp(path.join(os.tmpdir(), "taller-harness-"));
try {
  const noBlender = await resolverBlender({}, root);
  assert.ok("blocked" in noBlender, "missing ~/.local/opt/blender/current must be blocked");
  const invalidExecutable = await resolverBlender({ BLENDER_EXECUTABLE: path.join(root, "missing-blender") }, root);
  assert.ok("blocked" in invalidExecutable, "missing BLENDER_EXECUTABLE must be blocked");
  const blocked = construirEvidencia("REQ-021 SP-3 integration", { blockedReasons: ["Blender missing"] });
  assert.equal(blocked.status, "blocked");
  assert.notEqual(blocked.status, "passed", "missing Blender can never become a pass");

  const bytes = new TextEncoder().encode("archive");
  assert.throws(() => verificarHashArchivo(bytes, PINNED_SHA256), /SHA-256 no coincide/);

  const expectedPath = path.join(root, "expected.json"), observedPath = path.join(root, "observed.json");
  const expected = { schemaVersion: 1, elements: [{ type: "mesa-rectangular", objects: [{ name: "table", bounds_m: { min: { x: 0, y: 0, z: 0 }, max: { x: 1, y: 1, z: 1 } }, base_color: [[1, 0.5, 0.5, 1]] }] }] };
  const observed = structuredClone(expected);
  observed.elements[0]!.objects[0]!.bounds_m.max.z = 1.01;
  await writeFile(expectedPath, JSON.stringify(expected));
  await writeFile(observedPath, JSON.stringify(observed));
  const compared = spawnSync("python3", ["scripts/test/blender/comparar_glb.py", expectedPath, observedPath], { encoding: "utf8" });
  assert.equal(compared.status, 1);
  assert.match(compared.stderr, /mesa-rectangular\.table\.bounds_m\.max\.z/);

  for (const composition of [false, true]) {
    await (await import("./test-integracion-taller-esenciales")).modoAutoprueba(composition);
    const evidencePath = path.join(process.cwd(), ".evidence/REQ-021", composition ? "CG-2.integration.json" : "SP-3.integration.json");
    const evidence = JSON.parse(await readFile(evidencePath, "utf8")) as { status: string; perTypeResults: { type: string; status: string }[] };
    assert.equal(evidence.status, "blocked");
    assert.deepEqual(evidence.perTypeResults.map((item) => item.type), tiposElemento());
    assert.ok(evidence.perTypeResults.every((item) => item.status === "blocked"));
  }

  const incompleteEvidence = construirEvidencia("REQ-021 SP-3 integration", { perTypeResults: [{ type: "mesa", status: "passed" }], blockedReasons: ["missing app"] });
  assert.equal(incompleteEvidence.status, "blocked", "blocked reason takes precedence over partial passes");
  process.stdout.write("test-harness-taller-esenciales: ok (missing prerequisites block; comparison diagnostics; evidence schemas)\n");
} finally {
  await rm(root, { recursive: true, force: true });
}
}

void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
||||||| base
=======
import assert from "node:assert/strict";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { verificarHashArchivo, PINNED_SHA256 } from "../taller/preparar-blender";
import { construirEvidencia, resolverBlender, tiposElemento } from "./lib/harness-taller";

async function main(): Promise<void> {
const root = await mkdtemp(path.join(os.tmpdir(), "taller-harness-"));
try {
  const noBlender = await resolverBlender({ NODE_ENV: "test" }, root);
  assert.ok("blocked" in noBlender, "missing ~/.local/opt/blender/current must be blocked");
  const invalidExecutable = await resolverBlender({ NODE_ENV: "test", BLENDER_EXECUTABLE: path.join(root, "missing-blender") }, root);
  assert.ok("blocked" in invalidExecutable, "missing BLENDER_EXECUTABLE must be blocked");
  const blocked = construirEvidencia("REQ-021 SP-3 integration", { blockedReasons: ["Blender missing"] });
  assert.equal(blocked.status, "blocked");
  assert.notEqual(blocked.status, "passed", "missing Blender can never become a pass");

  const bytes = new TextEncoder().encode("archive");
  assert.throws(() => verificarHashArchivo(bytes, PINNED_SHA256), /SHA-256 no coincide/);

  const expectedPath = path.join(root, "expected.json"), observedPath = path.join(root, "observed.json");
  const expected = { schemaVersion: 1, elements: [{ type: "mesa-rectangular", objects: [{ name: "table", bounds_m: { min: { x: 0, y: 0, z: 0 }, max: { x: 1, y: 1, z: 1 } }, base_color: [[1, 0.5, 0.5, 1]] }] }] };
  const observed = structuredClone(expected);
  observed.elements[0]!.objects[0]!.bounds_m.max.z = 1.01;
  await writeFile(expectedPath, JSON.stringify(expected));
  await writeFile(observedPath, JSON.stringify(observed));
  const compared = spawnSync("python3", ["scripts/test/blender/comparar_glb.py", expectedPath, observedPath], { encoding: "utf8" });
  assert.equal(compared.status, 1);
  assert.match(compared.stderr, /mesa-rectangular\.table\.bounds_m\.max\.z/);

  for (const composition of [false, true]) {
    await (await import("./test-integracion-taller-esenciales")).modoAutoprueba(composition);
    const evidencePath = path.join(process.cwd(), ".evidence/REQ-021", composition ? "CG-2.integration.json" : "SP-3.integration.json");
    const evidence = JSON.parse(await readFile(evidencePath, "utf8")) as { status: string; perTypeResults: { type: string; status: string }[] };
    assert.equal(evidence.status, "blocked");
    assert.deepEqual(evidence.perTypeResults.map((item) => item.type), tiposElemento());
    assert.ok(evidence.perTypeResults.every((item) => item.status === "blocked"));
  }

  const incompleteEvidence = construirEvidencia("REQ-021 SP-3 integration", { perTypeResults: [{ type: "mesa", status: "passed" }], blockedReasons: ["missing app"] });
  assert.equal(incompleteEvidence.status, "blocked", "blocked reason takes precedence over partial passes");
  process.stdout.write("test-harness-taller-esenciales: ok (missing prerequisites block; comparison diagnostics; evidence schemas)\n");
} finally {
  await rm(root, { recursive: true, force: true });
}
}

void main().catch((error: unknown) => { console.error(error); process.exitCode = 1; });
>>>>>>> theirs

```

## Resolution request 67302a71b7947706bdbcbc0d72dbc129 (src/app/3d/page.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/67302a71b7947706bdbcbc0d72dbc129.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/67302a71b7947706bdbcbc0d72dbc129.diff3`
- blobs: base `650e89e355aa29fdf5e6048a8b2454d626cc7263`, ours `c194b0a62a400af397985389dfc8d5b06dc441e7`, theirs `d06542945c69c20db18505f56e083d49a187d3ee` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "217e5e5053d0497c4867ff21dae3c33e3fd8170a", "ours": "56f02a46dc6f0d169f587f41889681745874023c", "theirs": "c09fc4edda7a6699dec6af4bc7ea9e7786588193"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/67302a71b7947706bdbcbc0d72dbc129.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
import type { Metadata, Viewport } from "next";
import { Suspense } from "react";
import { Taller3D } from "@/components/tres-d/Taller3D";
import { Taller3DConPermisoPersonal } from "./Taller3DConPermisoPersonal";
import { SharedQuoteFlagsProvider } from "@/components/shared-quotes/SharedQuoteFlags";

export const metadata: Metadata = { title: "Globos en 3D · Sempertex" };

/** Como en /asistente: sin esto, env(safe-area-inset-*) vale 0 y el teclado del celular tapa el chat de la IA. */
export const viewport: Viewport = { width: "device-width", initialScale: 1, viewportFit: "cover", interactiveWidget: "resizes-content" };

export default async function Pagina3D({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const query = await searchParams;
  const requestedDecoration = Array.isArray(query.decoracion) ? query.decoracion[0] : query.decoracion;
  const readerEnabled = process.env.COTIZACION_COMPARTIDA_READER_ENABLED === "true";
  const writerEnabled = readerEnabled && process.env.COTIZACION_COMPARTIDA_WRITER_ENABLED === "true";
  return (
    <SharedQuoteFlagsProvider readerEnabled={readerEnabled} writerEnabled={writerEnabled}>
<<<<<<< ours (src/app/3d/page.tsx)
      <Suspense fallback={<Taller3D />}>
        <Taller3DConPermisoPersonal />
      </Suspense>
||||||| base
      <Taller3D />
=======
      <Suspense fallback={<Taller3D />}>
        <Taller3DConPermisoPersonal decoracionId={requestedDecoration ?? null} />
      </Suspense>
>>>>>>> theirs
    </SharedQuoteFlagsProvider>
  );
}

```

## Resolution request 6df4cea9605036b2ac01269b320741b1 (src/components/ui/shell/CabeceraApp.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/6df4cea9605036b2ac01269b320741b1.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/6df4cea9605036b2ac01269b320741b1.diff3`
- blobs: base `b19d503d7792e2ec79c4dceb5f262c9c8478d66c`, ours `a973c4c3be282937da6b50fd990d0ac2f82eeaa7`, theirs `26e1c70e379805a9b744a8017fe60dd56ef2fab8` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "b3f997fe050f00d031f8ff7103d279b1f33f08c5", "ours": "4a51d40d934170de8275f4e709cdf5f840eded91", "theirs": "88d643b5be177e0ba03178d7fddd523b9ba7f5c7"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/6df4cea9605036b2ac01269b320741b1.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "motion/react";
import { ChartColumn, FlaskConical, ListChecks, Monitor, Moon, Shield, Sun, Trash2 } from "lucide-react";
import { OPCIONES_TEMA } from "@/lib/tema/tema";
import { PERMISOS } from "@/lib/cuentas/permisos";
import { useTema } from "@/lib/tema/use-tema";
import type { NivelCreatividad } from "@/lib/ia/escena/creatividad";
import type { ModoVista } from "@/lib/estado/modo-vista";
import { SwitchModoVista } from "@/components/modo/SwitchModoVista";
import { InterruptorTema } from "@/components/ui/interruptor-tema";
import { MenuApp, type ItemMenu } from "./MenuApp";
import { SelectorCreatividad } from "./SelectorCreatividad";
import { textosHerramientas } from "@/components/herramientas/textos-herramientas";
import type { Idioma } from "@/lib/idioma/idioma";

type Props = {
  language?: Idioma;
  /** "Cumpleaños · rosa y plata · hasta $ 1.500.000" o null si el brief está vacío. */
  contexto: string | null;
  creatividad?: NivelCreatividad;
  onCreatividad?: (nivel: NivelCreatividad) => void;
  modoVista: ModoVista;
  onModoVista: (modo: ModoVista) => void;
  onLimpiar: () => void;
  limpiarDeshabilitado: boolean;
  /** Cómo se llama esa acción en el menú (la guiada: «Empezar de nuevo», que confirma antes); por defecto «Limpiar chat». */
  etiquetaLimpiar?: string;
  iconoLimpiar?: ReactNode;
  /** Abre la hoja de selección manual; undefined cuando no aplica (hay propuesta en modo usuario). */
  onAbrirSeleccion?: () => void;
  totalSeleccion: number;
  /** Controles técnicos: se muestran en una barra aparte solo en modo dev. */
  barraDev?: ReactNode;
  /** Vista guiada: sin el interruptor «Modo dev» (el cliente no lo necesita). */
  ocultarModoDev?: boolean;
  permisos?: readonly string[];
};

/** Marca simple de la maqueta: cuadro violeta con un anillo y un punto. */
function MarcaIcono() {
  return (
    <span className="app-marca-icono" aria-hidden="true">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeOpacity="0.65" strokeWidth="1.2" />
        <circle cx="8" cy="8" r="1.8" fill="currentColor" />
      </svg>
    </span>
  );
}

/**
 * Cabecera de una sola línea (maquetas Main y EstadoInicial): marca, contexto
 * del evento al centro, creatividad compacta, tema, "Modo dev" y menú.
 */
<<<<<<< ours (src/components/ui/shell/CabeceraApp.tsx)
export function CabeceraApp({ language = "es", contexto, creatividad, onCreatividad, modoVista, onModoVista, onLimpiar, limpiarDeshabilitado, etiquetaLimpiar, iconoLimpiar, onAbrirSeleccion, totalSeleccion, barraDev, ocultarModoDev = false }: Props) {
||||||| base
export function CabeceraApp({ contexto, creatividad, onCreatividad, modoVista, onModoVista, onLimpiar, limpiarDeshabilitado, etiquetaLimpiar = "Limpiar chat", iconoLimpiar, onAbrirSeleccion, totalSeleccion, barraDev, ocultarModoDev = false }: Props) {
=======
export function CabeceraApp({ contexto, creatividad, onCreatividad, modoVista, onModoVista, onLimpiar, limpiarDeshabilitado, etiquetaLimpiar = "Limpiar chat", iconoLimpiar, onAbrirSeleccion, totalSeleccion, barraDev, ocultarModoDev = false, permisos = [] }: Props) {
>>>>>>> theirs
  const pathname = usePathname();
  const copy = textosHerramientas(language);
  const esDev = modoVista === "dev";
  // Vista guiada (pensada para el móvil): tema y menú con el blanco táctil de 44 px.
  const tactil = pathname === "/asistente";
  const { preferencia: preferenciaTema, cambiar: cambiarTema } = useTema();
  const tienePermiso = (permiso: string) => permisos.includes(permiso);
  const ICONO_TEMA = { light: <Sun className="size-4" />, dark: <Moon className="size-4" />, sistema: <Monitor className="size-4" /> } as const;
  const items: ItemMenu[] = [
<<<<<<< ours (src/components/ui/shell/CabeceraApp.tsx)
||||||| base
    { tipo: "enlace", id: "catalogo", etiqueta: "Explorar catálogo", href: "/catalogo", icono: <LayoutGrid className="size-4" /> },
=======
    ...(tienePermiso(PERMISOS.catalogo) ? [{ tipo: "enlace" as const, id: "catalogo", etiqueta: "Explorar catálogo", href: "/catalogo", icono: <LayoutGrid className="size-4" /> }] : []),
>>>>>>> theirs
    ...(onAbrirSeleccion
      ? [{ tipo: "accion" as const, id: "seleccion", etiqueta: copy.selectSummary(totalSeleccion), onSeleccionar: onAbrirSeleccion, icono: <ListChecks className="size-4" /> }]
      : []),
<<<<<<< ours (src/components/ui/shell/CabeceraApp.tsx)
    { tipo: "accion", id: "limpiar", etiqueta: etiquetaLimpiar ?? copy.clearChat, onSeleccionar: onLimpiar, deshabilitado: limpiarDeshabilitado, icono: iconoLimpiar ?? <Trash2 className="size-4" /> },
||||||| base
    { tipo: "accion", id: "limpiar", etiqueta: etiquetaLimpiar, onSeleccionar: onLimpiar, deshabilitado: limpiarDeshabilitado, icono: iconoLimpiar ?? <Trash2 className="size-4" /> },
    pathname === "/asistente"
      ? { tipo: "enlace", id: "vista-clasica", etiqueta: "Vista clásica", href: "/" }
      : { tipo: "enlace", id: "vista-guiada", etiqueta: "Asistente guiado", href: "/asistente" },
    // El taller 3D de globos, en producción y en local.
    { tipo: "enlace", id: "taller-3d", etiqueta: "Globos en 3D", href: "/3d", icono: <Box className="size-4" /> },
=======
    { tipo: "accion", id: "limpiar", etiqueta: etiquetaLimpiar, onSeleccionar: onLimpiar, deshabilitado: limpiarDeshabilitado, icono: iconoLimpiar ?? <Trash2 className="size-4" /> },
    pathname === "/asistente"
      ? { tipo: "enlace", id: "vista-clasica", etiqueta: "Vista clásica", href: "/" }
      : { tipo: "enlace", id: "vista-guiada", etiqueta: "Asistente guiado", href: "/asistente" },
    ...(tienePermiso(PERMISOS.taller_3d) ? [{ tipo: "enlace" as const, id: "taller-3d", etiqueta: "Globos en 3D", href: "/3d", icono: <Box className="size-4" /> }] : []),
>>>>>>> theirs
    // D10: the header switch flips light/dark quickly; here the customer can also go back to "Sistema".
    { tipo: "separador", id: "sep-tema" },
    { tipo: "titulo", id: "titulo-tema", etiqueta: copy.theme },
    ...OPCIONES_TEMA.map((opcion): ItemMenu => ({ tipo: "opcion", id: `tema-${opcion.valor}`, etiqueta: opcion.valor === "light" ? copy.themeLight : opcion.valor === "dark" ? copy.themeDark : copy.themeSystem, marcado: preferenciaTema === opcion.valor, onSeleccionar: () => cambiarTema(opcion.valor), icono: ICONO_TEMA[opcion.valor] })),
    ...(esDev
      ? ([
<<<<<<< ours (src/components/ui/shell/CabeceraApp.tsx)
          { tipo: "separador", id: "sep-dev" },
          { tipo: "enlace", id: "estadisticas", etiqueta: copy.statistics, href: "/estadisticas", icono: <ChartColumn className="size-4" /> },
          { tipo: "enlace", id: "laboratorio", etiqueta: copy.laboratory, href: "/laboratorio-referencias", icono: <FlaskConical className="size-4" /> },
          { tipo: "enlace", id: "admin", etiqueta: copy.administration, href: "/admin", icono: <Shield className="size-4" /> },
||||||| base
          { tipo: "separador", id: "sep-dev" },
          { tipo: "enlace", id: "estadisticas", etiqueta: "Estadísticas", href: "/estadisticas", icono: <ChartColumn className="size-4" /> },
          { tipo: "enlace", id: "laboratorio", etiqueta: "Laboratorio JSON", href: "/laboratorio-referencias", icono: <FlaskConical className="size-4" /> },
          { tipo: "enlace", id: "admin", etiqueta: "Panel de administración", href: "/admin", icono: <Shield className="size-4" /> },
=======
          ...(tienePermiso(PERMISOS.herramientas_internas) ? [
            { tipo: "separador" as const, id: "sep-dev" },
            { tipo: "enlace" as const, id: "estadisticas", etiqueta: "Estadísticas", href: "/estadisticas", icono: <ChartColumn className="size-4" /> },
            { tipo: "enlace" as const, id: "laboratorio", etiqueta: "Laboratorio JSON", href: "/laboratorio-referencias", icono: <FlaskConical className="size-4" /> },
            { tipo: "enlace" as const, id: "admin", etiqueta: "Panel de administración", href: "/admin", icono: <Shield className="size-4" /> },
          ] : []),
          ...(tienePermiso(PERMISOS.administracion_usuarios) ? [
            { tipo: "enlace" as const, id: "admin-cuentas", etiqueta: "Administración de cuentas", href: "/admin/cuentas", icono: <Shield className="size-4" /> },
          ] : []),
>>>>>>> theirs
        ] satisfies ItemMenu[])
      : []),
  ];

  return (
    <>
      <header className="app-header">
        <div className="app-marca">
          <MarcaIcono />
          <h1 tabIndex={-1} className="sr-only truncate text-sm font-semibold tracking-[-0.015em] focus-visible:outline-3 focus-visible:outline-offset-4 focus-visible:outline-acento min-[480px]:not-sr-only">{copy.sceneTitle}</h1>
        </div>
        <div className="app-contexto" data-testid="contexto-evento">
          <AnimatePresence mode="wait" initial={false}>
            {contexto && (
              <motion.p key={contexto} className="truncate" title={contexto} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.2 }}>
                {contexto}
              </motion.p>
            )}
          </AnimatePresence>
        </div>
        <div className="app-acciones">
          {creatividad !== undefined && onCreatividad && <SelectorCreatividad valor={creatividad} onCambiar={onCreatividad} language={language} />}
          <InterruptorTema className={tactil ? "size-11" : ""} language={language} />
          {!ocultarModoDev && <SwitchModoVista modo={modoVista} onCambiar={onModoVista} language={language} />}
          <MenuApp items={items} etiqueta={copy.moreOptions} {...(tactil ? { claseBoton: "ui-icon-button size-11" } : {})} />
        </div>
      </header>
      {contexto && <p className="app-contexto-movil truncate">{contexto}</p>}
      {esDev && barraDev && (
        <div className="app-barra-dev" aria-label={copy.developmentControls} role="group">
          {barraDev}
        </div>
      )}
    </>
  );
}

```

## Resolution request 7e0709f8ac37f2164efc6081f259c5df (src/app/page.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/7e0709f8ac37f2164efc6081f259c5df.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/7e0709f8ac37f2164efc6081f259c5df.diff3`
- blobs: base `1286483217b68b40c892542cd729dab0f7447e61`, ours `92298fa69ce36192693304c7d08ff9f926c754c0`, theirs `76ceaebab26ee8e23f5518ab66b409770e9944a8` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "b3f997fe050f00d031f8ff7103d279b1f33f08c5", "ours": "4a51d40d934170de8275f4e709cdf5f840eded91", "theirs": "88d643b5be177e0ba03178d7fddd523b9ba7f5c7"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/7e0709f8ac37f2164efc6081f259c5df.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
<<<<<<< ours (src/app/page.tsx)
import { connection } from "next/server";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { PortadaHerramientas } from "@/components/herramientas/PortadaHerramientas";
import { SESSION_COOKIE } from "@/lib/auth/session";
import { resolverSesion } from "@/lib/cuentas/sesion";
import { getRequestLanguage } from "@/lib/idioma/servidor";

export const instant = false;

export default async function HomePage() {
  await connection();
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  const session = token && /^[A-Za-z0-9_-]{43}$/.test(token) ? await resolverSesion(token) : null;
  if (!session) redirect("/login");

  return <PortadaHerramientas permissions={session.permissions} roles={session.roles} language={await getRequestLanguage()} />;
||||||| base
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Lock, RefreshCw } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CREATIVIDAD_POR_DEFECTO, type NivelCreatividad } from "@/lib/ia/escena/creatividad";
import { DecoracionCard } from "@/components/DecoracionCard";
import { Lightbox } from "@/components/Lightbox";
import { PromptModal } from "@/components/PromptModal";
import { Markdown } from "@/components/Markdown";
import { ProductoCard } from "@/components/ProductoCard";
import { TarjetaCotizacion } from "@/components/TarjetaCotizacion";
import { CotizacionProfesional } from "@/components/cotizacion/CotizacionProfesional";
import { TarjetaPlanDecoracion } from "@/components/TarjetaPlanDecoracion";
import { ReferenceAnalysisController } from "@/components/references/ReferenceAnalysisController";
import { SOLO_ANALISIS_FOTO } from "@/lib/ia/nucleo/feature-flags";
import { cargarFactorPlazoCliente, factorPlazoCliente } from "@/lib/ia/plazo-cliente";
import type { ReferenceDraft } from "@/components/references/ReferenceReviewPanel";
import { PasosAsistente } from "@/components/propuesta";
import { useSeleccion } from "@/lib/estado/seleccion";
import type { Cotizacion } from "@/lib/cotizacion/motor";
import type { Imagen, PeticionImagen } from "@/lib/ia/nucleo/tipos";
import { prepararFotoReferencia, redimensionarImagen } from "@/lib/imagen-cliente/preparar-foto";
import { ASPECTOS_SOPORTADOS, aspectoMasCercano } from "@/lib/ia/nucleo/aspecto";
import type { ReferenceBlueprintV2 } from "@/lib/ia/referencia/reference-blueprint";
import type { PlanResuelto } from "@/lib/plan/resuelto";
import type { ItemRechazado, ItemValidado } from "@/lib/rag/chat/validar";
import type { Faceta, FiltrosCatalogo } from "@/lib/shopify/consultas";
import type { Brief, DecoracionConProductos, Producto } from "@/lib/types";
import { classifyGenerationIds, normalizeGenerationSources } from "@/lib/generacion/provenance";
import { cuerpoGeneracion } from "@/lib/generacion/cuerpo-generacion";
import { MENSAJE_SOLO_REFERENCIAS } from "@/lib/estado/mensaje-foto-referencia";

import { ChatSseEventV1Schema } from "@/lib/ia/contracts/chat-v1";
import { CATALOGO_ERRORES_UI_V1, construirUiErrorV1, leerUiErrorV1, type AccionUiV1, type UiErrorV1 } from "@/lib/ia/contracts/ui-error-v1";
import { AvisoError } from "@/components/errores/AvisoError";
import { useModoVista } from "@/lib/estado/modo-vista";
import { abrirPromptAutomaticamente } from "@/lib/estado/modo-vista-reglas";
import { aplicarEventoHerramienta, cerrarPasos, type PasoAsistente } from "@/lib/estado/pasos-asistente";
import { contextoEventoConversacion } from "@/lib/estado/contexto-evento";
import { crearEsperaAnalisis, type EstadoAnalisisReferencia } from "@/lib/estado/espera-analisis";
import { adjuntosParaGeneracion, contextoDeGeneracion } from "@/lib/estado/generacion-adjuntos";
import { aligerarAdjuntos, claveImagen, imagenesSinMiniatura, type AdjuntosTurno } from "@/lib/estado/persistencia-adjuntos";
import { respetarReintentable, uiErrorDesdeEventoChat, type OrigenError } from "@/lib/estado/estado-error";
import { mensajeErrorCliente } from "@/lib/estado/mensaje-error-cliente";
import { nuevaConversacion, obtenerIdConversacion, registrarEventoCliente } from "@/lib/registro/cliente";
import { CalificacionClasica } from "@/components/ui/shell/CalificacionClasica";
import {
  CLAVE_GENERACIONES,
  generacionParaRestaurar,
  leerGeneraciones,
  REDUCCIONES_IMAGEN_GENERADA,
  elegirImagenReducida,
  registrarGeneracion,
  registrarVistaPreviaNoDisponible,
  serializarGeneraciones,
  sinImagenes,
} from "@/lib/estado/persistencia-generacion";
import { creatividadGuardada } from "@/lib/estado/persistencia-creatividad";
import { imagenDeFotoEjemplo, type FotoEjemplo } from "@/lib/referencias-ejemplo/manifiesto";
import { CabeceraApp } from "@/components/ui/shell/CabeceraApp";
import { Compositor } from "@/components/ui/shell/Compositor";
import { EsperaAsistente } from "@/components/ui/shell/EsperaAsistente";
import { CargaImagen } from "@/components/propuesta/CargaImagen";
import { CierrePropuesta } from "@/components/propuesta/CierrePropuesta";
import { coloresCliente } from "@/lib/plan/presentacion-cliente";
import { DialogoEjemplos, GaleriaEjemplos } from "@/components/ui/shell/GaleriaEjemplos";
import { HojaSeleccion } from "@/components/ui/shell/HojaSeleccion";
import { volarFoto } from "@/components/ui/shell/vuelo-foto";
import { marcarProducido } from "@/components/feedback-ia/producidos";
import { BotonVoz } from "@/components/voz/BotonVoz";

type ProveedorId = "gemini";
const NOMBRE_PROVEEDOR: Record<ProveedorId, string> = {
  gemini: "Gemini 3.6 Flash (chat)",
};

type GeneracionVisible = {
  modo: "flux";
  solicitado: ProveedorId;
  etiqueta: string;
  prompts: Array<{ label: string; prompt: string }>;
};

type Mensaje = {
  /** Estable por mensaje (no el índice del array) — necesario para que
   * Motion pueda animar entradas/salidas de la lista de forma confiable. */
  id: string;
  role: "user" | "assistant";
  content: string;
  productos?: Producto[];
  decoraciones?: DecoracionConProductos[];
  categorias?: Faceta[];
  /** Filtros que produjeron `categorias` (ocasión, colores…) — se reusan al navegar a un tipo puntual sin pasar por la IA. */
  categoriasFiltros?: FiltrosCatalogo;
  plan?: PlanResuelto;
  /** Brief del evento `fin` de esta respuesta: la cabecera distingue si cambió después de la última propuesta. */
  brief?: Brief;
  cotizacion?: Cotizacion;
  referenceBlueprint?: ReferenceBlueprintV2;
  /** Debug: JSON crudo que usó el análisis de imágenes de referencia. Va
   * aparte del `content` markdown (que no interpreta HTML) para poder
   * mostrarlo colapsado sin reventar el layout del chat. */
  analisisReferencias?: unknown;
  /** Piezas ya validadas contra la DB real (plan Fase 4/6) — se muestran con
   * foto y link a la tienda para poder verificar que el modelo no inventó
   * nada, en vez de confiar a ciegas en la tabla de texto que redacta. */
  ragValidados?: ItemValidado[];
  /** Fase 3.11: piezas que el modelo propuso pero el backend descartó (no
   * estaban en la whitelist recuperada, variante agotada, etc.). El backend
   * ya calcula esto — antes se recibía en el SSE y se tiraba sin mostrarlo,
   * así que una sustitución o un descarte podía pasar sin que el cliente lo
   * viera nunca (viola "nunca sustituir en silencio"). */
  ragRechazados?: ItemRechazado[];
  /**
   * Fotos del turno que produjo este mensaje (iteración 4): miniatura en el
   * mensaje del cliente y recortes por pieza en la propuesta. El estado de
   * adjuntos del compositor puede cambiar después, así que se copian aquí al
   * enviar. En sessionStorage solo va una miniatura liviana de las más
   * recientes (src/lib/estado/persistencia-adjuntos.ts).
   */
  adjuntos?: AdjuntosTurno;
  /** Pasos en vivo del asistente para este turno (eventos SSE `herramienta`). */
  pasos?: PasoAsistente[];
};

/** Una foto restaurada de sessionStorage ya viene como data URL (su miniatura). */
function dataUrl(imagen: { base64: string; mime: string }): string {
  return imagen.base64.startsWith("data:") ? imagen.base64 : `data:${imagen.mime};base64,${imagen.base64}`;
}

/** Copia liviana de los adjuntos del turno; los ids siguen el orden que usa /api/references/analyze (REF_01…). */
function adjuntosDelTurno(referencias: readonly Imagen[], fotoEspacio: Imagen | null): AdjuntosTurno | undefined {
  if (!referencias.length && !fotoEspacio) return undefined;
  return {
    referencias: referencias.map(({ base64, mime }, indice) => ({ id: `REF_${String(indice + 1).padStart(2, "0")}`, base64, mime })),
    ...(fotoEspacio ? { fotoEspacio: { base64: fotoEspacio.base64, mime: fotoEspacio.mime } } : {}),
  };
}

const SALUDO: Mensaje = {
  id: "saludo",
  role: "assistant",
  content:
    "¡Hola! Soy el asistente de decoración. Cuéntame qué evento estás planeando y te armo una propuesta. En cualquier momento puedes tocar, agregar o quitar piezas tú mismo.",
};

// v2 invalida conversaciones que contienen planes resueltos antes de que
// existiera el límite de sustituciones (por ejemplo R-12→R-24). Reutilizar
// esos objetos haría que la UI siguiera mostrando una cotización que el
// servidor actual ya rechaza.
const CLAVE_CHAT = "demo_chat_v4";
const CLAVE_CHAT_LEGACY = "demo_chat_v1";

const SUGERENCIAS = [
  "Quiero ideas para mi boda en un jardín",
  "XV años estilo glamour en salón",
  "Algo boho en tonos tierra",
];

const LIMITE_INACTIVIDAD_CHAT_MS = 90_000;
/** Espera máxima de un análisis de la foto que no responde antes de enviar el turno sin él (p95 medido: 20 s). Si falla, no se espera. */
const LIMITE_ESPERA_ANALISIS_MS = 45_000;

/** `order` de flexbox para lo que va después de toda la conversación (visualización, errores, análisis sin enviar). */
const ORDEN_AL_FINAL = 1_000_000;

type DatosFin = {
  reply: string;
  brief?: Brief;
  recomendaciones?: Producto[];
  decoraciones?: DecoracionConProductos[];
  categorias?: Faceta[];
  filtrosCategorias?: FiltrosCatalogo;
  cotizacion?: Cotizacion;
  /** Piezas que la IA decidió proponer por su cuenta — dispara /api/generate sin que el cliente haga clic. */
  seleccionIA?: Producto[];
  instruccionIA?: string;
  ragValidados?: ItemValidado[];
  ragRechazados?: ItemRechazado[];
  plan?: PlanResuelto;
  referenceBlueprint?: ReferenceBlueprintV2;
};

type GenerarOverride = {
  ids: string[];
  /** Exact RAG variant ids. Kept separate from legacy/manual catalog ids. */
  ragVariantIds?: string[];
  paquetes?: Record<string, number>;
  instruccion?: string;
  brief?: Brief;
  solicitudUsuario?: string;
  /**
   * Cuando viene de aplicar una cotización editada a mano: `ids` ya es la
   * lista completa y definitiva de piezas (incluye lo que el cliente quitó
   * o reemplazó). Sin este flag, `generar()` reinyecta encima las piezas
   * del último `ragValidados` y las de la selección compartida — exacto lo
   * que se quiere evitar, porque una pieza recién quitada "reaparecería".
   */
  soloIds?: boolean;
  /**
   * Piezas manuales a usar tal cual cuando `soloIds` es true — no se puede
   * derivar de `seleccionados` porque `reemplazarTodo()` (que se llama justo
   * antes) todavía no aplicó su actualización de estado en este mismo tick.
   */
  manualProducts?: Producto[];
  /** Propuesta aprobada. Toda imagen sale de una (ADR-0023, paso 1). */
  plan: PlanResuelto;
  /** Mensaje exacto al que debe volver la cotización final de esta generación. */
  anchorMessageId?: string;
  /** Adjuntos de la propuesta anclada; evita usar fotos de otro turno. */
  adjuntos?: AdjuntosTurno;
};

type ErrorVisible = { ui: UiErrorV1; origen: OrigenError };

const ACCIONES_POR_ORIGEN: Readonly<Record<OrigenError, ReadonlySet<AccionUiV1>>> = {
  chat: new Set<AccionUiV1>(["reintentar", "ajustar_propuesta", "pedir_nueva_propuesta", "revisar_adjuntos"]),
  generacion: new Set<AccionUiV1>(["reintentar", "revisar_propuesta", "pedir_nueva_propuesta", "ajustar_propuesta", "revisar_adjuntos"]),
  catalogo: new Set<AccionUiV1>(),
  plan: new Set<AccionUiV1>(["revisar_propuesta"]),
};

function errorLocal(code: Parameters<typeof construirUiErrorV1>[0], mensaje: string, mensajeUsuario?: string): UiErrorV1 {
  return construirUiErrorV1(code, { mensaje, mensajeUsuario });
}

/** The page kept only thumbnails of the photos (a reload): the file itself was fine. */
const FOTOS_PERDIDAS_AL_RECARGAR = "La página se recargó y de tus fotos solo guardé miniaturas. Vuelve a adjuntarlas y creo la imagen.";

function campoTexto(valor: unknown, campo: string): string | undefined {
  if (typeof valor !== "object" || valor === null || !(campo in valor)) return undefined;
  const dato: unknown = (valor as Record<string, unknown>)[campo];
  return typeof dato === "string" && dato.length > 0 ? dato : undefined;
}

/** `retryable` del sobre de error (error.v1); undefined si no viene. */
function campoReintentable(valor: unknown): boolean | undefined {
  if (typeof valor !== "object" || valor === null || !("retryable" in valor)) return undefined;
  const dato: unknown = (valor as Record<string, unknown>).retryable;
  return typeof dato === "boolean" ? dato : undefined;
}

/**
 * Streaming real (§5.4 del plan): parsea a mano los bloques
 * `event: X\ndata: Y\n\n` de la respuesta SSE de /api/chat. No se usa
 * EventSource porque necesita ir por POST con cuerpo JSON, algo que
 * EventSource no soporta.
 */
async function consumirSSE(
  body: ReadableStream<Uint8Array>,
  manejadores: {
    onTexto: (delta: string) => void;
    onHerramienta: (nombre: string, estado: "ejecutando" | "lista", ok?: boolean) => void;
    onFin: (datos: DatosFin) => void;
    onError: (datos: { error?: string; code?: string; causa?: string; request_id?: string; retryable?: boolean }) => void;
    onActividad?: () => void;
  },
) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let recibioFinal = false;
  let recibioError = false;

  function procesarBloque(bloque: string) {
    let evento = "message";
    let datosCrudo = "";
    for (const linea of bloque.split("\n")) {
      if (linea.startsWith("event: ")) evento = linea.slice(7);
      else if (linea.startsWith("data: ")) datosCrudo += linea.slice(6);
    }
    if (!datosCrudo) return;
    const datos = JSON.parse(datosCrudo) as unknown;
    if (recibioFinal || recibioError) return;
    const eventoValidado = ChatSseEventV1Schema.safeParse(datos);
    if (!eventoValidado.success || eventoValidado.data.type !== evento) {
      throw new Error("El servidor devolvió un evento SSE inválido.");
    }
    const datosValidados = eventoValidado.data;
    manejadores.onActividad?.();
    if (datosValidados.type === "texto") manejadores.onTexto(datosValidados.delta);
    else if (datosValidados.type === "herramienta") manejadores.onHerramienta(datosValidados.nombre, datosValidados.estado, datosValidados.ok);
    else if (datosValidados.type === "fin") {
      recibioFinal = true;
      manejadores.onFin(datosValidados);
    } else if (datosValidados.type === "error") {
      recibioError = true;
      manejadores.onError(datosValidados);
    }
  }

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let indice: number;
    while ((indice = buffer.indexOf("\n\n")) !== -1) {
      procesarBloque(buffer.slice(0, indice));
      buffer = buffer.slice(indice + 2);
    }
  }
  if (!recibioFinal && !recibioError) throw new Error("El asistente cerró la respuesta antes de terminar.");
}

// Debe coincidir con LIMITE_REFERENCIAS_CLIENTE en src/app/api/generate/route.ts.
const LIMITE_REFERENCIAS_CLIENTE = 3;

/** Mapea una proporción real (ancho/alto) al aspecto soportado más cercano, comparando razones en escala logarítmica (así 3:2 y 2:3 no se confunden solo por estar "cerca" en valor absoluto). */
function aspectoDe(ancho: number, alto: number): PeticionImagen["aspecto"] {
  return aspectoMasCercano(ancho / alto);
}

// El redimensionado de las fotos vive en `src/lib/imagen-cliente/preparar-foto.ts`: la guiada prepara la foto de
// inspiración con la MISMA función (`prepararFotoReferencia`), así las dos vistas leen la misma imagen.

/**
 * Recorta al centro para que la imagen coincida EXACTO con uno de los 4
 * aspectos que soportan los proveedores, en vez de mandarla con su
 * proporción real y dejar que el modelo de edición decida cómo encajarla.
 * Sin este paso, una foto de celular en 4:3 se manda "tal cual" hacia un
 * lienzo 3:2 — el desajuste de proporción es una fuente real de distorsión
 * de perspectiva en la imagen generada (el modelo tiene que estirar o
 * recortar el espacio real para llenar un lienzo con otra forma).
 */
async function recortarAlAspecto(
  base64: string,
  mime: string,
  aspecto: PeticionImagen["aspecto"],
): Promise<{ base64: string; ancho: number; alto: number }> {
  const bitmap = await createImageBitmap(await (await fetch(`data:${mime};base64,${base64}`)).blob());
  try {
    const razonObjetivo = ASPECTOS_SOPORTADOS.find((a) => a.valor === aspecto)?.razon ?? 3 / 2;
    const razonActual = bitmap.width / bitmap.height;
    let anchoRecorte = bitmap.width;
    let altoRecorte = bitmap.height;
    if (razonActual > razonObjetivo) {
      anchoRecorte = Math.round(bitmap.height * razonObjetivo);
    } else {
      altoRecorte = Math.round(bitmap.width / razonObjetivo);
    }
    const offsetX = Math.floor((bitmap.width - anchoRecorte) / 2);
    const offsetY = Math.floor((bitmap.height - altoRecorte) / 2);

    const canvas = document.createElement("canvas");
    canvas.width = anchoRecorte;
    canvas.height = altoRecorte;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Este navegador no pudo procesar la imagen. Prueba con otro navegador.");
    ctx.drawImage(bitmap, offsetX, offsetY, anchoRecorte, altoRecorte, 0, 0, anchoRecorte, altoRecorte);

    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("No se pudo recortar la imagen."))), "image/jpeg", 0.85);
    });
    const base64Recortado = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve((reader.result as string).split(",")[1]);
      reader.onerror = () => reject(new Error("No se pudo leer la imagen recortada."));
      reader.readAsDataURL(blob);
    });
    return { base64: base64Recortado, ancho: anchoRecorte, alto: altoRecorte };
  } finally {
    bitmap.close();
  }
}

/** Miniatura JPEG liviana (data URL) de una foto del turno, para guardarla con la conversación. */
async function miniaturaImagen(imagen: { base64: string; mime: string }, maxDim = 480, calidad = 0.72): Promise<string> {
  const bitmap = await createImageBitmap(await (await fetch(dataUrl(imagen))).blob());
  try {
    const escala = Math.min(1, maxDim / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(bitmap.width * escala));
    canvas.height = Math.max(1, Math.round(bitmap.height * escala));
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Sin canvas 2D.");
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", calidad);
  } finally {
    bitmap.close();
  }
}

// Guard de generación, a nivel de módulo (una sola vez por pestaña, no por
// instancia de componente). Bug real: adjuntar una referencia y mandar un
// mensaje de chat casi a la vez puede hacer que DOS rutas independientes
// —la respuesta del chat (ve la referencia y confirma su propia selección)
// y el análisis automático de blueprint del panel de referencias— decidan
// generar cada una por su cuenta. `colaGeneracion` encadena ambas sobre la
// MISMA promesa: `.then()` en JavaScript garantiza qu
```

## Resolution request 8042b963196a321dcee14a10cf512e87 (scripts/test/test-integracion-decoraciones-personales.ts)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/8042b963196a321dcee14a10cf512e87.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/8042b963196a321dcee14a10cf512e87.diff3`
- blobs: base `-`, ours `e83a8e1bdf093d0384194ba72a587d436ea2eac8`, theirs `e915345d3dcb66e09faad83d06fde3629a7ff61f` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "217e5e5053d0497c4867ff21dae3c33e3fd8170a", "ours": "56f02a46dc6f0d169f587f41889681745874023c", "theirs": "c09fc4edda7a6699dec6af4bc7ea9e7786588193"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/8042b963196a321dcee14a10cf512e87.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
<<<<<<< ours (scripts/test/test-integracion-decoraciones-personales.ts)
import assert from "node:assert/strict";
import { spawn, spawnSync, type ChildProcess } from "node:child_process";
import { createServer } from "node:net";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { chromium, type Browser, type BrowserContext, type Page } from "playwright";
import { VERSION_AVISO_DATOS } from "../../src/lib/cuentas/aviso-datos";
import { createAccountService } from "../../src/lib/cuentas/servicio";
import { ESCENAS_PREDEFINIDAS } from "../../src/lib/globos3d/escenas-presets";
import { itemDeEscena } from "../../src/lib/globos3d/biblioteca";
import type { Escena } from "../../src/lib/globos3d/escena";
import { createIsolatedTestDatabase, resolveTestDatabaseTarget } from "./lib/base-prueba";

const ROOT = process.cwd();
const EVIDENCE_PATH = path.join(ROOT, ".evidence/REQ-021/SP-5.integration.json");
const PASSWORD = "REQ021-Personal-Library-Password";
const LEGACY_KEY = "taller3d:biblioteca-propia:v1";
const PROJECT_KEY = "taller3d:escena:v1";
const LEGACY_NAME = "Decoración antigua local REQ-021";
const SAVED_NAME = "Composición persistente REQ-021";
const MAX_LOG_BYTES = 10_000;

type Account = { accountId: string; email: string; roleId: string };
type Child = ChildProcess;

function appendTail(previous: string, chunk: Buffer): string {
  return `${previous}${chunk.toString("utf8")}`.slice(-MAX_LOG_BYTES);
}

function redact(value: string): string {
  return value
    .replace(/postgres(?:ql)?:\/\/[^\s"']+/gi, "[redacted-db-url]")
    .replace(/([?&]token=)[^&\s"']+/gi, "$1[redacted]")
    .replace(/(session=)[^;\s]+/gi, "$1[redacted]")
    .replace(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/g, "[redacted-email]");
}

function run(command: string, args: string[], env: NodeJS.ProcessEnv): { status: number | null; output: string } {
  const result = spawnSync(command, args, { cwd: ROOT, env, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
  if (result.error) throw result.error;
  return { status: result.status, output: `${result.stdout}\n${result.stderr}` };
}

async function availablePort(): Promise<number> {
  const listener = createServer();
  await new Promise<void>((resolve, reject) => {
    listener.once("error", reject);
    listener.listen(0, "127.0.0.1", resolve);
  });
  const address = listener.address();
  assert.ok(address && typeof address !== "string");
  const port = address.port;
  await new Promise<void>((resolve, reject) => listener.close((error) => error ? reject(error) : resolve()));
  return port;
}

function buildEnvironment(home: string): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = {
    PATH: process.env.PATH,
    HOME: home,
    CI: "true",
    APP_ENV: "test",
    NODE_ENV: "production",
    NODE_OPTIONS: "--max-old-space-size=4096",
    NEXT_TELEMETRY_DISABLED: "1",
    CAPTURA_RENDERS_ENABLED: "1",
    VERCEL: "1",
  };
  assert.equal(env.DATABASE_URL, undefined);
  assert.equal(env.PICTURES_REQ021_DATABASE_URL, undefined);
  return env;
}

async function waitForServer(origin: string, child: Child, logs: { stdout: string; stderr: string }): Promise<void> {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`next start exited before /3d became available. ${redact(`${logs.stdout}\n${logs.stderr}`)}`);
    try {
      const response = await fetch(`${origin}/3d`, { signal: AbortSignal.timeout(2_000), redirect: "manual" });
      if (response.status < 500) return;
    } catch {
      // Keep polling while next start initializes.
    }
    await delay(500);
  }
  throw new Error(`next start did not become ready within 60 seconds. ${redact(`${logs.stdout}\n${logs.stderr}`)}`);
}

async function newContext(browser: Browser): Promise<BrowserContext> {
  return browser.newContext({ locale: "es-CO", viewport: { width: 1440, height: 1100 } });
}

async function signIn(page: Page, origin: string, account: Account): Promise<void> {
  await page.goto(`${origin}/login`);
  await page.getByLabel("Correo electrónico", { exact: true }).fill(account.email);
  await page.getByLabel("Contraseña", { exact: true }).fill(PASSWORD);
  const login = page.waitForResponse((response) => response.url().endsWith("/api/login") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  const response = await login;
  assert.equal(response.status(), 200, `Seeded ${account.roleId} account can authenticate`);
  const loginBody: unknown = await response.json();
  assert.ok(typeof loginBody === "object" && loginBody !== null && "permissions" in loginBody && Array.isArray(loginBody.permissions));
  const permissions = loginBody.permissions.filter((value): value is string => typeof value === "string");
  assert.ok(permissions.includes("taller_3d"), `Seeded ${account.roleId} has the Taller permission needed by the library API`);
  await page.waitForURL((url) => url.pathname === (account.roleId === "entusiasta" ? "/asistente" : "/3d"));
}

async function openLibrary(page: Page): Promise<void> {
  await page.goto(new URL("/3d", page.url()).toString());
  await page.getByRole("region", { name: "Biblioteca personal", exact: true }).waitFor({ timeout: 60_000 });
  await page.getByRole("button", { name: "En mi cuenta", exact: true }).waitFor();
  await page.getByRole("button", { name: "Guardar toda la escena", exact: true }).waitFor();
}

function initialProjectScene(): Escena {
  const preset = ESCENAS_PREDEFINIDAS.find((item) => item.id === "arco_organico_columnas_guirnalda");
  assert.ok(preset, "SPEC scenario uses a real scene as the starting project");
  return structuredClone(preset.escena);
}

function legacyBrowserItem(scene: Escena): string {
  const item = itemDeEscena({ id: "legacy:req021:local-only", nombre: LEGACY_NAME, ocasiones: ["general"], escena: scene });
  assert.ok(item, "Legacy browser fixture is a serializable scene item");
  return JSON.stringify([{ ...item, propio: true }]);
}

async function installBrowserFixtures(context: BrowserContext, origin: string, scene: Escena, legacy: string): Promise<void> {
  await context.addInitScript(({ appOrigin, initialScene, legacyValue, legacyKey, projectKey }) => {
    if (window.location.origin !== appOrigin) return;
    if (window.localStorage.getItem(projectKey) === null) {
      window.localStorage.setItem(projectKey, JSON.stringify({ nombre: "Proyecto REQ-021", escena: initialScene, version: 2 }));
    }
    if (window.localStorage.getItem(legacyKey) === null) window.localStorage.setItem(legacyKey, legacyValue);
  }, { appOrigin: origin, initialScene: scene, legacyValue: legacy, legacyKey: LEGACY_KEY, projectKey: PROJECT_KEY });
}

async function storedProjectNodeCount(page: Page): Promise<number> {
  return page.evaluate((key) => {
    const raw = localStorage.getItem(key);
    if (!raw) return 0;
    const saved: unknown = JSON.parse(raw);
    if (typeof saved !== "object" || saved === null || !("escena" in saved) || typeof saved.escena !== "object" || saved.escena === null || !("nodos" in saved.escena) || !Array.isArray(saved.escena.nodos)) return 0;
    return saved.escena.nodos.length;
  }, PROJECT_KEY);
}

async function waitForNodeCount(page: Page, expected: number): Promise<void> {
  await page.waitForFunction(({ key, count }) => {
    const raw = localStorage.getItem(key);
    if (!raw) return false;
    try {
      const saved: unknown = JSON.parse(raw);
      return typeof saved === "object" && saved !== null && "escena" in saved && typeof saved.escena === "object" && saved.escena !== null && "nodos" in saved.escena && Array.isArray(saved.escena.nodos) && saved.escena.nodos.length >= count;
    } catch { return false; }
  }, { key: PROJECT_KEY, count: expected }, { timeout: 20_000 });
}

async function runFlow(): Promise<void> {
  const target = resolveTestDatabaseTarget(process.env);
  const database = await createIsolatedTestDatabase(target.connectionString);
  const home = await mkdtemp(path.join(os.tmpdir(), "req021-decoraciones-home-"));
  const browsers: Browser[] = [];
  let child: Child | undefined;
  const logs = { stdout: "", stderr: "" };
  const evidence: Record<string, unknown> = {
    schemaVersion: 1,
    check: "REQ-021 SP-5 saved decorations production browser integration",
    status: "running",
    runtime: "next build + next start",
    databaseSource: target.source,
    browser: "Chromium with independent browser profiles",
    expectedResults: {
      saveAndReload: "owner's confirmed account decoration survives reload",
      crossBrowser: "same account reads the saved composition in a separate browser profile",
      placement: "Add to my scene increases the open project's persisted node count",
      staff: "employee_internal reads the owner's item; direct PUT and DELETE are denied",
      isolation: "a second master_designer Usuario has an empty account list and cannot read the owner's item by id",
      legacy: "legacy item remains in this browser's local library and is absent from account storage",
    },
  };

  try {
    for (const migration of ["037_cuentas.sql", "038_cuentas_datos_administracion.sql", "039_decoraciones_personales.sql"]) {
      await database.pool.query(await readFile(path.join(ROOT, "scripts/migrations", migration), "utf8"));
    }
    const accountService = createAccountService(database.pool, VERSION_AVISO_DATOS);
    const accounts = await accountService.seedTestAccounts(PASSWORD);
    const owner = accounts.find((account) => account.roleId === "master_designer");
    const administrator = accounts.find((account) => account.roleId === "administrador");
    const staff = accounts.find((account) => account.roleId === "empleado_interno");
    assert.ok(owner && administrator && staff, "isolated REQ-021 database has owner, administrator and staff accounts");
    const invitedOther = await accountService.invite({
      actorAccountId: administrator.accountId,
      email: `req021-other-${crypto.randomUUID()}@example.test`,
      roleId: "master_designer",
    });
    const activatedOther = await accountService.activate({ token: invitedOther.token, password: PASSWORD, acceptDataNotice: true });
    const other: Account = { accountId: invitedOther.accountId, email: activatedOther.email, roleId: "master_designer" };

    const build = run("npm", ["run", "build"], buildEnvironment(home));
    assert.equal(build.status, 0, `Production build succeeds without database credentials. ${redact(build.output.slice(-3_000))}`);

    const port = await availablePort();
    const scopedDatabaseUrl = new URL(target.connectionString);
    scopedDatabaseUrl.searchParams.set("options", `-c search_path=${database.schema},public`);
    const origin = `http://localhost:${port}`;
    child = spawn(process.execPath, ["node_modules/next/dist/bin/next", "start", "--hostname", "127.0.0.1", "--port", String(port)], {
      cwd: ROOT,
      env: {
        PATH: process.env.PATH,
        HOME: home,
        APP_ENV: "test",
        DATABASE_URL: scopedDatabaseUrl.toString(),
        DATA_NOTICE_VERSION: VERSION_AVISO_DATOS,
        CAPTURA_RENDERS_ENABLED: "1",
        NODE_ENV: "production",
        NEXT_TELEMETRY_DISABLED: "1",
        VERCEL: "1",
        PORT: String(port),
        HOSTNAME: "127.0.0.1",
      },
      stdio: ["ignore", "pipe", "pipe"],
    });
    child.stdout?.on("data", (chunk: Buffer) => { logs.stdout = appendTail(logs.stdout, chunk); });
    child.stderr?.on("data", (chunk: Buffer) => { logs.stderr = appendTail(logs.stderr, chunk); });
    await waitForServer(origin, child, logs);

    const ownerBrowser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-dev-shm-usage"] });
    const secondBrowser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-dev-shm-usage"] });
    const staffBrowser = await chromium.launch({ headless: true, args: ["--no-sandbox", "--disable-dev-shm-usage"] });
    browsers.push(ownerBrowser, secondBrowser, staffBrowser);
    const ownerContext = await newContext(ownerBrowser);
    const secondContext = await newContext(secondBrowser);
    const staffContext = await newContext(staffBrowser);
    const scene = initialProjectScene();
    const legacy = legacyBrowserItem(scene);
    await installBrowserFixtures(ownerContext, origin, scene, legacy);
    const ownerPage = await ownerContext.newPage();
    await signIn(ownerPage, origin, owner);
    await openLibrary(ownerPage);
    const startingNodeCount = await storedProjectNodeCount(ownerPage);
    assert.ok(startingNodeCount > 0, "owner opens a populated project before saving its composition");

    await ownerPage.getByRole("button", { name: "Guardar toda la escena", exact: true }).click();
    await ownerPage.getByLabel("Nombre", { exact: true }).fill(SAVED_NAME);
    const saveResponse = ownerPage.waitForResponse((response) => response.url().endsWith("/api/decoraciones-personales") && response.request().method() === "POST");
    await ownerPage.getByRole("button", { name: "Guardar", exact: true }).click();
    const saved = await saveResponse;
    const savedBody: unknown = await saved.json();
    assert.equal(saved.status(), 201, `composition is persisted through the production API (${JSON.stringify(savedBody)})`);
    await ownerPage.getByRole("status").getByText("Guardado en mi cuenta", { exact: true }).waitFor();
    assert.ok(typeof savedBody === "object" && savedBody !== null && "decoracion" in savedBody && typeof savedBody.decoracion === "object" && savedBody.decoracion !== null && "id" in savedBody.decoracion && typeof savedBody.decoracion.id === "string");
    const decorationId = savedBody.decoracion.id;
    const stored = await database.pool.query<{ cuenta_id: string; nombre: string; composicion: Escena }>(
      "SELECT cuenta_id, nombre, composicion FROM decoraciones_personales WHERE id = $1",
      [decorationId],
    );
    assert.equal(stored.rowCount, 1);
    assert.equal(stored.rows[0]?.cuenta_id, owner.accountId);
    assert.equal(stored.rows[0]?.nombre, SAVED_NAME);
    assert.equal(stored.rows[0]?.composicion.nodos.length, startingNodeCount);

    await ownerPage.reload();
    await ownerPage.getByRole("region", { name: "Biblioteca personal", exact: true }).waitFor();
    await ownerPage.getByRole("button", { name: new RegExp(SAVED_NAME) }).waitFor();
    const accountRows = await ownerPage.evaluate(async () => {
      const response = await fetch("/api/decoraciones-personales", { cache: "no-store" });
      const body: unknown = await response.json();
      if (!response.ok || typeof body !== "object" || body === null || !("decoraciones" in body) || !Array.isArray(body.decoraciones)) return [];
      return body.decoraciones.map((record) => typeof record === "object" && record !== null && "nombre" in record ? record.nombre : null);
    });
    assert.deepEqual(accountRows, [SAVED_NAME], "account storage contains the saved item, not the legacy browser item");

    await ownerPage.getByRole("button", { name: "En este navegador", exact: true }).click();
    await ownerPage.getByRole("button", { name: new RegExp(LEGACY_NAME) }).waitFor();
    const legacyAfter = await ownerPage.evaluate((key) => localStorage.getItem(key), LEGACY_KEY);
    assert.equal(legacyAfter, legacy, "the pre-existing browser item stays byte-for-byte in local storage");
    await ownerContext.close();

    const secondPage = await secondContext.newPage();
    await signIn(secondPage, origin, owner);
    await openLibrary(secondPage);
    const remoteRecord = secondPage.getByRole("button", { name: new RegExp(SAVED_NAME) });
    await remoteRecord.waitFor();
    await remoteRecord.click();
    const beforePlacement = await storedProjectNodeCount(secondPage);
    await secondPage.getByRole("button", { name: "Añadir a mi escena", exact: true }).click();
    await waitForNodeCount(secondPage, beforePlacement + startingNodeCount);
    const placedNodeCount = await storedProjectNodeCount(secondPage);
    assert.equal(placedNodeCount, beforePlacement + startingNodeCount, "saved composition is placed into the second browser's open project");
    await secondContext.close();

    const staffPage = await staffContext.newPage();
    await signIn(staffPage, origin, staff);
    await openLibrary(staffPage);
    const ownerInput = staffPage.locator("#biblioteca-cuenta-ajena");
    assert.equal(await ownerInput.count(), 1, "employee staff sees the owner selector in their personal library");
    await ownerInput.fill(owner.accountId);
    await staffPage.getByRole("button", { name: "Ver cuenta", exact: true }).click();
    await staffPage.getByRole("button", { name: new RegExp(SAVED_NAME) }).waitFor();
    await staffPage.getByRole("button", { name: new RegExp(SAVED_NAME) }).click();
    await staffPage.getByText("Solo lectura", { exact: true }).first().waitFor();
    assert.equal(await staffPage.getByRole("button", { name: "Renombrar", exact: true }).count(), 0);
    assert.equal(await staffPage.getByRole("button", { name: "Editar", exact: true }).count(), 0);
    assert.equal(await staffPage.getByRole("button", { name: "Quitar de mi biblioteca", exact: true }).count(), 0);
    const directMutation = await staffPage.evaluate(async ({ id, composition }) => {
      const body = JSON.stringify({ nombre: "Staff no autorizado", ocasion: "general", miniatura: "data:image/png;base64,aGVsbG8=", composicion: composition });
      const update = await fetch(`/api/decoraciones-personales/${id}`, { method: "PUT", headers: { "content-type": "application/json" }, body });
      const remove = await fetch(`/api/decoraciones-personales/${id}`, { method: "DELETE" });
      return { put: update.status, delete: remove.status };
    }, { id: decorationId, composition: stored.rows[0]!.composicion });
    assert.ok([403, 404].includes(directMutation.put), `Staff direct PUT is refused (HTTP ${directMutation.put})`);
    assert.ok([403, 404].includes(directMutation.delete), `Staff direct DELETE is refused (HTTP ${directMutation.delete})`);
    const unchangedAfterStaff = await database.pool.query<{ nombre: string }>("SELECT nombre FROM decoraciones_personales WHERE id = $1", [decorationId]);
    assert.equal(unchangedAfterStaff.rows[0]?.nombre, SAVED_NAME, "staff mutations do not change or delete the owner's record");
    await staffContext.close();

    const otherContext = await newContext(secondBrowser);
    const otherPage = await otherContext.newPage();
    await signIn(otherPage, origin, other);
    await openLibrary(otherPage);
    await otherPage.getByText("Tu biblioteca está vacía", { exact: true }).waitFor();
    assert.equal(await otherPage.getByRole("button", { name: new RegExp(SAVED_NAME) }).count(), 0);
    const otherRead = await otherPage.evaluate(async (id) => (await fetch(`/api/decoraciones-personales/${id}`, { cache: "no-store" })).status, decorationId);
    assert.equal(otherRead, 404, "another Usuario cannot read the owner's item by id");
    await otherContext.close();

    evidence.status = "passed";
    evidence.owner = { role: owner.roleId, saveStatus: saved.status(), reloadRetainedRecord: true, browserLocalLegacyRetained: true };
    evidence.secondBrowser = { account: "same owner", role: owner.roleId, placedNodes: startingNodeCount, projectNodesBefore: beforePlacement, projectNodesAfter: placedNodeCount };
    evidence.staff = { role: staff.roleId, readOnlyUi: true, directPutStatus: directMutation.put, directDeleteStatus: directMutation.delete, ownerRecordUnchanged: true };
    evidence.otherUsuario = { role: other.roleId, collectionEmpty: true, directItemStatus: otherRead };
    await mkdir(path.dirname(EVIDENCE_PATH), { recursive: true });
    await writeFile(EVIDENCE_PATH, `${JSON.stringify(evidence, null, 2)}\n`, "utf8");
    proce
```

## Resolution request 87f60eeb77d9f299cfb7dd9902dd315c (.evidence/REQ-021/CG-2.integration.json)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/87f60eeb77d9f299cfb7dd9902dd315c.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/87f60eeb77d9f299cfb7dd9902dd315c.diff3`
- blobs: base `-`, ours `430552e2288a39814705f66e246398392ece5b87`, theirs `3e903d092e3562b1fbe051480bfa4339b59113f7` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "217e5e5053d0497c4867ff21dae3c33e3fd8170a", "ours": "56f02a46dc6f0d169f587f41889681745874023c", "theirs": "c09fc4edda7a6699dec6af4bc7ea9e7786588193"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/87f60eeb77d9f299cfb7dd9902dd315c.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
<<<<<<< ours (.evidence/REQ-021/CG-2.integration.json)
{
  "schemaVersion": 1,
  "check": "REQ-021 CG-2 composition",
  "status": "blocked",
  "tree": "self-test-fixture",
  "blender": {
    "version": null,
    "executable": null
  },
  "perTypeResults": [
    {
      "type": "columna",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "arco",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "pared_malla",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "pared_trenzas",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "organico",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "decoracion",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "arco_organico",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "guirnalda",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "escenografia",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "globo",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "forma",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "letras",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "metalizado",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "mural",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "techo",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "arbol_globos",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "modulo",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "mesa-redonda",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "mesa-cuadrada",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "mesa-rectangular",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "mesa-ovalada",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "mesa-coctel",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "mesa-media_luna",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "mesa-serpentina",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "mesa-u",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "mesa-imperial",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "mesa-infantil",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "mesa-barra",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "silla-tiffany",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "silla-crossback",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "silla-ghost",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "silla-plegable",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "silla-moderna",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "silla-banca",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "silla-taburete",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "backing-panel_redondo",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "backing-media_luna",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "backing-arcos_chiara",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "backing-pedestales",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "backing-aro_metalico",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "backing-aro_hexagonal",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "backing-arco_metalico",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "backing-panel_arco_apuntado",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "backing-marco_hexagonal",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "backing-marco_ventana",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "backing-pared_shimmer",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "backing-pedestales_cilindricos",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "backing-panel_dos_niveles",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "forma-caja",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "forma-cilindro",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "forma-panel",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "forma-arco_apuntado",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    },
    {
      "type": "sala",
      "status": "blocked",
      "details": "Self-test does not execute the app or Blender."
    }
  ],
  "knownDefects": [],
  "blockedReasons": [
    "Self-test mode deliberately does not start Next.js, Chromium, or Blender."
  ]
}
||||||| base
=======
{
  "schemaVersion": 1,
  "check": "REQ-021 CG-2 composition",
  "status": "blocked",
  "tree": "08b193b04e6c2e20a4e438da942c53a1b989676a",
  "blender": {
    "version": "Blender 4.5.15 LTS",
    "executable": "/home/david/.local/opt/blender/current/blender"
  },
  "perTypeResults": [
    {
      "type": "columna",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "arco",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "pared_malla",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "pared_trenzas",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "organico",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "decoracion",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "arco_organico",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "guirnalda",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "escenografia",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "globo",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "forma",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "letras",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "metalizado",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "mural",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "techo",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "arbol_globos",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "modulo",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "mesa-redonda",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "mesa-cuadrada",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "mesa-rectangular",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "mesa-ovalada",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "mesa-coctel",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "mesa-media_luna",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "mesa-serpentina",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "mesa-u",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "mesa-imperial",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "mesa-infantil",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "mesa-barra",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "silla-tiffany",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "silla-crossback",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "silla-ghost",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "silla-plegable",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "silla-moderna",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "silla-banca",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "silla-taburete",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "backing-panel_redondo",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "backing-media_luna",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "backing-arcos_chiara",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "backing-pedestales",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "backing-aro_metalico",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "backing-aro_hexagonal",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "backing-arco_metalico",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "backing-panel_arco_apuntado",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "backing-marco_hexagonal",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "backing-marco_ventana",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "backing-pared_shimmer",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "backing-pedestales_cilindricos",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "backing-panel_dos_niveles",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "forma-caja",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "forma-cilindro",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "forma-panel",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "forma-arco_apuntado",
      "status": "blocked",
      "details": "Not reached."
    },
    {
      "type": "sala",
      "status": "blocked",
      "details": "Not reached."
    }
  ],
  "knownDefects": [],
  "blockedReasons": [
    "The real CG-2 run reached `next build`, which failed type checking: scripts/test/test-harness-taller-esenciales.ts(12,43): `{}` is missing required `NODE_ENV` for ProcessEnv; scripts/test/test-harness-taller-esenciales.ts(14,51): `{ BLENDER_EXECUTABLE: string }` is missing required `NODE_ENV` for ProcessEnv. No Taller browser or GLB assertions ran."
  ]
}
>>>>>>> theirs

```

## Resolution request 8f4d1b7928b20f9f71fe0b9e76ef136b (src/components/guiado/VistaGuiada.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/8f4d1b7928b20f9f71fe0b9e76ef136b.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/8f4d1b7928b20f9f71fe0b9e76ef136b.diff3`
- blobs: base `8c35bb562163a0300bcc32e8ba694bdea5ac5d87`, ours `7f478910a68f8c367f9a2373bc6cfd9e1f597d08`, theirs `adb279712cadb5b1e325593cd65dcd835cf9b440` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "b3f997fe050f00d031f8ff7103d279b1f33f08c5", "ours": "4a51d40d934170de8275f4e709cdf5f840eded91", "theirs": "88d643b5be177e0ba03178d7fddd523b9ba7f5c7"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/8f4d1b7928b20f9f71fe0b9e76ef136b.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
"use client";

import { useTextos } from "@/lib/idioma/cliente";
import { TEXTOS_CHAT_GUIADO } from "@/components/guiado/textos/chat-guiado";
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Baby, Cake, Church, CircleCheck, Crown, Heart, ImagePlus, RotateCcw, Sparkles } from "lucide-react";
import { z } from "zod";
import { CabeceraApp } from "@/components/ui/shell/CabeceraApp";
import type { Idioma } from "@/lib/idioma/idioma";
import { Markdown } from "@/components/Markdown";
import { CarruselDecoraciones } from "./CarruselDecoraciones";
import { ComprarMateriales } from "./ComprarMateriales";
import { ChipsOpciones, OPCIONES_GUIADAS, type OpcionGuiada } from "./ChipsOpciones";
import { CostosMateriales } from "./CostosMateriales";
import { PasoAPaso } from "./PasoAPaso";
import { PreguntaUso } from "./PreguntaUso";
import { RespuestasRapidas, dedupeOpciones, separarOpciones } from "./RespuestasRapidas";
import { TarjetaEleccion } from "./TarjetaEleccion";
import type { DatosAgregarIdea, EstadoAgregarIdea } from "./AgregarIdea";
import { estadoAgregarIdea, propuestaAgregarIdea } from "./agregar-idea";
import { TarjetasProveedores } from "./TarjetasProveedores";
import { ReferenciaInspiracion } from "./ReferenciaInspiracion";
import { acabadosFotoSinComprar } from "./acabados-foto-plan";
import { avisosFloresFotoSinComprar } from "@/lib/plan/flores-pieza";
import { lecturaFoto } from "./lectura-foto";
import { TarjetaPlan, type AccionPlan, type EstadoImagen } from "./TarjetaPlan";
import { cancelarPrecioIdea, empezarPrecioIdea, fijarPrecioIdea, precioIdeaDesdePlanVigente, resolverPrecioIdea, reutilizarPlanIdea, vistaPrecioIdea, type EstadoPrecioIdea, type PlanIdeaGuardado } from "./precio-idea-elegida";
import { accionIdeaAlElegirUso, avanzarOpcionIdea, estadoDelTurnoDeIdea, ideasTrasArmarIdea, marcarChipAlElegir, resultadoPlanIdea, rutaOpcionIdea, TEXTO_OPCION_IDEA, type AccionIdea, type EsperaOpcionIdea, type EventoOpcionIdea, type PasoOpcionIdea, type ResultadoPlanIdea } from "./opcion-idea";
import { respuestaPrecioPlan, SELECTOR_PRECIO_TOTAL } from "./precio-chat";
import { contenidoPlanAjustado } from "./ajuste/ajuste-plan-guiado";
import { usePublicarAjustePlan } from "./ajuste/publicar-ajuste-plan";
import { planDelMensaje, totalDePlan } from "./plan-del-mensaje";
import type { AjustePublicado } from "./ajuste/usarAjustePlanGuiado";
import { useDeshacerAjuste } from "./usarDeshacerAjuste";
import { agregarPiezaEnServidor, avisoEdicionChat, editarPiezaEnServidor, ejecutarEdicionChat, type DependenciasEdicionChat } from "./ajuste/edicion-chat-guiada";
import { agregarColorEnServidor, aplicarEnServidor, mensajeAjuste, quitarPiezaEnServidor, reemplazarColorEnServidor } from "./ajuste/ejecutar-ajuste";
import { armarBusqueda, LIMITE_MAXIMO } from "@/components/plan/ajuste/ajuste-propuesta";
import { pedirBusqueda } from "@/components/plan/ajuste/cliente-explorador";
import { esCancelacion } from "@/lib/plan/peticion-plan-editar";
import { detectarPiezaNueva, IdeaElegidaSchema, LUGAR_EN_PALABRAS, PedidoEdicionPlanSchema, piezaIndefinida, type PedidoEdicionPlan, type PiezaNuevaChat } from "@/lib/ia/guiado/edicion-plan-chat";
import { TarjetaPropuesta } from "./TarjetaPropuesta";
import { TarjetaError } from "./TarjetaError";
import { PreguntaPropuesta } from "./PreguntaPropuesta";
import { GuiaPlan } from "./GuiaPlan";
import { BarraPlanVigente } from "./BarraPlanVigente";
import { Compositor } from "./Compositor";
import { FotosEjemploGuiada } from "./FotosEjemploGuiada";
import { fotoSubidaValida } from "./foto-subida";
import { BurbujaAsistente, BurbujaUsuario } from "./Burbujas";
import { CalificacionGuiada } from "./CalificacionGuiada";
import { IndicadorEscribiendo } from "./IndicadorEscribiendo";
import type { EtapaPlan } from "./Esqueletos";
import { EsqueletoPlan } from "./Esqueletos";
import { claveTexto, conMayuscula, nombreLineaCliente } from "./formato";
import { BotonIrAlFinal, useSeguirFinal } from "./animacion/useSeguirFinal";
import { DUR, EASE_SALIDA, entradaMensaje, entradaUsuario, grupoConRitmo, hijoEscalonado } from "./animacion/movimiento";
import { useModoVista } from "@/lib/estado/modo-vista";
import { DecoracionSempertexSchema, ProveedorSempertexSchema, type DecoracionSempertex, type ProveedorSempertex } from "@/lib/biblioteca-sempertex/esquemas";
import { CIUDADES_PROVEEDORES } from "@/lib/biblioteca-sempertex/ciudades";
import { ChatSseEventV1Schema } from "@/lib/ia/contracts/chat-v1";
import { BriefGuiadoSchema, CotizacionGuiadaSchema, CotizacionPlanGuiadoSchema, IdeaVisibleGuiadaSchema, PlanGuiadoSchema, PropuestaComposicionSchema, type BriefGuiado, type IdeaVisibleGuiada, type PlanActualGuiado } from "@/lib/ia/contracts/asistente-guiado-v1";
import { contextoClienteGuiado, entradaImagenGuiada, type ContextoClienteGuiado } from "@/lib/ia/guiado/contexto-cliente";
import { cargarFactorPlazoCliente, factorPlazoCliente } from "@/lib/ia/plazo-cliente";
import { prepararHistorialGuiado, sinUltimoTurnoGuiado } from "@/lib/ia/guiado/utilidades";
import { adaptarAnalisisReferencia } from "@/lib/ia/guiado/adaptar-analisis-referencia";
import { prepararFotoReferencia } from "@/lib/imagen-cliente/preparar-foto";
import type { WidgetGuiado } from "@/lib/ia/guiado/widgets";
import { CLAVE_ACCIONES_IDEA, EstadoGuardadoSchema, juntarAccionesIdea, MAX_MENSAJES_GUARDADOS, PREPARANDO_PLAN_IDEA, ReferenciaSchema, separarAccionesIdea, sinEsperaTransitoria, type Mensaje } from "./estado-guardado";
import { generarPasosPlan } from "@/lib/ia/guiado/generar-pasos-plan";
import { coloresFaltantesPlanGuiado, cuerpoPlanGuiado, defectoPlanGuiado, referenciaDelPlan, resumenPlanGuiado, type ReferenciaDelPlan } from "@/lib/ia/guiado/instruccion-plan";
import { cuerpoPlanFoto, lecturaConPiezaNueva, planLlevaPiezaPedida } from "@/lib/ia/guiado/foto-con-pieza";
import { responderConsultaPlan } from "@/lib/ia/guiado/consulta-plan-chat";
import type { ColorFotoFaltante } from "@/lib/plan/colores-foto-plan";
import { lecturaSinRemateGrande, tieneRemateGrande } from "@/lib/ia/guiado/remate-foto";
import type { EstructuraOficialId } from "@/lib/plan/estructuras-oficiales";
import { cuerpoGeneracion, fuentesDelPlan, resumenCuerpoGeneracion } from "@/lib/generacion/cuerpo-generacion";
// De /api/generate interesan la imagen y su aviso de lo no cotizado (el plan que devuelve no trae approval_token y el de
// la tarjeta sí): `ImagenGeneradaSchema` vive ahora en pedir-imagen.ts, con la recuperación ante cortes.
import { ErrorImagen, pedirImagenConRecuperacion, type ImagenObtenida } from "@/lib/generacion/pedir-imagen";
import { abrirConversacionGuiada, registrarAccionGuiada, registrarFalloGuiado, vaciarConversacionGuiada, type EstadoParaInstantanea } from "./registro-guiado";
import { AVISO_VERSION_NUEVA, CABECERA_VERSION_APP, RespuestaIncompatibleError, camposInvalidos, clasificarIncompatible, hayVersionNueva, idParaReintento, turnoSinRespuesta } from "./version-pagina";
import { borrarEstadoGuiado } from "./empezar-de-nuevo";
import { useMotorGuiada } from "./usarMotorGuiada";
import { useCorte3d } from "./useCorte3d";
import { claveDeWidget, useNoIncluidos } from "./useNoIncluidos";
import { avisarSiEsCorteDeLaImagen, sinAvisoDeCorte, TIPO_ACCION_RECALCULAR_3D } from "./aviso-corte-3d";
import { avisarAlCargarPlan } from "./avisar-corte-3d-al-cargar";
import { propuestaParaGuardar } from "./recalculo-3d";

import { TEXTO_IMAGEN_PLAN_3D } from "./Plan3DEnPreparacion";
import { falloDelPlan } from "./fallo-plan";
import { mensajeRecalculo } from "@/lib/guiada-motor/mensajes-cliente";
import { NotasPlan } from "./NotasPlan";
import { pedirImagenPlan3D } from "./imagen-plan-3d";
import { mensajeErrorImagen } from "./mensaje-error-imagen";
import { firmaDePlan } from "./motor3d/firma-plan";
import { crearDependenciasEdicion3d } from "./edicion-motor3d";
import { planActualDelPlan } from "./plan-actual";
import { NoIncluidosSchema } from "@/lib/guiada-motor/no-incluidos";
import type { MotorGuiada } from "@/lib/guiada-motor/tipos";
import { ConfirmarEmpezarDeNuevo } from "./ConfirmarEmpezarDeNuevo";
import { borrarImagenesNavegador, borrarImagenNavegador, guardarImagenNavegador, leerImagenesNavegador } from "./imagenes-navegador";
import { marcarProducido } from "@/components/feedback-ia/producidos";

/**
 * Vista guiada (/asistente). Cada pieza (ideas, plan, proveedores…) va PEGADA al mensaje que la trajo; solo las del
 * último mensaje del asistente se pueden usar y las anteriores quedan como historia con lo que se eligió. En todo
 * momento hay una siguiente acción a la vista: una pregunta con botones, la acción principal del plan, la barra del
 * plan vigente o, si algo falla, una tarjeta con «Reintentar» que repite LA ACCIÓN que falló.
 */
type Widget = WidgetGuiado;
type WidgetPlan = Extract<Widget, { tipo: "plan" }>;
type Propuesta = z.infer<typeof PropuestaComposicionSchema>;
type PlanGuiado = z.infer<typeof PlanGuiadoSchema>;
type Uso = "negocio" | "personal";
type FotoInspiracion = { base64: string; mime: "image/jpeg" | "image/png" | "image/webp" };
type PreguntaCiudad = "ciudad-decorador" | "ciudad-distribuidor";
type OpcionesEnvio = { uso?: Uso; reintentar?: boolean; alcance?: "completa" | "individual"; pieza?: EstructuraOficialId; accionIdea?: AccionIdea };

/** La idea de la biblioteca que trae un plan («Agregar al plan»): queda en el widget y dice «Está en tu plan». `sumada`: había plan. */
/** `avisos`: si el plan exacto de la idea no salió exacto, por qué (en palabras de cliente, de `/api/plan-idea`). */
type IdeaAgregada = { id: string; titulo: string; sumada: boolean; avisos?: string[] };
/** Qué repite «Reintentar»: se guarda la acción (no un cierre) para ejecutarla con el estado del momento del clic. */
type AccionFallo =
  | { tipo: "turno"; texto: string; opciones: OpcionesEnvio }
  | { tipo: "plan"; propuesta: Propuesta; mensajeId: string; planAnterior?: PlanActualGuiado; idea?: IdeaAgregada }
  | { tipo: "foto"; referenciaId: string; mensajeId: string; sinRemate?: boolean; piezaNueva?: PiezaNuevaChat }
  /** Un cambio del plan pedido por chat (`edicion-chat-guiada.ts`) que no salió: se repite ESE cambio, sin el modelo. */
  | { tipo: "edicion"; pedido: PedidoEdicionPlan; mensajeId: string }
  /** «Cuánto cuesta» / «Aprender» de una idea cuyo plan exacto no llegó: se pide ESE plan otra vez, sin el modelo. */
  | { tipo: "opcion-idea"; accion: AccionIdea; ideaId: string; usuarioId: string; mensajeId: string; opcionesId: string | null }
  /** «Recalcular mi plan» del aviso de corte del 3D (P-049): da el consentimiento y pide el plan de nuevo (Python, sin preguntar otra vez). */
  | { tipo: typeof TIPO_ACCION_RECALCULAR_3D; planHash: string; mensajeId: string }
  | { tipo: "subir-foto" }
  /** La página es de otro despliegue que el servidor (version-pagina.ts): recargar trae la nueva; la conversación queda. */
  | { tipo: "recargar" };
type AlternativaFallo = "otros-colores" | "otra-pieza" | "idea-parecida" | "otra-foto";
type Fallo = { titulo: string; detalle?: string; etiqueta?: string; accion: AccionFallo; alternativas?: AlternativaFallo[]; mensajeId?: string; variante?: "actualizar" };

const CLAVE_SESION = "demo_guiado_v2";
const ResultadoSchema = z.object({
  brief: BriefGuiadoSchema.optional(),
  decoraciones: z.array(DecoracionSempertexSchema).optional(),
  opciones: z.array(z.enum(["contratar", "costear", "comprar", "aprender"])).optional(),
  preguntaUso: z.boolean().optional(),
  cotizacion: z.unknown().optional(),
  noIncluidos: NoIncluidosSchema,
  uso: z.enum(["negocio", "personal"]).optional(),
  pasos: z.array(z.object({ orden: z.number().int().positive(), texto: z.string().min(1) }).strict()).optional(),
  proveedores: z.array(ProveedorSempertexSchema).optional(),
  propuesta: PropuestaComposicionSchema.optional(),
  ciudadProveedores: z.string().optional(),
  ciudadesDisponibles: z.array(z.string()).optional(),
  accionPlan: z.string().optional(),
}).passthrough();
const AccionModeloSchema = z.enum(["ver", "costear", "comprar", "aprender", "contratar"]);

const LIMITE_TURNO_MS = 75_000;
const LIMITE_PLAN_MS = 75_000;
/** El plan exacto de una idea solo pasa por Python (sin modelo): si tarda más, se arma por el camino de siempre. */
const LIMITE_PLAN_IDEA_MS = 40_000;
/**
 * Confirmaciones rechazadas que aguanta un intento de plan. El servidor ya repara solo lo reparable tras 2 rechazos
 * (`RECHAZOS_PARA_CONVERGER`): un tercero es que el catálogo no tiene lo que la lectura pide (ej04: un remate de 36"
 * dorado que no existe), y seguir solo gasta llamadas.
 */
const MAX_RECHAZOS_INTENTO = 3;
const LIMITE_IMAGEN_MS = 90_000;
// La lectura tarda 12-27 s en local y más en Vercel (va por el Python del VPS): con 12 s se cortaba siempre en
// producción, la guiada seguía sin la foto y adivinaba las piezas («un arco» donde había dos columnas; 2026-10-06).
const LIMITE_FOTO_MS = 100_000;

/** El saludo es fijo, sale al instante y no viaja en el historial: el prompt guiado sabe que ya se hizo. */
const SALUDO = "¡Hola! Te hago unas preguntas cortas y te muestro decoraciones Sempertex que encajen con tu celebración.\n\n**¿Qué vas a celebrar?**";
const CHIP_FOTO = "Tengo una foto de inspiración";
const OPCIONES_SALUDO: ReadonlyArray<{ texto: string; icono: ReactNode }> = [
  { texto: "Cumpleaños", icono: <Cake className="size-4" aria-hidden /> },
  { texto: "Baby shower", icono: <Baby className="size-4" aria-hidden /> },
  { texto: "Boda", icono: <Heart className="size-4" aria-hidden /> },
  { texto: "XV años", icono: <Crown className="size-4" aria-hidden /> },
  { texto: "Bautizo o comunión", icono: <Church className="size-4" aria-hidden /> },
  { texto: "Otra celebración", icono: <Sparkles className="size-4" aria-hidden /> },
];
const OTRAS_CELEBRACIONES = ["Divorcio", "Graduación", "Jubilación", "Fiesta de empresa", "Aniversario"];
const PROPONME = "Propónme algo";
const PROPONME_LOCAL = /^(?:oye,?\s*)?(?:prop[oó]nme algo|qu[eé] me recomiendas armar\??|arma t[uú] algo\.?)[.!?]*$/i;
/**
 * «Genera la imagen», «hazme la foto», «quiero ver cómo quedaría» con un plan a la vista: vuelve a la tarjeta del plan y
 * lanza «Ver cómo quedaría» sin pasar por el modelo (dueño, 2026-10-07). Se compara sin tildes; una negación no cuenta.
 */
const PIDE_IMAGEN_LOCAL = /\b(?:genera(?:r|me|la)?|crea(?:r|me|la)?|haz(?:me|la)?|hacer|dibuja(?:r|me|la)?|muestra(?:r|me|la)?|ensena(?:r|me|la)?|quiero ver|ver|veamos|dame)\b[^.?!]{0,40}\b(?:imagen|imagenes|foto|render|como (?:se ve|se veria|quedaria|queda))\b/;
function pideImagenDelPlan(texto: string): boolean {
  const plano = texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  return !/\bno\b/.test(plano) && PIDE_IMAGEN_LOCAL.test(plano);
}
const PREGUNTA_TIPO = "¿Quieres una decoración completa (varias piezas) o una pieza individual?";
const PLACEHOLDER_CAMBIO = "Pide un cambio: más rosa, sin columnas…";
const PLACEHOLDER_CIUDAD = "Escribe tu ciudad…";
/** Widgets que ya hacen la pregunta: con ellos, los botones «Opciones:» del texto sobran. */
const WIDGETS_QUE_PREGUNTAN = new Set<Widget["tipo"]>(["decoraciones", "opciones", "uso", "propuesta", "plan", "pregunta-propuesta", "pasos-plan"]);
/** Widgets altos: al llegar se muestra su cabecera, no su final. */
const WIDGETS_ALTOS = new Set<Widget["tipo"]>(["decoraciones", "propuesta", "plan", "proveedores", "pasos-plan"]);
const ORDEN_ETAPA: Record<EtapaPlan, number> = { preparando: 0, reintentando: 0, buscando: 1, calculando: 2, precio: 3 };
const SIN_DEFINIR = /^(?:pendiente|por[ _-]?definir|sin definir|ninguna)$/i;
/** Cursor de escritura al final del texto que llega (el Markdown es compartido: se aplica desde fuera). */
const CARET = "[&_.prose-chat>:last-child]:after:ml-0.5 [&_.prose-chat>:last-child]:after:inline-block [&_.prose-chat>:last-child]:after:h-[1em] [&_.prose-chat>:last-child]:after:w-0.5 [&_.prose-chat>:last-child]:after:bg-acento [&_.prose-chat>:last-child]:after:align-[-2px] [&_.prose-chat>:last-child]:after:content-[''] [&_.prose-chat>:last-child]:after:animate-[caret_1s_steps(2)_infinite]";

function nuevoId(): string { return crypto.randomUUID(); }

/** `versionPagina`: con qué código se sirvió la página (`versionCodigo().corta`); sin ella no se compara la del servidor. */
<<<<<<< ours (src/components/guiado/VistaGuiada.tsx)
export function VistaGuiada({ versionPagina, language = "es" }: { versionPagina?: string; language?: Idioma } = {}) {
  const _t10 = useTextos(TEXTOS_CHAT_GUIADO);
||||||| base
export function VistaGuiada({ versionPagina }: { versionPagina?: string } = {}) {
=======
export function VistaGuiada({ versionPagina, permisos = [] }: { versionPagina?: string; permisos?: readonly string[] } = {}) {
>>>>>>> theirs
  const { modo, cambiar } = useModoVista();
  const reducido = useReducedMotion();
  const { planDePropuesta: planDePropuestaMotor, planDeIdea: planDeIdeaMotor } = useMotorGuiada();
  const [mensajes, setMensajes] = useState<Mensaje[]>([]);
  const [brief, setBrief] = useState<BriefGuiado>({});
  const [entrada, setEntrada] = useState("");
  const [cargando, setCargandoEstado] = useState(false);
  const [fallo, setFallo] = useState<Fallo | null>(null);
  const [seleccionada, setSeleccionada] = useState<DecoracionSempertex | null>(null);
  const [precioIdea, setPrecioIdea] = useState<EstadoPrecioIdea | null>(null);
  const [uso, setUso] = useState<Uso | null>(null);
  const [imagenEnCurso, setImagenEnCurso] = useState<string | null>(null);
  /** Imágenes ya pagadas, en memoria, por id del mensaje del plan: se ven en el acto aunque guardarlas falle. */
  const [imagenesLocales, setImagenesLocales] = useState<Readonly<Record<string, string>>>({});
  /** Los planes de antes de cada ajuste de un plan del 3D (solo en memoria), para «Deshacer» (REQ-016, P-042). */
  const deshacerAjuste = useDeshacerAjuste();
  const limpiarDeshacer = deshacerAjuste.limpiar;

  // Las imágenes guardadas en este navegador vuelven tras una recarga (el servidor no guarda ninguna).
  useEffect(() => {
    void cargarFactorPlazoCliente();
    void leerImagenesNavegador().then((guardadas) => {
      if (Object.keys(guardadas).length) setImagenesLocales((actuales) => ({ ...guardadas, ...actuales }));
    });
  }, []);
  const [etapaPlan, setEtapaPlan] = useState<Readonly<Record<string, EtapaPlan>>>({});
  const { noIncluidos, registrarNoIncluidos } = useNoIncluidos();
  const [foto, setFoto] = useState<File | null>(null);
  const [analizandoFoto, setAnalizandoFoto] = useState(false);
  const [transmitiendoId, setTransmitiendoId] = useState<string | null>(null);
  const [placeholderForzado, setPlaceholderForzado] = useState<string | null>(null);
  const [sugerenciasCambio, setSugerenciasCambio] = useState<string[] | null>(null);
  const [anuncio, setAnuncio] = useState("");
  const ajustarPlan = usePublicarAjustePlan({
    mensajes, setMensajes, setImagenesLocales, setAnuncio,
    recordar: deshacerAjuste.recordar, decoracionDeLaConversacion,
  });
  /** La idea que se está sumando al plan («Agregar al plan»): su botón dice «Agregando a tu plan…». */
  const [agregandoId, setAgregandoId] = useState<string | null>(null);
  /** El plan (id de su mensaje) que se está cambiando por chat: su tarjeta muestra el esqueleto del recálculo. */
  const [editandoPlanId, setEditandoPlanId] = useState<string | null>(null);
  const [restaurado, setRestaurado] = useState(false);
  /** «Empezar de nuevo» del menú espera la confirmación, dentro de la página (sin diálogo del navegador). */
  const [confirmandoReinicio, setConfirmandoReinicio] = useState(false);
  /** Ids restaurados de la sesión: no se vuelven a animar al montar. */
  const [restaurados, setRestaurados] = useState<ReadonlySet<string>>(() => new Set());
  // Hasta hidratar, un clic
```

## Resolution request 9d3f9d9ac1350969fd6a4fe71204cd1c (src/app/login/page.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/9d3f9d9ac1350969fd6a4fe71204cd1c.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/9d3f9d9ac1350969fd6a4fe71204cd1c.diff3`
- blobs: base `b47f60af1fe8a683d99a948bf441fe1b70f21833`, ours `6d9ac809245754118ad1cb4b80cb5117f82d4b5f`, theirs `9dde4bbbd4f005815404a777b4160932a904b62e` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "b3f997fe050f00d031f8ff7103d279b1f33f08c5", "ours": "4a51d40d934170de8275f4e709cdf5f840eded91", "theirs": "88d643b5be177e0ba03178d7fddd523b9ba7f5c7"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/9d3f9d9ac1350969fd6a4fe71204cd1c.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
import { Suspense } from "react";
import { InterruptorTema } from "@/components/ui/interruptor-tema";
import { SelectorIdioma } from "@/lib/idioma/cliente";
import { getRequestLanguage } from "@/lib/idioma/servidor";
import { LoginForm } from "./LoginForm";
<<<<<<< ours (src/app/login/page.tsx)
||||||| base
import { idiomaAcceso } from "@/components/cuentas/textos-acceso";
=======
import { idiomaAcceso } from "@/components/cuentas/textos-acceso";
import { redirect } from "next/navigation";
import { resolveServerRequestSession } from "@/lib/cuentas/sesion-servidor";
import { destinoSolicitado } from "@/lib/auth/destino-por-defecto";
>>>>>>> theirs

export const instant = false;

export default async function LoginPage() {
<<<<<<< ours (src/app/login/page.tsx)
  const language = await getRequestLanguage();
||||||| base
  const language = idiomaAcceso((await headers()).get("accept-language") ?? "es");
=======
  const [requestHeaders, session] = await Promise.all([headers(), resolveServerRequestSession()]);
  if (session) redirect(destinoSolicitado("/", session.permissions));
  const language = idiomaAcceso(requestHeaders.get("accept-language") ?? "es");
>>>>>>> theirs
  return (
    <main className="relative flex min-h-dvh items-center justify-center bg-fondo px-4">
      <div className="absolute right-3 top-3 flex items-center gap-2">
        <SelectorIdioma idioma={language} />
        <InterruptorTema language={language} />
      </div>
      <Suspense>
        <LoginForm language={language} />
      </Suspense>
    </main>
  );
}

```

## Resolution request ba2580bb7203f67c81c4eadf632e2b62 (src/lib/cuentas/cuenta-actual.ts)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/ba2580bb7203f67c81c4eadf632e2b62.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/ba2580bb7203f67c81c4eadf632e2b62.diff3`
- blobs: base `f27871b61ac96a5c5ca702b95a65a773fb1b4171`, ours `6b3da47d5f39d487a128fa1d5c35a83fd0053132`, theirs `39645c68e8fffaefc527296ed798cb698dda336c` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "b3f997fe050f00d031f8ff7103d279b1f33f08c5", "ours": "4a51d40d934170de8275f4e709cdf5f840eded91", "theirs": "88d643b5be177e0ba03178d7fddd523b9ba7f5c7"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/ba2580bb7203f67c81c4eadf632e2b62.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
import "server-only";

<<<<<<< ours (src/lib/cuentas/cuenta-actual.ts)
import { cookies } from "next/headers";
import { SESSION_COOKIE } from "@/lib/auth/session";
||||||| base
import { cookies, headers } from "next/headers";
import { SESSION_COOKIE } from "@/lib/auth/session";
=======
import { headers } from "next/headers";
import { VERSION_AVISO_DATOS } from "./aviso-datos";
import { resolveServerRequestSession } from "./sesion-servidor";
>>>>>>> theirs
import { createAccountPool } from "./pool";
import { createAccountService, type OwnAccountRecord } from "./servicio";

let accounts: ReturnType<typeof createAccountService> | undefined;

function accountService() {
  accounts ??= createAccountService(createAccountPool(), process.env.DATA_NOTICE_VERSION ?? "v1");
  return accounts;
}

export type CurrentAccount = OwnAccountRecord & { permissions: readonly string[] };

export async function getCurrentAccount(): Promise<CurrentAccount | null> {
  const session = await resolveServerRequestSession();
  if (!session) return null;
  if (session.accountId === "administrador-local") {
    return {
      id: session.accountId,
      email: session.email,
      displayName: "Administrador local",
      roles: session.roles,
      dataNoticeVersion: VERSION_AVISO_DATOS,
      dataNoticeAcceptedAt: null,
      permissions: session.permissions,
    };
  }
  const account = await accountService().getOwnAccount(session.accountId);
  return account ? { ...account, permissions: session.permissions } : null;
}

```

## Resolution request dd4cc8117603023fa4561e12cdbe7254 (scripts/test/test-integracion-proyectos.ts)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/dd4cc8117603023fa4561e12cdbe7254.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/dd4cc8117603023fa4561e12cdbe7254.diff3`
- blobs: base `-`, ours `c63ad24013e75050310f7bb5e926ef66fd30262a`, theirs `2444ac2f1dee039c005aa8bacecf3483e36f04fc` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "217e5e5053d0497c4867ff21dae3c33e3fd8170a", "ours": "56f02a46dc6f0d169f587f41889681745874023c", "theirs": "c09fc4edda7a6699dec6af4bc7ea9e7786588193"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/dd4cc8117603023fa4561e12cdbe7254.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
<<<<<<< ours (scripts/test/test-integracion-proyectos.ts)
import assert from "node:assert/strict";
import { spawn, spawnSync, type ChildProcess } from "node:child_process";
import { createServer } from "node:net";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";
import { chromium, type Browser, type BrowserContext, type Page } from "playwright";
import { VERSION_AVISO_DATOS } from "../../src/lib/cuentas/aviso-datos";
import { createAccountService } from "../../src/lib/cuentas/servicio";
import { IDS_BACKING } from "../../src/lib/globos3d/backing";
import { SALA_INICIAL } from "../../src/lib/globos3d/escena";
import { TIPOS_MESA } from "../../src/lib/globos3d/mobiliario-conjunto-tipos";
import { createIsolatedTestDatabase, resolveTestDatabaseTarget } from "./lib/base-prueba";
import { deniedMutations, freshContextReopen, legacyImportAndAccountSwitch, staffReadAndCopy } from "./lib/proyectos-integracion-casos";

const ROOT = process.cwd();
const PASSWORD = "REQ021-Proyectos-Password";
const PAGE_SIZE = 50;
const COMPOSITION = process.argv.includes("--composicion");
const DENIALS_ONLY = process.argv.slice(2).join(" ") === "--solo denegaciones";
type Child = ChildProcess;
type ProjectDocument = { schemaVersion: 1; nombre: string; escena: ReturnType<typeof scene> };
let origin = "";
let browser: Browser | undefined;
let child: Child | undefined;

function scene() {
  return {
    sala: { ...SALA_INICIAL, tonos: { ...SALA_INICIAL.tonos }, mostrar: { ...SALA_INICIAL.mostrar } },
    nodos: [] as Array<{ id: string; nombre: string; pieza: Record<string, unknown>; colocacion: Record<string, unknown> }>,
  };
}

function documentFor(name: string, nodes = scene().nodos): ProjectDocument {
  return { schemaVersion: 1, nombre: name, escena: { ...scene(), nodos: nodes } };
}

function registryDocument(): ProjectDocument {
  const nodes = scene().nodos;
  for (const type of TIPOS_MESA) nodes.push({
    id: "table-" + type,
    nombre: "Mesa " + type,
    pieza: { tipo: "escenografia", elementos: [], mueble: { id: "mesa_param", mesa: { tipo: type, anchoCm: 100, fondoCm: 100, altoCm: 75, mantel: "piso", colorMantel: "#ffffff", colorPatas: "#ffffff", camino: null } } },
    colocacion: { en: "piso", xCm: 0, zCm: 0, giroGrados: 0 },
  });
  for (const id of IDS_BACKING) nodes.push({
    id: "backing-" + id,
    nombre: "Backing " + id,
    pieza: { tipo: "escenografia", elementos: [], mueble: { id } },
    colocacion: { en: "piso", xCm: 0, zCm: 0, giroGrados: 0 },
  });
  return documentFor("REQ-021 scene registry composition", nodes);
}

function redact(value: string): string {
  return value.replace(/postgres(?:ql)?:\/\/[^\s"']+/gi, "[redacted-db-url]")
    .replace(/([?&]token=)[^&\s"']+/gi, "$1[redacted]")
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, "[redacted-email]");
}

function run(command: string, args: string[], env: NodeJS.ProcessEnv): { status: number | null; output: string } {
  const result = spawnSync(command, args, { cwd: ROOT, env, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
  if (result.error) throw result.error;
  return { status: result.status, output: result.stdout + "\n" + result.stderr };
}

async function freePort(): Promise<number> {
  const server = createServer();
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const address = server.address();
  assert.ok(address && typeof address !== "string");
  const port = address.port;
  await new Promise<void>((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  return port;
}

function tail(previous: string, chunk: Buffer): string {
  return (previous + chunk.toString("utf8")).slice(-8_000);
}

async function waitForServer(logs: { stdout: string; stderr: string }): Promise<void> {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    if (child?.exitCode !== null) throw new Error("next start exited early: " + redact(logs.stdout + "\n" + logs.stderr));
    try {
      const response = await fetch(origin + "/proyectos", { signal: AbortSignal.timeout(2_000), redirect: "manual" });
      if (response.status < 500) return;
    } catch { /* Poll until the real entrypoint is ready. */ }
    await delay(500);
  }
  throw new Error("next start did not become ready: " + redact(logs.stdout + "\n" + logs.stderr));
}

async function newPage(): Promise<{ context: BrowserContext; page: Page }> {
  assert.ok(browser);
  const context = await browser.newContext({ locale: "es-CO" });
  const page = await context.newPage();
  page.setDefaultTimeout(20_000);
  return { context, page };
}

async function login(page: Page, email: string): Promise<void> {
  await page.goto(origin + "/login");
  await page.getByLabel("Correo electrónico", { exact: true }).fill(email);
  await page.getByLabel("Contraseña", { exact: true }).fill(PASSWORD);
  const pending = page.waitForResponse((response) => response.url().endsWith("/api/login") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  assert.equal((await pending).status(), 200);
  await page.waitForURL((url) => url.pathname === "/asistente" || url.pathname === "/3d");
}

async function api<T>(page: Page, pathname: string, init?: { method?: string; body?: unknown; key?: string }): Promise<{ status: number; body: T }> {
  return page.evaluate(async (input) => {
    const headers: Record<string, string> = {};
    if (input.body !== undefined) headers["content-type"] = "application/json";
    if (input.key) headers["idempotency-key"] = input.key;
    const response = await fetch(input.pathname, {
      method: input.method ?? "GET", headers,
      ...(input.body === undefined ? {} : { body: JSON.stringify(input.body) }),
      credentials: "same-origin", cache: "no-store",
    });
    return { status: response.status, body: await response.json() as T };
  }, { pathname, method: init?.method, body: init?.body, key: init?.key });
}

function record(value: unknown): asserts value is Record<string, unknown> {
  assert.ok(typeof value === "object" && value !== null && !Array.isArray(value));
}

async function createProject(page: Page, name: string, document = documentFor(name)): Promise<{ id: string; ownerId: string }> {
  const result = await api<unknown>(page, "/api/proyectos", { method: "POST", body: { documento: document }, key: crypto.randomUUID() });
  assert.equal(result.status, 201, "browser saves project " + name + " (HTTP " + result.status + ", " + JSON.stringify(result.body) + ")");
  record(result.body);
  record(result.body.proyecto);
  assert.equal(result.body.proyecto.nombre, name);
  assert.equal(typeof result.body.proyecto.id, "string");
  assert.equal(typeof result.body.proyecto.ownerId, "string");
  return { id: result.body.proyecto.id as string, ownerId: result.body.proyecto.ownerId as string };
}

async function persistenceAndDenial(owner: Page, outsider: Page): Promise<{ id: string; ownerId: string }> {
  const saved = await createProject(owner, "REQ-021 owner persistence");
  const reopened = await api<unknown>(owner, "/api/proyectos/" + saved.id);
  assert.equal(reopened.status, 200);
  record(reopened.body);
  record(reopened.body.proyecto);
  assert.equal(reopened.body.proyecto.id, saved.id);
  const denied = await api<unknown>(outsider, "/api/proyectos/" + saved.id);
  assert.equal(denied.status, 404);
  record(denied.body);
  assert.equal(denied.body.code, "PROYECTO_NO_DISPONIBLE");
  const ownList = await api<unknown>(outsider, "/api/proyectos");
  assert.equal(ownList.status, 200);
  record(ownList.body);
  assert.deepEqual(ownList.body.items, [], "unauthorized browser receives no foreign project metadata");
  const deniedFilter = await api<unknown>(outsider, "/api/proyectos?propietarioId=" + saved.ownerId);
  assert.equal(deniedFilter.status, 403, "owner filtering requires permission");
  record(deniedFilter.body);
  assert.deepEqual(Object.keys(deniedFilter.body).sort(), ["code"]);
  return saved;
}

async function conflict(first: Page, second: Page, id: string): Promise<void> {
  const update = (name: string) => ({ expectedRevision: 1, documento: documentFor(name) });
  const winner = await api<unknown>(first, "/api/proyectos/" + id, { method: "PUT", body: update("REQ-021 conflict winner"), key: crypto.randomUUID() });
  assert.equal(winner.status, 200);
  const stale = await api<unknown>(second, "/api/proyectos/" + id, { method: "PUT", body: update("REQ-021 conflict loser"), key: crypto.randomUUID() });
  assert.equal(stale.status, 409, "the second context cannot overwrite a stale revision");
  record(stale.body);
  assert.equal(stale.body.code, "REVISION_CONFLICTO");
}

async function seedMany(page: Page): Promise<{ ownerId: string; targetId: string; count: number }> {
  const target = await createProject(page, "REQ-021 deep page match");
  let count = 1;
  for (let index = 1; index <= 54; index += 1) {
    await createProject(page, "REQ-021 pagination seed " + String(index).padStart(2, "0"));
    count += 1;
  }
  return { ownerId: target.ownerId, targetId: target.id, count };
}

async function pagination(page: Page, ownerId: string, targetId: string, expectedCount: number): Promise<void> {
  let cursor: string | null = null;
  let pages = 0;
  let targetIndex = -1;
  let itemCount = 0;
  do {
    const params = new URLSearchParams();
    if (cursor) params.set("cursor", cursor);
    const response = await api<unknown>(page, "/api/proyectos" + (params.size ? "?" + params.toString() : ""));
    assert.equal(response.status, 200);
    record(response.body);
    assert.ok(Array.isArray(response.body.items));
    for (const item of response.body.items) {
      record(item);
      assert.equal(item.ownerId, ownerId);
      if (item.id === targetId) targetIndex = itemCount;
      itemCount += 1;
    }
    cursor = typeof response.body.nextCursor === "string" ? response.body.nextCursor : null;
    pages += 1;
  } while (cursor);
  assert.ok(pages >= 2, "more than fifty projects span multiple pages");
  assert.equal(itemCount, expectedCount);
  assert.ok(targetIndex >= PAGE_SIZE, "matching saved project is beyond the first page");
  await page.goto(origin + "/proyectos");
  await page.getByLabel("Buscar por nombre", { exact: true }).fill("REQ-021 deep page match");
  await page.getByRole("heading", { name: "REQ-021 deep page match", exact: true }).waitFor();
}

async function nextPageRetry(page: Page): Promise<void> {
  let failed = false;
  await page.route("**/api/proyectos?*", async (route) => {
    const url = new URL(route.request().url());
    if (!url.searchParams.has("cursor") || failed) { await route.continue(); return; }
    failed = true;
    await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ code: "PROYECTO_NO_DISPONIBLE" }) });
  });
  await page.goto(origin + "/proyectos");
  await page.getByRole("button", { name: "Cargar más", exact: true }).click();
  await page.getByRole("alert").getByRole("button", { name: "Reintentar", exact: true }).click();
  await page.getByRole("heading", { name: "REQ-021 pagination seed 04", exact: true }).waitFor();
  assert.equal(failed, true);
  await page.unrouteAll();
}

async function staleSearch(page: Page): Promise<void> {
  let release: (() => void) | undefined;
  const started = new Promise<void>((resolve) => { release = resolve; });
  let staleRoute: import("playwright").Route | undefined;
  await page.route("**/api/proyectos?*", async (route) => {
    const url = new URL(route.request().url());
    if (url.searchParams.get("nombre") === "REQ-021 slow search") {
      staleRoute = route;
      release?.();
      return;
    }
    await route.continue();
  });
  await page.goto(origin + "/proyectos");
  const input = page.getByLabel("Buscar por nombre", { exact: true });
  await input.fill("REQ-021 slow search");
  await started;
  await input.fill("REQ-021 pagination seed 54");
  await page.getByRole("heading", { name: "REQ-021 pagination seed 54", exact: true }).waitFor();
  assert.ok(staleRoute);
  await staleRoute!.fulfill({
    status: 200, contentType: "application/json",
    body: JSON.stringify({ items: [{ id: "00000000-0000-4000-8000-000000000001", ownerId: "00000000-0000-4000-8000-000000000002", ownerName: "foreign metadata", nombre: "REQ-021 slow search", revision: 1 }], nextCursor: null }),
  });
  await delay(200);
  assert.equal(await page.getByRole("heading", { name: "REQ-021 pagination seed 54", exact: true }).count(), 1);
  assert.equal(await page.getByText("foreign metadata", { exact: true }).count(), 0);
  await page.unrouteAll();
}

async function authorizedOwnerFilter(page: Page, adminId: string, memberId: string): Promise<void> {
  for (const id of [adminId, memberId]) {
    const result = await api<unknown>(page, "/api/proyectos?propietarioId=" + id);
    assert.equal(result.status, 200, "administrator may filter by an authorized owner");
    record(result.body);
    assert.ok(Array.isArray(result.body.items));
    for (const item of result.body.items) {
      record(item);
      assert.equal(item.ownerId, id);
    }
  }
}

async function composition(page: Page): Promise<void> {
  const document = registryDocument();
  const saved = await createProject(page, document.nombre, document);
  await page.goto(origin + "/proyectos/" + saved.id);
  await page.getByRole("heading", { name: document.nombre, exact: true }).waitFor();
  await page.getByText("Consultar todos los datos de la escena", { exact: true }).click();
  const raw = await page.locator("pre").textContent();
  assert.ok(raw);
  const reopened: unknown = JSON.parse(raw);
  record(reopened);
  assert.ok(Array.isArray(reopened.nodos));
  const tables: unknown[] = [];
  const backings: unknown[] = [];
  for (const node of reopened.nodos) {
    record(node);
    record(node.pieza);
    if (node.pieza.tipo !== "escenografia" || node.pieza.mueble === undefined) continue;
    record(node.pieza.mueble);
    if ("mesa" in node.pieza.mueble) tables.push(node.pieza.mueble.mesa);
    else backings.push(node.pieza.mueble.id);
  }
  assert.equal(tables.length, TIPOS_MESA.length);
  assert.equal(backings.length, IDS_BACKING.length);
  assert.deepEqual(tables.map((table) => { record(table); return table.tipo; }).sort(), [...TIPOS_MESA].sort());
  assert.deepEqual(backings.sort(), [...IDS_BACKING].sort());
}

async function close(database: Awaited<ReturnType<typeof createIsolatedTestDatabase>>, home: string): Promise<void> {
  await browser?.close();
  if (child && child.exitCode === null) {
    child.kill("SIGTERM");
    await Promise.race([new Promise<void>((resolve) => child?.once("exit", () => resolve())), delay(5_000)]);
    if (child.exitCode === null) child.kill("SIGKILL");
  }
  await database.drop();
  await rm(home, { recursive: true, force: true });
}

export async function main(): Promise<void> {
  const target = resolveTestDatabaseTarget(process.env);
  const database = await createIsolatedTestDatabase(target.connectionString);
  const home = await mkdtemp(path.join(os.tmpdir(), "req021-projects-home-"));
  const logs = { stdout: "", stderr: "" };
  try {
    for (const migration of ["037_cuentas.sql", "038_cuentas_datos_administracion.sql", "039_proyectos.sql"]) {
      await database.pool.query(await readFile(path.join(ROOT, "scripts/migrations", migration), "utf8"));
    }
    const accountService = createAccountService(database.pool, VERSION_AVISO_DATOS);
    const accounts = await accountService.seedTestAccounts(PASSWORD);
    const byRole = new Map(accounts.map((account) => [account.roleId, account]));
    const admin = byRole.get("administrador");
    const owner = byRole.get("master_designer");
    const employee = byRole.get("empleado_interno");
    assert.ok(admin && owner && employee, "isolated schema has owner, employee and administrator accounts");
    const otherEmail = "req021-second-owner@example.test";
    const invitation = await accountService.invite({
      actorAccountId: admin.accountId,
      email: otherEmail,
      roleId: "master_designer",
    });
    await accountService.activate({ token: invitation.token, password: PASSWORD, acceptDataNotice: true });
    const other = { accountId: invitation.accountId, email: otherEmail, roleId: "master_designer" };
    const build = run("npm", ["run", "build"], {
      PATH: process.env.PATH, HOME: home, CI: "true", APP_ENV: "test", NODE_ENV: "production",
      NODE_OPTIONS: "--max-old-space-size=4096", NEXT_TELEMETRY_DISABLED: "1", CAPTURA_RENDERS_ENABLED: "1", VERCEL: "1",
    });
    assert.equal(build.status, 0, "production build succeeds without database credentials: " + redact(build.output.slice(-3_000)));
    const port = await freePort();
    const databaseUrl = new URL(target.connectionString);
    databaseUrl.searchParams.set("options", "-c search_path=" + database.schema + ",public");
    origin = "http://localhost:" + port;
    child = spawn(process.execPath, ["node_modules/next/dist/bin/next", "start", "--hostname", "127.0.0.1", "--port", String(port)], {
      cwd: ROOT,
      env: {
        PATH: process.env.PATH, HOME: home, APP_ENV: "test", DATABASE_URL: databaseUrl.toString(),
        DATA_NOTICE_VERSION: VERSION_AVISO_DATOS, CAPTURA_RENDERS_ENABLED: "1", NODE_ENV: "production",
        NEXT_TELEMETRY_DISABLED: "1", VERCEL: "1", PORT: String(port), HOSTNAME: "127.0.0.1",
      },
      stdio: ["ignore", "pipe", "pipe"],
    });
    child.stdout?.on("data", (part: Buffer) => { logs.stdout = tail(logs.stdout, part); });
    child.stderr?.on("data", (part: Buffer) => { logs.stderr = tail(logs.stderr, part); });
    await waitForServer(logs);
    browser = await chromium.launch({
      headless: true,
      ...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ? { executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE } : process.platform === "linux" ? { executablePath: "/usr/bin/chromium" } : {}),
      args: ["--no-sandbox", "--disable-dev-shm-usage"],
    });
    const ownerA = await newPage();
    const ownerB = await newPage();
    const freshOwner = await newPage();
    const otherPage = await newPage();
    const employeePage = await newPage();
    const adminPage = await newPage();
    try {
      await Promise.all([
        login(ownerA.page, owner.email), login(ownerB.page, owner.email), login(freshOwner.page, owner.email),
        login(otherPage.page, other.email), login(employeePage.page, employee.email), login(adminPage.page, admin.email),
      ]);
      const saved = await persistenceAndDenial(ownerA.page, otherPage.page);
      await deniedMutations({ database, user: otherPage.page, staff: employeePage.page, projectId: saved.id, api, documentFor });
      if (DENIALS_ONLY) {
        process.stdout.write("test-integracion-proyectos: PASS (production build, Usuario GET/PUT/DELETE=404, staff PUT=403, original row unchanged)\n");
        return;
      }
      await freshContextReopen({ page: freshOwner.page, origin, projectId: saved.id, expectedScene: scene() });
      await staffReadAndCopy({ page: employeePage.page, origin, staffAccountId: employee.accountId, projectId: saved.id, api });
      await staffReadAndCopy({ page: adminPage.page, origin, staffAccountId: admin.accountId, projectId: saved.id, api });
      await conflict(ownerA.page, ownerB.page, saved.id);
      await legacyImportAndAccountSwitch({ page: ownerA.page, origin, ownerEmail: owner.email, otherEmail: employee.email, api, login, scene });
      if (COMPOSITION) await composition(ownerA.page);
      else {
        const seeded = await seedMany(otherPage.page);
        await pagination(otherPage.page, seeded.ownerId, seeded.targetId, seeded.count);
        await nextPageRetry(otherPage.page);
        await staleSearch(otherPage.page);
      }
      awai
```

## Resolution request deec9ffa25d6d1798fe3f9da9ac100df (src/app/asistente/page.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/deec9ffa25d6d1798fe3f9da9ac100df.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/deec9ffa25d6d1798fe3f9da9ac100df.diff3`
- blobs: base `757b7680e18a3ee394143e439961ce722d7c0431`, ours `8682ad542760cc60a572e3e366f76891b89a6cb8`, theirs `d3d03a14c7025488ad3b2460987b84a8535dda19` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "b3f997fe050f00d031f8ff7103d279b1f33f08c5", "ours": "4a51d40d934170de8275f4e709cdf5f840eded91", "theirs": "88d643b5be177e0ba03178d7fddd523b9ba7f5c7"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/deec9ffa25d6d1798fe3f9da9ac100df.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
import type { Viewport } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ShellHerramientas } from "@/components/herramientas/ShellHerramientas";
import { VistaGuiada } from "@/components/guiado/VistaGuiada";
import { SESSION_COOKIE } from "@/lib/auth/session";
import { resolverSesion } from "@/lib/cuentas/sesion";
import { getRequestLanguage } from "@/lib/idioma/servidor";
import { resolverVersionCodigo } from "@/lib/registro/version";
import { resolveServerRequestSession } from "@/lib/cuentas/sesion-servidor";

/** Sin esto, env(safe-area-inset-*) vale 0 y el teclado del celular tapa el compositor. */
export const viewport: Viewport = { width: "device-width", initialScale: 1, viewportFit: "cover", interactiveWidget: "resizes-content" };
export const instant = false;

<<<<<<< ours (src/app/asistente/page.tsx)
export default async function PaginaAsistenteGuiado() {
||||||| base
export default function PaginaAsistenteGuiado() {
=======
export default async function PaginaAsistenteGuiado() {
  const session = await resolveServerRequestSession();
>>>>>>> theirs
  // Con qué código se sirvió la página: si un turno lo responde otro despliegue, la vista pide recargar (version-pagina.ts).
  // `resolverVersionCodigo` y no `versionCodigo`: la de caché lee Date.now(), que con cacheComponents no se puede usar al
  // prerenderizar la página (Next lo marca como ruta bloqueante y rompe la construcción).
<<<<<<< ours (src/app/asistente/page.tsx)
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  const session = token && /^[A-Za-z0-9_-]{43}$/.test(token) ? await resolverSesion(token) : null;
  if (!session) redirect("/login");

  const language = await getRequestLanguage();
  return (
    <ShellHerramientas permissions={session.permissions} language={language} variant="app">
      <VistaGuiada language={language} versionPagina={resolverVersionCodigo().corta} />
    </ShellHerramientas>
  );
||||||| base
  return <VistaGuiada versionPagina={resolverVersionCodigo().corta} />;
=======
  return <VistaGuiada versionPagina={resolverVersionCodigo().corta} permisos={session?.permissions ?? []} />;
>>>>>>> theirs
}

```

## Resolution request 585d3876c7dcbf3c967460530ce058d6 (src/app/page.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/585d3876c7dcbf3c967460530ce058d6.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/585d3876c7dcbf3c967460530ce058d6.diff3`
- blobs: base `1286483217b68b40c892542cd729dab0f7447e61`, ours `92298fa69ce36192693304c7d08ff9f926c754c0`, theirs `b8a38ca27333ce0f98ce49303b31173ff1be80bd` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "b3f997fe050f00d031f8ff7103d279b1f33f08c5", "ours": "4a51d40d934170de8275f4e709cdf5f840eded91", "theirs": "e3dfac3eea2f350c12d5e22981e3189361214203"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/585d3876c7dcbf3c967460530ce058d6.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
<<<<<<< ours (src/app/page.tsx)
import { connection } from "next/server";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { PortadaHerramientas } from "@/components/herramientas/PortadaHerramientas";
import { SESSION_COOKIE } from "@/lib/auth/session";
import { resolverSesion } from "@/lib/cuentas/sesion";
import { getRequestLanguage } from "@/lib/idioma/servidor";

export const instant = false;

export default async function HomePage() {
  await connection();
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  const session = token && /^[A-Za-z0-9_-]{43}$/.test(token) ? await resolverSesion(token) : null;
  if (!session) redirect("/login");

  return <PortadaHerramientas permissions={session.permissions} roles={session.roles} language={await getRequestLanguage()} />;
||||||| base
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { Lock, RefreshCw } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { CREATIVIDAD_POR_DEFECTO, type NivelCreatividad } from "@/lib/ia/escena/creatividad";
import { DecoracionCard } from "@/components/DecoracionCard";
import { Lightbox } from "@/components/Lightbox";
import { PromptModal } from "@/components/PromptModal";
import { Markdown } from "@/components/Markdown";
import { ProductoCard } from "@/components/ProductoCard";
import { TarjetaCotizacion } from "@/components/TarjetaCotizacion";
import { CotizacionProfesional } from "@/components/cotizacion/CotizacionProfesional";
import { TarjetaPlanDecoracion } from "@/components/TarjetaPlanDecoracion";
import { ReferenceAnalysisController } from "@/components/references/ReferenceAnalysisController";
import { SOLO_ANALISIS_FOTO } from "@/lib/ia/nucleo/feature-flags";
import { cargarFactorPlazoCliente, factorPlazoCliente } from "@/lib/ia/plazo-cliente";
import type { ReferenceDraft } from "@/components/references/ReferenceReviewPanel";
import { PasosAsistente } from "@/components/propuesta";
import { useSeleccion } from "@/lib/estado/seleccion";
import type { Cotizacion } from "@/lib/cotizacion/motor";
import type { Imagen, PeticionImagen } from "@/lib/ia/nucleo/tipos";
import { prepararFotoReferencia, redimensionarImagen } from "@/lib/imagen-cliente/preparar-foto";
import { ASPECTOS_SOPORTADOS, aspectoMasCercano } from "@/lib/ia/nucleo/aspecto";
import type { ReferenceBlueprintV2 } from "@/lib/ia/referencia/reference-blueprint";
import type { PlanResuelto } from "@/lib/plan/resuelto";
import type { ItemRechazado, ItemValidado } from "@/lib/rag/chat/validar";
import type { Faceta, FiltrosCatalogo } from "@/lib/shopify/consultas";
import type { Brief, DecoracionConProductos, Producto } from "@/lib/types";
import { classifyGenerationIds, normalizeGenerationSources } from "@/lib/generacion/provenance";
import { cuerpoGeneracion } from "@/lib/generacion/cuerpo-generacion";
import { MENSAJE_SOLO_REFERENCIAS } from "@/lib/estado/mensaje-foto-referencia";

import { ChatSseEventV1Schema } from "@/lib/ia/contracts/chat-v1";
import { CATALOGO_ERRORES_UI_V1, construirUiErrorV1, leerUiErrorV1, type AccionUiV1, type UiErrorV1 } from "@/lib/ia/contracts/ui-error-v1";
import { AvisoError } from "@/components/errores/AvisoError";
import { useModoVista } from "@/lib/estado/modo-vista";
import { abrirPromptAutomaticamente } from "@/lib/estado/modo-vista-reglas";
import { aplicarEventoHerramienta, cerrarPasos, type PasoAsistente } from "@/lib/estado/pasos-asistente";
import { contextoEventoConversacion } from "@/lib/estado/contexto-evento";
import { crearEsperaAnalisis, type EstadoAnalisisReferencia } from "@/lib/estado/espera-analisis";
import { adjuntosParaGeneracion, contextoDeGeneracion } from "@/lib/estado/generacion-adjuntos";
import { aligerarAdjuntos, claveImagen, imagenesSinMiniatura, type AdjuntosTurno } from "@/lib/estado/persistencia-adjuntos";
import { respetarReintentable, uiErrorDesdeEventoChat, type OrigenError } from "@/lib/estado/estado-error";
import { mensajeErrorCliente } from "@/lib/estado/mensaje-error-cliente";
import { nuevaConversacion, obtenerIdConversacion, registrarEventoCliente } from "@/lib/registro/cliente";
import { CalificacionClasica } from "@/components/ui/shell/CalificacionClasica";
import {
  CLAVE_GENERACIONES,
  generacionParaRestaurar,
  leerGeneraciones,
  REDUCCIONES_IMAGEN_GENERADA,
  elegirImagenReducida,
  registrarGeneracion,
  registrarVistaPreviaNoDisponible,
  serializarGeneraciones,
  sinImagenes,
} from "@/lib/estado/persistencia-generacion";
import { creatividadGuardada } from "@/lib/estado/persistencia-creatividad";
import { imagenDeFotoEjemplo, type FotoEjemplo } from "@/lib/referencias-ejemplo/manifiesto";
import { CabeceraApp } from "@/components/ui/shell/CabeceraApp";
import { Compositor } from "@/components/ui/shell/Compositor";
import { EsperaAsistente } from "@/components/ui/shell/EsperaAsistente";
import { CargaImagen } from "@/components/propuesta/CargaImagen";
import { CierrePropuesta } from "@/components/propuesta/CierrePropuesta";
import { coloresCliente } from "@/lib/plan/presentacion-cliente";
import { DialogoEjemplos, GaleriaEjemplos } from "@/components/ui/shell/GaleriaEjemplos";
import { HojaSeleccion } from "@/components/ui/shell/HojaSeleccion";
import { volarFoto } from "@/components/ui/shell/vuelo-foto";
import { marcarProducido } from "@/components/feedback-ia/producidos";
import { BotonVoz } from "@/components/voz/BotonVoz";

type ProveedorId = "gemini";
const NOMBRE_PROVEEDOR: Record<ProveedorId, string> = {
  gemini: "Gemini 3.6 Flash (chat)",
};

type GeneracionVisible = {
  modo: "flux";
  solicitado: ProveedorId;
  etiqueta: string;
  prompts: Array<{ label: string; prompt: string }>;
};

type Mensaje = {
  /** Estable por mensaje (no el índice del array) — necesario para que
   * Motion pueda animar entradas/salidas de la lista de forma confiable. */
  id: string;
  role: "user" | "assistant";
  content: string;
  productos?: Producto[];
  decoraciones?: DecoracionConProductos[];
  categorias?: Faceta[];
  /** Filtros que produjeron `categorias` (ocasión, colores…) — se reusan al navegar a un tipo puntual sin pasar por la IA. */
  categoriasFiltros?: FiltrosCatalogo;
  plan?: PlanResuelto;
  /** Brief del evento `fin` de esta respuesta: la cabecera distingue si cambió después de la última propuesta. */
  brief?: Brief;
  cotizacion?: Cotizacion;
  referenceBlueprint?: ReferenceBlueprintV2;
  /** Debug: JSON crudo que usó el análisis de imágenes de referencia. Va
   * aparte del `content` markdown (que no interpreta HTML) para poder
   * mostrarlo colapsado sin reventar el layout del chat. */
  analisisReferencias?: unknown;
  /** Piezas ya validadas contra la DB real (plan Fase 4/6) — se muestran con
   * foto y link a la tienda para poder verificar que el modelo no inventó
   * nada, en vez de confiar a ciegas en la tabla de texto que redacta. */
  ragValidados?: ItemValidado[];
  /** Fase 3.11: piezas que el modelo propuso pero el backend descartó (no
   * estaban en la whitelist recuperada, variante agotada, etc.). El backend
   * ya calcula esto — antes se recibía en el SSE y se tiraba sin mostrarlo,
   * así que una sustitución o un descarte podía pasar sin que el cliente lo
   * viera nunca (viola "nunca sustituir en silencio"). */
  ragRechazados?: ItemRechazado[];
  /**
   * Fotos del turno que produjo este mensaje (iteración 4): miniatura en el
   * mensaje del cliente y recortes por pieza en la propuesta. El estado de
   * adjuntos del compositor puede cambiar después, así que se copian aquí al
   * enviar. En sessionStorage solo va una miniatura liviana de las más
   * recientes (src/lib/estado/persistencia-adjuntos.ts).
   */
  adjuntos?: AdjuntosTurno;
  /** Pasos en vivo del asistente para este turno (eventos SSE `herramienta`). */
  pasos?: PasoAsistente[];
};

/** Una foto restaurada de sessionStorage ya viene como data URL (su miniatura). */
function dataUrl(imagen: { base64: string; mime: string }): string {
  return imagen.base64.startsWith("data:") ? imagen.base64 : `data:${imagen.mime};base64,${imagen.base64}`;
}

/** Copia liviana de los adjuntos del turno; los ids siguen el orden que usa /api/references/analyze (REF_01…). */
function adjuntosDelTurno(referencias: readonly Imagen[], fotoEspacio: Imagen | null): AdjuntosTurno | undefined {
  if (!referencias.length && !fotoEspacio) return undefined;
  return {
    referencias: referencias.map(({ base64, mime }, indice) => ({ id: `REF_${String(indice + 1).padStart(2, "0")}`, base64, mime })),
    ...(fotoEspacio ? { fotoEspacio: { base64: fotoEspacio.base64, mime: fotoEspacio.mime } } : {}),
  };
}

const SALUDO: Mensaje = {
  id: "saludo",
  role: "assistant",
  content:
    "¡Hola! Soy el asistente de decoración. Cuéntame qué evento estás planeando y te armo una propuesta. En cualquier momento puedes tocar, agregar o quitar piezas tú mismo.",
};

// v2 invalida conversaciones que contienen planes resueltos antes de que
// existiera el límite de sustituciones (por ejemplo R-12→R-24). Reutilizar
// esos objetos haría que la UI siguiera mostrando una cotización que el
// servidor actual ya rechaza.
const CLAVE_CHAT = "demo_chat_v4";
const CLAVE_CHAT_LEGACY = "demo_chat_v1";

const SUGERENCIAS = [
  "Quiero ideas para mi boda en un jardín",
  "XV años estilo glamour en salón",
  "Algo boho en tonos tierra",
];

const LIMITE_INACTIVIDAD_CHAT_MS = 90_000;
/** Espera máxima de un análisis de la foto que no responde antes de enviar el turno sin él (p95 medido: 20 s). Si falla, no se espera. */
const LIMITE_ESPERA_ANALISIS_MS = 45_000;

/** `order` de flexbox para lo que va después de toda la conversación (visualización, errores, análisis sin enviar). */
const ORDEN_AL_FINAL = 1_000_000;

type DatosFin = {
  reply: string;
  brief?: Brief;
  recomendaciones?: Producto[];
  decoraciones?: DecoracionConProductos[];
  categorias?: Faceta[];
  filtrosCategorias?: FiltrosCatalogo;
  cotizacion?: Cotizacion;
  /** Piezas que la IA decidió proponer por su cuenta — dispara /api/generate sin que el cliente haga clic. */
  seleccionIA?: Producto[];
  instruccionIA?: string;
  ragValidados?: ItemValidado[];
  ragRechazados?: ItemRechazado[];
  plan?: PlanResuelto;
  referenceBlueprint?: ReferenceBlueprintV2;
};

type GenerarOverride = {
  ids: string[];
  /** Exact RAG variant ids. Kept separate from legacy/manual catalog ids. */
  ragVariantIds?: string[];
  paquetes?: Record<string, number>;
  instruccion?: string;
  brief?: Brief;
  solicitudUsuario?: string;
  /**
   * Cuando viene de aplicar una cotización editada a mano: `ids` ya es la
   * lista completa y definitiva de piezas (incluye lo que el cliente quitó
   * o reemplazó). Sin este flag, `generar()` reinyecta encima las piezas
   * del último `ragValidados` y las de la selección compartida — exacto lo
   * que se quiere evitar, porque una pieza recién quitada "reaparecería".
   */
  soloIds?: boolean;
  /**
   * Piezas manuales a usar tal cual cuando `soloIds` es true — no se puede
   * derivar de `seleccionados` porque `reemplazarTodo()` (que se llama justo
   * antes) todavía no aplicó su actualización de estado en este mismo tick.
   */
  manualProducts?: Producto[];
  /** Propuesta aprobada. Toda imagen sale de una (ADR-0023, paso 1). */
  plan: PlanResuelto;
  /** Mensaje exacto al que debe volver la cotización final de esta generación. */
  anchorMessageId?: string;
  /** Adjuntos de la propuesta anclada; evita usar fotos de otro turno. */
  adjuntos?: AdjuntosTurno;
};

type ErrorVisible = { ui: UiErrorV1; origen: OrigenError };

const ACCIONES_POR_ORIGEN: Readonly<Record<OrigenError, ReadonlySet<AccionUiV1>>> = {
  chat: new Set<AccionUiV1>(["reintentar", "ajustar_propuesta", "pedir_nueva_propuesta", "revisar_adjuntos"]),
  generacion: new Set<AccionUiV1>(["reintentar", "revisar_propuesta", "pedir_nueva_propuesta", "ajustar_propuesta", "revisar_adjuntos"]),
  catalogo: new Set<AccionUiV1>(),
  plan: new Set<AccionUiV1>(["revisar_propuesta"]),
};

function errorLocal(code: Parameters<typeof construirUiErrorV1>[0], mensaje: string, mensajeUsuario?: string): UiErrorV1 {
  return construirUiErrorV1(code, { mensaje, mensajeUsuario });
}

/** The page kept only thumbnails of the photos (a reload): the file itself was fine. */
const FOTOS_PERDIDAS_AL_RECARGAR = "La página se recargó y de tus fotos solo guardé miniaturas. Vuelve a adjuntarlas y creo la imagen.";

function campoTexto(valor: unknown, campo: string): string | undefined {
  if (typeof valor !== "object" || valor === null || !(campo in valor)) return undefined;
  const dato: unknown = (valor as Record<string, unknown>)[campo];
  return typeof dato === "string" && dato.length > 0 ? dato : undefined;
}

/** `retryable` del sobre de error (error.v1); undefined si no viene. */
function campoReintentable(valor: unknown): boolean | undefined {
  if (typeof valor !== "object" || valor === null || !("retryable" in valor)) return undefined;
  const dato: unknown = (valor as Record<string, unknown>).retryable;
  return typeof dato === "boolean" ? dato : undefined;
}

/**
 * Streaming real (§5.4 del plan): parsea a mano los bloques
 * `event: X\ndata: Y\n\n` de la respuesta SSE de /api/chat. No se usa
 * EventSource porque necesita ir por POST con cuerpo JSON, algo que
 * EventSource no soporta.
 */
async function consumirSSE(
  body: ReadableStream<Uint8Array>,
  manejadores: {
    onTexto: (delta: string) => void;
    onHerramienta: (nombre: string, estado: "ejecutando" | "lista", ok?: boolean) => void;
    onFin: (datos: DatosFin) => void;
    onError: (datos: { error?: string; code?: string; causa?: string; request_id?: string; retryable?: boolean }) => void;
    onActividad?: () => void;
  },
) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let recibioFinal = false;
  let recibioError = false;

  function procesarBloque(bloque: string) {
    let evento = "message";
    let datosCrudo = "";
    for (const linea of bloque.split("\n")) {
      if (linea.startsWith("event: ")) evento = linea.slice(7);
      else if (linea.startsWith("data: ")) datosCrudo += linea.slice(6);
    }
    if (!datosCrudo) return;
    const datos = JSON.parse(datosCrudo) as unknown;
    if (recibioFinal || recibioError) return;
    const eventoValidado = ChatSseEventV1Schema.safeParse(datos);
    if (!eventoValidado.success || eventoValidado.data.type !== evento) {
      throw new Error("El servidor devolvió un evento SSE inválido.");
    }
    const datosValidados = eventoValidado.data;
    manejadores.onActividad?.();
    if (datosValidados.type === "texto") manejadores.onTexto(datosValidados.delta);
    else if (datosValidados.type === "herramienta") manejadores.onHerramienta(datosValidados.nombre, datosValidados.estado, datosValidados.ok);
    else if (datosValidados.type === "fin") {
      recibioFinal = true;
      manejadores.onFin(datosValidados);
    } else if (datosValidados.type === "error") {
      recibioError = true;
      manejadores.onError(datosValidados);
    }
  }

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let indice: number;
    while ((indice = buffer.indexOf("\n\n")) !== -1) {
      procesarBloque(buffer.slice(0, indice));
      buffer = buffer.slice(indice + 2);
    }
  }
  if (!recibioFinal && !recibioError) throw new Error("El asistente cerró la respuesta antes de terminar.");
}

// Debe coincidir con LIMITE_REFERENCIAS_CLIENTE en src/app/api/generate/route.ts.
const LIMITE_REFERENCIAS_CLIENTE = 3;

/** Mapea una proporción real (ancho/alto) al aspecto soportado más cercano, comparando razones en escala logarítmica (así 3:2 y 2:3 no se confunden solo por estar "cerca" en valor absoluto). */
function aspectoDe(ancho: number, alto: number): PeticionImagen["aspecto"] {
  return aspectoMasCercano(ancho / alto);
}

// El redimensionado de las fotos vive en `src/lib/imagen-cliente/preparar-foto.ts`: la guiada prepara la foto de
// inspiración con la MISMA función (`prepararFotoReferencia`), así las dos vistas leen la misma imagen.

/**
 * Recorta al centro para que la imagen coincida EXACTO con uno de los 4
 * aspectos que soportan los proveedores, en vez de mandarla con su
 * proporción real y dejar que el modelo de edición decida cómo encajarla.
 * Sin este paso, una foto de celular en 4:3 se manda "tal cual" hacia un
 * lienzo 3:2 — el desajuste de proporción es una fuente real de distorsión
 * de perspectiva en la imagen generada (el modelo tiene que estirar o
 * recortar el espacio real para llenar un lienzo con otra forma).
 */
async function recortarAlAspecto(
  base64: string,
  mime: string,
  aspecto: PeticionImagen["aspecto"],
): Promise<{ base64: string; ancho: number; alto: number }> {
  const bitmap = await createImageBitmap(await (await fetch(`data:${mime};base64,${base64}`)).blob());
  try {
    const razonObjetivo = ASPECTOS_SOPORTADOS.find((a) => a.valor === aspecto)?.razon ?? 3 / 2;
    const razonActual = bitmap.width / bitmap.height;
    let anchoRecorte = bitmap.width;
    let altoRecorte = bitmap.height;
    if (razonActual > razonObjetivo) {
      anchoRecorte = Math.round(bitmap.height * razonObjetivo);
    } else {
      altoRecorte = Math.round(bitmap.width / razonObjetivo);
    }
    const offsetX = Math.floor((bitmap.width - anchoRecorte) / 2);
    const offsetY = Math.floor((bitmap.height - altoRecorte) / 2);

    const canvas = document.createElement("canvas");
    canvas.width = anchoRecorte;
    canvas.height = altoRecorte;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Este navegador no pudo procesar la imagen. Prueba con otro navegador.");
    ctx.drawImage(bitmap, offsetX, offsetY, anchoRecorte, altoRecorte, 0, 0, anchoRecorte, altoRecorte);

    const blob = await new Promise<Blob>((resolve, reject) => {
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("No se pudo recortar la imagen."))), "image/jpeg", 0.85);
    });
    const base64Recortado = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve((reader.result as string).split(",")[1]);
      reader.onerror = () => reject(new Error("No se pudo leer la imagen recortada."));
      reader.readAsDataURL(blob);
    });
    return { base64: base64Recortado, ancho: anchoRecorte, alto: altoRecorte };
  } finally {
    bitmap.close();
  }
}

/** Miniatura JPEG liviana (data URL) de una foto del turno, para guardarla con la conversación. */
async function miniaturaImagen(imagen: { base64: string; mime: string }, maxDim = 480, calidad = 0.72): Promise<string> {
  const bitmap = await createImageBitmap(await (await fetch(dataUrl(imagen))).blob());
  try {
    const escala = Math.min(1, maxDim / Math.max(bitmap.width, bitmap.height));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(bitmap.width * escala));
    canvas.height = Math.max(1, Math.round(bitmap.height * escala));
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Sin canvas 2D.");
    ctx.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", calidad);
  } finally {
    bitmap.close();
  }
}

// Guard de generación, a nivel de módulo (una sola vez por pestaña, no por
// instancia de componente). Bug real: adjuntar una referencia y mandar un
// mensaje de chat casi a la vez puede hacer que DOS rutas independientes
// —la respuesta del chat (ve la referencia y confirma su propia selección)
// y el análisis automático de blueprint del panel de referencias— decidan
// generar cada una por su cuenta. `colaGeneracion` encadena ambas sobre la
// MISMA promesa: `.then()` en JavaScript garantiza qu
```

## Resolution request 6d4aa822010fb3ca2b27ee9dbbdc64e0 (src/components/ui/shell/CabeceraApp.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/6d4aa822010fb3ca2b27ee9dbbdc64e0.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/6d4aa822010fb3ca2b27ee9dbbdc64e0.diff3`
- blobs: base `b19d503d7792e2ec79c4dceb5f262c9c8478d66c`, ours `a973c4c3be282937da6b50fd990d0ac2f82eeaa7`, theirs `fbaaa1edcb927714a23092881963a8a7d4d9ebd9` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "b3f997fe050f00d031f8ff7103d279b1f33f08c5", "ours": "4a51d40d934170de8275f4e709cdf5f840eded91", "theirs": "e3dfac3eea2f350c12d5e22981e3189361214203"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/6d4aa822010fb3ca2b27ee9dbbdc64e0.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "motion/react";
import { ChartColumn, FlaskConical, ListChecks, Monitor, Moon, Shield, Sun, Trash2 } from "lucide-react";
import { OPCIONES_TEMA } from "@/lib/tema/tema";
import { useTema } from "@/lib/tema/use-tema";
import type { NivelCreatividad } from "@/lib/ia/escena/creatividad";
import type { ModoVista } from "@/lib/estado/modo-vista";
import { SwitchModoVista } from "@/components/modo/SwitchModoVista";
import { InterruptorTema } from "@/components/ui/interruptor-tema";
import { MenuApp, type ItemMenu } from "./MenuApp";
import { SelectorCreatividad } from "./SelectorCreatividad";
<<<<<<< ours (src/components/ui/shell/CabeceraApp.tsx)
import { textosHerramientas } from "@/components/herramientas/textos-herramientas";
import type { Idioma } from "@/lib/idioma/idioma";
||||||| base
=======
import { usePermisosNavegacion } from "@/components/cuentas/PermisosNavegacion";
import { PERMISOS } from "@/lib/cuentas/permisos";
>>>>>>> theirs

type Props = {
  language?: Idioma;
  /** "Cumpleaños · rosa y plata · hasta $ 1.500.000" o null si el brief está vacío. */
  contexto: string | null;
  creatividad?: NivelCreatividad;
  onCreatividad?: (nivel: NivelCreatividad) => void;
  modoVista: ModoVista;
  onModoVista: (modo: ModoVista) => void;
  onLimpiar: () => void;
  limpiarDeshabilitado: boolean;
  /** Cómo se llama esa acción en el menú (la guiada: «Empezar de nuevo», que confirma antes); por defecto «Limpiar chat». */
  etiquetaLimpiar?: string;
  iconoLimpiar?: ReactNode;
  /** Abre la hoja de selección manual; undefined cuando no aplica (hay propuesta en modo usuario). */
  onAbrirSeleccion?: () => void;
  totalSeleccion: number;
  /** Controles técnicos: se muestran en una barra aparte solo en modo dev. */
  barraDev?: ReactNode;
  /** Vista guiada: sin el interruptor «Modo dev» (el cliente no lo necesita). */
  ocultarModoDev?: boolean;
};

/** Marca simple de la maqueta: cuadro violeta con un anillo y un punto. */
function MarcaIcono() {
  return (
    <span className="app-marca-icono" aria-hidden="true">
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="5.5" stroke="currentColor" strokeOpacity="0.65" strokeWidth="1.2" />
        <circle cx="8" cy="8" r="1.8" fill="currentColor" />
      </svg>
    </span>
  );
}

/**
 * Cabecera de una sola línea (maquetas Main y EstadoInicial): marca, contexto
 * del evento al centro, creatividad compacta, tema, "Modo dev" y menú.
 */
export function CabeceraApp({ language = "es", contexto, creatividad, onCreatividad, modoVista, onModoVista, onLimpiar, limpiarDeshabilitado, etiquetaLimpiar, iconoLimpiar, onAbrirSeleccion, totalSeleccion, barraDev, ocultarModoDev = false }: Props) {
  const pathname = usePathname();
<<<<<<< ours (src/components/ui/shell/CabeceraApp.tsx)
  const copy = textosHerramientas(language);
||||||| base
=======
  const permissions = usePermisosNavegacion();
>>>>>>> theirs
  const esDev = modoVista === "dev";
  // Vista guiada (pensada para el móvil): tema y menú con el blanco táctil de 44 px.
  const tactil = pathname === "/asistente";
  const puedeVerCatalogo = permissions.includes(PERMISOS.catalogo);
  const puedeVerChat = permissions.includes(PERMISOS.chat_asistido);
  const puedeVer3d = permissions.includes(PERMISOS.taller_3d);
  const puedeVerAdministracion = permissions.includes(PERMISOS.herramientas_internas);
  const { preferencia: preferenciaTema, cambiar: cambiarTema } = useTema();
  const ICONO_TEMA = { light: <Sun className="size-4" />, dark: <Moon className="size-4" />, sistema: <Monitor className="size-4" /> } as const;
  const items: ItemMenu[] = [
<<<<<<< ours (src/components/ui/shell/CabeceraApp.tsx)
||||||| base
    { tipo: "enlace", id: "catalogo", etiqueta: "Explorar catálogo", href: "/catalogo", icono: <LayoutGrid className="size-4" /> },
=======
    ...(puedeVerCatalogo ? [{ tipo: "enlace" as const, id: "catalogo", etiqueta: "Explorar catálogo", href: "/catalogo", icono: <LayoutGrid className="size-4" /> }] : []),
>>>>>>> theirs
    ...(onAbrirSeleccion
      ? [{ tipo: "accion" as const, id: "seleccion", etiqueta: copy.selectSummary(totalSeleccion), onSeleccionar: onAbrirSeleccion, icono: <ListChecks className="size-4" /> }]
      : []),
<<<<<<< ours (src/components/ui/shell/CabeceraApp.tsx)
    { tipo: "accion", id: "limpiar", etiqueta: etiquetaLimpiar ?? copy.clearChat, onSeleccionar: onLimpiar, deshabilitado: limpiarDeshabilitado, icono: iconoLimpiar ?? <Trash2 className="size-4" /> },
||||||| base
    { tipo: "accion", id: "limpiar", etiqueta: etiquetaLimpiar, onSeleccionar: onLimpiar, deshabilitado: limpiarDeshabilitado, icono: iconoLimpiar ?? <Trash2 className="size-4" /> },
    pathname === "/asistente"
      ? { tipo: "enlace", id: "vista-clasica", etiqueta: "Vista clásica", href: "/" }
      : { tipo: "enlace", id: "vista-guiada", etiqueta: "Asistente guiado", href: "/asistente" },
    // El taller 3D de globos, en producción y en local.
    { tipo: "enlace", id: "taller-3d", etiqueta: "Globos en 3D", href: "/3d", icono: <Box className="size-4" /> },
=======
    { tipo: "accion", id: "limpiar", etiqueta: etiquetaLimpiar, onSeleccionar: onLimpiar, deshabilitado: limpiarDeshabilitado, icono: iconoLimpiar ?? <Trash2 className="size-4" /> },
    ...(puedeVerChat ? [pathname === "/asistente"
      ? { tipo: "enlace" as const, id: "vista-clasica", etiqueta: "Vista clásica", href: "/" }
      : { tipo: "enlace" as const, id: "vista-guiada", etiqueta: "Asistente guiado", href: "/asistente" }] : []),
    // El taller 3D de globos, en producción y en local.
    ...(puedeVer3d ? [{ tipo: "enlace" as const, id: "taller-3d", etiqueta: "Globos en 3D", href: "/3d", icono: <Box className="size-4" /> }] : []),
>>>>>>> theirs
    // D10: the header switch flips light/dark quickly; here the customer can also go back to "Sistema".
    { tipo: "separador", id: "sep-tema" },
<<<<<<< ours (src/components/ui/shell/CabeceraApp.tsx)
    { tipo: "titulo", id: "titulo-tema", etiqueta: copy.theme },
    ...OPCIONES_TEMA.map((opcion): ItemMenu => ({ tipo: "opcion", id: `tema-${opcion.valor}`, etiqueta: opcion.valor === "light" ? copy.themeLight : opcion.valor === "dark" ? copy.themeDark : copy.themeSystem, marcado: preferenciaTema === opcion.valor, onSeleccionar: () => cambiarTema(opcion.valor), icono: ICONO_TEMA[opcion.valor] })),
    ...(esDev
||||||| base
    { tipo: "titulo", id: "titulo-tema", etiqueta: "Tema" },
    ...OPCIONES_TEMA.map((opcion): ItemMenu => ({ tipo: "opcion", id: `tema-${opcion.valor}`, etiqueta: opcion.etiqueta, marcado: preferenciaTema === opcion.valor, onSeleccionar: () => cambiarTema(opcion.valor), icono: ICONO_TEMA[opcion.valor] })),
    ...(esDev
=======
    { tipo: "titulo", id: "titulo-tema", etiqueta: "Tema" },
    ...OPCIONES_TEMA.map((opcion): ItemMenu => ({ tipo: "opcion", id: `tema-${opcion.valor}`, etiqueta: opcion.etiqueta, marcado: preferenciaTema === opcion.valor, onSeleccionar: () => cambiarTema(opcion.valor), icono: ICONO_TEMA[opcion.valor] })),
    ...(esDev && puedeVerAdministracion
>>>>>>> theirs
      ? ([
          { tipo: "separador", id: "sep-dev" },
          { tipo: "enlace", id: "estadisticas", etiqueta: copy.statistics, href: "/estadisticas", icono: <ChartColumn className="size-4" /> },
          { tipo: "enlace", id: "laboratorio", etiqueta: copy.laboratory, href: "/laboratorio-referencias", icono: <FlaskConical className="size-4" /> },
          { tipo: "enlace", id: "admin", etiqueta: copy.administration, href: "/admin", icono: <Shield className="size-4" /> },
        ] satisfies ItemMenu[])
      : []),
  ];

  return (
    <>
      <header className="app-header">
        <div className="app-marca">
          <MarcaIcono />
          <h1 tabIndex={-1} className="sr-only truncate text-sm font-semibold tracking-[-0.015em] focus-visible:outline-3 focus-visible:outline-offset-4 focus-visible:outline-acento min-[480px]:not-sr-only">{copy.sceneTitle}</h1>
        </div>
        <div className="app-contexto" data-testid="contexto-evento">
          <AnimatePresence mode="wait" initial={false}>
            {contexto && (
              <motion.p key={contexto} className="truncate" title={contexto} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.2 }}>
                {contexto}
              </motion.p>
            )}
          </AnimatePresence>
        </div>
        <div className="app-acciones">
          {creatividad !== undefined && onCreatividad && <SelectorCreatividad valor={creatividad} onCambiar={onCreatividad} language={language} />}
          <InterruptorTema className={tactil ? "size-11" : ""} language={language} />
          {!ocultarModoDev && <SwitchModoVista modo={modoVista} onCambiar={onModoVista} language={language} />}
          <MenuApp items={items} etiqueta={copy.moreOptions} {...(tactil ? { claseBoton: "ui-icon-button size-11" } : {})} />
        </div>
      </header>
      {contexto && <p className="app-contexto-movil truncate">{contexto}</p>}
      {esDev && barraDev && (
        <div className="app-barra-dev" aria-label={copy.developmentControls} role="group">
          {barraDev}
        </div>
      )}
    </>
  );
}

```

## Resolution request 88054d9772b8651d2e5deb8410a8f05a (src/app/asistente/page.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/88054d9772b8651d2e5deb8410a8f05a.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/88054d9772b8651d2e5deb8410a8f05a.diff3`
- blobs: base `757b7680e18a3ee394143e439961ce722d7c0431`, ours `8682ad542760cc60a572e3e366f76891b89a6cb8`, theirs `5ab7d87822f8f792c2324d7b15233caf05743141` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "b3f997fe050f00d031f8ff7103d279b1f33f08c5", "ours": "4a51d40d934170de8275f4e709cdf5f840eded91", "theirs": "e3dfac3eea2f350c12d5e22981e3189361214203"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/88054d9772b8651d2e5deb8410a8f05a.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
import type { Viewport } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { ShellHerramientas } from "@/components/herramientas/ShellHerramientas";
import { VistaGuiada } from "@/components/guiado/VistaGuiada";
import { SESSION_COOKIE } from "@/lib/auth/session";
import { resolverSesion } from "@/lib/cuentas/sesion";
import { getRequestLanguage } from "@/lib/idioma/servidor";
import { resolverVersionCodigo } from "@/lib/registro/version";
import { Suspense } from "react";
import { resolveServerSession } from "@/lib/cuentas/sesion-servidor";
import { PermisosNavegacionProvider } from "@/components/cuentas/PermisosNavegacion";

/** Sin esto, env(safe-area-inset-*) vale 0 y el teclado del celular tapa el compositor. */
export const viewport: Viewport = { width: "device-width", initialScale: 1, viewportFit: "cover", interactiveWidget: "resizes-content" };

export default async function PaginaAsistenteGuiado() {
  // Con qué código se sirvió la página: si un turno lo responde otro despliegue, la vista pide recargar (version-pagina.ts).
  // `resolverVersionCodigo` y no `versionCodigo`: la de caché lee Date.now(), que con cacheComponents no se puede usar al
  // prerenderizar la página (Next lo marca como ruta bloqueante y rompe la construcción).
<<<<<<< ours (src/app/asistente/page.tsx)
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  const session = token && /^[A-Za-z0-9_-]{43}$/.test(token) ? await resolverSesion(token) : null;
  if (!session) redirect("/login");

  const language = await getRequestLanguage();
  return (
    <ShellHerramientas permissions={session.permissions} language={language} variant="app">
      <VistaGuiada language={language} versionPagina={resolverVersionCodigo().corta} />
    </ShellHerramientas>
  );
||||||| base
  return <VistaGuiada versionPagina={resolverVersionCodigo().corta} />;
=======
  return <Suspense fallback={null}><AsistenteConPermisos /></Suspense>;
}

async function AsistenteConPermisos() {
  const session = await resolveServerSession();
  return <PermisosNavegacionProvider permissions={session?.permissions ?? []}><VistaGuiada versionPagina={resolverVersionCodigo().corta} /></PermisosNavegacionProvider>;
>>>>>>> theirs
}

```

## Resolution request f97d80d9d2fc59d46ef6cd1c461f869c (src/app/login/page.tsx)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/f97d80d9d2fc59d46ef6cd1c461f869c.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/f97d80d9d2fc59d46ef6cd1c461f869c.diff3`
- blobs: base `b47f60af1fe8a683d99a948bf441fe1b70f21833`, ours `6d9ac809245754118ad1cb4b80cb5117f82d4b5f`, theirs `70a16d3cb604edfbd59c9ef925dfee0e30ae8316` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "b3f997fe050f00d031f8ff7103d279b1f33f08c5", "ours": "4a51d40d934170de8275f4e709cdf5f840eded91", "theirs": "e3dfac3eea2f350c12d5e22981e3189361214203"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/f97d80d9d2fc59d46ef6cd1c461f869c.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
import { Suspense } from "react";
import { InterruptorTema } from "@/components/ui/interruptor-tema";
import { SelectorIdioma } from "@/lib/idioma/cliente";
import { getRequestLanguage } from "@/lib/idioma/servidor";
import { LoginForm } from "./LoginForm";
<<<<<<< ours (src/app/login/page.tsx)
||||||| base
import { idiomaAcceso } from "@/components/cuentas/textos-acceso";
=======
import { idiomaAcceso } from "@/components/cuentas/textos-acceso";
import { resolveServerSession } from "@/lib/cuentas/sesion-servidor";
import { redirect } from "next/navigation";
import { CUENTA_ADMINISTRADOR_LOCAL_ID } from "@/lib/cuentas/modo-local";
import { destinoPorDefecto } from "@/lib/auth/destino-por-defecto";
>>>>>>> theirs

export const instant = false;

export default async function LoginPage() {
<<<<<<< ours (src/app/login/page.tsx)
  const language = await getRequestLanguage();
||||||| base
  const language = idiomaAcceso((await headers()).get("accept-language") ?? "es");
=======
  const session = await resolveServerSession();
  if (session) redirect(session.accountId === CUENTA_ADMINISTRADOR_LOCAL_ID ? "/" : destinoPorDefecto(session.permissions));
  const language = idiomaAcceso((await headers()).get("accept-language") ?? "es");
>>>>>>> theirs
  return (
    <main className="relative flex min-h-dvh items-center justify-center bg-fondo px-4">
      <div className="absolute right-3 top-3 flex items-center gap-2">
        <SelectorIdioma idioma={language} />
        <InterruptorTema language={language} />
      </div>
      <Suspense>
        <LoginForm language={language} />
      </Suspense>
    </main>
  );
}

```

## Resolution request fbddea742dcfc000eb541a6dcedd0981 (src/lib/cuentas/cuenta-actual.ts)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/fbddea742dcfc000eb541a6dcedd0981.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/fbddea742dcfc000eb541a6dcedd0981.diff3`
- blobs: base `f27871b61ac96a5c5ca702b95a65a773fb1b4171`, ours `6b3da47d5f39d487a128fa1d5c35a83fd0053132`, theirs `3f91cd0dda8a5fc606f1520840f3830fa858b109` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "b3f997fe050f00d031f8ff7103d279b1f33f08c5", "ours": "4a51d40d934170de8275f4e709cdf5f840eded91", "theirs": "e3dfac3eea2f350c12d5e22981e3189361214203"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/fbddea742dcfc000eb541a6dcedd0981.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. Then answer the task's open decision with `retry` (or `reverify` when the same snapshot only needs to be integrated again).

```diff3
import "server-only";

<<<<<<< ours (src/lib/cuentas/cuenta-actual.ts)
import { cookies } from "next/headers";
import { SESSION_COOKIE } from "@/lib/auth/session";
||||||| base
import { cookies, headers } from "next/headers";
import { SESSION_COOKIE } from "@/lib/auth/session";
=======
import { headers } from "next/headers";
>>>>>>> theirs
import { createAccountPool } from "./pool";
import { createAccountService, type OwnAccountRecord } from "./servicio";
import { resolveServerSession } from "./sesion-servidor";
import { CUENTA_ADMINISTRADOR_LOCAL_ID } from "./modo-local";
import { VERSION_AVISO_DATOS } from "./aviso-datos";

let accounts: ReturnType<typeof createAccountService> | undefined;

function accountService() {
  accounts ??= createAccountService(createAccountPool(), process.env.DATA_NOTICE_VERSION ?? "v1");
  return accounts;
}

export async function getCurrentAccount(): Promise<(OwnAccountRecord & { permissions: readonly string[] }) | null> {
  const session = await resolveServerSession();
  if (!session) return null;
  if (session.accountId === CUENTA_ADMINISTRADOR_LOCAL_ID) {
    return {
      id: session.accountId,
      email: session.email,
      displayName: "Administrador local",
      roles: session.roles,
      permissions: session.permissions,
      dataNoticeVersion: VERSION_AVISO_DATOS,
      dataNoticeAcceptedAt: null,
    };
  }

  const account = await accountService().getOwnAccount(session.accountId);
  return account ? { ...account, permissions: session.permissions } : null;
}

```

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## T2.55

Workflow `bt:pictures:REQ-021:r27:T2.55:k1` (PENDING); state: `{"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}`

```
Run pictures:REQ-021:r27, task T2.55: Resolve local administrator consistently in server-rendered pages
Subplan: SP-2; depends on: T2.6
Objective: Unify server-rendered session resolution with the existing resolveRequestSession/local administrator path. Evidence at snapshot 6c7ef4a2: API guard honours sesionAdministradorLocal(request), but app/page.tsx reads SESSION_COOKIE/resolverSesion directly and login/page.tsx never redirects an existing session. Inventory every server-rendered page/layout/server component using cookies() for session identity; introduce/reuse one server-only request-context resolver using the same local-mode policy and ordinary cookie resolution as the guard, and migrate those session readers. Do not change unrelated cookie uses (language/theme/consent), permissions or roles. With AUTH_LOCAL_SIN_RESTRICCIONES=1, next dev and a genuine loopback request, / renders the signed-in tool home and /login redirects there; /3d and /admin/cuentas agree on the same local administrator. Without this local session, preserve normal sign-in and existing authorization. Never enable local access in production builds, next start or non-loopback requests; do not trust spoofed Host/Forwarded/X-Forwarded-* as proof of locality, and retain existing local-mode security boundaries. Author/register cuentas:test-sesion-local-paginas with real dev entrypoints, no-cookie mode-on and mode-off cases, ordinary valid/invalid cookie cases, /login redirect without loops, production refusal and non-loopback/forged-forwarding refusal; no paid calls. Record inventory and actual statuses without secrets. The follow-up starts after the existing account integration checkpoint, and downstream verification and audit must consume it. Operator addendum: include all server-rendered navigation/session consumers, specifically header account menu, Administración entry and home tool permissions. Use the shared resolver for both visibility and destination authorization; the local administrator must reach /admin/cuentas by clicking through the UI from home. Do not merely expose a link or hard-code local visibility while retaining cookie-only session resolution. Mode-off signed-out navigation and normal non-admin role menus must remain unchanged.
Acceptance criteria:
- In next dev on genuine loopback with AUTH_LOCAL_SIN_RESTRICCIONES=1 and no cookie, home, login redirect, layouts and protected server pages resolve the same local administrator as the API guard; with mode off, invalid cookies, production or non-loopback/forged-forwarding requests, normal login and permission checks remain enforced without redirect loops. Server-rendered header/account navigation, the Administración entry and home tools use that same resolved session: the local administrator can click from home through the account menu to accounts administration without typing a URL, while mode-off signed-out users see no administrator links and ordinary signed-in roles see only permitted navigation.
Checks:
- npm run cuentas:test-sesion-local-paginas (integration; requires PICTURES_REQ021_DATABASE_URL)
Decision T2.55:d2 (round k1): still not proven after re-verification: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14); limit -
Failure: integration INTEGRATION_CONFLICT: conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
Offered options in this runtime:
- reverify: verify the same snapshot again (only after its manual checks were attested)
- retry: a new attempt of the task from its last snapshot
- retry_with_note: a new attempt with your note first in its prompt
- retry_other_route: a new attempt on another model or account
- stop: stop the task
Failure evidence:
conflicts with accepted work in: src/components/cuentas/MenuCuenta.tsx, src/components/cuentas/textos-cuenta.ts (line of SP-14)
```

Diagnosis (bt_block_agent, read-only, may be wrong):
```json
{
 "request": "pictures:REQ-021:r27:T2.55:T2.55:d2@k1",
 "state": "failed",
 "error": "la respuesta no trae JSON",
 "source": "agente · haiku",
 "model": "haiku",
 "profile": "claude",
 "at": "2026-10-30T12:07:10",
 "seconds": 88.5
}
```

Attempt history: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.notes/T2.55.history.jsonl` (none yet)

## Run status

Run workflow `bt:pictures:REQ-021:r27`: PENDING; summary status running. Full status: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.solver/20261030-120814-28ad/status.json`.

- T2.55: PENDING {"task_id": "T2.55", "state": "needs_decision", "request_id": "T2.55:d2"}

## Composition gates

Composed: `{}`; rejected: `{}`. A composition that fails is tried again on later turns of the run loop (`COMPOSE_TURNS`) before the gate counts as rejected; the owner's `retry-task` of the gate task composes it again.


## Files

- requirement: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t` (SPEC.md, PLAN.md, PLAN.json, SPEC.es.md)
- the frozen plan this run executes: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/plan-revisions/PLAN.r27.json`
- project decisions: `/home/david/bitacora/pictures/DECISIONS.md`
- metodologia decisions: `/home/david/bitacora/metodologia/DECISIONS.md`
- day log: `/home/david/bitacora/pictures/2026-10/W5/2026-10-29.md`
- day log: `/home/david/bitacora/pictures/2026-10/W5/2026-10-30.md`
- day log: `/home/david/bitacora/metodologia/2026-10/W5/2026-10-29.md`
- day log: `/home/david/bitacora/metodologia/2026-10/W5/2026-10-30.md`
- diagnoses: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.diagnoses`; healing: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.durable-healing.json`; activity: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/.planning/activity.jsonl`; telemetry and attempts: `/home/david/bitacora/.state/durable`

## Commands

- run status: `uv run --project ~/dev/metodologia bt-durable status pictures REQ-021`
- engine journal: `journalctl --user -u bt-durable.service --since -3h --no-pager -o cat`
- answer a decision: `uv run --project ~/dev/metodologia bt-durable answer pictures REQ-021 <task> <request>@k<round> <action> --note "..." --by solver`
- the run's Planner: `python3 /home/david/dev/metodologia/skill/scripts/bt_agent_terminal.py tell-planner pictures REQ-021 "<change request>"`
- integrate a metodologia fix: `python3 ~/dev/metodologia/skill/scripts/bt_integrate.py --branch solver/20261030-120814-28ad --worktree /home/david/.local/share/bitacora-solver/pictures/20261030-120814-28ad/wt --title "<what> (D-NNN)" --session 20261030-120814-28ad --trailer "<your attribution line>"` (`--dry-run` first; `--help` for the steps)

## Your session

- session folder (REPORT.md, result.json, NOTES.md, inbox.jsonl): `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.solver/20261030-120814-28ad`
- working folder (your worktree goes in `/home/david/.local/share/bitacora-solver/pictures/20261030-120814-28ad/wt`): `/home/david/.local/share/bitacora-solver/pictures/20261030-120814-28ad`
- trigger keys for result.json `handled`: pictures:REQ-021:r27:resolution:000cc420754a9d752462160c5452618a, pictures:REQ-021:r27:resolution:312b5f3cde0689853fe078d348f08bb0, pictures:REQ-021:r27:resolution:67302a71b7947706bdbcbc0d72dbc129, pictures:REQ-021:r27:resolution:6df4cea9605036b2ac01269b320741b1, pictures:REQ-021:r27:resolution:7e0709f8ac37f2164efc6081f259c5df, pictures:REQ-021:r27:resolution:8042b963196a321dcee14a10cf512e87, pictures:REQ-021:r27:resolution:87f60eeb77d9f299cfb7dd9902dd315c, pictures:REQ-021:r27:resolution:8f4d1b7928b20f9f71fe0b9e76ef136b, pictures:REQ-021:r27:resolution:9d3f9d9ac1350969fd6a4fe71204cd1c, pictures:REQ-021:r27:resolution:ba2580bb7203f67c81c4eadf632e2b62, pictures:REQ-021:r27:resolution:dd4cc8117603023fa4561e12cdbe7254, pictures:REQ-021:r27:resolution:deec9ffa25d6d1798fe3f9da9ac100df, pictures:REQ-021:r27:resolution:585d3876c7dcbf3c967460530ce058d6, pictures:REQ-021:r27:resolution:6d4aa822010fb3ca2b27ee9dbbdc64e0, pictures:REQ-021:r27:resolution:88054d9772b8651d2e5deb8410a8f05a, pictures:REQ-021:r27:resolution:f97d80d9d2fc59d46ef6cd1c461f869c, pictures:REQ-021:r27:resolution:fbddea742dcfc000eb541a6dcedd0981, pictures:REQ-021:r27:T2.55:T2.55:d2@k1
- keep NOTES.md current (what you found, what you changed, what is next): you may be restarted on another account and must be able to continue from your files.
