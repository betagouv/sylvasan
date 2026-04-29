import { defineStore } from "pinia"
import { ref } from "vue"
import type { LoggedUser } from "@shared-types/api"
import type { VocabularySet } from "@shared-types/survey"
import { useApiFetch } from "../utils/data-fetching"

export const useRootStore = defineStore("root", () => {
  const loggedUser = ref<LoggedUser | null>(null)
  const vocabularies = ref<VocabularySet[]>([])
  const initialDataLoaded = ref<boolean>(false)

  const fetchCsrfToken = async () => {
    await useApiFetch("/auth/csrf/").json()
  }

  const setLoggedUser = (userData: LoggedUser | null) => {
    loggedUser.value = userData
  }

  const fetchLoggedUser = async () => {
    const { data } = await useApiFetch("/auth/me/").json()
    setLoggedUser(data.value)
  }

  const fetchVocabularies = async () => {
    const { data } = await useApiFetch("/vocabularies/").json()
    vocabularies.value = data.value
  }

  const fetchInitialData: () => Promise<undefined> = async () => {
    await fetchCsrfToken()
    await Promise.all([fetchLoggedUser(), fetchVocabularies()])
    initialDataLoaded.value = true
  }

  return {
    setLoggedUser,
    loggedUser,
    vocabularies,
    initialDataLoaded,
    fetchInitialData,
  }
})
