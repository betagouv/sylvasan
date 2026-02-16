import { createFetch } from "@vueuse/core"
import { useAuthStore } from "../stores/auth"
import { storeToRefs } from "pinia"
import { useFetch } from "@vueuse/core"

const adjustOptions = (options: RequestInit) => {
  const { access } = storeToRefs(useAuthStore())
  const unsafe = ["POST", "PUT", "PATCH", "DELETE"]
  const headers = new Headers(options.headers || {})
  const isUnsafeMethod = unsafe.includes(
    (options.method || "GET").toUpperCase()
  )

  // Ajout de l'entête d'authorisation si le token est disponible
  if (access.value) headers.set("Authorization", `Bearer ${access.value}`)

  // JSON par défaut si non spécifié
  if (!headers.has("Content-Type") && isUnsafeMethod)
    headers.set("Content-Type", "application/json")
  options.headers = headers

  options.credentials = (import.meta.env.VITE_CREDENTIALS ||
    "same-origin") as RequestCredentials
  return options
}

export const useApiFetch = createFetch({
  baseUrl: import.meta.env.VITE_API_ROOT,
  options: {
    updateDataOnError: true,
    async beforeFetch({ options }) {
      return { options: adjustOptions(options) }
    },
    async onFetchError(ctx) {
      const authStore = useAuthStore()
      const { refresh } = storeToRefs(useAuthStore())
      const shouldRetry = ctx.response?.status === 401 && refresh.value

      if (shouldRetry) {
        const refreshSuccessful = await authStore.refreshToken()

        if (refreshSuccessful) {
          const adjustedOptions = adjustOptions(ctx.context.options)

          const retriedReponse = await useFetch(
            ctx.context.url,
            adjustedOptions
          ).json()
          if (retriedReponse.response.value?.ok)
            return { ...ctx, data: retriedReponse.data.value, error: null }
        }
      }
      return ctx
    },
  },
})
