<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue"
import {
  IonPage,
  IonContent,
  IonHeader,
  IonToolbar,
  IonButtons,
  IonMenuButton,
  IonTitle,
} from "@ionic/vue"
import maplibregl from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import MapDownloader from "../components/MapDownloader.vue"
import type { BoundaryBox } from "../types/maps"
import { useIonRouter } from "@ionic/vue"
const router = useIonRouter()
const IGN_STYLE_URL =
  "https://data.geopf.fr/annexes/ressources/vectorTiles/styles/PLAN.IGN/standard.json"

function getZoomLevels(currentZoom: number): number[] {
  const minZ = Math.min(16, Math.floor(currentZoom))
  const levels: number[] = []
  for (let z = minZ; z <= 16; z++) levels.push(z)
  return levels
}

const mapContainer = ref<HTMLDivElement | null>(null)
const currentZoom = ref(5)

const selectionBbox = ref<BoundaryBox | null>(null)
const zoomLevels = ref<number[]>([])

let map: maplibregl.Map | null = null

// Conversion d'un point à lon/lat
function getBboxFromSelectionBox(): BoundaryBox {
  if (!map) throw new Error("map not ready")

  const el = map.getContainer()
  const cx = el.offsetWidth / 2
  const cy = el.offsetHeight / 2
  const half = 120 // px — doit être la taille du .selection-box

  const sw = map.unproject([cx - half, cy + half])
  const ne = map.unproject([cx + half, cy - half])

  return {
    minLng: sw.lng,
    minLat: sw.lat,
    maxLng: ne.lng,
    maxLat: ne.lat,
  }
}

onMounted(async () => {
  // Check pour apaiser TypeScript
  if (!mapContainer.value) return

  const hexagone: maplibregl.LngLatLike = [2.35, 46.8]

  map = new maplibregl.Map({
    container: mapContainer.value,
    style: IGN_STYLE_URL,
    zoom: 5,
    center: hexagone,
    maxZoom: 18.9,
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

  map.on("zoom", () => {
    currentZoom.value = map!.getZoom()
    selectionBbox.value = getBboxFromSelectionBox()
    zoomLevels.value = getZoomLevels(currentZoom.value)
  })

  // Petit hack pour forcer la carte à prendre l'espace total de son div
  // après le premier chargement
  map.on("load", () => {
    selectionBbox.value = getBboxFromSelectionBox()
    zoomLevels.value = getZoomLevels(currentZoom.value)
  })
})

onBeforeUnmount(() => {
  map?.remove()
  map = null
})
</script>

<template>
  <ion-page class="ion-padding">
    <ion-header>
      <ion-toolbar>
        <ion-title>Téléchargez une zone</ion-title>
        <ion-buttons slot="start">
          <ion-menu-button />
        </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <ion-content :scroll-y="false">
      <div class="flex flex-col w-full h-full">
        <div class="w-full h-full relative">
          <div ref="mapContainer" class="w-full h-full" />

          <!-- carré au centre de la carte -->
          <div
            class="absolute inset-0 flex items-center justify-center pointer-events-none"
            aria-hidden="true"
          >
            <div class="selection-box">
              <span class="selection-box__corner selection-box__corner--tl" />
              <span class="selection-box__corner selection-box__corner--tr" />
              <span class="selection-box__corner selection-box__corner--bl" />
              <span class="selection-box__corner selection-box__corner--br" />
            </div>
          </div>
        </div>
        <div class="p-4 text-center border-t border-gray-200">
          <MapDownloader
            v-if="selectionBbox && zoomLevels"
            :boundary-box="selectionBbox"
            :zoom-levels="zoomLevels"
            @saved="router.back()"
          />
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
/* Carré CSS dans le centre de la carte */

.selection-box {
  position: relative;
  width: 240px;
  height: 240px;
  opacity: 0.6;
}

.selection-box__corner {
  position: absolute;
  width: 20px;
  height: 20px;
  border-color: black;
  border-style: solid;
  border-width: 0;
}
.selection-box__corner--tl {
  top: 0;
  left: 0;
  border-top-width: 3px;
  border-left-width: 3px;
}
.selection-box__corner--tr {
  top: 0;
  right: 0;
  border-top-width: 3px;
  border-right-width: 3px;
}
.selection-box__corner--bl {
  bottom: 0;
  left: 0;
  border-bottom-width: 3px;
  border-left-width: 3px;
}
.selection-box__corner--br {
  bottom: 0;
  right: 0;
  border-bottom-width: 3px;
  border-right-width: 3px;
}
</style>
