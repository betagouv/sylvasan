import { ref, watch, onBeforeUnmount } from "vue"
import type { ShallowRef } from "vue"
import maplibregl from "maplibre-gl"
import { useApiFetch } from "../utils/data-fetching"
import { useAuthStore } from "../stores/auth"
import type { ResponseGeo } from "@shared-types/response"
import type { PinData } from "./useMapPins"

const COLOR_OWN = "#000091"      // --blue-france-sun-113
const COLOR_OTHER = "#7ab1e8"    // bleu clair pour les réponses des collègues

function toPin(r: ResponseGeo): PinData {
  return {
    responseId: r.id,
    surveyId: r.surveyId,
    isLocal: false,
    lat: r.lat,
    lon: r.lon,
    surveyTitle: r.surveyTitle ?? "",
    date: r.creationDate,
    status: r.status,
    respondant: r.respondant,
  }
}

export function useGeoPins(mapRef: ShallowRef<maplibregl.Map | null>) {
  const authStore = useAuthStore()
  const selectedPin = ref<PinData | null>(null)
  const showSearchHere = ref(false)
  const loading = ref(false)

  const markers: maplibregl.Marker[] = []

  const clearMarkers = () => {
    markers.forEach((m) => m.remove())
    markers.length = 0
  }

  const renderMarkers = (mapInstance: maplibregl.Map, pins: PinData[]) => {
    const currentUserId = authStore.loggedUser?.id
    clearMarkers()
    for (const pin of pins) {
      const isOwn = pin.respondant?.id === currentUserId
      const marker = new maplibregl.Marker({ color: isOwn ? COLOR_OWN : COLOR_OTHER })
        .setLngLat([pin.lon, pin.lat])
        .addTo(mapInstance)

      marker.getElement().addEventListener("click", (e) => {
        e.stopPropagation()
        selectedPin.value =
          selectedPin.value?.responseId === pin.responseId ? null : pin
      })

      markers.push(marker)
    }
  }

  const fetchPins = async () => {
    const map = mapRef.value
    if (!map || loading.value) return

    loading.value = true
    selectedPin.value = null

    const b = map.getBounds()
    const { data, error } = await useApiFetch(
      `/mobile/responses/geo/?south=${b.getSouth()}&west=${b.getWest()}&north=${b.getNorth()}&east=${b.getEast()}`
    ).json<ResponseGeo[]>()

    loading.value = false
    showSearchHere.value = false

    if (error.value || !data.value || !mapRef.value) return

    renderMarkers(mapRef.value, data.value.map(toPin))
  }

  watch(mapRef, (mapInstance) => {
    if (mapInstance) {
      fetchPins()

      mapInstance.on("moveend", () => {
        showSearchHere.value = true
      })

      mapInstance.on("click", () => {
        selectedPin.value = null
      })
    } else {
      clearMarkers()
      selectedPin.value = null
      showSearchHere.value = false
      loading.value = false
    }
  })

  onBeforeUnmount(clearMarkers)

  return { selectedPin, showSearchHere, loading, fetchPins }
}
