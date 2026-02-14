import { createRouter, createWebHistory } from "@ionic/vue-router"
import HomePage from "../pages/HomePage.vue"
import LoginPage from "../pages/LoginPage.vue"
import { Preferences } from "@capacitor/preferences"

const routes = [
  {
    path: "/",
    redirect: "/accueil",
  },
  {
    path: "/accueil",
    name: "HomePage",
    component: HomePage,
  },
  {
    path: "/s-identifier",
    name: "LoginPage",
    component: LoginPage,
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(async (to) => {
  const token = await Preferences.get({ key: "auth_token" })

  if (!token.value && to.name !== "LoginPage") {
    return { name: "LoginPage" }
  }

  if (token.value && to.name === "LoginPage") {
    return { name: "HomePage" }
  }
})

export default router
