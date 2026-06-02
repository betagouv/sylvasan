import tseslint from "typescript-eslint"

export default [
  tseslint.configs.base,
  {
    files: ["**/*.ts", "**/*.vue", "**/*.js"],
    rules: {},
  },
]
