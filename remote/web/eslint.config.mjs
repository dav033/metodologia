import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

const baseDirectory = dirname(fileURLToPath(import.meta.url));
let eslintConfig;

try {
  const { FlatCompat } = await import("@eslint/eslintrc");
  const compat = new FlatCompat({ baseDirectory });
  eslintConfig = [
    ...compat.extends("next/core-web-vitals", "next/typescript"),
    { ignores: [".next/**", "node_modules/**", "next-env.d.ts"] },
  ];
} catch (error) {
  if (!(error instanceof Error) || error.code !== "ERR_MODULE_NOT_FOUND") throw error;

  // ESLint 10 images may omit FlatCompat while retaining the project's Next lint plugins.
  const [nextPlugin, tsParser, tsPlugin, reactPlugin, hooksPlugin] = await Promise.all([
    import("@next/eslint-plugin-next"),
    import("@typescript-eslint/parser"),
    import("@typescript-eslint/eslint-plugin"),
    import("eslint-plugin-react"),
    import("eslint-plugin-react-hooks"),
  ]);
  const next = nextPlugin.default;
  const typescript = tsPlugin.default;
  const react = reactPlugin.default;
  const reactHooks = hooksPlugin.default;
  eslintConfig = [
    {
      files: ["**/*.{js,jsx,mjs,cjs,ts,tsx}"],
      languageOptions: {
        parser: tsParser.default,
        parserOptions: { ecmaFeatures: { jsx: true }, sourceType: "module" },
      },
      plugins: {
        "@next/next": next,
        "@typescript-eslint": typescript,
        react,
        "react-hooks": reactHooks,
      },
      settings: { react: { version: "detect" } },
      rules: {
        ...typescript.configs.recommended.rules,
        ...react.configs.recommended.rules,
        ...reactHooks.configs.recommended.rules,
        ...next.configs.recommended.rules,
        ...next.configs["core-web-vitals"].rules,
      },
    },
    { ignores: [".next/**", "node_modules/**", "next-env.d.ts"] },
  ];
}

export default eslintConfig;
