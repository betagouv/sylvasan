import { createFetch } from "@vueuse/core"
import { useCookies } from "@vueuse/integrations/useCookies"

const cookies = useCookies()

export const useApiFetch = createFetch({
  baseUrl: import.meta.env.VITE_API_ROOT,
  options: {
    async beforeFetch({ options }) {
      const csrfCookie = cookies.get("csrftoken")

      const unsafe = ["POST", "PUT", "PATCH", "DELETE"]
      const isUnsafeMethod = unsafe.includes(
        (options.method || "GET").toUpperCase()
      )

      const headers = new Headers(options.headers || {})

      // Ajout de l'entête nécessaire pour le CSRF si besoin
      if (isUnsafeMethod && csrfCookie) headers.set("X-CSRFToken", csrfCookie)

      // JSON par défaut si non spécifié
      if (!headers.has("Content-Type") && isUnsafeMethod)
        headers.set("Content-Type", "application/json")

      options.headers = headers

      options.credentials = (import.meta.env.VITE_CREDENTIALS ||
        "same-origin") as RequestCredentials

      return { options }
    },
  },
})
