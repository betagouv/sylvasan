import { createApp } from "vue"
import App from "./App.vue"
import "@gouvfr/dsfr/dist/dsfr.min.css"
import "@gouvminint/vue-dsfr/dist/vue-dsfr.css"
import VueDsfr from "@gouvminint/vue-dsfr"
import router from "./router/root.ts"
import { createPinia } from "pinia"

const pinia = createPinia()

createApp(App).use(pinia).use(router).use(VueDsfr).mount("#app")
