import { defineStore } from "pinia"
import { Preferences } from "@capacitor/preferences"
import { useApiFetch } from "../utils/data-fetching"
import type { VocabularySet } from "@shared-types/survey"

const VOCABULARIES_KEY = "vocabularies_cache"

export const useVocabulariesStore = defineStore("vocabularies", {
  state: () => ({
    vocabularySets: [] as VocabularySet[],
    syncedAt: null as string | null,
    syncing: false,
  }),

  getters: {
    getByCode: (state) => (code: string) =>
      state.vocabularySets.find((v) => v.code === code),

    getEntries: (state) => (code: string) =>
      state.vocabularySets.find((v) => v.code === code)?.entries ?? [],
  },

  actions: {
    async loadFromStorage() {
      const raw = await Preferences.get({ key: VOCABULARIES_KEY })
      if (raw.value) this.vocabularySets = JSON.parse(raw.value)
    },

    async persist() {
      await Preferences.set({
        key: VOCABULARIES_KEY,
        value: JSON.stringify(this.vocabularySets),
      })
    },

    async sync() {
      this.syncing = true
      try {
        const { data, response } = await useApiFetch("/vocabularies/")
          .get()
          .json()
        if (response.value?.ok) {
          this.vocabularySets = data.value
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
        // Hors ligne, usage du cache
      }
    },
  },
})
