import { readFileSync } from "node:fs";
import assert from "node:assert/strict";
import { services } from "/home/david/dev/oraldenti/src/content/services.ts";

const blocks = JSON.parse(readFileSync(new URL("./reference-services-blocks.json", import.meta.url), "utf8"));
const block = (prefix) => {
  const entry = blocks.find((item) => item.text.startsWith(prefix));
  assert.ok(entry, `Missing source block: ${prefix}`);
  return entry.text;
};
const lines = (text) => text.split(/\n+/).map((line) => line.trim()).filter(Boolean);
const from = (text, first) => { const offset = text.indexOf(first); assert.ok(offset >= 0); return text.slice(offset); };
const cosmetic = block("La odontología estética").split("REHABILITACION ORAL");
const expected = {
  general: lines(block("Consulta general")),
  cosmetica: lines(from(cosmetic[0], "Resina fotocurado")),
  rehabilitacion: lines(cosmetic[1]),
  ortodoncia: lines(from(block("El estudio, prevención"), "Consulta especializada")),
  implantes: [],
  endodoncia: lines(from(block("Consiste en la extirpación"), "Endodoncia uniradicular")),
  periodoncia: lines(from(block("Es la especialidad odontológica"), "Consulta especializada")),
  cirugia: lines(from(block("Es una especialidad quirúrgica"), "Consulta especializada")),
  pediatria: lines(from(block("Es la rama de la odontología"), "Profilaxis y aplicación")),
};
// Ignore only spelling/spacing normalization and added grammatical prepositions.
const normalize = (text) => text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().replace(/\bde\b/g, "").replace(/rradicular/g, "radicular").replace(/\s+/g, " ").trim();
for (const service of services) {
  assert.deepEqual(service.treatments.map(normalize), expected[service.id].map(normalize), service.name);
  console.log(`${service.name}: ${service.treatments.length} source procedures verified`);
}
assert.equal(services.length, Object.keys(expected).length);
console.log(`Complete source coverage: ${services.length} categories, ${services.reduce((sum, service) => sum + service.treatments.length, 0)} procedures.`);
