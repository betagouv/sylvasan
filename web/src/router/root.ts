import { createWebHistory, createRouter } from "vue-router"
import type {
  Router,
  RouteLocationNormalizedLoaded,
  RouteLocationNormalizedGeneric,
} from "vue-router"
import type { StoreGeneric } from "pinia"
import { ref } from "vue"
import { useStorage } from "@vueuse/core"
import { useRootStore } from "../stores/root.ts"
import { routes, handleHotUpdate } from "vue-router/auto-routes"
import NotFoundPage from "../pages/NotFoundPage.vue"

const previousRoute = ref<RouteLocationNormalizedGeneric | null>(null)
type SylvaSanRouter = Router & {
  getPreviousRoute?: () => typeof previousRoute
}

const extendedRoutes = [
  ...routes,
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: NotFoundPage,
  },
]

const router: SylvaSanRouter = createRouter({
  history: createWebHistory("/"),
  routes: extendedRoutes,
  scrollBehavior(to, from, savedPosition) {
    if (to.hash) return { el: to.hash }

    // Ne pas scroller en haut si c'est simplement un changement de queryparam
    if (from.name === to.name && from.fullPath !== to.fullPath) return

    if (savedPosition) return savedPosition
    return { top: 0 }
  },
})

router.getPreviousRoute = () => previousRoute

const chooseAuthorisedRoute = async (
  to: RouteLocationNormalizedGeneric,
  store: StoreGeneric
) => {
  // Vérifie si les données initiales sont chargées, sinon le fait avant toute chose
  if (!store.initialDataLoaded) {
    try {
      await store.fetchInitialData()
    } catch (e) {
      console.error(`An error occurred: ${e}`)
      return { name: "/" }
    }
  }

  // Vérifie les règles de redirection
  if (to.meta?.home) {
    return {
      name: store.loggedUser ? "/DashboardPage" : "/HomePage",
    }
  }

  if (to.meta.omitIfLoggedIn && store.loggedUser) {
    return to.query.next?.toString() || { name: "/" }
  }

  const authenticationCheck =
    !to.meta.authenticationRequired || store.loggedUser

  if (!authenticationCheck) {
    return {
      name: "/LoginPage",
      query: { next: to.path },
    }
  }

  return true
}

const objectIsEmpty = (obj: object) => {
  // https://stackoverflow.com/a/59787784/3845770
  for (let _ in obj) return false
  return true
}

const ensureDefaultQueryParams = (route: RouteLocationNormalizedLoaded) => {
  let needsRedirection = false
  const savedQuery = useStorage(route.path, {})

  const newQuery = { ...route.query }

  if (objectIsEmpty(route.query) && !objectIsEmpty(savedQuery.value)) {
    Object.assign(newQuery, savedQuery.value)
    needsRedirection = true
  }

  if (route.meta.defaultQueryParams) {
    for (const [queryParam, value] of Object.entries(
      route.meta.defaultQueryParams
    )) {
      if (!(queryParam in newQuery)) {
        newQuery[queryParam] = value
        needsRedirection = true
      }
    }
  }

  if (!needsRedirection) return true

  return {
    ...route,
    query: newQuery,
  }
}

router.beforeEach(async (to, from) => {
  // Sauvegarde de la query précédente
  if (from.meta.saveQuery) {
    const savedQuery = useStorage(from.path, {})
    savedQuery.value = from.query
  }

  const store = useRootStore()
  previousRoute.value = from

  // Mettre les query params
  const queryResult = ensureDefaultQueryParams(to)
  if (queryResult !== true) return queryResult

  // Retourner la route autorisée
  return await chooseAuthorisedRoute(to, store)
})

if (import.meta.hot) {
  handleHotUpdate(router)
}

export default router
