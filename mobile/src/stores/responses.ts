import { defineStore } from "pinia"
import { Preferences } from "@capacitor/preferences"
import { useApiFetch } from "../utils/data-fetching"
import type { ResponseFull, LocalResponse } from "@shared-types/response"
import { useAuthStore } from "../stores/auth"
import { storeToRefs } from "pinia"

const LOCAL_RESPONSES_KEY = "local_responses" // Draft et pending
const RESPONSES_KEY = "responses_cache"
const RESPONSES_SYNCED_AT_KEY = "responses_synced_at"

export const useResponsesStore = defineStore("responses", {
  state: () => ({
    localResponses: [] as LocalResponse[], // Draft et pending
    responses: [] as ResponseFull[],
    syncedAt: null as string | null,
    syncing: false,
  }),

  getters: {
    drafts: (state) => state.localResponses.filter((r) => r.status === "draft"),
    pending: (state) =>
      state.localResponses.filter((r) => r.status === "pending"),

    getResponseById: (state) => (id: number) =>
      state.responses.find((response) => response.id === id),

    allResponses: (state) => [...state.localResponses, ...state.responses],

    getByLocalId: (state) => (localId: string) =>
      state.localResponses.find((r) => r.localId === localId),

    getDraftsBySurveyId: (state) => (surveyId: number) =>
      state.localResponses.filter(
        (r) => r.surveyId === surveyId && r.status === "draft"
      ),
  },

  actions: {
    async loadFromStorage() {
      const [localRaw, syncedRaw, syncedAt] = await Promise.all([
        Preferences.get({ key: LOCAL_RESPONSES_KEY }),
        Preferences.get({ key: RESPONSES_KEY }),
        Preferences.get({ key: RESPONSES_SYNCED_AT_KEY }),
      ])
      if (localRaw.value) this.localResponses = JSON.parse(localRaw.value)
      if (syncedRaw.value) this.responses = JSON.parse(syncedRaw.value)
      this.syncedAt = syncedAt.value
    },

    async persistLocal() {
      await Preferences.set({
        key: LOCAL_RESPONSES_KEY,
        value: JSON.stringify(this.localResponses),
      })
    },

    async persist() {
      await Promise.all([
        Preferences.set({
          key: RESPONSES_KEY,
          value: JSON.stringify(this.responses),
        }),
        Preferences.set({
          key: RESPONSES_SYNCED_AT_KEY,
          value: new Date().toISOString(),
        }),
      ])
    },

    async upsertDraft(
      surveyId: number,
      surveyTitle: string,
      data: Record<string, unknown>,
      localId?: string
    ): Promise<string> {
      const now = new Date().toISOString()
      const existing = localId
        ? this.localResponses.find((r) => r.localId === localId)
        : null

      if (existing) {
        existing.data = data
        existing.modificationDate = now
        await this.persistLocal()
        return existing.localId
      } else {
        const newLocalId = crypto.randomUUID()
        this.localResponses.push({
          localId: newLocalId,
          surveyId,
          surveyTitle,
          status: "draft",
          data,
          context: {},
          creationDate: now,
          modificationDate: now,
        })
        await this.persistLocal()
        return newLocalId
      }
    },

    async submitResponse(localId: string) {
      const authStore = useAuthStore()
      const { loggedUser } = storeToRefs(authStore)

      const localResponse = this.localResponses.find(
        (r) => r.localId === localId
      )
      if (!localResponse) return false

      try {
        const { response } = await useApiFetch("/responses/")
          .post({
            survey: localResponse.surveyId,
            data: localResponse.data,
            respondant: loggedUser.value?.id,
          })
          .json()

        if (response.value?.ok) {
          // On enleve la réponse locale car elle a bien été sauvegardé dans le backend
          this.deleteDraft(localResponse.localId)
          await this.sync()
          return true
        } else {
          localResponse.status = "pending"
          localResponse.modificationDate = new Date().toISOString()
          await this.persistLocal()
          return false
        }
      } catch {
        // Pas de connexion
        localResponse.status = "pending"
        localResponse.modificationDate = new Date().toISOString()
        await this.persistLocal()
        return false
      }
    },

    async deleteDraft(localId: string) {
      this.localResponses = this.localResponses.filter(
        (r) => r.localId !== localId
      )
      await this.persistLocal()
    },

    async retryPending() {
      const pendingIds = this.pending.map((r) => r.localId)
      const results = await Promise.allSettled(
        pendingIds.map((localId) => this.submitResponse(localId))
      )
      // Retourne le nombre de soumissions réussies
      return results.filter((r) => r.status === "fulfilled" && r.value === true)
        .length
    },

    async sync() {
      // À utiliser lors d'un pull to refresh par exemple
      this.syncing = true
      try {
        await this.retryPending()
        const { data, response } = await useApiFetch("/mobile/responses/")
          .get()
          .json()
        if (response.value?.ok) {
          this.responses = data.value
          this.syncedAt = new Date().toISOString()
          await this.persist()
        }
      } finally {
        this.syncing = false
      }
    },

    async bootstrap() {
      await this.loadFromStorage()
      try {
        await this.sync()
      } catch {
        // On échoue en silence : on est peut-être hors ligne
      }
    },
  },
})
