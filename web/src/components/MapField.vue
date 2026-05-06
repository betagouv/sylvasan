<script setup lang="ts">
import { ref, watch, nextTick, onBeforeUnmount } from "vue"
import maplibregl from "maplibre-gl"
import "maplibre-gl/dist/maplibre-gl.css"
import type { MapValue } from "@shared-types/survey"

const IGN_STYLE_URL =
  "https://data.geopf.fr/annexes/ressources/vectorTiles/styles/PLAN.IGN/standard.json"

const props = defineProps<{
  label: string
  required?: boolean
  disabled?: boolean
  hint?: string
}>()

const modelValue = defineModel<MapValue | undefined>()

const opened = ref(false)
const mapContainer = ref<HTMLDivElement | null>(null)
let map: maplibregl.Map | null = null
let resizeObserver: ResizeObserver | null = null

const getUserPosition = (): Promise<[number, number] | null> =>
  new Promise((resolve) => {
    if (!("geolocation" in navigator)) return resolve(null)
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve([coords.longitude, coords.latitude]),
      () => resolve(null),
      { timeout: 5000, maximumAge: 60_000 }
    )
  })

const initMap = (container: HTMLDivElement) => {
  map?.remove()
  map = null

  const initialCenter: [number, number] = modelValue.value
    ? [modelValue.value.lon, modelValue.value.lat]
    : [2.35, 46.8]
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

  // Une fois que les tuiles ont été chargées, aller à la position de l'usager
  if (!modelValue.value) {
    getUserPosition().then((pos) => {
      if (pos && map) map.flyTo({ center: pos, zoom: 17 })
    })
  }
}

watch(opened, async (isOpen) => {
  if (!isOpen) {
    resizeObserver?.disconnect()
    resizeObserver = null
    map?.remove()
    map = null
    return
  }

  await nextTick()
  if (!mapContainer.value) return

  const container = mapContainer.value

  // Si le containeur a déjà des dimensions, on init
  if (container.offsetWidth > 0 && container.offsetHeight > 0) {
    initMap(container)
    return
  }

  // Sinon, on attend avant d'initialiser à nouveau
  resizeObserver = new ResizeObserver((entries) => {
    const { width, height } = entries[0].contentRect
    if (width > 0 && height > 0) {
      resizeObserver!.disconnect()
      resizeObserver = null
      initMap(container)
    }
  })
  resizeObserver.observe(container)
})

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
  resizeObserver?.disconnect()
  resizeObserver = null
  map?.remove()
  map = null
})
</script>

<template>
  <div>
    <p class="fr-label mb-1">
      {{ label }}
      <span v-if="required" class="text-[var(--text-default-error)]"> *</span>
      <span v-if="hint" class="fr-hint-text">{{ hint }}</span>
    </p>
    <div class="flex items-center gap-3 flex-wrap mt-1">
      <span
        v-if="modelValue"
        class="font-mono text-sm bg-gray-100 px-2 py-1 rounded border border-gray-200"
      >
        {{ modelValue.lat }}, {{ modelValue.lon }}
      </span>
      <span v-else class="text-sm text-gray-500 italic">
        Aucune coordonnée sélectionnée
      </span>
      <DsfrButton
        label="Choisir sur la carte"
        icon="ri-map-pin-line"
        secondary
        size="sm"
        :disabled="disabled"
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

  <Teleport to="body">
    <DsfrModal
      :opened="opened"
      title="Choisir une position"
      size="xl"
      @close="opened = false"
    >
      <p class="fr-text--sm text-gray-500 mb-3">
        Déplacez la carte pour centrer la croix sur le point souhaité, puis
        confirmez.
      </p>
      <div class="relative" style="height: 480px">
        <div ref="mapContainer" style="width: 100%; height: 100%" />
        <!-- Crosshair centered on the map -->
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
      </div>
      <template #footer>
        <div class="flex justify-end gap-2 w-full">
          <DsfrButton label="Annuler" secondary @click="opened = false" />
          <DsfrButton
            label="Confirmer la position"
            icon="ri-check-line"
            @click="confirm"
          />
        </div>
      </template>
    </DsfrModal>
  </Teleport>
</template>
