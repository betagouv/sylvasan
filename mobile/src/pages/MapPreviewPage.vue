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
import { Capacitor } from "@capacitor/core"
import { Filesystem, Directory, Encoding } from "@capacitor/filesystem"
import { openDB } from "idb"
import { loadAllMapRecords } from "../composables/offlineMapMetadata"
import type { OfflineMapRecord } from "@shared-types/maps"

const IGN_STYLE_URL =
  "https://data.geopf.fr/annexes/ressources/vectorTiles/styles/PLAN.IGN/standard.json"
const OFFLINE_PROTOCOL = "offline"

const route = useRoute()
const mapContainer = ref<HTMLDivElement | null>(null)
const record = ref<OfflineMapRecord | null>(null)
const tilesLoading = ref(true)
let map: maplibregl.Map | null = null

// Conversion base64 → ArrayBuffer pour passer les tuiles à MapLibre
const base64ToArrayBuffer = (b64: string): ArrayBuffer => {
  const binary = atob(b64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  return bytes.buffer
}

// Enregistre un protocole custom qui sert les tuiles depuis le stockage local
const registerOfflineProtocol = () => {
  maplibregl.addProtocol(OFFLINE_PROTOCOL, async (params) => {
    const key = params.url.replace(`${OFFLINE_PROTOCOL}://`, "")
    try {
      if (Capacitor.isNativePlatform()) {
        const result = await Filesystem.readFile({
          path: `tiles/${key}.pbf`,
          directory: Directory.Data,
          encoding: Encoding.UTF8,
        })
        return { data: base64ToArrayBuffer(result.data as string) }
      } else {
        const db = await openDB("ign-tile-store", 1)
        const b64 = await db.get("tiles", key)
        if (!b64) return { data: new ArrayBuffer(0) }
        return { data: base64ToArrayBuffer(b64) }
      }
    } catch {
      return { data: new ArrayBuffer(0) }
    }
  })
}

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

  // TODO : cache pour le style IGN ? Le mettre directement dans les fichiers en local ?
  // Télécharger le style IGN et remplacer les tuiles en ligne par le protocole offline
  const styleResponse = await fetch(IGN_STYLE_URL)
  const style = await styleResponse.json()

  for (const source of Object.values(style.sources) as any[]) {
    if (Array.isArray(source.tiles)) {
      source.tiles = source.tiles.map((url: string) =>
        url.replace(
          "https://data.geopf.fr/tms/1.0.0/PLAN.IGN/{z}/{x}/{y}.pbf",
          `${OFFLINE_PROTOCOL}://PLAN.IGN/{z}/{x}/{y}`
        )
      )
    }
  }

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
  maplibregl.removeProtocol(OFFLINE_PROTOCOL)
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
