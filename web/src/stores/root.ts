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

  const { data: meData, execute: executeFetchMe } = useApiFetch("/auth/me/", {
    immediate: false,
  }).json()

  const fetchLoggedUser = async () => {
    await executeFetchMe()
    setLoggedUser(meData.value)
  }

  // NOTE: Ce n'est pas optimal d'appeller /me juste pour rafraîchir les vocabulaires.
  // À terme, un endpoint dédié pourrait être utilisé
  const refreshVocabularies = async () => {
    await executeFetchMe()
    if (meData.value?.vocabularies) vocabularies.value = meData.value.vocabularies
  }

  const fetchVocabularyDetail = async (code: string) => {
    if (vocabularyDetails.value[code]) return
    const { data, response } = await useApiFetch(
      `/vocabularies/${code}/`
    ).json()
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
    refreshVocabularies,
    initialDataLoaded,
    fetchInitialData,
  }
})
