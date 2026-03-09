import { createApp } from "vue"
import App from "./App.vue"
import "@gouvfr/dsfr/dist/dsfr.min.css"
import "@gouvminint/vue-dsfr/dist/vue-dsfr.css"
import VueDsfr from "@gouvminint/vue-dsfr"
import router from "./router/root.ts"
import { createPinia } from "pinia"

// @ts-ignore
import VueMatomo from "vue-matomo"

const pinia = createPinia()

const app = createApp(App)
app.use(pinia)
app.use(router)
app.use(VueDsfr)

// Si Matomo est configuré, on utilise vue-matomo
const matomoUrl = import.meta.env.VITE_MATOMO_URL
const matomoSiteId = import.meta.env.VITE_MATOMO_ID

if (matomoUrl && matomoSiteId) {
  app.use(VueMatomo, {
    host: matomoUrl,
    siteId: Number(matomoSiteId),
    router,
    enableLinkTracking: true,
    debug: import.meta.env.DEV,
  })
}
app.mount("#app")
