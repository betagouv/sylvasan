<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from "vue"
import { IonPage, IonContent, IonSpinner, IonIcon } from "@ionic/vue"
import { cloudOfflineOutline } from "ionicons/icons"
import { Network } from "@capacitor/network"
import type { PluginListenerHandle } from "@capacitor/core"
import maplibregl, { type StyleSpecification } from "maplibre-gl"
import ignStyle from "../assets/ign-style.json"

const centerOfFrance: [number, number] = [2.35, 46.8]

const ready = ref(false)
const isOnline = ref(false)
const tilesLoaded = ref(false)
const mapContainer = ref<HTMLDivElement | null>(null)
let map: maplibregl.Map | null = null
let networkListener: PluginListenerHandle | null = null

const getUserPosition = (): Promise<[number, number] | null> =>
  new Promise((resolve) => {
    if (!("geolocation" in navigator)) return resolve(null)
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve([coords.longitude, coords.latitude]),
      () => resolve(null),
      { timeout: 5000, maximumAge: 60_000 }
    )
  })

const destroyMap = () => {
  map?.remove()
  map = null
  tilesLoaded.value = false
}

const initMap = () => {
  if (!mapContainer.value) return
  destroyMap()

  map = new maplibregl.Map({
    container: mapContainer.value,
    style: ignStyle as StyleSpecification,
    center: centerOfFrance,
    zoom: 6,
    maxZoom: 18.9,
    attributionControl: false,
  })

  map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-left")
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right")

  map.once("idle", () => {
    tilesLoaded.value = true
  })

  getUserPosition().then((pos) => {
    if (pos && map) map.flyTo({ center: pos, zoom: 13 })
  })
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

      <!-- En ligne : carte + spinner de chargement des tuiles -->
      <div v-else class="relative h-full">
        <div ref="mapContainer" class="w-full h-full" />

        <Transition name="fade">
          <div
            v-if="!tilesLoaded"
            class="absolute inset-0 flex items-center justify-center bg-white/60"
          >
            <ion-spinner name="crescent" style="width: 2rem; height: 2rem" />
          </div>
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
</style>
