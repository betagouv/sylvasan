import { defineStore } from "pinia"
import { Preferences } from "@capacitor/preferences"
import { useApiFetch } from "../utils/data-fetching"

const ACCESS_KEY = "auth_access"
const REFRESH_KEY = "auth_refresh"

export const useAuthStore = defineStore("auth", {
  state: () => ({
    access: null as string | null,
    refresh: null as string | null,
    ready: false,
  }),

  getters: {
    isLoggedIn: (s) => !!s.access,
  },

  actions: {
    async loadFromStorage() {
      const [accessToken, refreshToken] = await Promise.all([
        Preferences.get({ key: ACCESS_KEY }),
        Preferences.get({ key: REFRESH_KEY }),
      ])
      this.access = accessToken.value
      this.refresh = refreshToken.value
    },

    async persist() {
      if (this.access)
        await Preferences.set({ key: ACCESS_KEY, value: this.access })
      if (this.refresh)
        await Preferences.set({ key: REFRESH_KEY, value: this.refresh })
    },

    async clearStorage() {
      await Preferences.remove({ key: ACCESS_KEY })
      await Preferences.remove({ key: REFRESH_KEY })
    },

    async login(username: string, password: string) {
      const { response, data } = await useApiFetch("/mobile/token/")
        .post({ username, password })
        .json()

      if (!response.value?.ok) throw new Error("login failed")

      this.access = data.value.access
      this.refresh = data.value.refresh

      await this.persist()
    },

    async refreshToken() {
      if (!this.refresh) return false

      const { response, data } = await useApiFetch("/mobile/token/refresh/")
        .post({ refresh: this.refresh })
        .json()

      if (!response.value?.ok) {
        await this.logout()
        return false
      }

      this.access = data.value.access
      await this.persist()

      return true
    },

    async logout() {
      this.access = null
      this.refresh = null
      await this.clearStorage()
    },

    async bootstrap() {
      await this.loadFromStorage()

      // Au démarrage de l'app on fait un refresh du token
      if (this.refresh) await this.refreshToken()

      this.ready = true
    },
  },
})
