# Solucionador 20261101-174711-3b88 — pictures REQ-021 (run pictures:REQ-021:r39)

Started 2026-11-01T17:47:11 by the durable engine's maintenance pass.

## Triggers

- `pictures:REQ-021:r39:resolution:397579b9ac08eda823b51203c92f4397` — resolution · SP-12×SP-10: SP-12 builds on SP-10 and cannot take its current line: src/app/api/asistente-guiado/route.ts needs a recorded resolution; no retry can settle it

## Resolution request 397579b9ac08eda823b51203c92f4397 (src/app/api/asistente-guiado/route.ts)

- request: `/home/david/bitacora/.state/durable/composition/resolutions/397579b9ac08eda823b51203c92f4397.json`; diff3: `/home/david/bitacora/.state/durable/composition/resolutions/397579b9ac08eda823b51203c92f4397.diff3`
- blobs: base `437e198cf8670cef356d97b11bfa6f196fb67707`, ours `e5fc3da513b13b79298353f3cfb6c25bd62400ef`, theirs `9b485464d35fe05b91b5a7ae369a1cb513de6742` (`git cat-file -p <blob>` in the project's repository)
- commits: {"base": "a48cda8905287a7bfc743a6835fdd89b296310b9", "ours": "03c954ab5fc801df1d7f794d2efd8a97ee2634da", "theirs": "5b3ac6faadff38c761d51c67d22b1f02d3b63464"}
- write the final content to: `/home/david/bitacora/.state/durable/composition/resolutions/397579b9ac08eda823b51203c92f4397.resolved`
- the final content keeps BOTH sides' intent: never drop either side's change; when they truly exclude each other, ask the owner. This is the reconciliation of a subplan's line with a subplan it builds on (D-297): no task or decision waits for it. Do not move any ref and do not commit to the project: once every file of the round has its `.resolved` the engine's next pass combines them and moves the lines itself, or opens the next round. The resolved file must still fit the rest of the merged tree (imports and names from both sides).

```diff3
import { ejecutarConversacionStream } from "@sempertex/agente-core";
import type { Herramienta, Mensaje } from "@sempertex/agente-core";
import { NextResponse } from "next/server";
import { z } from "zod";
import { bibliotecaVisible, coloresTipicosDe, esPersonaje, normalizarBusqueda, paletasSugeridasDe, proveedoresVisibles, tematicasDisponibles } from "@/lib/biblioteca-sempertex/biblioteca";
import { detectarCambioTematica } from "@/lib/ia/guiado/cambio-tematica";
import { diferenciaOpciones, sanearOpcionesCatalogo } from "@/lib/ia/guiado/opciones-catalogo";
import { eventoDeMensajes, generosBabyShower, ideasGuiadas, ideasRealesDeOpcion, ideasYaVistas, NOMBRE_GENERO, tematicaFielAlCliente } from "@/lib/ia/guiado/ideas-guiadas";
import { esPedidoParecidasAFoto, ideasParecidasAFoto, ordenarIdeasPorPieza, pedidoDeIdeas } from "@/lib/ia/guiado/pedido-ideas";
import { CHIP_FOTO_GUIADA, FiltroFlujoGuiado, FRASE_IDEAS_GUIADAS, fraseCercanasYaDicha, sanearRespuestaGuiada, type CercanasPorColor, type ContextoRespuesta } from "@/lib/ia/guiado/respuesta-guiada";
import { AsistenteGuiadoRequestSchema, PropuestaComposicionSchema } from "@/lib/ia/contracts/asistente-guiado-v1";
import { chatOmoikaneDe, resolverProveedor } from "@/lib/ia/nucleo/registro";
import { construirPromptGuiado } from "@/lib/ia/guiado/prompt-guiado";
import { ChatSseEventV1Schema, CHAT_SSE_CONTRACT_VERSION } from "@/lib/ia/contracts/chat-v1";
import { avisoEdicionDelPlanAbierto } from "@/lib/ia/guiado/aviso-edicion-plan";
import { registrarAuditoriaPlan3d } from "@/lib/guiada-motor/auditoria-plan";
import { costearIdeaElegida, type EntornoCosteoIdea } from "@/lib/guiada-motor/costear-idea-elegida";
import { devolverCosteoIdeaDurable, tomarCosteoIdeaDurable } from "@/lib/guiada-motor/tope-costeo-idea";
import { responderAccionIdea, respuestaCosteoBloqueado } from "@/lib/ia/guiado/accion-idea";
import { datosDelCosteo, dependenciasDeCosteo } from "@/lib/guiada-motor/dependencias-costeo";
import { ErrorIA } from "@/lib/ia/nucleo/tipos";
import type { ErrorCodeV1 } from "@/lib/ia/contracts/chat-v1";
import { normalizarCiudad, protegerHerramientas } from "@/lib/ia/guiado/utilidades";
import { pasosParaCliente } from "@/lib/ia/guiado/pasos-cliente";
import { ESTRUCTURAS_OFICIALES, ESTRUCTURAS_OFICIALES_IDS, type EstructuraOficialId } from "@/lib/plan/estructuras-oficiales";
import { COLORES_PROPUESTA_V2 } from "@/lib/rag/taxonomy/v2";
import { coloresConTonosDelCliente } from "@/lib/plan/tonos-color";
import { normalizarPropuestaComposicion } from "@/lib/ia/guiado/propuesta-composicion";
import { recortarCantidades } from "@/lib/plan/piezas-individuales";
import { esquemaHerramientaPropuesta, type AlcancePropuesta } from "@/lib/ia/guiado/esquema-herramienta-propuesta";
import { textoPlanActual } from "@/lib/ia/guiado/instruccion-plan";
import { briefConHechos, etiquetaEdadCliente, hechosDelCliente, pedidoCompletoDePieza, piezaOrganicaDelBoton, propuestaConLoPedido, textoHechosCliente, usoDeTexto } from "@/lib/ia/guiado/hechos-cliente";
import type { BriefGuiado } from "@/lib/ia/contracts/asistente-guiado-v1";
import { conRegistro, contextoActual, decidir, envolverRegistroHerramientas } from "@/lib/registro";
import { crearDeadlineIA } from "@/lib/ia/plazo-servidor";
import { responderConsultaIdea } from "@/lib/ia/guiado/consulta-plan-chat";
import { detectarEleccionIdea, detectarPedidoEdicion, fraseDelPedido, HERRAMIENTA_ELEGIR_IDEA, HERRAMIENTAS_EDICION, herramientasConEdicion, ideaDesdeHerramienta, pedidoDesdeHerramienta, textoIdeasParaModelo, textoPiezasParaModelo, type DeteccionEdicion, type HerramientaEdicion } from "@/lib/ia/guiado/edicion-plan-chat";
import { requireApiPermission, resolveRequestSession, withApiPermission } from "@/lib/cuentas/guardia";
import { PERMISOS } from "@/lib/cuentas/permisos";
import { getRequestLanguage } from "@/lib/idioma/servidor";
import { mensajeAsistenteGuiado } from "@/lib/idioma/mensajes-ia";
import { getRagPool } from "@/lib/rag/db";
import { construirContenidoVisible } from "@/lib/ia/guiado/contenido-visible";
import { DecoracionSempertexSchema } from "@/lib/biblioteca-sempertex/esquemas";
import { accionIdeaRequierePermisoCostos, herramientasSegunPermiso, protegerRespuestaSinPrecios, reglaPreciosSegunPermiso, respuestaSinPreciosGuiado, textoEnStreamGuiado } from "@/lib/ia/guiado/politica-precios-guiado";
import { briefDeRecomendacionListo } from "@/lib/recomendaciones-3d/recomendar";
import { ProtectorStreamRecomendaciones } from "@/lib/recomendaciones-3d/proteger-stream";
import { ejecutarHerramientaRecomendaciones3d, HERRAMIENTA_RECOMENDACIONES_3D } from "@/lib/recomendaciones-3d/herramienta-guiada";


export const maxDuration = 75;

/** Tiempo máximo de un turno guiado: pasado esto el cliente recibe un error reintentable en vez de quedarse esperando. */
const DEADLINE_TURNO_MS = 60_000;
const ACCIONES_PLAN = ["ver", "costear", "comprar", "aprender", "contratar"] as const;

const herramientas: Herramienta[] = [
  { nombre: "guardar_brief_guiado", descripcion: "Guarda el evento y la temática que el cliente ya indicó; la edad solo si es un cumpleaños.", esquema: { type: "object", properties: { evento: { type: "string" }, edad: { type: "integer" }, tematica: { type: "string" } }, required: ["evento", "tematica"], additionalProperties: false } },
  { nombre: "buscar_decoraciones_sempertex", descripcion: "Busca ideas de decoración según evento y temática (y la edad solo en un cumpleaños).", esquema: { type: "object", properties: { evento: { type: "string" }, edad: { type: "integer" }, tematica: { type: "string" } }, required: ["evento", "tematica"], additionalProperties: false } },
  HERRAMIENTA_RECOMENDACIONES_3D,
  { nombre: "proponer_composicion", descripcion: "Propone entre una y tres estructuras oficiales para esta celebración. Usa exclusivamente ids oficiales y colores de la paleta Sempertex permitida. Llama cuando el cliente pida que le propongas algo, o un cambio de su plan que no cabe en las herramientas de edición (otra temática, varias piezas distintas a la vez, más sencillo). Sumar UNA pieza al plan no es esto: es agregar_pieza_plan.", esquema: { type: "object", properties: { frase: { type: "string" }, colores: { type: "array", description: "Usa el tono que dijo el cliente si es uno de los claros (celeste, rosa pastel, durazno), no su familia.", items: { type: "string", enum: [...COLORES_PROPUESTA_V2] }, minItems: 1, maxItems: 5 }, piezas: { type: "array", items: { type: "object", properties: { estructura: { type: "string", enum: [...ESTRUCTURAS_OFICIALES_IDS] }, cantidad: { type: "integer", minimum: 1, maximum: 12 } }, required: ["estructura", "cantidad"], additionalProperties: false }, minItems: 1, maxItems: 3 } }, required: ["frase", "colores", "piezas"], additionalProperties: false } },
  { nombre: "ofrecer_opciones", descripcion: "Ofrece las cuatro opciones para continuar con una decoración elegida.", esquema: { type: "object", properties: {}, additionalProperties: false } },
  { nombre: "preguntar_uso", descripcion: "Solicita elegir entre negocio y uso personal antes de consultar precios.", esquema: { type: "object", properties: {}, additionalProperties: false } },
  { nombre: "pasos_decoracion", descripcion: "Muestra los pasos de montaje de la decoración que el cliente eligió en la interfaz. No necesita argumentos.", esquema: { type: "object", properties: {}, additionalProperties: false } },
  { nombre: "buscar_proveedores", descripcion: "Busca decoradores, distribuidores o tiendas en la ciudad que el cliente escribió. Si el cliente todavía no dijo su ciudad, pregúntala antes de llamar.", esquema: { type: "object", properties: { tipo: { type: "string", enum: ["decorador_happia", "mbp", "distribuidor", "ecommerce"] }, ciudad: { type: "string" } }, required: ["tipo", "ciudad"], additionalProperties: false } },
  { nombre: "costear_decoracion", descripcion: "Cotiza los materiales de la decoración que el cliente eligió en la interfaz, con el uso que eligió (negocio o personal). No necesita argumentos: el servidor usa lo que el cliente confirmó.", esquema: { type: "object", properties: {}, additionalProperties: false } },
];

/** Solo existe cuando el cliente tiene un plan a medida a la vista. */
const herramientaAccionPlan: Herramienta = {
  nombre: "abrir_accion_plan",
  descripcion: "Abre una acción sobre el plan vigente del cliente cuando la pide con palabras: ver (cómo quedaría, imagen), costear (precio de los materiales), comprar, aprender (cómo armarlo) o contratar (un decorador).",
  esquema: { type: "object", properties: { accion: { type: "string", enum: [...ACCIONES_PLAN] } }, required: ["accion"], additionalProperties: false },
};

/** Herramientas que solo tienen sentido con una idea del catálogo elegida en la interfaz. */
const HERRAMIENTAS_DE_DECORACION: ReadonlySet<string> = new Set(["costear_decoracion", "preguntar_uso", "pasos_decoracion", "ofrecer_opciones"]);

/** «Elegante negro y dorado (Cumpleaños, Graduación)» por cada temática con al menos una decoración visible. */
function textoTematicasCatalogo(): string {
  const eventosPorTematica = new Map<string, Set<string>>();
  for (const decoracion of bibliotecaVisible()) {
    const eventos = eventosPorTematica.get(decoracion.tematica) ?? new Set<string>();
    decoracion.eventos.forEach((evento) => eventos.add(evento));
    eventosPorTematica.set(decoracion.tematica, eventos);
  }
  return [...eventosPorTematica].map(([tematica, eventos]) => `${tematica} (${[...eventos].join(", ")})`).join(" | ");
}

const ArgsSchema = z.object({ evento: z.string().optional(), edad: z.number().int().optional(), tematica: z.string().optional(), decoracionId: z.string().optional(), tipo: z.enum(["decorador_happia", "mbp", "distribuidor", "ecommerce"]).optional(), ciudad: z.string().optional(), uso: z.enum(["negocio", "personal"]).optional() }).strict();
const BriefCompletoSchema = z.object({ evento: z.string().min(1).max(120), edad: z.number().int().min(0).max(120), tematica: z.string().min(1).max(160) }).strict();
type BriefCompleto = z.infer<typeof BriefCompletoSchema>;

/** Botones de pieza individual del cliente anterior → id oficial (compatibilidad mientras no mande `piezaPedida`). */
const PIEZA_POR_BOTON: Readonly<Record<string, EstructuraOficialId>> = { "arco orgánico": "arco", columna: "columna", guirnalda: "guirnalda", semiarco: "semiarco", bouquet: "bouquet" };

function piezaDeTextoBoton(texto: string): EstructuraOficialId | undefined {
  const coincidencia = /^Propónme una pieza individual:\s*(.+?)\.?$/.exec(texto.trim());
  const nombre = coincidencia?.[1]?.trim().toLocaleLowerCase("es");
  if (!nombre) return undefined;
  return PIEZA_POR_BOTON[nombre] ?? ESTRUCTURAS_OFICIALES_IDS.find((id) => ESTRUCTURAS_OFICIALES[id].nombre.toLocaleLowerCase("es") === nombre);
}

/** Alcance de la propuesta: el que manda el cliente, o (compatibilidad) solo los textos EXACTOS de sus botones. */
function alcanceDelTurno(declarado: AlcancePropuesta | undefined, ultimoUsuario: string, piezaPedida: EstructuraOficialId | undefined): AlcancePropuesta | null {
  if (declarado) return declarado;
  if (/^Propónme algo para una decoración completa/.test(ultimoUsuario)) return "completa";
  if (/^Propónme una pieza individual:/.test(ultimoUsuario) || piezaPedida) return "individual";
  return null;
}

function envelopeHttp(requestId: string, code: ErrorCodeV1, message: string, retryable: boolean) {
  return { schema_version: "error.v1", code, message, retryable, request_id: requestId, error: message };
}

function falloProveedor(error: unknown, idioma: "es" | "en"): { code: ErrorCodeV1; message: string; status: number; retryable: boolean } {
  if (!(error instanceof ErrorIA)) return { code: "INTERNAL_ERROR", message: mensajeAsistenteGuiado("startFailed", idioma), status: 503, retryable: true };
  if (error.causa === "sin_llave") return { code: "AI_KEY_MISSING", message: mensajeAsistenteGuiado("providerMissing", idioma), status: 503, retryable: false };
  if (error.causa === "cuota") return { code: "AI_QUOTA", message: mensajeAsistenteGuiado("providerQuota", idioma), status: 429, retryable: true };
  if (error.causa === "timeout") return { code: "AI_TIMEOUT", message: mensajeAsistenteGuiado("providerTimeout", idioma), status: 504, retryable: true };
  if (error.causa === "filtrado") return { code: "AI_FILTERED", message: mensajeAsistenteGuiado("providerFiltered", idioma), status: 422, retryable: false };
  if (error.causa === "red") return { code: "AI_NETWORK", message: mensajeAsistenteGuiado("providerUnavailable", idioma), status: 502, retryable: true };
  return { code: "AI_PROVIDER", message: mensajeAsistenteGuiado("startFailed", idioma), status: 502, retryable: true };
}

/** Un turno resuelto por reglas: el mismo SSE (texto y fin) que el del modelo, sin llamarlo. */
function respuestaSinModelo(requestId: string, headers: Record<string, string>, reply: string, result: Record<string, unknown>): Response {
  const eventos = [
    { type: "texto", delta: reply },
    { type: "fin", reply, brief: {}, proveedor: "reglas", modelo: "reglas", result },
  ].map((campos) => {
    const evento = { schema_version: CHAT_SSE_CONTRACT_VERSION, request_id: requestId, correlation_id: requestId, ...campos };
    if (!ChatSseEventV1Schema.safeParse(evento).success) throw new Error("EVENTO_GUIADO_INVALIDO");
    return `event: ${campos.type}\ndata: ${JSON.stringify(evento)}\n\n`;
  });
  return new Response(eventos.join(""), { headers: { ...headers, "Content-Type": "text/event-stream; charset=utf-8", "Cache-Control": "no-cache, no-transform", Connection: "keep-alive" } });
}

/** El request_id del turno es el de la petición registrada (x-request-id), si es un UUID: así el SSE, la telemetría, el Python y la auditoría hablan del mismo id. */
function requestIdDelTurno(): string {
  const solicitud = contextoActual()?.solicitud;
  return solicitud && z.string().uuid().safeParse(solicitud).success ? solicitud : crypto.randomUUID();
}

// Auditado (src/lib/registro): entrada, cada llamada al modelo, cada herramienta, las decisiones de abajo y el SSE de salida.
export const POST = withApiPermission(PERMISOS.chat_asistido, conRegistro("/api/asistente-guiado", turnoGuiado, { vista: "guiada" }));

async function turnoGuiado(request: Request) {
  const permissionError = await requireApiPermission(request, PERMISOS.chat_asistido);
  if (permissionError) return permissionError;
  const session = await resolveRequestSession(request);
  if (!session) return Response.json({ code: "SESION_REQUERIDA" }, { status: 401 });
  const puedeCostear = session.permissions.includes(PERMISOS.calculadora_costos);
  const idioma = await getRequestLanguage();
  const requestId = requestIdDelTurno();
  const headers = { "X-Request-ID": requestId };
  const length = Number(request.headers.get("content-length"));
  if (Number.isFinite(length) && length > 25_000_000) {
    const message = mensajeAsistenteGuiado("payloadTooLarge", idioma);
    return Response.json(envelopeHttp(requestId, "PAYLOAD_TOO_LARGE", message, false), { status: 413, headers });
  }
  let body: unknown;
  try { body = await request.json(); } catch {
    const message = mensajeAsistenteGuiado("invalidJson", idioma);
    return NextResponse.json(envelopeHttp(requestId, "INVALID_JSON", message, false), { status: 400, headers });
  }
  const parsed = AsistenteGuiadoRequestSchema.safeParse(body);
  if (!parsed.success) {
    const message = mensajeAsistenteGuiado("invalidInput", idioma);
    return NextResponse.json(envelopeHttp(requestId, "INVALID_INPUT", message, false), { status: 400, headers });
  }
  const { messages } = parsed.data;
  const estado = parsed.data.estadoGuiado;
  const ultimoUsuario = [...messages].reverse().find((mensaje) => mensaje.role === "user")?.content.trim() ?? "";
  const planActual = estado?.planActual;
  const alcanceDeBoton = alcanceDelTurno(estado?.alcancePropuesta, ultimoUsuario, estado?.piezaPedida ?? piezaDeTextoBoton(ultimoUsuario));
  // Un pedido completo de UNA pieza («un arco orgánico de unos 3 metros en blanco y dorado para una boda») va directo a
  // su propuesta, como si hubiera tocado «Propónme algo» con esa pieza (probador 141, I-6: antes recibía 4 ideas de la
  // biblioteca que no eran arcos orgánicos). Solo sin plan, sin idea elegida, sin foto y sin otro alcance ya decidido.
  const pedidoDirecto = !alcanceDeBoton && !planActual && !estado?.decoracionId && !parsed.data.fotoInspiracion ? pedidoCompletoDePieza(ultimoUsuario) : null;
  const piezaBoton = estado?.piezaPedida ?? piezaDeTextoBoton(ultimoUsuario) ?? pedidoDirecto?.estructura.id;
  const alcancePropuesta = alcanceDeBoton ?? (pedidoDirecto ? "individual" : null);
  // Una pieza pedida solo restringe la pieza individual: en la decoración completa se ignora.
  const piezaPedida = alcancePropuesta === "individual" ? piezaBoton : undefined;
  decidir("regla:alcance_turno_guiado", "alcance de la propuesta y pieza pedida", { alcancePropuesta, piezaPedida: piezaPedida ?? null, pedidoDirecto: pedidoDirecto ? { pieza: pedidoDirecto.estructura.texto, medida: pedidoDirecto.medida.texto } : null }, {
    entrada: { alcanceDeclarado: estado?.alcancePropuesta ?? null, piezaDeclarada: estado?.piezaPedida ?? null, piezaBoton: piezaBoton ?? null, ultimoUsuario },
    motivo: estado?.alcancePropuesta ? "lo declaró la interfaz" : alcanceDeBoton ? "texto exacto de un botón" : pedidoDirecto ? "el cliente pidió una pieza con su medida: va directo a su propuesta (sin ideas de la biblioteca)" : "turno libre (sin alcance)",
  });
  // Lo que el cliente ya dijo, leído sin modelo (hechos-cliente.ts): evento, uso, medida, pieza, lugar, momento y
  // presupuesto. Usabilidad 97: «Soy decorador… arco orgánico de unos 3 metros… para una boda… cotizarle» perdía todo
  // menos los colores, y el uso se preguntaba otra vez aunque ya lo hubiera dicho o elegido.
  const mensajesDelCliente = messages.filter((mensaje) => mensaje.role === "user").map((mensaje) => mensaje.content);
  // El botón «Arco orgánico» (pieza individual) es el arco completo con mezcla de tamaños, como el texto «arco orgánico»:
  // su etiqueta se lee igual (`piezaOrganicaDelBoton`) y va al brief, de donde la vista saca las piezas orgánicas del plan.
  const organicaDelBoton = piezaOrganicaDelBoton(ultimoUsuario, piezaPedida);
  const hechosLeidos = hechosDelCliente(mensajesDelCliente);
  const hechos = organicaDelBoton ? { ...hechosLeidos, estructura: organicaDelBoton } : hechosLeidos;
  if (organicaDelBoton) decidir("regla:pieza_organica_boton", "el botón «Arco orgánico» es el arco completo con mezcla de tamaños (como el texto «arco orgánico»)", organicaDelBoton, { entrada: { piezaPedida: piezaPedida ?? null, ultimoUsuario } });
  // El uso: lo que dice el último mensaje («es para mi negocio»), lo que ya eligió (botones) o lo que dijo antes.
  const usoDelTurno = usoDeTexto(ultimoUsuario);
  const usoConfirmado = usoDelTurno ?? estado?.uso ?? hechos.uso;
  if (usoConfirmado && usoConfirmado !== estado?.uso) {
    decidir("regla:uso_del_cliente", "uso (negocio o personal) que el cliente ya dijo con sus palabras: no se vuelve a preguntar", usoConfirmado, {
      entrada: { usoInterfaz: estado?.uso ?? null, usoUltimoMensaje: usoDelTurno, usoConversacion: hechos.uso ?? null, ultimoUsuario },
      motivo: usoDelTurno ? "lo dice el último mensaje" : "lo dijo antes en la conversación",
    });
  }
  if (Object.keys(hechos).length) decidir("regla:hechos_cliente", "lo que el cliente ya dijo, leído sin modelo (evento, uso, medida, pieza, lugar, momento, presupuesto)", hechos, { entrada: { mensajesCliente: mensajesDelCliente.length, ultimoUsuario } });
  const decoracionConfirmada = estado?.decoracionId;
  const proveedores = bibliotecaVisible();
  const directorio = proveedoresVisibles();
  // Editar el plan vigente y elegir una idea POR CHAT, sin rehacer nada (edicion-plan-chat.ts; probador 104: «el azul
  // cám
```

## Run status

Run workflow `bt:pictures:REQ-021:r39`: PENDING; summary status running. Full status: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.solver/20261101-174711-3b88/status.json`.

- T10.5: PENDING {"task_id": "T10.5", "state": "needs_decision", "request_id": "T10.5:d1"}
- T99: PENDING {"task_id": "T99", "state": "running", "attempt": "pictures-REQ-021-r39-T99-a1-b0de0020"}

## Composition gates

Composed: `{"CG-9": "C1"}`; rejected: `{}`. A composition that fails is tried again on later turns of the run loop (`COMPOSE_TURNS`) before the gate counts as rejected; the owner's `retry-task` of the gate task composes it again.

Last gate and line events (telemetry):
- subplan_line_conflict: {}
- subplan_line_conflict: {}
- gate_stale: {"gate": "CG-9", "previous": "", "members": ["SP-2", "SP-14", "SP-3", "SP-4", "SP-5", "SP-6", "SP-7", "SP-8", "SP-9"]}
- gate_composed: {"gate": "CG-9", "state": "rejected", "reason": "RECONCILE_PENDING: SP-5, SP-6, SP-7, SP-8, SP-9"}
- gate_recompose: {"gate": "CG-9", "previous": "RECONCILE_PENDING: SP-5, SP-6, SP-7, SP-8, SP-9"}
- gate_stale: {"gate": "CG-9", "previous": "", "members": ["SP-2", "SP-14", "SP-3", "SP-4", "SP-5", "SP-6", "SP-7", "SP-8", "SP-9"]}
- gate_composed: {"gate": "CG-9", "state": "candidate", "candidate_id": "C1", "reason": "", "members": {"SP-1": 1, "SP-14": 1, "SP-2": 1, "SP-3": 1, "SP-4": 1, "SP-5": 1, "SP-6": 1, "SP-7": 1, "SP-8": 1, "SP-9": 1}}

## Files

- requirement: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t` (SPEC.md, PLAN.md, PLAN.json, SPEC.es.md)
- the frozen plan this run executes: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/plan-revisions/PLAN.r39.json`
- project decisions: `/home/david/bitacora/pictures/DECISIONS.md`
- metodologia decisions: `/home/david/bitacora/metodologia/DECISIONS.md`
- day log: `/home/david/bitacora/pictures/2026-10/W5/2026-10-31.md`
- day log: `/home/david/bitacora/pictures/2026-11/W1/2026-11-01.md`
- day log: `/home/david/bitacora/metodologia/2026-10/W5/2026-10-31.md`
- day log: `/home/david/bitacora/metodologia/2026-11/W1/2026-11-01.md`
- diagnoses: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.diagnoses`; healing: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.durable-healing.json`; activity: `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/.planning/activity.jsonl`; telemetry and attempts: `/home/david/bitacora/.state/durable`

## Commands

- run status: `uv run --project ~/dev/metodologia bt-durable status pictures REQ-021`
- engine journal: `journalctl --user -u bt-durable.service --since -3h --no-pager -o cat`
- answer a decision: `uv run --project ~/dev/metodologia bt-durable answer pictures REQ-021 <task> <request>@k<round> <action> --note "..." --by solver`
- the run's Planner: `python3 /home/david/dev/metodologia/skill/scripts/bt_agent_terminal.py tell-planner pictures REQ-021 "<change request>"` (exit 0: it has it; 3: no account has quota, it is held and sent again on its own when the quota returns; 1: not delivered)
- integrate a metodologia fix: `python3 ~/dev/metodologia/skill/scripts/bt_integrate.py --branch solver/20261101-174711-3b88 --worktree /home/david/.local/share/bitacora-solver/pictures/20261101-174711-3b88/wt --title "<what> (D-NNN)" --session 20261101-174711-3b88 --trailer "<your attribution line>"` (`--dry-run` first; `--help` for the steps)

## Your session

- session folder (REPORT.md, result.json, NOTES.md, inbox.jsonl): `/home/david/bitacora/pictures/requirements/REQ-021-pilot-release-bilingual-ui-rectangular-t/RUN.solver/20261101-174711-3b88`
- working folder (your worktree goes in `/home/david/.local/share/bitacora-solver/pictures/20261101-174711-3b88/wt`): `/home/david/.local/share/bitacora-solver/pictures/20261101-174711-3b88`
- trigger keys for result.json `handled`: pictures:REQ-021:r39:resolution:397579b9ac08eda823b51203c92f4397
- keep NOTES.md current (what you found, what you changed, what is next): you may be restarted on another account and must be able to continue from your files.
