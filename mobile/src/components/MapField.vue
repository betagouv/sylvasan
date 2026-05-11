<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from "vue"
import {
  IonModal,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonButton,
  IonContent,
  IonIcon,
} from "@ionic/vue"
import { closeOutline } from "ionicons/icons"
import maplibregl, { type StyleSpecification } from "maplibre-gl"
import { loadAllMapRecords } from "../composables/offlineMapMetadata"
import {
  registerOfflineProtocol,
  deregisterOfflineProtocol,
  loadOfflineStyle,
} from "../composables/offlineProtocol"
import type { OfflineMapRecord } from "@shared-types/maps"
import type { MapValue } from "@shared-types/survey"

const props = defineProps<{
  label: string
  required?: boolean
  disabled?: boolean
  hint?: string
}>()

const IGN_STYLE_URL =
  "https://data.geopf.fr/annexes/ressources/vectorTiles/styles/PLAN.IGN/standard.json"

const modelValue = defineModel<MapValue | undefined>()

const opened = ref(false)
const mapContainer = ref<HTMLDivElement | null>(null)
let map: maplibregl.Map | null = null

const mapMode = ref<"online" | "offline">("online")
const offlineMaps = ref<OfflineMapRecord[]>([])
const selectedMapId = ref("")
const mapError = ref<string | null>(null)
const mapInitialized = ref(false)

const modeOptions = [
  { label: "Carte en ligne", value: "online", icon: "ri-global-fill" },
  {
    label: "Carte téléchargée",
    value: "offline",
    icon: "ri-mobile-download-line",
  },
]

onMounted(async () => {
  offlineMaps.value = await loadAllMapRecords()
  if (offlineMaps.value.length > 0) {
    selectedMapId.value = offlineMaps.value[0].id
  }
})

const getUserPosition = (): Promise<[number, number] | null> =>
  new Promise((resolve) => {
    if (!("geolocation" in navigator)) return resolve(null)
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve([coords.longitude, coords.latitude]),
      () => resolve(null),
      { timeout: 5000, maximumAge: 60_000 }
    )
  })

// Cycle de vie de la carte

const destroyMap = () => {
  map?.remove()
  map = null
  mapInitialized.value = false
}

// Long / Lat et non pas Lat / Lon (https://maplibre.org/maplibre-gl-js/docs/API/classes/LngLat/)
const centerOfFrance: [number, number] = [2.35, 46.8]

const initOnlineMap = (container: HTMLDivElement) => {
  const initialCenter: [number, number] = modelValue.value
    ? [modelValue.value.lon, modelValue.value.lat]
    : centerOfFrance
  const initialZoom = modelValue.value ? 17 : 5

  map = new maplibregl.Map({
    container,
    style: IGN_STYLE_URL,
    center: initialCenter,
    zoom: initialZoom,
    maxZoom: 18.9,
    attributionControl: false,
  })

  map.resize()
  map.addControl(
    new maplibregl.AttributionControl({ compact: true }),
    "bottom-left"
  )
  map.addControl(
    new maplibregl.NavigationControl({ showCompass: false }),
    "bottom-right"
  )

  if (!modelValue.value) {
    getUserPosition().then((pos) => {
      if (pos && map) map.flyTo({ center: pos, zoom: 17 })
    })
  }

  mapInitialized.value = true
}

const initOfflineMap = (container: HTMLDivElement) => {
  const record = offlineMaps.value.find((m) => m.id === selectedMapId.value)
  if (!record) {
    mapError.value = "Aucune carte téléchargée disponible."
    return
  }

  registerOfflineProtocol()

  let style: StyleSpecification
  try {
    style = loadOfflineStyle()
  } catch {
    mapError.value = "Impossible de charger le style de la carte."
    return
  }

  const { boundaryBox, zoomLevels } = record
  const centerLng = (boundaryBox.minLng + boundaryBox.maxLng) / 2
  const centerLat = (boundaryBox.minLat + boundaryBox.maxLat) / 2
  const minZoom = Math.min(...zoomLevels)
  const maxZoom = Math.max(...zoomLevels)

  const initialCenter: [number, number] = modelValue.value
    ? [modelValue.value.lon, modelValue.value.lat]
    : [centerLng, centerLat]
  const initialZoom = modelValue.value ? Math.min(maxZoom, 17) : maxZoom - 1

  map = new maplibregl.Map({
    container,
    style,
    center: initialCenter,
    zoom: initialZoom,
    minZoom,
    maxZoom: maxZoom + 0.9,
    maxBounds: [
      [boundaryBox.minLng, boundaryBox.minLat],
      [boundaryBox.maxLng, boundaryBox.maxLat],
    ],
    attributionControl: false,
  })

  map.resize()
  map.addControl(
    new maplibregl.AttributionControl({ compact: true }),
    "bottom-left"
  )
  map.addControl(
    new maplibregl.NavigationControl({ showCompass: false }),
    "bottom-right"
  )

  mapInitialized.value = true
}

const initMap = async () => {
  if (!mapContainer.value) return
  mapError.value = null
  destroyMap()
  deregisterOfflineProtocol()

  if (mapMode.value === "online") {
    initOnlineMap(mapContainer.value)
  } else {
    initOfflineMap(mapContainer.value)
  }
}

// Re-initialise à chaque fois que le mode ou le hors-ligne change
watch([mapMode, selectedMapId], () => {
  if (opened.value) initMap()
})

const onModalPresent = () => {
  initMap()
}

const onModalDismiss = () => {
  opened.value = false
  destroyMap()
  deregisterOfflineProtocol()
  mapError.value = null
}

const confirm = () => {
  if (!map) return
  const { lat, lng } = map.getCenter()
  modelValue.value = {
    lat: Math.round(lat * 1_000_000) / 1_000_000,
    lon: Math.round(lng * 1_000_000) / 1_000_000,
  }
  opened.value = false
}

onBeforeUnmount(() => {
  destroyMap()
  deregisterOfflineProtocol()
})
</script>

<template>
  <div>
    <!-- Affichage des coordonnées -->
    <div>
      <p class="fr-label mb-2!">
        {{ label }}
        <span v-if="required" class="text-[var(--text-default-error)]"> *</span>
        <span v-if="hint" class="fr-hint-text">{{ hint }}</span>
      </p>
      <div class="flex items-center gap-3 flex-wrap mt-1">
        <div
          class="font-mono text-sm bg-gray-100 px-2 py-1 rounded border border-gray-200"
          v-if="modelValue"
        >
          {{ modelValue.lat }}, {{ modelValue.lon }}
        </div>
        <DsfrButton
          v-if="!modelValue && !disabled"
          label="Choisir sur la carte"
          icon="ri-map-pin-line"
          secondary
          size="sm"
          :disabled="disabled"
          @click="opened = true"
        />
        <DsfrButton
          v-if="modelValue && !disabled"
          label="Modifier la position"
          icon="ri-pencil-line"
          tertiary
          size="sm"
          icon-only
          @click="opened = true"
        />
        <DsfrButton
          v-if="modelValue && !disabled"
          label="Effacer la position"
          icon="ri-delete-bin-line"
          tertiary
          size="sm"
          icon-only
          @click="modelValue = undefined"
        />
      </div>
    </div>

    <IonModal
      :is-open="opened"
      @did-present="onModalPresent"
      @did-dismiss="onModalDismiss"
    >
      <IonHeader>
        <IonToolbar>
          <IonTitle>Choisir une position</IonTitle>
          <IonButtons slot="end">
            <IonButton @click="opened = false">
              <IonIcon slot="icon-only" :icon="closeOutline" />
            </IonButton>
          </IonButtons>
        </IonToolbar>
      </IonHeader>

      <IonContent :scroll-y="false">
        <div class="flex flex-col h-full">
          <div class="box-border!">
            <DsfrSegmentedSet
              :options="modeOptions"
              :model-value="mapMode"
              @update:model-value="(v: string) => (mapMode = v as 'online' | 'offline')"
            />
          </div>
          <!-- Sélection du mode -->
          <div class="py-2 flex flex-wrap items-end gap-3">
            <DsfrSelect
              v-if="mapMode === 'offline' && offlineMaps.length > 0"
              label="Choisissez une carte"
              :options="offlineMaps.map((m) => ({ text: m.name, value: m.id }))"
              :model-value="selectedMapId"
              @update:model-value="(v: string) => (selectedMapId = v as string)"
              class="mb-0! min-w-40"
            />
            <p
              v-if="mapMode === 'offline' && offlineMaps.length === 0"
              class="text-sm text-red-600 mb-0!"
            >
              Aucune carte téléchargée. Rendez-vous dans la section Cartes pour
              en télécharger.
            </p>
          </div>

          <div v-if="mapError" class="p-4">
            <DsfrAlert type="error" :title="mapError" />
          </div>

          <!-- La carte + crosshair -->
          <div class="relative flex-1">
            <div ref="mapContainer" class="w-full h-full bg-gray-100" />

            <div
              class="pointer-events-none absolute inset-0 flex items-center justify-center z-10"
            >
              <div class="relative w-10 h-10">
                <div
                  class="absolute top-1/2 left-0 w-full h-px bg-orange-600 shadow"
                />
                <div
                  class="absolute left-1/2 top-0 h-full w-px bg-orange-600 shadow"
                />
                <div
                  class="absolute top-1/2 left-1/2 w-2 h-2 rounded-full border-2 border-orange-600 bg-white"
                  style="transform: translate(-50%, -50%)"
                />
              </div>
            </div>

            <div
              class="pointer-events-none absolute bottom-14 left-0 right-0 flex justify-center z-10"
            >
              <span
                class="bg-black/50 text-white text-xs px-3 py-1.5 rounded-full"
              >
                Déplacez la carte pour centrer la croix sur le point souhaité
              </span>
            </div>
          </div>

          <!-- Footer -->
          <div class="p-3 border-t border-gray-200 flex justify-end">
            <DsfrButton
              label="Confirmer la position"
              icon="ri-check-line"
              :disabled="!mapInitialized || !!mapError"
              @click="confirm"
            />
          </div>
        </div>
      </IonContent>
    </IonModal>
  </div>
</template>
