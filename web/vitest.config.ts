import { defineConfig } from "vitest/config"

// Si besoin de tester des composants Vue dans un environnement
// browser (donc avec window, document, etc), le document de test
// doit avoir en première ligne le commentaire :
// `@vitest-environment jsdom`

export default defineConfig({
  test: {
    environment: "node",
    globals: true,
  },
})
