import { defineStore } from "pinia"
import { ref } from "vue"
import type { LoggedUser } from "../types/api"
import { useApiFetch } from "../utils/data-fetching"

export const useRootStore = defineStore("root", () => {
  const loggedUser = ref<LoggedUser | null>(null)
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

  const fetchInitialData: () => Promise<undefined> = async () => {
    await fetchCsrfToken()
    await fetchLoggedUser()
    initialDataLoaded.value = true
  }

  return {
    setLoggedUser,
    loggedUser,
    initialDataLoaded,
    fetchInitialData,
  }
})
