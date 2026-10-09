// Architecture rules for a NestJS API (layout: stacks/nestjs.md). Verified with dependency-cruiser 18.
// Rules match both a small flat feature (orders.controller.ts, orders.service.ts, orders.repository.ts,
// order.entity.ts) and a layered one (presentation/ application/ domain/ infrastructure/).
// Install: npm i -D dependency-cruiser
// Script:  "arch": "depcruise src --config .dependency-cruiser.cjs"
const MOD = "^src/modules/[^/]+";
const PRESENTATION = MOD + ".*(/presentation/|\\.controller\\.ts$)";
const APPLICATION = MOD + ".*(/application/|\\.service\\.ts$|\\.facade\\.ts$)";
// a *.entity.ts under domain/ is a pure domain entity, not a TypeORM one
const DATA = MOD + "(?!.*/domain/).*(/infrastructure/|\\.(repository|entity|subscriber)\\.ts$)";
const ORM = "node_modules/(typeorm|@nestjs/typeorm)/";
const TESTS = "\\.(spec|e2e-spec)\\.ts$";

/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "no-circular",
      severity: "error",
      comment: "Cycles break Nest DI (forwardRef). TypeORM entity relations are exempt.",
      from: { pathNot: "\\.entity\\.ts$" },
      to: { circular: true },
    },
    {
      name: "feature-public-entry-only",
      severity: "error",
      comment: "Another feature is reached only through its index.ts (module + facade + event types).",
      from: { path: "^src/modules/([^/]+)/", pathNot: TESTS },
      to: { path: MOD + "/", pathNot: ["^src/modules/$1/", MOD + "/index\\.ts$"] },
    },
    {
      name: "no-inner-barrels",
      severity: "error",
      comment: "index.ts only at a feature root. In common/, config/ and layer folders import the file directly.",
      from: {},
      to: { path: "^src/.+/index\\.ts$", pathNot: "^src/modules/[^/]+/index\\.ts$" },
    },
    {
      name: "root-uses-feature-entry",
      severity: "error",
      comment: "app.module.ts / main.ts import features through their index.ts.",
      from: { path: "^src/[^/]+\\.ts$" },
      to: { path: MOD + "/", pathNot: MOD + "/index\\.ts$" },
    },
    {
      name: "controllers-not-to-data",
      severity: "error",
      comment: "Controllers: DTO in, call the service, DTO out. No repositories or ORM entities.",
      from: { path: PRESENTATION },
      to: { path: [DATA, ORM] },
    },
    {
      name: "services-not-to-controllers",
      severity: "error",
      from: { path: APPLICATION, pathNot: TESTS },
      to: { path: PRESENTATION },
    },
    {
      name: "only-infrastructure-touches-orm",
      severity: "error",
      comment: "typeorm only in repositories, ORM entities, subscribers and *.module.ts. Transactions via common/database.",
      from: { path: MOD + "/", pathNot: [DATA, "\\.module\\.ts$", TESTS] },
      to: { path: ORM },
    },
    {
      name: "domain-is-pure",
      severity: "error",
      comment: "domain/ is plain TypeScript: no Nest, no ORM, no other layer.",
      from: { path: MOD + "/domain/" },
      to: { path: [PRESENTATION, APPLICATION, DATA, "\\.module\\.ts$",
        "node_modules/(@nestjs|typeorm|class-validator|class-transformer)/"] },
    },
    {
      name: "common-not-to-modules",
      severity: "error",
      from: { path: "^src/(common|config)/" },
      to: { path: "^src/modules/" },
    },
    {
      name: "not-to-dev-dep",
      severity: "error",
      comment: "Production code must not import devDependencies.",
      from: { path: "^src/", pathNot: TESTS },
      to: { dependencyTypes: ["npm-dev"], dependencyTypesNot: ["type-only"] },
    },
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    tsPreCompilationDeps: true,
    tsConfig: { fileName: "tsconfig.json" },
    exclude: { path: "^dist/" },
  },
};
