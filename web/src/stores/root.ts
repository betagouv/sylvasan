import { defineStore } from "pinia"
import { ref } from "vue"
import type { LoggedUser } from "@shared-types/api"
import type { VocabularySet } from "@shared-types/survey"
import { useApiFetch } from "../utils/data-fetching"

export const useRootStore = defineStore("root", () => {
  const loggedUser = ref<LoggedUser | null>(null)
  const vocabularies = ref<VocabularySet[]>([])
  const vocabularyDetails = ref<Record<string, VocabularySet>>({})
  const initialDataLoaded = ref<boolean>(false)

  const fetchCsrfToken = async () => {
    await useApiFetch("/auth/csrf/").json()
  }

  const setLoggedUser = (userData: LoggedUser | null) => {
    loggedUser.value = userData
    vocabularies.value = userData?.vocabularies ?? []
  }

  const fetchLoggedUser = async () => {
    const { data } = await useApiFetch("/auth/me/").json()
    setLoggedUser(data.value)
  }

  const fetchVocabularyDetail = async (code: string) => {
    if (vocabularyDetails.value[code]) return
    const { data, response } = await useApiFetch(`/vocabularies/${code}/`).json()
    if (response.value?.ok) vocabularyDetails.value[code] = data.value
  }

  const fetchInitialData: () => Promise<undefined> = async () => {
    await fetchCsrfToken()
    await fetchLoggedUser()
    initialDataLoaded.value = true
  }

  return {
    setLoggedUser,
    loggedUser,
    vocabularies,
    vocabularyDetails,
    fetchVocabularyDetail,
    initialDataLoaded,
    fetchInitialData,
  }
})
