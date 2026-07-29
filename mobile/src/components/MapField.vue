<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from "vue"
import { useDebounceFn } from "@vueuse/core"
import {
  IonModal,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonButton,
  IonContent,
  IonIcon,
  IonSpinner,
} from "@ionic/vue"
import { closeOutline } from "ionicons/icons"
import maplibregl, { type StyleSpecification } from "maplibre-gl"
import { loadAllMapRecords } from "../composables/offlineMapMetadata"
import { Geolocation } from "@capacitor/geolocation"
import { Capacitor } from "@capacitor/core"
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
const mapLoadError = ref(false)
const mapInitialized = ref(false)
const tilesLoaded = ref(false)
const pickedPosition = ref<{ lat: number; lon: number } | null>(null)
const latInput = ref("")
const lonInput = ref("")
let marker: maplibregl.Marker | null = null

const livePosition = ref<{ lat: number; lon: number; accuracy: number } | null>(
  null
)
const gpsUnavailable = ref(false)
let gpsWatchId: string | null = null
let gpsStartGeneration = 0

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

const addGeolocateControl = (m: maplibregl.Map, autoTrigger: boolean) => {
  const geolocate = new maplibregl.GeolocateControl({
    positionOptions: { enableHighAccuracy: true, timeout: 30000 },
    trackUserLocation: false,
    showUserLocation: true,
    showAccuracyCircle: true,
    fitBoundsOptions: { maxZoom: 17 },
  })
  m.addControl(geolocate, "bottom-right")
  m.once("load", async () => {
    if (Capacitor.isNativePlatform()) await Geolocation.requestPermissions()
    if (autoTrigger) geolocate.trigger()
  })
}

// Cycle de vie de la carte

const destroyMap = () => {
  marker?.remove()
  marker = null
  map?.remove()
  map = null
  mapInitialized.value = false
  tilesLoaded.value = false
  mapLoadError.value = false
  pickedPosition.value = null
  latInput.value = ""
  lonInput.value = ""
}

const updateMarker = (lng: number, lat: number) => {
  if (!map) return
  pickedPosition.value = {
    lat: Math.round(lat * 1_000_000) / 1_000_000,
    lon: Math.round(lng * 1_000_000) / 1_000_000,
  }
  if (marker) {
    marker.setLngLat([lng, lat])
  } else {
    marker = new maplibregl.Marker({ color: "#000091" })
      .setLngLat([lng, lat])
      .addTo(map)
  }
}

// Appelé depuis un clic sur la carte — met aussi à jour les inputs
const placeMarker = (lng: number, lat: number) => {
  updateMarker(lng, lat)
  latInput.value = String(pickedPosition.value!.lat)
  lonInput.value = String(pickedPosition.value!.lon)
}

// Appelé depuis les inputs — déplace le marqueur sans écraser ce que l'utilisateur tape
const onCoordinatesInput = useDebounceFn(() => {
  const lat = parseFloat(latInput.value)
  const lon = parseFloat(lonInput.value)
  if (
    isNaN(lat) ||
    isNaN(lon) ||
    lat < -90 ||
    lat > 90 ||
    lon < -180 ||
    lon > 180
  )
    return
  if (tilesLoaded.value) {
    updateMarker(lon, lat)
    if (map)
      map.flyTo({ center: [lon, lat], zoom: Math.max(map.getZoom(), 13) })
  } else {
    // Carte pas encore rendue : on stocke la position sans placer de marqueur.
    // setupMapInteractions la placera via pickedPosition une fois l'idle reçu.
    pickedPosition.value = {
      lat: Math.round(lat * 1_000_000) / 1_000_000,
      lon: Math.round(lon * 1_000_000) / 1_000_000,
    }
  }
}, 500)

const startGpsWatch = async () => {
  const gen = ++gpsStartGeneration
  gpsUnavailable.value = false
  try {
    if (Capacitor.isNativePlatform()) {
      const { location } = await Geolocation.requestPermissions()
      if (gen !== gpsStartGeneration) return // stopGpsWatch appelé pendant l'attente
      if (location === "denied") {
        gpsUnavailable.value = true
        return
      }
    }
    const watchId = await Geolocation.watchPosition(
      { enableHighAccuracy: true, timeout: 30000, minimumUpdateInterval: 1000 },
      (pos, err) => {
        if (err || !pos) {
          gpsUnavailable.value = true
          return
        }
        livePosition.value = {
          lat: Math.round(pos.coords.latitude * 1_000_000) / 1_000_000,
          lon: Math.round(pos.coords.longitude * 1_000_000) / 1_000_000,
          accuracy: Math.round(pos.coords.accuracy),
        }
      }
    )
    if (gen !== gpsStartGeneration) {
      // stopGpsWatch appelé pendant watchPosition — on nettoie immédiatement
      Geolocation.clearWatch({ id: watchId })
      return
    }
    gpsWatchId = watchId
  } catch {
    gpsUnavailable.value = true
  }
}

const stopGpsWatch = () => {
  gpsStartGeneration++ // invalide tout startGpsWatch en cours
  if (gpsWatchId !== null) {
    Geolocation.clearWatch({ id: gpsWatchId })
    gpsWatchId = null
    livePosition.value = null
    gpsUnavailable.value = false
  }
}

const fillWithGps = () => {
  if (!livePosition.value) return
  const { lat, lon } = livePosition.value
  latInput.value = String(lat)
  lonInput.value = String(lon)
  pickedPosition.value = { lat, lon }
  // N'affiche le marqueur que si la carte est déjà rendue ; sinon setupMapInteractions
  // le placera à l'idle suivant en lisant pickedPosition.
  if (map && tilesLoaded.value) {
    updateMarker(lon, lat)
    map.flyTo({ center: [lon, lat], zoom: Math.max(map.getZoom(), 13) })
  }
}

const setupMapInteractions = (m: maplibregl.Map) => {
  m.on("click", (e) => {
    placeMarker(e.lngLat.lng, e.lngLat.lat)
  })
  m.once("idle", () => {
    tilesLoaded.value = true
    // Priorité : position GPS remplie pendant le chargement, sinon valeur sauvegardée
    const pos = pickedPosition.value ?? modelValue.value
    if (pos) {
      placeMarker(pos.lon, pos.lat)
      m.flyTo({ center: [pos.lon, pos.lat], zoom: Math.max(m.getZoom(), 13) })
    }
  })
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

  addGeolocateControl(map, !modelValue.value)
  setupMapInteractions(map)

  map.on("error", (e) => {
    // Ne traiter que les erreurs survenant avant le premier rendu complet.
    // status 0 = NetworkError via XHR (AJAXError) ; message = fetch sans réseau.
    if (!tilesLoaded.value && e.error) {
      const err = e.error as Error & { status?: number }
      if (
        err.status === 0 ||
        !navigator.onLine ||
        err.message?.includes("NetworkError")
      ) {
        mapLoadError.value = true
      }
    }
  })

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

  addGeolocateControl(map, false)
  setupMapInteractions(map)
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
  startGpsWatch()
}

const onModalDismiss = () => {
  gpsUnavailable.value = false
  opened.value = false
  stopGpsWatch()
  destroyMap()
  deregisterOfflineProtocol()
  mapError.value = null
}

const confirm = () => {
  if (!pickedPosition.value) return
  modelValue.value = pickedPosition.value
  opened.value = false
}

onBeforeUnmount(() => {
  stopGpsWatch()
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

          <div class="relative flex-1">
            <div ref="mapContainer" class="w-full h-full bg-gray-100" />

            <Transition name="fade">
              <div
                v-if="!tilesLoaded"
                class="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-white/70 z-10"
              >
                <template v-if="mapLoadError">
                  <p class="px-4 text-center">
                    <span class="text-sm text-stone-500"
                      >Vous êtes hors connexion.
                      <span
                        ><br />Vous pouvez néanmoins remplir votre position
                        actuelle ci-dessous.</span
                      >
                    </span>
                  </p>
                </template>
                <template v-else>
                  <IonSpinner
                    name="crescent"
                    style="width: 2rem; height: 2rem"
                  />
                  <span class="text-sm text-stone-500"
                    >Chargement de la carte en cours</span
                  >
                </template>
              </div>
            </Transition>

            <div
              class="pointer-events-none absolute bottom-14 left-0 right-0 flex justify-center z-10"
              v-if="tilesLoaded"
            >
              <span
                class="bg-black/50 text-white text-xs px-3 py-1.5 rounded-full"
              >
                {{
                  pickedPosition
                    ? "Appuyez sur la carte pour déplacer le marqueur"
                    : "Appuyez sur la carte pour choisir une position"
                }}
              </span>
            </div>
          </div>

          <!-- Position actuelle -->

          <div class="border rounded border-slate-200 p-4 pb-0">
            <div class="mb-3">
              <DsfrButton
                label="Remplir avec ma position actuelle"
                icon="ri-focus-3-line"
                secondary
                size="sm"
                :disabled="!livePosition"
                @click="fillWithGps"
              />
            </div>

            <p v-if="livePosition" class="fr-text--sm mb-2!">
              <span class="live-dot">●</span>
              Précision actuelle :
              <strong>{{ livePosition.accuracy }} m</strong>
            </p>
            <p
              v-else-if="gpsUnavailable"
              class="fr-text--sm text-red-600 mb-2!"
            >
              Localisation GPS non disponible.
            </p>
            <p v-else class="fr-text--sm text-stone-500 mb-2!">
              Recherche du signal GPS…
            </p>
          </div>

          <!-- Footer -->
          <div class="pt-0 pb-3 border-t border-gray-200">
            <div class="flex gap-2 lat-lon">
              <DsfrInputGroup>
                <DsfrInput
                  label="Latitude"
                  placeholder="Latitude"
                  inputmode="decimal"
                  v-model="latInput"
                  @update:model-value="onCoordinatesInput"
                />
              </DsfrInputGroup>
              <DsfrInputGroup>
                <DsfrInput
                  label="Longitude"
                  placeholder="Longitude"
                  inputmode="decimal"
                  v-model="lonInput"
                  @update:model-value="onCoordinatesInput"
                />
              </DsfrInputGroup>
            </div>
            <div class="flex justify-end">
              <DsfrButton
                label="Confirmer la position"
                icon="ri-check-line"
                :disabled="!pickedPosition || !!mapError"
                @click="confirm"
              />
            </div>
          </div>
        </div>
      </IonContent>
    </IonModal>
  </div>
</template>

<style scoped>
.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-leave-to {
  opacity: 0;
}
.lat-lon :deep(.fr-input-group) {
  box-sizing: border-box;
}
.live-dot {
  color: #18753c;
  animation: gps-pulse 1.5s ease-in-out infinite;
}
@keyframes gps-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.2;
  }
}
</style>
