// Cycle and barrel checks for a Next.js app; eslint-boundaries.config.mjs covers import direction.
// Verified with dependency-cruiser 18.
// Install: npm i -D dependency-cruiser
// Script:  "arch": "depcruise src --config .dependency-cruiser.cjs"
/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "no-circular",
      severity: "error",
      comment: "Import cycles; index.ts files make them easy to create.",
      from: {},
      to: { circular: true },
    },
    {
      name: "no-inner-barrels",
      severity: "error",
      comment: "index.ts only at a feature root. In shared/ and inside feature layers import the file directly.",
      from: {},
      to: { path: "^src/(shared|features/[^/]+/.+)/index(\\.server)?\\.tsx?$" },
    },
    {
      name: "feature-root-is-index-only",
      severity: "error",
      comment: "A feature's code lives in its layer folders; the root holds only index.ts / index.server.ts.",
      from: {},
      to: { path: "^src/features/[^/]+/[^/]+\\.tsx?$", pathNot: "/index(\\.server)?\\.tsx?$" },
    },
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    tsPreCompilationDeps: true,
    tsConfig: { fileName: "tsconfig.json" },
  },
};
