// Builds self-contained HTML from TSX that uses the REAL installed libraries (kit workspace, outside git).
//
//   node build.mjs mockup <entry.tsx> --out <file.html> [--ws <workspace>] [--title <t>]
//   node build.mjs gallery --out <dir> [--ws <workspace>] [--only id,id]
//   node build.mjs check <file.tsx> [...]          # compile only (no output): for demo authors
//
// Everything runs from the workspace's node_modules (esbuild, Tailwind 4) with no network and no temporary files: the
// bundle and the CSS are produced in memory and written only to --out. `@/…` resolves to the workspace's src (shadcn
// components, React Bits, Bencho), `@kit/…` to this folder's runtime. Output HTML carries one <style> and one <script>.
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath, pathToFileURL } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const flag = (name, dflt) => { const i = args.indexOf(name); return i >= 0 ? args.splice(i, 2)[1] : dflt; };
const WS = path.resolve(flag("--ws", process.env.BITACORA_KIT_WORKSPACE || path.join(process.env.XDG_DATA_HOME || path.join(process.env.HOME, ".local/share"), "bitacora/kit-workspace")));
const OUT = flag("--out", "");
const TITLE = flag("--title", "");
const ONLY = (flag("--only", "") || "").split(",").filter(Boolean);
const [mode, ...rest] = args;

function die(msg, code = 2) { console.error(`BUILD FAILED: ${msg}`); process.exit(code); }
if (!fs.existsSync(path.join(WS, "node_modules"))) die(`kit workspace not installed at ${WS}: run \`bitacora.py components install\``);
const req = createRequire(path.join(WS, "package.json"));
const load = async (name) => import(pathToFileURL(req.resolve(name)).href);
const esbuild = await load("esbuild");
const tw = await load("@tailwindcss/node");
const { Scanner } = await load("@tailwindcss/oxide");

const CSS_INPUT = `@import "tailwindcss";\n@import "tw-animate-css";\n@import "shadcn/tailwind.css";\n@import "${path.join(HERE, "theme.css")}";\n@import "${path.join(HERE, "bencho-theme.css")}";\n@import "${path.join(HERE, "overrides.css")}";\n`;
const FONT_EXT = /\.(woff2?|ttf|otf)$/i;

function esbuildOptions(extra) {
  return {
    bundle: true, write: false, format: "iife", platform: "browser", target: "es2020", minify: true, metafile: true,
    jsx: "automatic", legalComments: "none", logLevel: "silent", absWorkingDir: WS, outdir: path.join(WS, ".virtual-out"),
    nodePaths: [path.join(WS, "node_modules")],
    alias: { "@": path.join(WS, "src"), "@kit": path.join(HERE, "runtime") },
    define: { "process.env.NODE_ENV": '"production"' },
    loader: { ".png": "dataurl", ".jpg": "dataurl", ".jpeg": "dataurl", ".webp": "dataurl", ".gif": "dataurl", ".svg": "dataurl",
              ".woff": "dataurl", ".woff2": "dataurl", ".ttf": "dataurl", ".glsl": "text", ".css": "css" },
    ...extra,
  };
}

/** Tailwind CSS for exactly the files in the bundle (+ any CSS they import), fonts inlined as data: URIs. */
async function cssFor(files, importedCss) {
  const compiler = await tw.compile(CSS_INPUT + importedCss.map((f) => `@import "${f}";\n`).join(""), {
    base: WS, onDependency: () => {}, shouldRewriteUrls: true,
  });
  const scanner = new Scanner({ sources: [] });
  const candidates = scanner.scanFiles(files.map((file) => ({ content: fs.readFileSync(file, "utf8"), extension: path.extname(file).slice(1) || "tsx" })));
  let css = compiler.build(candidates);
  css = css.replace(/url\((["']?)([^)"']+)\1\)/g, (m, q, url) => {
    if (/^(data:|#|https?:)/.test(url) || !FONT_EXT.test(url)) return m;
    const file = [path.resolve(WS, url), ...importedCss.map((c) => path.resolve(path.dirname(c), url))].find((p) => fs.existsSync(p));
    if (!file) return m;
    const type = { ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".otf": "font/otf" }[path.extname(file).toLowerCase()];
    return `url(data:${type};base64,${fs.readFileSync(file).toString("base64")})`;
  });
  return tw.optimize(css, { minify: true }).code;
}

function inputsOf(metafile) {
  const files = [], css = [];
  for (const rel of Object.keys(metafile.inputs)) {
    const abs = path.resolve(WS, rel.replace(/^[a-z-]+:/, ""));
    if (!fs.existsSync(abs)) continue;
    if (abs.endsWith(".css")) css.push(abs);
    else if (/\.(tsx?|jsx?|mjs)$/.test(abs) && !/node_modules[\\/](react|react-dom|scheduler|motion-dom|motion-utils|framer-motion|gsap|three|ogl|recharts|d3-[a-z]+)[\\/]/.test(abs)) files.push(abs);
  }
  return { files, css };
}

const safeJs = (code) => code.replace(/<\/(script)/gi, "<\\/$1").replace(/<!--/g, "<\\!--");
const safeCss = (code) => code.replace(/<\/(style)/gi, "<\\/$1");

function page({ title, css, js, kitAttrs = "" }) {
  return `<!doctype html>\n<html lang="es" data-kit="real" data-theme="light"${kitAttrs}><head><meta charset="utf-8">` +
    `<meta name="viewport" content="width=device-width, initial-scale=1"><title>${title.replace(/[<&"]/g, "")}</title>` +
    `<style data-kit="real">${safeCss(css)}</style></head><body><div id="root"></div>` +
    `<script data-kit="real">${safeJs(js)}</script></body></html>\n`;
}

async function bundle(entryCode, resolveDir, name, entryFile) {
  const result = await esbuild.build(esbuildOptions(entryFile ? { entryPoints: [entryFile] }
    : { stdin: { contents: entryCode, resolveDir, loader: "tsx", sourcefile: name } }));
  const js = result.outputFiles.find((f) => f.path.endsWith(".js"));
  const extraCss = "";   // CSS a component imports goes through Tailwind (cssFor), not esbuild's own CSS output
  return { js: js ? js.text : "", extraCss, meta: result.metafile };
}

function fmtErrors(e) {
  return (e.errors || []).slice(0, 8).map((x) => `${x.location ? `${x.location.file}:${x.location.line}: ` : ""}${x.text}`).join("\n") || String(e.message || e);
}

async function buildMockup(entry, out) {
  if (!entry || !out) die("usage: node build.mjs mockup <entry.tsx> --out <file.html>");
  const abs = path.resolve(entry);
  if (!fs.existsSync(abs)) die(`${entry} does not exist`);
  let b;
  try {
    b = await bundle("", "", "", abs);
  } catch (e) { die(fmtErrors(e), 1); }
  if (!/mountMockup/.test(fs.readFileSync(abs, "utf8"))) die(`${entry} never calls mountMockup(App, {...}) from "@kit/mockup"`, 1);
  const { files, css } = inputsOf(b.meta);
  const sheet = (await cssFor(files, css)) + "\n" + b.extraCss;
  const html = page({ title: TITLE || path.basename(out, ".html"), css: sheet, js: b.js });
  fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
  fs.writeFileSync(out, html);
  console.log(`built ${out} (${Math.round(html.length / 1024)} KB, ${files.length} source files, offline)`);
}

/** Every gallery demo: `demos/<source>/<id>.tsx` (default export) → `<out>/<id>.js`; one shared `gallery.css`. */
async function buildGallery(out) {
  if (!out) die("usage: node build.mjs gallery --out <dir>");
  fs.mkdirSync(out, { recursive: true });
  const demos = [];
  for (const source of fs.readdirSync(path.join(HERE, "demos"))) {
    for (const f of fs.readdirSync(path.join(HERE, "demos", source))) {
      if (f.endsWith(".tsx") && (!ONLY.length || ONLY.includes(f.slice(0, -4)))) demos.push({ id: f.slice(0, -4), source, file: path.join(HERE, "demos", source, f) });
    }
  }
  const status = {}, allFiles = new Set(), allCss = new Set();
  let extra = "";
  await Promise.all(demos.map(async (d) => {
    const code = `import Demo from ${JSON.stringify(d.file)};\nimport { mountFrame } from "@kit/frame";\nmountFrame(Demo);\n`;
    try {
      const b = await bundle(code, path.dirname(d.file), `${d.id}.entry.tsx`);
      fs.writeFileSync(path.join(out, `${d.id}.js`), safeJs(b.js));
      const { files, css } = inputsOf(b.meta);
      files.forEach((f) => allFiles.add(f)); css.forEach((f) => allCss.add(f));
      extra += b.extraCss;
      status[d.id] = { ok: true, source: d.source, kb: Math.round(b.js.length / 1024) };
    } catch (e) {
      status[d.id] = { ok: false, source: d.source, error: fmtErrors(e).slice(0, 600) };
    }
  }));
  const refs = path.join(HERE, "reference");
  for (const f of fs.existsSync(refs) ? fs.readdirSync(refs) : []) {
    if (!f.endsWith(".tsx") || (ONLY.length && !ONLY.includes(`ref-${f.slice(0, -4)}`))) continue;
    const id = f.slice(0, -4);
    try {
      await buildMockup(path.join(refs, f), path.join(out, "reference", `${id}.html`));
      status[`ref-${id}`] = { ok: true, source: "reference" };
    } catch (e) { status[`ref-${id}`] = { ok: false, source: "reference", error: String(e).slice(0, 600) }; }
  }
  if (ONLY.length) {                     // a partial build still needs every demo's classes in the shared sheet
    const walk = (d) => fs.readdirSync(d, { withFileTypes: true }).flatMap((x) => x.isDirectory() ? walk(path.join(d, x.name)) : /\.(tsx?|jsx?)$/.test(x.name) ? [path.join(d, x.name)] : []);
    [...walk(path.join(HERE, "demos")), ...walk(path.join(WS, "src"))].forEach((f) => allFiles.add(f));
  }
  if (allFiles.size) fs.writeFileSync(path.join(out, "gallery.css"), (await cssFor([...allFiles, ...fs.readdirSync(path.join(HERE, "runtime")).map((f) => path.join(HERE, "runtime", f))], [...allCss])) + "\n" + extra);
  const prev = ONLY.length && fs.existsSync(path.join(out, "status.json")) ? JSON.parse(fs.readFileSync(path.join(out, "status.json"), "utf8")).entries : {};
  fs.writeFileSync(path.join(out, "status.json"), JSON.stringify({ built: new Date().toISOString(), workspace: WS, entries: { ...prev, ...status } }, null, 1));
  const bad = Object.entries(status).filter(([, s]) => !s.ok);
  console.log(`gallery: ${Object.keys(status).length - bad.length} built, ${bad.length} failed → ${out}`);
  for (const [id, s] of bad) console.log(`  FAIL ${id}: ${s.error.split("\n")[0]}`);
  return bad.length ? 1 : 0;
}

async function check(files) {
  let bad = 0;
  for (const f of files) {
    try { await bundle("", "", "", path.resolve(f)); console.log(`ok   ${f}`); }
    catch (e) { bad++; console.log(`FAIL ${f}\n${fmtErrors(e)}`); }
  }
  return bad ? 1 : 0;
}

if (mode === "mockup") await buildMockup(rest[0], OUT);
else if (mode === "gallery") process.exit(await buildGallery(OUT));
else if (mode === "check") process.exit(await check(rest));
else die("usage: node build.mjs mockup|gallery|check …");
