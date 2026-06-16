<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue"
import { useRoute } from "vue-router"
import {
  IonPage,
  IonContent,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonButtons,
  IonBackButton,
  IonSpinner,
} from "@ionic/vue"
import maplibregl from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import { loadAllMapRecords } from "../composables/offlineMapMetadata"
import {
  registerOfflineProtocol,
  deregisterOfflineProtocol,
  loadOfflineStyle,
} from "../composables/offlineProtocol"
import type { OfflineMapRecord } from "@shared-types/maps"

const route = useRoute()
const mapContainer = ref<HTMLDivElement | null>(null)
const record = ref<OfflineMapRecord | null>(null)
const tilesLoaded = ref(false)
let map: maplibregl.Map | null = null

onMounted(async () => {
  if (!mapContainer.value) return

  const id = route.params.id as string
  const records = await loadAllMapRecords()
  record.value = records.find((r) => r.id === id) ?? null
  if (!record.value) return

  const { boundaryBox, zoomLevels } = record.value
  const centerLng = (boundaryBox.minLng + boundaryBox.maxLng) / 2
  const centerLat = (boundaryBox.minLat + boundaryBox.maxLat) / 2
  const minZoom = Math.min(...zoomLevels)
  const maxZoom = Math.max(...zoomLevels)

  registerOfflineProtocol()

  const style = loadOfflineStyle()

  map = new maplibregl.Map({
    container: mapContainer.value,
    style,
    center: [centerLng, centerLat],
    zoom: maxZoom - 1,
    minZoom: minZoom,
    maxZoom: maxZoom + 0.9,
    maxBounds: [
      [boundaryBox.minLng, boundaryBox.minLat],
      [boundaryBox.maxLng, boundaryBox.maxLat],
    ],
    attributionControl: false,
  })

  map.addControl(
    new maplibregl.AttributionControl({ compact: true }),
    "bottom-left"
  )
  map.addControl(
    new maplibregl.NavigationControl({ showCompass: false }),
    "bottom-right"
  )

  // Masquer le spinner une fois que toutes les tuiles sont chargées et rendues
  map.once("idle", () => {
    tilesLoaded.value = true
  })
})

onBeforeUnmount(() => {
  map?.remove()
  map = null
  deregisterOfflineProtocol()
})
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button :default-href="{ name: 'MapsPage' }" />
        </ion-buttons>
        <ion-title>{{ record?.name ?? "Aperçu carte" }}</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content :scroll-y="false">
      <div class="w-full h-full relative">
        <div ref="mapContainer" class="w-full h-full" />
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
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
ion-content::part(scroll) {
  padding: 0;
}

.fade-leave-active {
  transition: opacity 0.4s ease;
}
.fade-leave-to {
  opacity: 0;
}
</style>
