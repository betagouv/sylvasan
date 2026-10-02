import { StatusBar, Style } from "@capacitor/status-bar"
import { Capacitor } from "@capacitor/core"

if (Capacitor.isNativePlatform()) {
  StatusBar.setStyle({ style: Style.Light })
}

import { createApp } from "vue"
import "./style.css"
import App from "./App.vue"
import { IonicVue } from "@ionic/vue"

import "@gouvfr/dsfr/dist/dsfr.min.css"
import "@gouvminint/vue-dsfr/dist/vue-dsfr.css"
import VueDsfr from "@gouvminint/vue-dsfr"

import { createPinia } from "pinia"

import { addCollection } from "@iconify/vue"
import collections from "./icon-collections"

// Register all icons before mounting the app
for (const collection of collections) {
  addCollection(collection)
}

import "@ionic/vue/css/core.css"
// import "@ionic/vue/css/normalize.css"
// import "@ionic/vue/css/structure.css"
// import "@ionic/vue/css/typography.css"

import "maplibre-gl/dist/maplibre-gl.css"
// Vite regroupe le worker et ses dépendances (maplibre-gl-shared.mjs) dans un seul fichier,
// évitant les erreurs 404 sur les imports internes du worker en mode natif Capacitor.
import { setWorkerUrl } from "maplibre-gl"
import maplibreWorkerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url"
setWorkerUrl(maplibreWorkerUrl)

import * as Sentry from "@sentry/capacitor"
import * as SentryVue from "@sentry/vue"
import router from "./router/root"

const pinia = createPinia()
const app = createApp(App).use(pinia).use(VueDsfr).use(IonicVue)

if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init(
    {
      app,
      dsn: import.meta.env.VITE_SENTRY_DSN,
      integrations: [SentryVue.browserTracingIntegration({ router })],
      tracesSampleRate: 0.2,
    },
    SentryVue.init,
  )
}

import { useAuthStore } from "./stores/auth"
const auth = useAuthStore()
await auth.bootstrap()

import { setupAutoSync } from "./utils/autoSync"
await setupAutoSync()

app.use(router)
await router.isReady()

app.mount("#app")
