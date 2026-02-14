import { createFetch } from "@vueuse/core"
import { Preferences } from "@capacitor/preferences"

export const useFetch = createFetch({
  baseUrl: import.meta.env.VITE_API_ROOT,
  options: {
    async beforeFetch({ options }) {
      const token = await Preferences.get({ key: "auth_token" })

      const unsafe = ["POST", "PUT", "PATCH", "DELETE"]
      const isUnsafeMethod = unsafe.includes(
        (options.method || "GET").toUpperCase()
      )

      const headers = new Headers(options.headers || {})

      // Ajout de l'entête d'authorisation si le token est disponible
      if (isUnsafeMethod && token)
        headers.set("Authorization", `Bearer ${token}`)

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
