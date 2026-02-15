import { createFetch } from "@vueuse/core"
import { useAuthStore } from "../stores/auth"
import { storeToRefs } from "pinia"

export const useApiFetch = createFetch({
  baseUrl: import.meta.env.VITE_API_ROOT,
  options: {
    async beforeFetch({ options }) {
      const { access } = storeToRefs(useAuthStore())
      const unsafe = ["POST", "PUT", "PATCH", "DELETE"]
      const isUnsafeMethod = unsafe.includes(
        (options.method || "GET").toUpperCase()
      )

      const headers = new Headers(options.headers || {})

      // Ajout de l'entête d'authorisation si le token est disponible
      if (access.value) headers.set("Authorization", `Bearer ${access.value}`)

      // JSON par défaut si non spécifié
      if (!headers.has("Content-Type") && isUnsafeMethod)
        headers.set("Content-Type", "application/json")

      options.headers = headers

      options.credentials = (import.meta.env.VITE_CREDENTIALS ||
        "same-origin") as RequestCredentials

      return { options }
    },
    async onFetchError({ data, response, context, execute }) {
      const authStore = useAuthStore()
      const { refresh } = storeToRefs(useAuthStore())
      if (response?.status === 403 && refresh.value) {
        const refreshSuccessful = await authStore.refreshToken()

        if (refreshSuccessful) return await execute()
      }
      return { data, response, context }
    },
  },
})
