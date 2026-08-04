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
// Le worker GeoJSON de MapLibre est créé depuis le bundle principal minifié par Vite,
// ce qui casse les références à des variables renommées dans le scope isolé du worker.
// On pointe explicitement vers le worker pré-compilé et auto-suffisant fourni par MapLibre.
import { setWorkerUrl } from "maplibre-gl"
import maplibreWorkerUrl from "maplibre-gl/dist/maplibre-gl-csp-worker?url"
setWorkerUrl(maplibreWorkerUrl)

const pinia = createPinia()
const app = createApp(App).use(pinia).use(VueDsfr).use(IonicVue)

import { useAuthStore } from "./stores/auth"
const auth = useAuthStore()
await auth.bootstrap()

import { setupAutoSync } from "./utils/autoSync"
await setupAutoSync()

import router from "./router/root"
app.use(router)
await router.isReady()

app.mount("#app")
