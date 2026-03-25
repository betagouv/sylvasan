<script setup lang="ts">
import { formatBytes, formatDate } from "../../composables/offlineMapMetadata"
import type { OfflineMapRecord } from "../../types/maps"

const { map } = defineProps<{
  map: OfflineMapRecord
}>()

const emit = defineEmits(["open-actions"])
</script>

<template>
  <div>
    <DsfrCard :title="map.name">
      <template #end-details>
        <p>
          {{ formatDate(map.createdAt) }}
          &nbsp;·&nbsp;
          {{ formatBytes(map.bytes) }}
          &nbsp;·&nbsp;
          {{ map.tiles.toLocaleString("fr-FR") }} tuiles
          <br />
          Zoom {{ map.zoomLevels[0] }}–{{
            map.zoomLevels[map.zoomLevels.length - 1]
          }}
        </p>
        <div class="flex gap-4">
          <DsfrButton label="Visualiser" icon="ri-map-2-line" />
          <DsfrButton
            secondary
            label="Options"
            icon="ri-edit-line"
            @click="() => emit('open-actions')"
          />
        </div>
      </template>
    </DsfrCard>

    <!-- <div class="map-card__icon" aria-hidden="true">
      <span class="fr-icon-map-2-line" />
    </div>

    <div class="map-card__body">
      <p class="map-card__name">{{ map.name }}</p>
      <p class="map-card__meta">
        {{ formatDate(map.createdAt) }}
        &nbsp;·&nbsp;
        {{ formatBytes(map.bytes) }}
        &nbsp;·&nbsp;
        {{ map.tiles.toLocaleString("fr-FR") }} tuiles
      </p>
      <p class="map-card__zoom">
        Zoom {{ map.zoomLevels[0] }}–{{
          map.zoomLevels[map.zoomLevels.length - 1]
        }}
      </p>
    </div>

    <button
      class="map-card__menu"
      :aria-label="`Options pour ${map.name}`"
      @click="openActions(map)"
    >
      <span class="fr-icon-more-2-fill" aria-hidden="true" />
    </button> -->
  </div>
</template>
