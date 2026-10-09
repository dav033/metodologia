// ESLint half of the NestJS architecture rules. Verified with eslint 10 + typescript-eslint 8.
// Use: import arch from "./eslint-arch.config.mjs";  export default [...yourConfig, ...arch];
export default [
  {
    files: ["src/**/*.ts"],
    rules: {
      "no-restricted-syntax": ["error", {
        selector: "ExportAllDeclaration",
        message: "No `export *`: list the public API with named exports.",
      }],
    },
  },
  {
    // Business code never throws HTTP exceptions: services and domain throw domain errors (common/errors),
    // one exception filter maps them to problem+json.
    files: [
      "src/modules/**/application/**/*.ts",
      "src/modules/**/domain/**/*.ts",
      "src/modules/**/*.service.ts",
      "src/modules/**/*.facade.ts",
    ],
    ignores: ["**/*.spec.ts"],
    rules: {
      "no-restricted-imports": ["error", { patterns: [{
        group: ["@nestjs/common"],
        importNamePattern: "Exception$",
        message: "Throw a domain error from common/errors; the exception filter maps it to HTTP.",
      }] }],
    },
  },
];
