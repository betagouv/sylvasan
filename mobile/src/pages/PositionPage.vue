<script setup lang="ts">
import {
  ref,
  shallowRef,
  watch,
  onMounted,
  onBeforeUnmount,
  nextTick,
} from "vue"
import { IonPage, IonContent, IonSpinner, IonIcon } from "@ionic/vue"
import { cloudOfflineOutline } from "ionicons/icons"
import { Network } from "@capacitor/network"
import { Geolocation } from "@capacitor/geolocation"
import { Capacitor } from "@capacitor/core"
import type { PluginListenerHandle } from "@capacitor/core"
import maplibregl, { type StyleSpecification } from "maplibre-gl"
import ignStyle from "../assets/ign-style.json"
import { useMapPins } from "../composables/useMapPins"
import ResponsePinCard from "../components/ResponsePinCard.vue"

const centerOfFrance: [number, number] = [2.35, 46.8]

const ready = ref(false)
const isOnline = ref(false)
const tilesLoaded = ref(false)
const mapContainer = ref<HTMLDivElement | null>(null)
const mapRef = shallowRef<maplibregl.Map | null>(null)
let networkListener: PluginListenerHandle | null = null

const { selectedPin } = useMapPins(mapRef)

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
  })

  m.addControl(
    new maplibregl.AttributionControl({ compact: true }),
    "bottom-left"
  )
  m.addControl(
    new maplibregl.NavigationControl({ showCompass: false }),
    "bottom-right"
  )

  const geolocate = new maplibregl.GeolocateControl({
    positionOptions: { enableHighAccuracy: true, timeout: 5000 },
    trackUserLocation: true,
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

onBeforeUnmount(() => {
  destroyMap()
  networkListener?.remove()
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

        <Transition name="slide-up">
          <ResponsePinCard
            v-if="selectedPin"
            :pin="selectedPin"
            @close="selectedPin = null"
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

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(1rem);
  opacity: 0;
}
</style>
