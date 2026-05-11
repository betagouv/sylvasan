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
const tilesLoading = ref(true)
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
    tilesLoading.value = false
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
        <div v-if="tilesLoading" class="tiles-loading-overlay">
          <ion-spinner name="crescent" />
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
ion-content::part(scroll) {
  padding: 0;
}

.tiles-loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.6);
  z-index: 10;
}
</style>
