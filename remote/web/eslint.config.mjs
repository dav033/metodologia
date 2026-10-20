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
  const [tsParser, tsPlugin, reactPlugin, hooksPlugin] = await Promise.all([
    import("@typescript-eslint/parser"),
    import("@typescript-eslint/eslint-plugin"),
    import("eslint-plugin-react"),
    import("eslint-plugin-react-hooks"),
  ]);
  let next;
  try {
    next = (await import("@next/eslint-plugin-next")).default;
  } catch (pluginError) {
    if (!(pluginError instanceof Error) || pluginError.code !== "ERR_MODULE_NOT_FOUND") throw pluginError;
  }
  const typescript = tsPlugin.default;
  const react = reactPlugin.default;
  const reactHooks = hooksPlugin.default;
  const plugins = {
    "@typescript-eslint": typescript,
    react,
    "react-hooks": reactHooks,
  };
  const rules = {
    ...typescript.configs.recommended.rules,
    ...react.configs.recommended.rules,
    ...reactHooks.configs.recommended.rules,
  };
  if (next) {
    plugins["@next/next"] = next;
    Object.assign(rules, next.configs.recommended.rules, next.configs["core-web-vitals"].rules);
  }
  eslintConfig = [
    {
      files: ["**/*.{js,jsx,mjs,cjs,ts,tsx}"],
      languageOptions: {
        parser: tsParser.default,
        parserOptions: { ecmaFeatures: { jsx: true }, sourceType: "module" },
      },
      plugins,
      settings: { react: { version: "detect" } },
      rules,
    },
    { ignores: [".next/**", "node_modules/**", "next-env.d.ts"] },
  ];
}

export default eslintConfig;
