import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";

export default tseslint.config(
  {
    ignores: ["dist", "coverage"],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: {
      parserOptions: {
        project: ["./tsconfig.app.json"],
        tsconfigRootDir: import.meta.dirname,
      },
    },
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-refresh/only-export-components": "warn",
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            {
              group: ["@tma.js/*"],
              message: "Import Telegram SDK only from src/telegram adapter.",
            },
            {
              group: ["@telegram-apps/telegram-ui"],
              message: "Import telegram-ui only from src/components/ui wrappers.",
            },
          ],
        },
      ],
    },
  },
  {
    files: ["src/telegram/**/*.{ts,tsx}", "src/components/ui/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-imports": "off",
    },
  },
);
