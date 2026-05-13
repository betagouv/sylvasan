import { defineStore } from "pinia"
import { Preferences } from "@capacitor/preferences"
import { Browser } from "@capacitor/browser"
import { useApiFetch } from "../utils/data-fetching"
import type { LoggedUser } from "@shared-types/api"
import { useSurveysStore } from "./surveys"

const ACCESS_KEY = "auth_access"
const REFRESH_KEY = "auth_refresh"
const USER_KEY = "auth_user"
const DSF_NONCE_KEY = "dsf_oauth_nonce"
const DSF_REDIRECT_URI = "sylvasan://oauth/callback"

export const useAuthStore = defineStore("auth", {
  state: () => ({
    access: null as string | null,
    refresh: null as string | null,
    ready: false,
    loggedUser: null as LoggedUser | null,
  }),

  getters: {
    isLoggedIn: (s) => !!s.access,
  },

  actions: {
    async loadFromStorage() {
      const [accessToken, refreshToken, user] = await Promise.all([
        Preferences.get({ key: ACCESS_KEY }),
        Preferences.get({ key: REFRESH_KEY }),
        Preferences.get({ key: USER_KEY }),
      ])
      this.access = accessToken.value
      this.refresh = refreshToken.value
      this.loggedUser = user.value ? JSON.parse(user.value) : null
    },

    async persist() {
      const ops: Promise<void>[] = []
      if (this.access)
        ops.push(Preferences.set({ key: ACCESS_KEY, value: this.access }))
      if (this.refresh)
        ops.push(Preferences.set({ key: REFRESH_KEY, value: this.refresh }))
      if (this.loggedUser)
        ops.push(
          Preferences.set({
            key: USER_KEY,
            value: JSON.stringify(this.loggedUser),
          })
        )
      await Promise.all(ops)
    },

    async clearStorage() {
      await Promise.all([
        Preferences.remove({ key: ACCESS_KEY }),
        Preferences.remove({ key: REFRESH_KEY }),
        Preferences.remove({ key: USER_KEY }),
      ])
    },

    async fetchUser() {
      const { response, data } = await useApiFetch("/auth/me/").get().json()
      if (!response.value?.ok) return
      this.loggedUser = data.value

      // Note: Je suis pas convaincu d'avoir la sauvegarde directement ici, à
      // voir si ce serait mieux de la séparer
      await Preferences.set({
        key: USER_KEY,
        value: JSON.stringify(data.value),
      })
    },

    async login(username: string, password: string) {
      const { response, data } = await useApiFetch("/mobile/token/")
        .post({ username, password })
        .json()

      if (!response.value?.ok) throw new Error("login failed")

      this.access = data.value.access
      this.refresh = data.value.refresh

      await Promise.all([this.persist(), this.fetchUser()])

      // Fetch les enquêtes
      const surveyStore = useSurveysStore()
      await surveyStore.sync()
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

    async loginWithDsf() {
      const nonce = crypto.randomUUID()
      await Preferences.set({ key: DSF_NONCE_KEY, value: nonce })

      const authUrl = new URL(import.meta.env.VITE_DSF_AUTHORIZATION_URL)
      authUrl.searchParams.set("client_id", import.meta.env.VITE_DSF_CLIENT_ID)
      authUrl.searchParams.set("redirect_uri", DSF_REDIRECT_URI)
      authUrl.searchParams.set("response_type", "code")
      authUrl.searchParams.set("scope", "openid")
      authUrl.searchParams.set("nonce", nonce)

      await Browser.open({ url: authUrl.toString() })
    },

    async handleDsfCallback(callbackUrl: string) {
      const code = new URL(callbackUrl).searchParams.get("code")
      const { value: nonce } = await Preferences.get({ key: DSF_NONCE_KEY })
      await Preferences.remove({ key: DSF_NONCE_KEY })

      if (!code || !nonce) throw new Error("Missing code or nonce")

      const platformBase = import.meta.env.VITE_API_ROOT.replace(/\/api$/, "")
      const res = await fetch(`${platformBase}/dsf/oauth/app/callback/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, nonce }),
      })

      if (!res.ok) throw new Error("DSF OAuth exchange failed")

      const data = await res.json()
      this.access = data.access
      this.refresh = data.refresh

      await Promise.all([this.persist(), this.fetchUser()])

      const surveyStore = useSurveysStore()
      await surveyStore.sync()
    },

    async logout() {
      this.access = null
      this.refresh = null
      this.loggedUser = null
      await this.clearStorage()
    },

    async bootstrap() {
      await this.loadFromStorage()

      // Au démarrage de l'app on fait un refresh du token
      if (this.refresh) {
        const refreshed = await this.refreshToken()
        if (refreshed) this.fetchUser().catch(() => {})
      }

      this.ready = true
    },
  },
})
