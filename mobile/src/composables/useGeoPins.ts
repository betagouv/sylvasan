import { ref, watch } from "vue"
import type { ShallowRef } from "vue"
import maplibregl from "maplibre-gl"
import { useApiFetch } from "../utils/data-fetching"
import { useAuthStore } from "../stores/auth"
import type { GeoFollowUp, ResponseGeo } from "@shared-types/response"
import type { PinData } from "./useMapPins"

// Paramètres à ajuster pour le comportement du clustering
const CLUSTER_MAX_ZOOM = 14
const CLUSTER_RADIUS = 50

const COLOR_OWN = "#000091" // --blue-france-sun-113
const COLOR_OTHER = "#7ab1e8" // bleu clair pour les réponses des collègues

const SOURCE_ID = "geo-pins"
const LAYER_CLUSTERS = "geo-pins-clusters"
const LAYER_CLUSTER_COUNT = "geo-pins-cluster-count"
const LAYER_UNCLUSTERED = "geo-pins-unclustered"
const IMAGE_PIN_OWN = "pin-own"
const IMAGE_PIN_OTHER = "pin-other"

function makePinSvg(color: string): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="27" height="41" viewBox="0 0 27 41">
    <path fill="${color}" d="M27,13.5C27,19.07 20.25,27 14.75,34.5C14.02,35.5 12.98,35.5 12.25,34.5C6.75,27 0,19.22 0,13.5C0,6.04 6.04,0 13.5,0C20.96,0 27,6.04 27,13.5Z"/>
    <path opacity="0.25" fill="black" d="M13.5,0C6.04,0 0,6.04 0,13.5C0,19.22 6.75,27 12.25,34.5C13,35.5 14.02,35.5 14.75,34.5C20.25,27 27,19.07 27,13.5C27,6.04 20.96,0 13.5,0Z M13.5,1C20.42,1 26,6.58 26,13.5C26,15.9 24.97,19.38 22.47,23.32C20.07,27.13 16.61,31.54 13.5,35.61C10.39,31.54 6.93,27.13 4.53,23.32C2.03,19.38 1,15.9 1,13.5C1,6.58 6.58,1 13.5,1Z"/>
    <circle fill="white" cx="13.5" cy="13.5" r="5.5"/>
  </svg>`
}

function loadPinImage(
  mapInstance: maplibregl.Map,
  id: string,
  color: string
): Promise<void> {
  return new Promise((resolve, reject) => {
    const img = new Image(27, 41)
    img.onload = () => {
      if (!mapInstance.hasImage(id)) mapInstance.addImage(id, img)
      resolve()
    }
    img.onerror = reject
    img.src = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(
      makePinSvg(color)
    )}`
  })
}

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
    followUps: r.followUps ?? [],
  }
}

function pinToFeature(pin: PinData, currentUserId: number | undefined) {
  return {
    type: "Feature" as const,
    geometry: {
      type: "Point" as const,
      coordinates: [pin.lon, pin.lat] as [number, number],
    },
    properties: {
      responseId: pin.responseId,
      surveyId: pin.surveyId,
      isLocal: pin.isLocal,
      lat: pin.lat,
      lon: pin.lon,
      surveyTitle: pin.surveyTitle,
      date: pin.date,
      status: pin.status,
      isOwn: !pin.respondant || pin.respondant.id === currentUserId,
      // Il nous faut sérialiser les objets de sorte qu'on puisse les récupérer après le GeoJSON
      respondant:
        pin.respondant != null ? JSON.stringify(pin.respondant) : null,
      followUps: pin.followUps.length > 0 ? JSON.stringify(pin.followUps) : null,
    },
  }
}

function pinFromProperties(props: Record<string, unknown>): PinData {
  return {
    responseId: props.responseId as string | number,
    surveyId: props.surveyId as number | null,
    isLocal: Boolean(props.isLocal),
    lat: Number(props.lat),
    lon: Number(props.lon),
    surveyTitle: String(props.surveyTitle ?? ""),
    date: String(props.date ?? ""),
    status: String(props.status ?? ""),
    respondant: props.respondant
      ? JSON.parse(props.respondant as string)
      : null,
    followUps: props.followUps
      ? (JSON.parse(props.followUps as string) as GeoFollowUp[])
      : [],
  }
}

export function useGeoPins(mapRef: ShallowRef<maplibregl.Map | null>) {
  const authStore = useAuthStore()
  const selectedPin = ref<PinData | null>(null)
  const showSearchHere = ref(false)
  const loading = ref(false)

  const setupLayers = async (mapInstance: maplibregl.Map) => {
    await Promise.all([
      loadPinImage(mapInstance, IMAGE_PIN_OWN, COLOR_OWN),
      loadPinImage(mapInstance, IMAGE_PIN_OTHER, COLOR_OTHER),
    ])

    mapInstance.addSource(SOURCE_ID, {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
      cluster: true,
      clusterMaxZoom: CLUSTER_MAX_ZOOM,
      clusterRadius: CLUSTER_RADIUS,
    })

    // Le cercle du clustering (celui avec le numéro à l'intérieur)
    mapInstance.addLayer({
      id: LAYER_CLUSTERS,
      type: "circle",
      source: SOURCE_ID,
      filter: ["has", "point_count"],
      paint: {
        "circle-color": COLOR_OWN,
        "circle-radius": 18,
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
      },
    })

    // Le numéro à l'intérieur du cercle du clustering
    mapInstance.addLayer({
      id: LAYER_CLUSTER_COUNT,
      type: "symbol",
      source: SOURCE_ID,
      filter: ["has", "point_count"],
      layout: {
        "text-field": ["get", "point_count_abbreviated"],
        "text-size": 13,
      },
      paint: {
        "text-color": "#ffffff",
      },
    })

    // Le map pin individuel
    mapInstance.addLayer({
      id: LAYER_UNCLUSTERED,
      type: "symbol",
      source: SOURCE_ID,
      filter: ["!", ["has", "point_count"]],
      layout: {
        "icon-image": [
          "case",
          ["==", ["get", "isOwn"], true],
          IMAGE_PIN_OWN,
          IMAGE_PIN_OTHER,
        ],
        "icon-size": 1,
        "icon-anchor": "bottom",
        "icon-allow-overlap": true,
        "icon-ignore-placement": true,
      },
    })

    // Click dans un cercle de cluster
    mapInstance.on("click", LAYER_CLUSTERS, async (e) => {
      const feature = e.features?.[0]
      if (!feature || feature.geometry.type !== "Point") return
      const clusterId = feature.properties?.cluster_id as number
      const coordinates = feature.geometry.coordinates as [number, number]
      const source = mapInstance.getSource(
        SOURCE_ID
      ) as maplibregl.GeoJSONSource
      const zoom = await source.getClusterExpansionZoom(clusterId)
      mapInstance.easeTo({ center: coordinates, zoom })
    })

    // Click dans le pin individuel
    mapInstance.on("click", LAYER_UNCLUSTERED, (e) => {
      const feature = e.features?.[0]
      if (!feature?.properties) return
      const pin = pinFromProperties(
        feature.properties as Record<string, unknown>
      )
      selectedPin.value =
        selectedPin.value?.responseId === pin.responseId ? null : pin
    })

    // Click dans un endroit vide sur la carte
    mapInstance.on("click", (e) => {
      const hits = mapInstance.queryRenderedFeatures(e.point, {
        layers: [LAYER_CLUSTERS, LAYER_UNCLUSTERED],
      })
      if (hits.length === 0) selectedPin.value = null
    })

    for (const layer of [LAYER_CLUSTERS, LAYER_UNCLUSTERED]) {
      mapInstance.on("mouseenter", layer, () => {
        mapInstance.getCanvas().style.cursor = "pointer"
      })
      mapInstance.on("mouseleave", layer, () => {
        mapInstance.getCanvas().style.cursor = ""
      })
    }
  }

  const updateSource = (mapInstance: maplibregl.Map, pins: PinData[]) => {
    const source = mapInstance.getSource(SOURCE_ID) as
      | maplibregl.GeoJSONSource
      | undefined
    if (!source) return
    const currentUserId = authStore.loggedUser?.id
    source.setData({
      type: "FeatureCollection",
      features: pins.map((pin) => pinToFeature(pin, currentUserId)),
    })
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

    updateSource(mapRef.value, data.value.map(toPin))
  }

  watch(mapRef, (mapInstance) => {
    if (mapInstance) {
      // Les sources et couches nécessitent que le style soit chargé.
      // Le style étant un objet JSON embarqué dans le bundle, l'événement `load`
      // peut avoir déjà été émis avant que ce watcher s'exécute — on vérifie d'abord.
      const init = () => {
        setupLayers(mapInstance)
        fetchPins()
      }
      if (mapInstance.isStyleLoaded()) {
        init()
      } else {
        mapInstance.once("load", init)
      }

      mapInstance.on("moveend", () => {
        showSearchHere.value = true
      })
    } else {
      selectedPin.value = null
      showSearchHere.value = false
      loading.value = false
    }
  })

  return { selectedPin, showSearchHere, loading, fetchPins }
}
