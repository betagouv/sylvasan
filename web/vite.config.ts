import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import tailwindcss from "@tailwindcss/vite"
import VueRouter from "vue-router/vite"
import path from "path"

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  ssr: {
    noExternal: mode === "development" ? ["vue-router"] : [],
  },
  plugins: [VueRouter(), vue(), tailwindcss()],
  base: "/",
  resolve: {
    alias: {
      "@shared-types": path.resolve(__dirname, "../shared/types"),
    },
  },
}))
