import { createRouter, createWebHistory } from "@ionic/vue-router"
import LoginPage from "../pages/LoginPage.vue"
import type { RouteRecordRaw } from "vue-router"
import { useAuthStore } from "../stores/auth"
import AppShell from "../pages/AppShell.vue"

import SurveyListPage from "../pages/SurveyListPage.vue"
import SurveyPage from "../pages/SurveyPage.vue"
import MapsPage from "../pages/MapsPage/index.vue"
import ProfilePage from "../pages/ProfilePage.vue"
import MapDownloadPage from "../pages/MapDownloadPage.vue"

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
        name: "SurveyListPage",
        component: SurveyListPage,
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
  {
    path: "/telecharger-une-carte",
    name: "MapDownloadPage",
    component: MapDownloadPage,
  },
  {
    path: "/enquete/:id",
    name: "SurveyPage",
    component: SurveyPage,
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
    return { name: "SurveyListPage" }
})

export default router
