import { defineStore } from "pinia"
import { Preferences } from "@capacitor/preferences"
import { useApiFetch } from "../utils/data-fetching"
import type { SurveySchema } from "@shared-types/survey"

const SURVEYS_KEY = "surveys_cache"
const SURVEYS_SYNCED_AT_KEY = "surveys_synced_at"

export interface Survey {
  id: number
  title: string
  jsonSchema: SurveySchema
  surveyType: string
}

export const useSurveysStore = defineStore("surveys", {
  state: () => ({
    surveys: [] as Survey[],
    syncedAt: null as string | null,
    syncing: false,
  }),

  getters: {
    getSurveyById: (s) => (id: number) =>
      s.surveys.find((survey) => survey.id === id),
  },

  actions: {
    async loadFromStorage() {
      const [surveysRaw, syncedAt] = await Promise.all([
        Preferences.get({ key: SURVEYS_KEY }),
        Preferences.get({ key: SURVEYS_SYNCED_AT_KEY }),
      ])
      if (surveysRaw.value) {
        this.surveys = JSON.parse(surveysRaw.value)
      }
      this.syncedAt = syncedAt.value
    },

    async persist() {
      await Promise.all([
        Preferences.set({
          key: SURVEYS_KEY,
          value: JSON.stringify(this.surveys),
        }),
        Preferences.set({
          key: SURVEYS_SYNCED_AT_KEY,
          value: new Date().toISOString(),
        }),
      ])
    },

    async sync() {
      // À utiliser lors d'un pull to refresh par exemple
      this.syncing = true
      try {
        const { data, response } = await useApiFetch("/mobile/surveys/")
          .get()
          .json()
        if (response.value?.ok) {
          this.surveys = data.value
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
