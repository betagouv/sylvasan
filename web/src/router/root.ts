import { createWebHistory, createRouter } from "vue-router"
import type {
  Router,
  NavigationGuardNext,
  RouteLocationNormalizedLoaded,
  RouteLocationNormalizedGeneric,
} from "vue-router"
import type { StoreGeneric } from "pinia"

import { ref } from "vue"

import { useStorage } from "@vueuse/core"

import { useRootStore } from "../stores/root.ts"

import HomeView from "../components/HomeView.vue"
import LoginView from "../components/LoginView.vue"
import DashboardView from "../components/DashboardView.vue"

const routes = [
  {
    path: "/",
    name: "HomeView",
    component: HomeView,
    meta: {
      home: true,
    },
  },
  {
    path: "/s-identifier",
    name: "LoginView",
    component: LoginView,
    meta: {
      title: "S'identifier",
      omitIfLoggedIn: true,
      sitemap: true,
    },
  },
  {
    path: "/dashboard",
    name: "DashboardView",
    component: DashboardView,
    meta: {
      authenticationRequired: true,
    },
  },
]

const previousRoute = ref<RouteLocationNormalizedGeneric | null>(null)
type SylvaSanRouter = Router & {
  getPreviousRoute?: () => typeof previousRoute
}

const router: SylvaSanRouter = createRouter({
  history: createWebHistory(),
  routes,
})

// This utility function allows us to find the previous route
router.getPreviousRoute = () => previousRoute

const chooseAuthorisedRoute = async (
  to: RouteLocationNormalizedGeneric,
  from: RouteLocationNormalizedGeneric,
  next: NavigationGuardNext,
  store: StoreGeneric
) => {
  // 1) vérifie si les données initiales sont chargées, sinon le fait avant toute chose
  // if (!store.initialDataLoaded) {
  //   store
  //     .fetchInitialData()
  //     .then(() => chooseAuthorisedRoute(to, from, next, store))
  //     .catch((e) => {
  //       console.error(`An error occurred: ${e}`)
  //       next({ name: "LandingPage" })
  //     })
  //   return

  // 2) vérifie les règles de redirection
  // if (to.meta?.home) {
  //   next({ name: store.loggedUser ? "DashboardPage" : "LandingPage" })
  //   return
  // }
  if (to.meta.omitIfLoggedIn && store.loggedUser) {
    next(to.query.next?.toString() || { name: "HelloWorld" })
    return
  }
  const authenticationCheck =
    !to.meta.authenticationRequired || store.loggedUser
  const globalRoles =
    store.loggedUser?.globalRoles?.map((x: any) => x.name) || []
  const roles = [...globalRoles]
  const roleCheck =
    !to.meta.requiredRoles ||
    (to.meta.requiredRoles as []).some((x) => roles.indexOf(x) > -1)

  if (!authenticationCheck)
    next({ name: "LoginView", query: { next: to.path } })
  else if (!roleCheck) next({ name: "DashboardView" })
  else next()
}

const objectIsEmpty = (obj: object) => {
  // https://stackoverflow.com/a/59787784/3845770
  for (let i in obj) return false
  return true
}

const ensureDefaultQueryParams = (
  route: RouteLocationNormalizedLoaded,
  next: NavigationGuardNext
) => {
  let needsRedirection = false
  const savedQuery = useStorage(route.path, {})
  if (objectIsEmpty(route.query) && !objectIsEmpty(savedQuery.value)) {
    route.query = savedQuery.value
    needsRedirection = true
  }
  if (route.meta.defaultQueryParams) {
    for (const [queryParam, value] of Object.entries(
      route.meta.defaultQueryParams
    ))
      if (!(queryParam in route.query)) {
        route.query[queryParam] = value
        needsRedirection = true
      }
  }
  if (!needsRedirection) return true
  next(route)
  return false
}

router.beforeEach((to, from, next) => {
  // sauvegarder la query de la page précédente
  if (from.meta.saveQuery) {
    const savedQuery = useStorage(from.path, {})
    savedQuery.value = from.query
  }
  // preparer la page suivante
  const store = useRootStore()
  previousRoute.value = from
  if (ensureDefaultQueryParams(to, next))
    chooseAuthorisedRoute(to, from, next, store)
})

export default router
