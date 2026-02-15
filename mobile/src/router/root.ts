import { createRouter, createWebHistory } from "@ionic/vue-router"
import HomePage from "../pages/HomePage.vue"
import LoginPage from "../pages/LoginPage.vue"
import type { RouteRecordRaw } from "vue-router"
import { useAuthStore } from "../stores/auth"
import { storeToRefs } from "pinia"
const routes: Array<RouteRecordRaw> = [
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
  const authStore = useAuthStore()
  if (!authStore.isLoggedIn && to.name !== "LoginPage")
    return { name: "LoginPage" }
  if (authStore.isLoggedIn && to.name === "LoginPage")
    return { name: "HomePage" }
})

export default router
