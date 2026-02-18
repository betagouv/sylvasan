import { createRouter, createWebHistory } from "@ionic/vue-router"
import LoginPage from "../pages/LoginPage.vue"
import type { RouteRecordRaw } from "vue-router"
import { useAuthStore } from "../stores/auth"
import AppShell from "../pages/AppShell.vue"

import ProjectsPage from "../pages/ProjectsPage.vue"
import MapsPage from "../pages/MapsPage.vue"
import ProfilePage from "../pages/ProfilePage.vue"

const routes: Array<RouteRecordRaw> = [
  {
    path: "/",
    redirect: "/projets",
  },
  {
    path: "/",
    component: AppShell,
    children: [
      {
        path: "",
        redirect: "/projets",
      },
      {
        path: "projets",
        name: "ProjectsPage",
        component: ProjectsPage,
      },
      {
        path: "gestion-des-cartes",
        name: "MapsPage",
        component: MapsPage,
      },
      {
        path: "mon-profil",
        name: "ProfilePage",
        component: ProfilePage,
      },
    ],
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
  if (!authStore.ready) await authStore.bootstrap()
  if (!authStore.isLoggedIn && to.name !== "LoginPage")
    return { name: "LoginPage" }
  if (authStore.isLoggedIn && to.name === "LoginPage")
    return { name: "ProjectsPage" }
})

export default router
