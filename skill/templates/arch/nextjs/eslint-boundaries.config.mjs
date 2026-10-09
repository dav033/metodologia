// Architecture boundaries for a Next.js app (layout: stacks/nextjs.md).
// Verified with eslint 10, eslint-plugin-boundaries 7.2, eslint-plugin-check-file 3.3, typescript-eslint 8.
//
// Install: npm i -D eslint-plugin-boundaries eslint-import-resolver-typescript eslint-plugin-check-file typescript-eslint
// Use:     import arch from "./eslint-boundaries.config.mjs";
//          export default [...nextConfig, ...arch];
//
// Rules:
// - app -> features (only index.ts / index.server.ts) -> shared. shared imports only shared.
// - Features never import each other: compose them in app/.
/// - A feature always uses the layer folders; its root holds only index.ts / index.server.ts.
// - Inside a feature: domain imports nothing but domain + shared; presentation never touches infrastructure;
//   application MAY import its own infrastructure (TanStack hooks call the feature's API client).
// - No `export *`; kebab-case file and folder names (app/ folders exempt: [id], (group), _components).
import boundaries from "eslint-plugin-boundaries";
import checkFile from "eslint-plugin-check-file";
import tseslint from "typescript-eslint";

const own = { feature: "{{ from.element.captured.feature }}" };
const layer = (type) => ({ element: { type, captured: own } });
const shared = { element: { type: "shared" } };
const publicApi = [
  { element: { type: "feature", fileInternalPath: "index.{ts,tsx}" } },
  { element: { type: "feature", fileInternalPath: "index.server.{ts,tsx}" } },
];

export default [
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: { parser: tseslint.parser },
    plugins: { boundaries, "check-file": checkFile },
    settings: {
      "import/resolver": { typescript: { alwaysTryTypes: true } },
      "boundaries/elements": [
        { type: "domain", pattern: "src/features/*/domain", capture: ["feature"] },
        { type: "application", pattern: "src/features/*/application", capture: ["feature"] },
        { type: "infrastructure", pattern: "src/features/*/infrastructure", capture: ["feature"] },
        { type: "presentation", pattern: "src/features/*/presentation", capture: ["feature"] },
        { type: "feature", pattern: "src/features/*", capture: ["feature"] },
        { type: "shared", pattern: "src/shared" },
        { type: "app", pattern: "src/app" },
      ],
      "boundaries/files": [
        { category: "root", pattern: "src/*.{ts,tsx}" }, // proxy.ts, instrumentation.ts
        { category: "support", pattern: "src/{mocks,test,types}/**" }, // MSW handlers, test setup, *.d.ts
      ],
    },
    rules: {
      "boundaries/dependencies": [2, {
        default: "disallow",
        policies: [
          { from: { element: { type: "domain" } }, allow: { to: [layer("domain"), shared] } },
          { from: { element: { type: "infrastructure" } },
            allow: { to: [layer("domain"), layer("infrastructure"), shared] } },
          { from: { element: { type: "application" } },
            allow: { to: [layer("domain"), layer("application"), layer("infrastructure"), shared] } },
          { from: { element: { type: "presentation" } },
            allow: { to: [layer("domain"), layer("application"), layer("presentation"), shared] } },
          // feature root holds only index.ts / index.server.ts, which re-export the layers
          { from: { element: { type: "feature" } },
            allow: { to: [layer("domain"), layer("application"), layer("infrastructure"), layer("presentation")] } },
          { from: { element: { type: "shared" } }, allow: { to: shared } },
          { from: { element: { type: "app" } }, allow: { to: [...publicApi, shared, { element: { type: "app" } }] } },
          { from: { file: { categories: "root" } }, allow: { to: [...publicApi, shared] } },
          { from: { file: { categories: "support" } },
            allow: { to: [...publicApi, shared, { file: { categories: "support" } }] } },
        ],
      }],
      "boundaries/no-unknown-files": 2,
      "no-restricted-syntax": ["error", {
        selector: "ExportAllDeclaration",
        message: "No `export *`: list the public API with named exports.",
      }],
      "check-file/filename-naming-convention": ["error",
        { "src/**/*.{ts,tsx}": "KEBAB_CASE" }, { ignoreMiddleExtensions: true }],
      "check-file/folder-naming-convention": ["error", { "src/!(app)/**/": "KEBAB_CASE" }],
    },
  },
  {
    // boundaries/dependencies only checks local files; framework packages are kept out of the domain here
    files: ["src/features/*/domain/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": ["error", { patterns: [{
        group: ["react", "react-dom", "next", "next/*", "@tanstack/*"],
        message: "domain/ is plain TypeScript: no React, Next or TanStack.",
      }] }],
    },
  },
];
