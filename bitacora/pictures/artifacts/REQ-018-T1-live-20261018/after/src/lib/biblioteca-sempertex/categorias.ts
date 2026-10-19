import { normalizarBusqueda } from "./biblioteca";
import type { DecoracionSempertex } from "./esquemas";

/**
 * Categoría = celebración o evento de una decoración (`eventos`). Equivalencia ESTRICTA: solo nombres de una misma
 * celebración. No son los grupos de afinidad de la búsqueda legacy (`sinonimosEvento`), que acercan bautizo con primera
 * comunión o cualquier evento con «fiesta infantil». Las etiquetas que no están aquí se descubren de los registros
 * visibles y valen por sí mismas: una celebración nueva en la biblioteca no necesita editar esta tabla.
 */
const CELEBRACIONES: ReadonlyArray<readonly [string, readonly string[]]> = [
  ["boda", ["boda", "bodas", "matrimonio", "casamiento"]],
  ["cumpleanos", ["cumpleanos", "cumple"]],
  ["baby shower", ["baby shower", "babyshower", "bienvenida de bebe"]],
  ["xv", ["xv", "xv anos", "quince", "quince anos", "quinceanos", "quinceanera", "15 anos"]],
  ["bautizo", ["bautizo", "bautismo"]],
  ["comunion", ["comunion", "primera comunion"]],
  ["san valentin", ["san valentin", "dia de los enamorados", "enamorados"]],
  ["navidad", ["navidad", "navideno", "navidena", "novena", "novena navidena", "nochebuena"]],
  ["dia de la madre", ["dia de la madre", "dia de las madres", "dia de la mama", "dia de mama"]],
  ["halloween", ["halloween", "noche de brujas"]],
  ["graduacion", ["graduacion", "grado"]],
];

export type VocabularioCategorias = ReadonlyArray<{ forma: string; clave: string }>;
export type ClaveCategoria = string;

/** Formas (normalizadas) y su clave: la tabla de alias más las etiquetas de evento de los registros dados. */
export function vocabularioDeCategorias(catalogo: readonly DecoracionSempertex[]): VocabularioCategorias {
  const formas = new Map<string, string>();
  for (const [clave, alias] of CELEBRACIONES) for (const forma of alias) formas.set(forma, clave);
  for (const decoracion of catalogo) {
    for (const evento of decoracion.eventos) {
      const forma = normalizarBusqueda(evento);
      if (forma && !formas.has(forma)) formas.set(forma, forma);
    }
  }
  return [...formas].map(([forma, clave]) => ({ forma, clave })).sort((a, b) => b.forma.length - a.forma.length);
}

function contiene(texto: string, forma: string): number {
  return ` ${texto} `.indexOf(` ${forma} `);
}

/**
 * Clave de la categoría que nombra el texto: la etiqueta más larga manda y los tramos ya usados no se reutilizan.
 * `null` si no nombra ninguna celebración conocida; `"ambigua"` si nombra varias distintas (no se adivina una).
 */
export function claveDeCategoria(texto: string, vocabulario: VocabularioCategorias): ClaveCategoria | "ambigua" | null {
  let resto = ` ${normalizarBusqueda(texto)} `;
  const claves = new Set<string>();
  for (const { forma, clave } of vocabulario) {
    const posicion = resto.indexOf(` ${forma} `);
    if (posicion < 0) continue;
    claves.add(clave);
    resto = resto.slice(0, posicion + 1) + " ".repeat(forma.length) + resto.slice(posicion + 1 + forma.length);
  }
  if (claves.size === 0) return null;
  return claves.size === 1 ? [...claves][0]! : "ambigua";
}

/** Todas las claves que una etiqueta de evento de un registro nombra («Primer cumpleaños» → él mismo y «cumpleanos»). */
export function clavesDeEtiqueta(etiqueta: string, vocabulario: VocabularioCategorias): Set<ClaveCategoria> {
  const texto = normalizarBusqueda(etiqueta);
  return new Set(vocabulario.filter(({ forma }) => contiene(texto, forma) >= 0).map(({ clave }) => clave));
}

/** Formas con las que se nombra una categoría: sirven para no tratar «boda» como un estilo pedido. */
export function formasDeCategoria(clave: ClaveCategoria, vocabulario: VocabularioCategorias): string[] {
  return vocabulario.filter((entrada) => entrada.clave === clave).map((entrada) => entrada.forma);
}

export function decoracionEsDeCategoria(decoracion: DecoracionSempertex, clave: ClaveCategoria, vocabulario: VocabularioCategorias): boolean {
  return decoracion.eventos.some((evento) => clavesDeEtiqueta(evento, vocabulario).has(clave));
}
