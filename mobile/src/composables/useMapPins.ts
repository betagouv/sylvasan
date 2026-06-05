import { ref, computed, watch, onBeforeUnmount } from "vue"
import type { ShallowRef } from "vue"
import maplibregl from "maplibre-gl"
import { storeToRefs } from "pinia"
import { useResponsesStore } from "../stores/responses"
import { useSurveysStore } from "../stores/surveys"
import type { LocalResponse, ResponseFull } from "@shared-types/response"
import type { SurveySchema } from "@shared-types/survey"

export interface PinData {
  responseId: string | number
  isLocal: boolean
  lat: number
  lon: number
  surveyTitle: string
  date: string
  status: string
}

function getSchema(
  response: LocalResponse | ResponseFull,
  getSurveyById: (id: number) => any
): SurveySchema | null {
  if ("localId" in response) {
    return (
      getSurveyById((response as LocalResponse).surveyId)?.jsonSchema ?? null
    )
  }
  return (response as any).survey?.jsonSchema ?? null
}

function getSurveyTitle(response: LocalResponse | ResponseFull): string {
  if ("localId" in response) return (response as LocalResponse).surveyTitle
  return (response as any).survey?.title ?? ""
}

export function useMapPins(mapRef: ShallowRef<maplibregl.Map | null>) {
  const { allResponses } = storeToRefs(useResponsesStore())
  const { getSurveyById } = storeToRefs(useSurveysStore())

  const selectedPin = ref<PinData | null>(null)

  const pins = computed<PinData[]>(() =>
    allResponses.value.flatMap((response) => {
      const schema = getSchema(response, getSurveyById.value)
      if (!schema) return []

      const mapField = schema.fields.find((f) => f.ui?.widget === "map")
      if (!mapField) return []

      const value = (response.data as Record<string, any>)[mapField.id]
      if (
        !value ||
        typeof value.lat !== "number" ||
        typeof value.lon !== "number"
      )
        return []

      const isLocal = "localId" in response
      return [
        {
          responseId: isLocal
            ? (response as LocalResponse).localId
            : (response as ResponseFull).id,
          isLocal,
          lat: value.lat,
          lon: value.lon,
          surveyTitle: getSurveyTitle(response),
          date: response.creationDate,
          status: response.status,
        },
      ]
    })
  )

  const markers: maplibregl.Marker[] = []

  const clearMarkers = () => {
    markers.forEach((m) => m.remove())
    markers.length = 0
  }

  const syncMarkers = (mapInstance: maplibregl.Map) => {
    clearMarkers()
    for (const pin of pins.value) {
      const marker = new maplibregl.Marker({
        color: "#000091", // --blue-france-sun-113
      })
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

  watch(mapRef, (mapInstance) => {
    if (mapInstance) {
      syncMarkers(mapInstance)
      mapInstance.on("click", () => {
        selectedPin.value = null
      })
    } else {
      clearMarkers()
      selectedPin.value = null
    }
  })

  // Re-sync whenever the responses store updates
  watch(pins, () => {
    if (mapRef.value) syncMarkers(mapRef.value)
  })

  onBeforeUnmount(clearMarkers)

  return { selectedPin }
}
