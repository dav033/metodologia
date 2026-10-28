// One source for the /flow decisions: skill/assets/flow-core.js. The phone serves a build copy from public/.
//   node scripts/sync-flow-core.mjs          copy the source over public/flow-core.js (runs before dev and build)
//   node scripts/sync-flow-core.mjs --check  exit 1 when the copy drifted from the source
// A deploy that only ships remote/web (no skill/ next to it) keeps the committed copy, which the check guards.
import { copyFile, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const source = fileURLToPath(new URL("../../../skill/assets/flow-core.js", import.meta.url));
const copy = fileURLToPath(new URL("../public/flow-core.js", import.meta.url));
const check = process.argv.includes("--check");

let original;
try { original = await readFile(source); }
catch {
  if (check) { console.error(`flow-core source not found at ${source}`); process.exit(1); }
  console.log("flow-core source not available here; keeping the committed public/flow-core.js");
  process.exit(0);
}
const current = await readFile(copy).catch(() => null);
if (current && Buffer.compare(original, current) === 0) process.exit(0);
if (check) { console.error("public/flow-core.js drifted from skill/assets/flow-core.js; run `npm run sync:flow-core`"); process.exit(1); }
await copyFile(source, copy);
console.log("public/flow-core.js updated from skill/assets/flow-core.js");
