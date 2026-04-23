import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import tailwindcss from "@tailwindcss/vite"
import path from "path"

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  css: {
    lightningcss: {
      // Fix d'un bug de lightningCSS décrit ici : https://github.com/parcel-bundler/lightningcss/issues/214
      errorRecovery: true,
    },
  },
  resolve: {
    alias: {
      "@shared-types": path.resolve(__dirname, "../shared/types"),
      "@shared-utils": path.resolve(__dirname, "../shared/utils"),
      "@shared-components": path.resolve(__dirname, "../shared/components"),
    },
  },
})
