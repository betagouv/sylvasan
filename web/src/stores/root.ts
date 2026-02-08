import { defineStore } from "pinia"
import { ref } from "vue"

export const useRootStore = defineStore("root", () => {
  const loggedUser = ref<object | null>(null)
  const initialDataLoaded = ref<boolean>(false)

  const fetchInitialData: () => Promise<undefined> = async () => {
    console.log("Fetch initial data")
    initialDataLoaded.value = true
  }

  return { loggedUser, initialDataLoaded, fetchInitialData }
})
