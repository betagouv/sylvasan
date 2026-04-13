import { defineStore } from "pinia"
import { Preferences } from "@capacitor/preferences"
import { useApiFetch } from "../utils/data-fetching"
import type { ResponseFull } from "@shared-types/response"

const RESPONSES_KEY = "responses_cache"
const RESPONSES_SYNCED_AT_KEY = "responses_synced_at"

export const useResponsesStore = defineStore("responses", {
  state: () => ({
    responses: [] as ResponseFull[],
    syncedAt: null as string | null,
    syncing: false,
  }),

  getters: {
    getResponseById: (s) => (id: number) =>
      s.responses.find((response) => response.id === id),
  },

  actions: {
    async loadFromStorage() {
      const [responsesRaw, syncedAt] = await Promise.all([
        Preferences.get({ key: RESPONSES_KEY }),
        Preferences.get({ key: RESPONSES_SYNCED_AT_KEY }),
      ])
      if (responsesRaw.value) {
        this.responses = JSON.parse(responsesRaw.value)
      }
      this.syncedAt = syncedAt.value
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

    async sync() {
      // À utiliser lors d'un pull to refresh par exemple
      this.syncing = true
      try {
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
