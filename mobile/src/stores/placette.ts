import { defineStore } from "pinia"
import { ref } from "vue"
import type { PlacetteData } from "../composables/useGeoPins"

export const usePlacetteStore = defineStore("placette", () => {
  const currentPlacette = ref<PlacetteData | null>(null)
  return { currentPlacette }
})
