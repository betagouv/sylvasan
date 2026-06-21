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

const pinia = createPinia()
const app = createApp(App).use(pinia).use(VueDsfr).use(IonicVue)

import { useAuthStore } from "./stores/auth"
const auth = useAuthStore()
await auth.bootstrap()

import { useSyncStore } from "./stores/sync"
// Instantiate individual stores so they are registered before the sync store uses them
import { useSurveysStore } from "./stores/surveys"
import { useResponsesStore } from "./stores/responses"
import { useVocabulariesStore } from "./stores/vocabularies"
useSurveysStore()
useResponsesStore()
useVocabulariesStore()
const syncStore = useSyncStore()
if (auth.isLoggedIn) {
  await syncStore.bootstrap()
}

import router from "./router/root"
app.use(router)
await router.isReady()

app.mount("#app")
