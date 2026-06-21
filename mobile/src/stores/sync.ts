import { defineStore } from "pinia"
import { Preferences } from "@capacitor/preferences"
import { useSurveysStore } from "./surveys"
import { useResponsesStore } from "./responses"
import { useVocabulariesStore } from "./vocabularies"

const SYNC_AT_KEY = "sync_synced_at"

export const useSyncStore = defineStore("sync", {
  state: () => ({
    syncedAt: null as string | null,
    syncing: false,
  }),

  actions: {
    async loadFromStorage() {
      const { value } = await Preferences.get({ key: SYNC_AT_KEY })
      this.syncedAt = value
    },

    async syncAll() {
      this.syncing = true
      try {
        await Promise.all([
          useSurveysStore().sync(),
          useResponsesStore().sync(),
          useVocabulariesStore().sync(),
        ])
        this.syncedAt = new Date().toISOString()
        await Preferences.set({ key: SYNC_AT_KEY, value: this.syncedAt })
      } finally {
        this.syncing = false
      }
    },

    async bootstrap() {
      await Promise.all([
        this.loadFromStorage(),
        useSurveysStore().loadFromStorage(),
        useResponsesStore().loadFromStorage(),
        useVocabulariesStore().loadFromStorage(),
      ])
      try {
        await this.syncAll()
      } catch {
        // Hors ligne — on utilise le cache
      }
    },
  },
})
