import { clasificarColores, clasificarTonos, TONOS_V2, type TonoClaroV2 } from "@/lib/rag/taxonomy/v2";
import { motivosNombrados, normalizarBusqueda, sinMotivosAjenos, tituloComparable, type CoincidenciaDecoracion } from "./biblioteca";
import { claveDeCategoria, decoracionEsDeCategoria, formasDeCategoria, vocabularioDeCategorias } from "./categorias";
import type { DecoracionSempertex } from "./esquemas";
import { ALIAS_COLORES, ALIAS_TONOS, analizarPolaridad, formasLexicasEstrictas, PALABRAS_GENERO, PALABRAS_RELLENO, separarFrasesLexicas } from "./preferencias-texto";

/**
 * Recomendación ESTRICTA por categoría (REQ-018, SPEC «Matching and decision contract» 1-5). Función pura: recibe los
 * registros visibles y devuelve solo coincidencias reales, en el orden de la fuente, sin mínimo ni relleno. No usa la
 * búsqueda legacy (`buscarDecoracionesSempertex`), que completa con ideas cercanas.
 */

export const TOPE_RECOMENDACIONES = 6;

export type PreferenciasCategoria = {
  /** Estilo o temática pedidos: cada uno debe estar evidenciado en el título o la temática de la idea. */
  estilos: string[];
  /** Colores de la paleta pedidos (cada uno debe estar presente). */
  colores: string[];
  /** Tonos claros pedidos («celeste»): el tono debe estar presente, no basta su familia. */
  tonos: TonoClaroV2[];
  /** Términos excluidos de forma literal (colores, tonos o palabras). Nunca cuentan como petición positiva. */
  excluir: string[];
  /** El cliente limitó los colores («solo blanco y dorado»): la idea no puede traer otros. */
  soloColores: boolean;
};

export type ConsultaCategoria = {
  categoria: string;
  /** 0 o ausente = edad desconocida: nunca filtra. */
  edad?: number;
  /** Temática guardada: sus palabras que no son color ni categoría son estilos pedidos. */
  tematica?: string;
  /** Último mensaje del cliente: aporta colores, tonos, motivos reconocidos y negativas, no palabras sueltas. */
  mensaje?: string;
  /** Filtro adicional entre los candidatos de la categoría (p. ej. el género del baby shower). */
  admite?: (decoracion: DecoracionSempertex) => boolean;
};

export type EstadoRecomendacion = "coincidencias" | "vacio" | "categoria_desconocida" | "categoria_ambigua";
export type ResultadoCategoria = { estado: EstadoRecomendacion; ideas: CoincidenciaDecoracion[] };

const escapar = (texto: string): string => texto.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const CUE_SOLO = /(?:^| )(?:solo|solamente|unicamente|exclusivamente)(?= |$)/;
/** Palabras que anuncian un estilo o temática explícitos («quiero un estilo gótico», «temática de dinosaurios»). */
const ANUNCIOS_DE_ESTILO = new Set(["estilo", "estilos", "tematica", "tematicas", "tema", "temas", "motivo"]);

function quitarFormas(texto: string, formas: readonly string[]): string {
  return formas.reduce((resto, forma) => resto.replace(new RegExp(`(?<=^| )${escapar(forma)}(?= |$)`, "g"), " "), ` ${texto} `).replace(/\s+/g, " ").trim();
}

function coloresDeTexto(texto: string): { colores: string[]; tonos: TonoClaroV2[] } {
  return { tonos: clasificarTonos(texto).values, colores: clasificarColores(quitarFormas(normalizarBusqueda(texto), ALIAS_TONOS)).values };
}

/**
 * Estilos que el cliente anuncia con «estilo», «temática», «tema» o «motivo»: las palabras que siguen, hasta el primer
 * relleno conversacional («gótico» en «quiero un estilo gótico para mi hija»). No depende del vocabulario del catálogo:
 * un estilo desconocido sigue siendo una petición que ninguna idea satisface.
 */
function estilosAnunciados(positivo: string): string[] {
  const palabras = positivo.split(" ").filter(Boolean);
  const estilos: string[] = [];
  let anunciado = false;
  palabras.forEach((palabra, indice) => {
    if (ANUNCIOS_DE_ESTILO.has(palabra)) { anunciado = true; return; }
    if (!anunciado) return;
    if (PALABRAS_RELLENO.has(palabra) || PALABRAS_GENERO.has(palabra) || /^\d+$/.test(palabra)) {
      const siguiente = palabras[indice + 1];
      const enumeracion = (palabra === "y" || palabra === "e") && siguiente !== undefined && !PALABRAS_RELLENO.has(siguiente);
      if (estilos.length > 0 && !enumeracion) anunciado = false;
      return;
    }
    estilos.push(palabra);
  });
  return estilos;
}

function analizarTexto(entrada: { tematica?: string; mensaje?: string; ignorar?: readonly string[] }): { preferencias: PreferenciasCategoria; positivo: string } {
  const delTema = analizarPolaridad(entrada.tematica);
  const delMensaje = analizarPolaridad(entrada.mensaje);
  const positivo = `${delTema.positivo} ${delMensaje.positivo}`.trim();
  const { colores, tonos } = coloresDeTexto(positivo);
  const antesDeSolo = CUE_SOLO.exec(positivo);
  const tras = antesDeSolo ? positivo.slice(antesDeSolo.index + antesDeSolo[0].length) : "";
  const soloColores = Boolean(antesDeSolo) && (clasificarColores(tras).values.length > 0 || clasificarTonos(tras).values.length > 0);
  const sinColores = quitarFormas(delTema.positivo, [...(entrada.ignorar ?? []), ...ALIAS_TONOS, ...ALIAS_COLORES]);
  const { frases, resto } = separarFrasesLexicas(sinColores);
  const delTemaEstilos = [...frases, ...resto.split(" ").filter((palabra) => palabra && !PALABRAS_RELLENO.has(palabra) && !PALABRAS_GENERO.has(palabra) && !/^\d+$/.test(palabra))];
  // Los motivos o personajes que el cliente nombra en su último mensaje también son petición («quiere dinosaurios»).
  const delMensajeSinFormas = quitarFormas(delMensaje.positivo, entrada.ignorar ?? []);
  const delMensajeMotivos = motivosNombrados(delMensajeSinFormas).map((motivo) => motivo.palabra);
  const delMensajeAnunciados = estilosAnunciados(quitarFormas(delMensajeSinFormas, [...ALIAS_TONOS, ...ALIAS_COLORES]));
  return {
    positivo,
    preferencias: { estilos: [...new Set([...delTemaEstilos, ...delMensajeMotivos, ...delMensajeAnunciados])], colores, tonos, excluir: [...delTema.negativos, ...delMensaje.negativos], soloColores },
  };
}

/**
 * Preferencias explícitas de un texto. Conservador (SPEC A2): solo colores y tonos de los clasificadores existentes, el
 * estilo de la temática guardada y las negativas literales; no se infiere ningún color típico ni ninguna preferencia.
 */
export function preferenciasDeTexto(entrada: { tematica?: string; mensaje?: string; ignorar?: readonly string[] }): PreferenciasCategoria {
  return analizarTexto(entrada).preferencias;
}

function textoDe(decoracion: DecoracionSempertex): string {
  return normalizarBusqueda(`${decoracion.titulo} ${decoracion.tematica}`);
}

function contiene(texto: string, forma: string): boolean {
  return ` ${texto} `.includes(` ${forma} `);
}

function tieneEvidenciaDeEstilo(texto: string, estilo: string): boolean {
  return formasLexicasEstrictas(estilo).some((forma) => contiene(texto, forma));
}

function cumpleEdad(decoracion: DecoracionSempertex, edad: number | undefined): boolean {
  if (!edad || edad <= 0 || decoracion.edad === null) return true;
  return edad >= decoracion.edad.min && edad <= decoracion.edad.max;
}

function cumplePreferencias(decoracion: DecoracionSempertex, preferencias: PreferenciasCategoria): boolean {
  const texto = textoDe(decoracion);
  // Lo que la idea dice: su «celeste» cuenta como azul para quien pide azul (la taxonomía lo agrupa), pero no al revés.
  const suyos = { colores: new Set<string>(clasificarColores(texto).values), tonos: new Set<string>(clasificarTonos(texto).values) };
  if (!preferencias.colores.every((color) => suyos.colores.has(color))) return false;
  if (!preferencias.tonos.every((tono) => suyos.tonos.has(tono))) return false;
  if (preferencias.soloColores) {
    const permitidos = new Set([...preferencias.colores, ...preferencias.tonos.map((tono) => TONOS_V2[tono].familia as string)]);
    if (![...suyos.colores].every((color) => permitidos.has(color))) return false;
  }
  if (preferencias.excluir.some((termino) => {
    const pedido = coloresDeTexto(termino);
    return formasLexicasEstrictas(termino).some((forma) => contiene(texto, forma)) || pedido.colores.some((color) => suyos.colores.has(color)) || pedido.tonos.some((tono) => suyos.tonos.has(tono));
  })) return false;
  return preferencias.estilos.every((estilo) => tieneEvidenciaDeEstilo(texto, estilo));
}

/** Antes de deduplicar y topar: ID repetido y título equivalente salen una vez, en el orden de la fuente. */
function sinRepetidas(ideas: readonly DecoracionSempertex[]): DecoracionSempertex[] {
  const ids = new Set<string>();
  const titulos = new Set<string>();
  return ideas.filter((idea) => {
    const titulo = tituloComparable(idea.titulo);
    if (ids.has(idea.id) || titulos.has(titulo)) return false;
    ids.add(idea.id);
    titulos.add(titulo);
    return true;
  });
}

export function recomendarPorCategoria(catalogo: readonly DecoracionSempertex[], consulta: ConsultaCategoria): ResultadoCategoria {
  const vocabulario = vocabularioDeCategorias(catalogo);
  const clave = claveDeCategoria(consulta.categoria, vocabulario);
  if (clave === null) return { estado: "categoria_desconocida", ideas: [] };
  if (clave === "ambigua") return { estado: "categoria_ambigua", ideas: [] };
  const { preferencias, positivo } = analizarTexto({ tematica: consulta.tematica, mensaje: consulta.mensaje, ignorar: formasDeCategoria(clave, vocabulario) });
  const delEvento = catalogo.filter((decoracion) => decoracionEsDeCategoria(decoracion, clave, vocabulario));
  // Un motivo (Halloween, fútbol, una temporada) solo se ofrece si el cliente lo nombra en la categoría o lo pide (positivo).
  const sinAjenos = sinMotivosAjenos([...delEvento], { evento: consulta.categoria, tematica: positivo });
  const elegibles = sinAjenos.filter((decoracion) => cumpleEdad(decoracion, consulta.edad) && (consulta.admite?.(decoracion) ?? true) && cumplePreferencias(decoracion, preferencias));
  const ideas = sinRepetidas(elegibles).slice(0, TOPE_RECOMENDACIONES).map((decoracion): CoincidenciaDecoracion => ({ ...decoracion, coincidencia: "exacta" }));
  return { estado: ideas.length ? "coincidencias" : "vacio", ideas };
}
