import { createApp } from "vue"
import "./style.css"
import App from "./App.vue"
import { IonicVue } from "@ionic/vue"

import "@gouvfr/dsfr/dist/dsfr.min.css"
import "@gouvminint/vue-dsfr/dist/vue-dsfr.css"
import VueDsfr from "@gouvminint/vue-dsfr"

import { createPinia } from "pinia"

import "@ionic/vue/css/core.css"
// import "@ionic/vue/css/normalize.css"
// import "@ionic/vue/css/structure.css"
// import "@ionic/vue/css/typography.css"

const pinia = createPinia()
const app = createApp(App).use(pinia).use(VueDsfr).use(IonicVue)

import { useAuthStore } from "./stores/auth"
const auth = useAuthStore()

await auth.bootstrap()

import router from "./router/root"
app.use(router)
await router.isReady()

app.mount("#app")
