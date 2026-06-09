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

      // @vueuse/core set Content-Type sur defaultFetchOptions.headers (objet brut) avant d'appeler
      // beforeFetch, puis fusionne les deux sources dans le fetch final via un spread :
      //   { ...headersToObject(defaultFetchOptions.headers),   ← 'Content-Type' (majuscule, objet brut)
      //     ...headersToObject(context.options.headers) }      ← 'content-type' (minuscule, Headers.entries())
      // Chrome interprète les deux clés comme deux en-têtes Content-Type distincts.
      // La solution : supprimer Content-Type de context.options.headers pour que defaultFetchOptions
      // reste la seule source, et éviter le doublon.
      headers.delete("Content-Type")

      // Ajout de l'entête nécessaire pour le CSRF si besoin
      if (isUnsafeMethod && csrfCookie) headers.set("X-CSRFToken", csrfCookie)

      options.headers = headers

      options.credentials = (import.meta.env.VITE_CREDENTIALS ||
        "same-origin") as RequestCredentials

      return { options }
    },
  },
})
