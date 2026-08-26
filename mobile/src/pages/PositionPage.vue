<script setup lang="ts">
import {
  ref,
  computed,
  shallowRef,
  watch,
  onMounted,
  onBeforeUnmount,
  nextTick,
} from "vue"
import {
  IonPage,
  IonContent,
  IonSpinner,
  IonIcon,
  onIonViewDidEnter,
  onIonViewWillLeave,
} from "@ionic/vue"
import { cloudOfflineOutline } from "ionicons/icons"
import { Network } from "@capacitor/network"
import { Geolocation } from "@capacitor/geolocation"
import { Capacitor } from "@capacitor/core"
import type { PluginListenerHandle } from "@capacitor/core"
import maplibregl, { type StyleSpecification } from "maplibre-gl"
import ignStyle from "../assets/ign-style.json"
import { useGeoPins, DEFAULT_GEO_FILTERS } from "../composables/useGeoPins"
import type { GeoFilters } from "../composables/useGeoPins"
import ResponsePinCard from "../components/ResponsePinCard.vue"
import GeoFiltersPanel from "../components/GeoFiltersPanel.vue"
import { useSurveysStore } from "../stores/surveys"
import { storeToRefs } from "pinia"

const { surveys } = storeToRefs(useSurveysStore())

const centerOfFrance: [number, number] = [2.35, 46.8]

const activeFilters = ref<GeoFilters>({ ...DEFAULT_GEO_FILTERS })
const filterPanelOpen = ref(false)

const activeFilterCount = computed(() => {
  let n = 0
  if (activeFilters.value.onlyMine) n++
  if (activeFilters.value.period !== null) n++
  if (activeFilters.value.surveyIds.length > 0) n++
  return n
})

const ready = ref(false)
const isOnline = ref(false)
const tilesLoaded = ref(false)
const liveAccuracy = ref<number | null>(null)
const mapContainer = ref<HTMLDivElement | null>(null)
const mapRef = shallowRef<maplibregl.Map | null>(null)
let networkListener: PluginListenerHandle | null = null
let gpsWatchId: string | null = null

const { selectedPin, showSearchHere, loading, fetchPins } = useGeoPins(
  mapRef,
  activeFilters
)

const startAccuracyWatch = async () => {
  try {
    if (Capacitor.isNativePlatform()) await Geolocation.requestPermissions()
    gpsWatchId = await Geolocation.watchPosition(
      { enableHighAccuracy: true, timeout: 30000, minimumUpdateInterval: 1000 },
      (pos, err) => {
        if (err || !pos) return
        liveAccuracy.value = Math.round(pos.coords.accuracy)
      }
    )
  } catch {
    // GPS non disponible
  }
}

const stopAccuracyWatch = () => {
  if (gpsWatchId !== null) {
    Geolocation.clearWatch({ id: gpsWatchId })
    gpsWatchId = null
    liveAccuracy.value = null
  }
}

const destroyMap = () => {
  mapRef.value?.remove()
  mapRef.value = null
  tilesLoaded.value = false
}

const initMap = () => {
  if (!mapContainer.value) return
  destroyMap()

  const m = new maplibregl.Map({
    container: mapContainer.value,
    style: ignStyle as StyleSpecification,
    center: centerOfFrance,
    zoom: 6,
    maxZoom: 18.9,
    attributionControl: false,
    fadeDuration: 0,
  })

  m.addControl(
    new maplibregl.AttributionControl({ compact: true }),
    "bottom-left"
  )
  m.addControl(
    new maplibregl.ScaleControl({ maxWidth: 100, unit: "metric" }),
    "bottom-left"
  )
  m.addControl(
    new maplibregl.NavigationControl({ showCompass: false }),
    "bottom-right"
  )

  const geolocate = new maplibregl.GeolocateControl({
    positionOptions: { enableHighAccuracy: true, timeout: 30000 },
    trackUserLocation: false,
    showUserLocation: true,
    showAccuracyCircle: true,
    fitBoundsOptions: { maxZoom: 13 },
  })
  m.addControl(geolocate, "bottom-right")

  m.once("idle", async () => {
    tilesLoaded.value = true
    if (Capacitor.isNativePlatform()) await Geolocation.requestPermissions()
    geolocate.trigger()
  })

  mapRef.value = m
}

watch(isOnline, async (online, wasOnline) => {
  if (online && !wasOnline) {
    await nextTick()
    initMap()
  } else if (!online) {
    destroyMap()
  }
})

onMounted(async () => {
  const status = await Network.getStatus()
  isOnline.value = status.connected
  ready.value = true

  networkListener = await Network.addListener("networkStatusChange", (s) => {
    isOnline.value = s.connected
  })

  if (isOnline.value) {
    await nextTick()
    initMap()
  }
})

onIonViewDidEnter(() => {
  fetchPins()
  startAccuracyWatch()
})

onIonViewWillLeave(() => {
  stopAccuracyWatch()
})

onBeforeUnmount(() => {
  destroyMap()
  networkListener?.remove()
  stopAccuracyWatch()
})
</script>

<template>
  <ion-page>
    <ion-content :scroll-y="false">
      <!-- Vérification de la connectivité en cours -->
      <div v-if="!ready" class="flex items-center justify-center h-full">
        <ion-spinner name="crescent" />
      </div>

      <!-- Hors connexion -->
      <div
        v-else-if="!isOnline"
        class="flex flex-col items-center justify-center h-full gap-4 text-stone-400"
      >
        <ion-icon :icon="cloudOfflineOutline" style="font-size: 3rem" />
        <p class="text-sm mb-0!">Carte indisponible hors connexion</p>
      </div>

      <!-- En ligne : carte + spinner de chargement des tuiles + fiche -->
      <div v-else class="relative h-full">
        <div
          ref="mapContainer"
          :class="{ 'w-full': true, 'h-full': true, invisible: !tilesLoaded }"
        />

        <Transition name="fade">
          <div
            v-if="!tilesLoaded"
            class="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-white/70 z-10 pointer-events-none"
          >
            <IonSpinner name="crescent" style="width: 2rem; height: 2rem" />
            <span class="text-sm text-stone-500"
              >Chargement de la carte en cours</span
            >
          </div>
        </Transition>

        <div
          v-if="tilesLoaded && liveAccuracy !== null"
          class="accuracy-badge absolute right-2 z-10 bg-white/90 text-xs px-2 py-1 rounded-full shadow-sm flex items-center gap-1 pointer-events-none"
        >
          <span class="live-dot">●</span>
          <span>{{ liveAccuracy }} m</span>
        </div>

        <Transition name="drop">
          <div
            v-if="showSearchHere && tilesLoaded"
            class="absolute top-4 left-0 right-0 flex justify-center z-10 pointer-events-none sylvasan-search-container"
          >
            <button
              class="pointer-events-auto bg-white! px-4 py-2 shadow-md font-medium flex items-center gap-2 disabled:opacity-60!"
              :disabled="loading"
              @click="fetchPins"
            >
              <IonSpinner
                v-if="loading"
                name="crescent"
                style="width: 1rem; height: 1rem"
              />
              Rechercher dans cette zone
            </button>
          </div>
        </Transition>

        <!-- Bouton filtre -->
        <button
          v-if="tilesLoaded"
          class="filter-button absolute z-10 flex items-center justify-center rounded-full shadow-lg bg-white!"
          @click="filterPanelOpen = true"
        >
          <v-icon name="ri-filter-line" scale="1.2" />
          <span
            v-if="activeFilterCount > 0"
            class="filter-badge absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#000091]! text-white text-xs font-bold flex items-center justify-center"
          >
            {{ activeFilterCount }}
          </span>
        </button>

        <Transition name="slide-up">
          <ResponsePinCard
            v-if="selectedPin"
            :pin="selectedPin"
            @close="selectedPin = null"
          />
        </Transition>

        <!-- Panneau de filtres -->
        <Transition name="fade-panel">
          <GeoFiltersPanel
            v-if="filterPanelOpen"
            v-model="activeFilters"
            :surveys="surveys"
            @apply="fetchPins"
            @close="filterPanelOpen = false"
            class="z-index-top"
          />
        </Transition>
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
ion-content {
  --padding-top: 0;
  --padding-bottom: 0;
  --padding-start: 0;
  --padding-end: 0;
}

.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-leave-to {
  opacity: 0;
}

.drop-enter-active,
.drop-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.drop-enter-from,
.drop-leave-to {
  transform: translateY(-0.5rem);
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(1rem);
  opacity: 0;
}
div :deep(.maplibregl-marker.maplibregl-user-location-accuracy-circle) {
  z-index: 0;
}

.filter-button {
  top: calc(env(safe-area-inset-top) + 3rem);
  right: 0.75rem;
  width: 50px;
  height: 50px;
  border: 1.5px solid #e2e8f0;
}

.fade-panel-enter-active,
.fade-panel-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.fade-panel-enter-from,
.fade-panel-leave-to {
  opacity: 0;
  transform: translateY(0.5rem);
}

div.sylvasan-search-container {
  padding-top: env(safe-area-inset-top);
  z-index: 999999;
}

.z-index-top {
  z-index: 1000000;
}

.accuracy-badge {
  top: calc(0.5rem + env(safe-area-inset-top));
  margin-top: env(safe-area-inset-top);
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
