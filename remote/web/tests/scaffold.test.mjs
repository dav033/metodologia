import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { test } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const read = (path) => readFile(join(root, path), "utf8");

test("theme uses Catppuccin Mocha tokens with mauve as its accent", async () => {
  const css = await read("src/app/globals.css");
  assert.match(css, /--ctp-base:\s*#1e1e2e/i);
  assert.match(css, /--ctp-mantle:\s*#181825/i);
  assert.match(css, /--ctp-crust:\s*#11111b/i);
  assert.match(css, /--ctp-mauve:\s*#cba6f7/i);
  assert.match(css, /--ctp-lavender:\s*#b4befe/i);
  assert.match(css, /--accent:\s*var\(--ctp-mauve\)/);
});

test("app fonts are bundled locally and referenced by the root layout", async () => {
  const layout = await read("src/app/layout.tsx");
  assert.match(layout, /next\/font\/local/);
  assert.match(layout, /Manrope-400-latin\.woff2/);
  assert.match(layout, /JetBrainsMono-400-latin\.woff2/);
  await access(join(root, "public/fonts/Manrope-400-latin.woff2"));
  await access(join(root, "public/fonts/JetBrainsMono-400-latin.woff2"));
});

test("PWA manifest and same-origin API rewrite are configured", async () => {
  const manifest = JSON.parse(await read("public/manifest.webmanifest"));
  assert.equal(manifest.name, "Flow Remote");
  assert.equal(manifest.display, "standalone");
  assert.equal(manifest.theme_color, "#1e1e2e");

  const config = await read("next.config.ts");
  assert.match(config, /source:\s*"\/api\/:path\*"/);
  assert.match(config, /destination:\s*`\$\{gatewayOrigin\}\/api\/:path\*`/);
});

test("Tailwind CSS 4 is configured through PostCSS", async () => {
  const packageJson = JSON.parse(await read("package.json"));
  const postcssConfig = await read("postcss.config.mjs");
  const css = await read("src/app/globals.css");

  assert.match(packageJson.devDependencies.tailwindcss, /^4\./);
  assert.match(packageJson.devDependencies["@tailwindcss/postcss"], /^4\./);
  assert.match(postcssConfig, /"@tailwindcss\/postcss"/);
  assert.match(css, /^@import "tailwindcss";/);
});
