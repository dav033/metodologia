// Builds HTML from TSX that uses the component pool `@bitacora/ui` (skill/ui, D-280) with the kit workspace's toolchain.
//
//   node build.mjs mockup <entry.tsx> --out <file.html> [--ws <workspace>] [--title <t>] [--project <p>]
//        self-contained export: one <style> and one <script>, the project's theme and mockup fonts inlined
//   node build.mjs mockup <entry.tsx> --live --registry <pool dir> --project <p> --out <file.html>
//        live page: links the built pool (/ui/<digest>/bitacora-ui.{css,js}) and /ui/theme/<p>.css; only the entry's
//        own code and utilities are inlined, every pool import is read from the pool at view time
//   node build.mjs pool --out <dir> [--version <v>]       # the pool registry: bitacora-ui.js/.css/.json
//   node build.mjs gallery --out <dir> [--ws <workspace>] [--only id,id]
//   node build.mjs check <file.tsx> [...]          # compile only (no output): for demo authors
//
// Everything runs from the workspace's node_modules (esbuild, Tailwind 4) with no network and no temporary files: the
// bundle and the CSS are produced in memory and written only to --out. `@bitacora/ui/…` and the legacy `@/…` resolve
// to the package's src (skill/ui/src), `@kit/…` to this folder's runtime.
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
const REGISTRY = flag("--registry", "");
const PROJECT = flag("--project", "");
const VERSION = flag("--version", "");
const LIVE = (() => { const i = args.indexOf("--live"); return i >= 0 ? (args.splice(i, 1), true) : false; })();
const UI = path.resolve(flag("--ui", process.env.BITACORA_UI_ROOT || path.resolve(HERE, "../../../../../ui")));   // the package (skill/ui)
const UI_SRC = path.join(UI, "src");
const [mode, ...rest] = args;

function die(msg, code = 2) { console.error(`BUILD FAILED: ${msg}`); process.exit(code); }
if (!fs.existsSync(path.join(WS, "node_modules"))) die(`kit workspace not installed at ${WS}: run \`bitacora.py components install\``);
const req = createRequire(path.join(WS, "package.json"));
const load = async (name) => import(pathToFileURL(req.resolve(name)).href);
const esbuild = await load("esbuild");
const tw = await load("@tailwindcss/node");
const { Scanner } = await load("@tailwindcss/oxide");

const CSS_STRUCTURE = `@import "tailwindcss";\n@import "${path.join(UI_SRC, "styles.css")}";\n`;
const CSS_INPUT = CSS_STRUCTURE + `@import "${path.join(UI_SRC, "theme.css")}";\n`;
if (PROJECT && !/^[a-z0-9][a-z0-9_-]{0,63}$/.test(PROJECT)) die(`invalid --project ${PROJECT}`);
/** The project's theme for a self-contained export: its file and the fontsource packages it names for mockups. */
function projectTheme() {
  const file = PROJECT ? path.join(UI, "themes", `${PROJECT}.css`) : "";
  if (!file || !fs.existsSync(file)) return "";
  const fonts = (/@mockup-fonts:\s*([^*]+)\*\//.exec(fs.readFileSync(file, "utf8")) || [, ""])[1]
    .split(",").map((x) => x.trim()).filter((x) => /^@fontsource(-variable)?\/[a-z0-9-]+$/.test(x));
  return fonts.map((f) => `@import "${f}";\n`).join("") + `@import "${file}";\n`;
}
const FONT_EXT = /\.(woff2?|ttf|otf)$/i;

function esbuildOptions(extra) {
  return {
    bundle: true, write: false, format: "iife", platform: "browser", target: "es2020", minify: true, metafile: true,
    jsx: "automatic", legalComments: "none", logLevel: "silent", absWorkingDir: WS, outdir: path.join(WS, ".virtual-out"),
    nodePaths: [path.join(WS, "node_modules")],
    alias: { "@bitacora/ui": UI_SRC, "@": UI_SRC, "@kit": path.join(HERE, "runtime") },
    define: { "process.env.NODE_ENV": '"production"' },
    loader: { ".png": "dataurl", ".jpg": "dataurl", ".jpeg": "dataurl", ".webp": "dataurl", ".gif": "dataurl", ".svg": "dataurl",
              ".woff": "dataurl", ".woff2": "dataurl", ".ttf": "dataurl", ".glsl": "text", ".css": "css" },
    ...extra,
  };
}

/** Tailwind CSS for exactly the files in the bundle (+ any CSS they import), fonts inlined as data: URIs. */
async function cssFor(files, importedCss, input = CSS_INPUT) {
  const compiler = await tw.compile(input + importedCss.map((f) => `@import "${f}";\n`).join(""), {
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

async function bundle(entryCode, resolveDir, name, entryFile, plugins = [], banner = "") {
  const result = await esbuild.build(esbuildOptions({ plugins, ...(banner ? { banner: { js: banner } } : {}), ...(entryFile ? { entryPoints: [entryFile] }
    : { stdin: { contents: entryCode, resolveDir, loader: "tsx", sourcefile: name } }) }));
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
  if (LIVE) return buildLive(abs, out);
  let b;
  try {
    b = await bundle("", "", "", abs);
  } catch (e) { die(fmtErrors(e), 1); }
  if (!/mountMockup/.test(fs.readFileSync(abs, "utf8"))) die(`${entry} never calls mountMockup(App, {...}) from "@kit/mockup"`, 1);
  const { files, css } = inputsOf(b.meta);
  const sheet = (await cssFor(files, css, CSS_INPUT + projectTheme())) + "\n" + b.extraCss;
  const html = page({ title: TITLE || path.basename(out, ".html"), css: sheet, js: b.js });
  fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
  fs.writeFileSync(out, html);
  console.log(`built ${out} (${Math.round(html.length / 1024)} KB, ${files.length} source files, offline)`);
}

// ------------------------------------------------------------------------------------------------ pool registry
const walk = (d) => fs.existsSync(d) ? fs.readdirSync(d, { withFileTypes: true }).flatMap((x) => x.isDirectory() ? walk(path.join(d, x.name)) : [path.join(d, x.name)]) : [];
const CODE = /\.(tsx?|jsx?|mjs)$/;
/** Every module a mockup may import from the pool, by the key mockups use: the package's own modules
 *  (`@bitacora/ui/<path>`), the kit runtime (`@kit/<name>`) and every bare package the pool imports (one React, one
 *  Base UI, one Motion for the pool and the mockup alike). */
// packages that hold React context or module state: one copy for the pool and every mockup. Stateless libraries
// (icons, charts, class helpers) stay inside whatever imports them, so the registry carries only what it must.
const SHARED = /^(react|react-dom|@base-ui\/react|@animate-ui\/react|motion|framer-motion|sonner|next-themes|gsap|@gsap\/react)(\/[\w./-]+)?$/;
function poolModules() {
  const own = walk(UI_SRC).filter((f) => CODE.test(f) && !f.endsWith(".d.ts"))
    .map((f) => ({ key: "@bitacora/ui/" + path.relative(UI_SRC, f).replace(/\\/g, "/").replace(CODE, ""), file: f }));
  const runtime = walk(path.join(HERE, "runtime")).filter((f) => CODE.test(f))
    .map((f) => ({ key: "@kit/" + path.basename(f).replace(CODE, ""), file: f }));
  const bare = new Set(["react", "react-dom", "react-dom/client", "react/jsx-runtime"]);
  for (const { file } of [...own, ...runtime]) {
    for (const m of fs.readFileSync(file, "utf8").matchAll(/(?:from\s+|import\s+|import\(\s*)["']([^"']+)["']/g)) {
      const spec = m[1];
      if (SHARED.test(spec)) bare.add(spec);
    }
  }
  return [...own, ...runtime, ...[...bare].sort().map((key) => ({ key, file: key }))];
}

async function buildPool(out) {
  if (!out) die("usage: node build.mjs pool --out <dir>");
  const mods = poolModules();
  const code = mods.map((m, i) => `import * as m${i} from ${JSON.stringify(m.file)};`).join("\n") +
    "\nconst R = (window.__bitacoraUI = window.__bitacoraUI || {});\n" +
    mods.map((m, i) => `R[${JSON.stringify(m.key)}] = Object.assign({ __esModule: true }, m${i});`).join("\n") + "\n";
  let b;
  // a pool module may read process.env beyond NODE_ENV (next/navigation does): give the browser an empty one
  const shim = 'var process = globalThis.process || (globalThis.process = { env: { NODE_ENV: "production" } });';
  try { b = await bundle(code, UI_SRC, "bitacora-ui.entry.tsx", undefined, [], shim); } catch (e) { die(fmtErrors(e), 1); }
  const { files, css } = inputsOf(b.meta);
  const sheet = await cssFor([...new Set([...files, ...walk(UI_SRC).filter((f) => CODE.test(f)), ...walk(path.join(HERE, "runtime"))])], css);
  fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(path.join(out, "bitacora-ui.js"), b.js);
  fs.writeFileSync(path.join(out, "bitacora-ui.css"), sheet);
  const pkg = JSON.parse(fs.readFileSync(path.join(UI, "package.json"), "utf8"));
  fs.writeFileSync(path.join(out, "bitacora-ui.json"), JSON.stringify({
    name: pkg.name, version: VERSION || pkg.version, built: new Date().toISOString(), keys: mods.map((m) => m.key),
    kb: { js: Math.round(b.js.length / 1024), css: Math.round(sheet.length / 1024) } }, null, 1));
  console.log(`pool ${VERSION || pkg.version}: ${mods.length} modules, ${Math.round(b.js.length / 1024)} KB js, ${Math.round(sheet.length / 1024)} KB css → ${out}`);
}

/** esbuild plugin: an import the pool registry holds is read from `window.__bitacoraUI` instead of bundled. */
function registryPlugin(keys) {
  const keyOf = (spec) => {
    if (spec.startsWith("@bitacora/ui/")) return spec.replace(CODE, "");
    if (spec.startsWith("@/")) return "@bitacora/ui/" + spec.slice(2).replace(CODE, "");
    return spec;
  };
  return { name: "bitacora-ui-registry", setup(build) {
    build.onResolve({ filter: /^[^.\/]/ }, (args) => {
      const key = keyOf(args.path);
      return keys.has(key) ? { path: key, namespace: "bitacora-ui" } : undefined;
    });
    build.onLoad({ filter: /.*/, namespace: "bitacora-ui" }, (args) => ({ loader: "js", contents:
      `var m = window.__bitacoraUI && window.__bitacoraUI[${JSON.stringify(args.path)}];\n` +
      `if (!m) throw new Error("@bitacora/ui: the pool has no module " + ${JSON.stringify(JSON.stringify(args.path))});\nmodule.exports = m;\n` }));
  } };
}

async function buildLive(abs, out) {
  if (!REGISTRY || !fs.existsSync(path.join(REGISTRY, "bitacora-ui.json"))) die("--live needs --registry <built pool dir>");
  const reg = JSON.parse(fs.readFileSync(path.join(REGISTRY, "bitacora-ui.json"), "utf8"));
  const digest = path.basename(path.resolve(REGISTRY));
  let b;
  try { b = await bundle("", "", "", abs, [registryPlugin(new Set(reg.keys))]); } catch (e) { die(fmtErrors(e), 1); }
  if (!/mountMockup/.test(fs.readFileSync(abs, "utf8"))) die(`${abs} never calls mountMockup(App, {...}) from "@kit/mockup"`, 1);
  const { files, css } = inputsOf(b.meta);
  const sheet = files.length || css.length ? await cssFor(files, css, CSS_STRUCTURE) : "";
  const title = (TITLE || path.basename(out, ".html")).replace(/[<&"]/g, "");
  const theme = PROJECT ? `<link rel="stylesheet" href="/ui/theme/${PROJECT}.css" data-ui-theme>` : "";
  const html = `<!doctype html>\n<html lang="es" data-kit="real" data-ui-live="${reg.version}" data-theme="light"><head><meta charset="utf-8">` +
    `<meta name="viewport" content="width=device-width, initial-scale=1"><title>${title}</title>` +
    `<link rel="stylesheet" href="/ui/${digest}/bitacora-ui.css" data-ui-pool><style data-kit="mockup">${safeCss(sheet)}</style>${theme}` +
    `</head><body><div id="root"></div><script src="/ui/${digest}/bitacora-ui.js" data-ui-pool></script>` +
    `<script data-kit="mockup">${safeJs(b.js)}</script></body></html>\n`;
  fs.mkdirSync(path.dirname(path.resolve(out)), { recursive: true });
  fs.writeFileSync(out, html);
  console.log(`built live ${out} (${Math.round(html.length / 1024)} KB, pool ${reg.version})`);
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
    [...walk(path.join(HERE, "demos")), ...walk(UI_SRC)].filter((f) => CODE.test(f)).forEach((f) => allFiles.add(f));
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
else if (mode === "pool") await buildPool(OUT);
else die("usage: node build.mjs mockup|gallery|check …");
