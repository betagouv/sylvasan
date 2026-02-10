import { createApp } from "vue"
import "./style.css"
import App from "./App.vue"
import { IonicVue } from "@ionic/vue"
import router from "./router/root"
// import VueDsfr from "@gouvminint/vue-dsfr"

import "@ionic/vue/css/core.css"
import "@ionic/vue/css/normalize.css"
import "@ionic/vue/css/structure.css"
import "@ionic/vue/css/typography.css"

const app = createApp(App).use(IonicVue).use(router)

router.isReady().then(() => {
  app.mount("#app")
})
