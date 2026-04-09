<script setup lang="ts">
import { formatBytes, formatDate } from "../../composables/offlineMapMetadata"
import type { OfflineMapRecord } from "@shared-types/maps"

const { map } = defineProps<{
  map: OfflineMapRecord
}>()

const emit = defineEmits(["open-actions"])
</script>

<template>
  <div>
    <div class="border border-slate-200 p-4 bg-white">
      <h2 class="fr-h6 mb-3!">{{ map.name }}</h2>
      <div>
        <div class="flex">
          <v-icon icon="ri-calendar-line" scale="0.9" class="mt-[3px] mr-2" />
          <p class="mb-0! fr-text--sm text-stone-600">
            {{ formatDate(map.createdAt) }}
          </p>
        </div>
        <div class="flex">
          <v-icon icon="ri-calendar-line" scale="0.9" class="mt-[3px] mr-2" />
          <p class="mb-0! fr-text--sm text-stone-600">
            Zoom {{ map.zoomLevels[0] }}–{{
              map.zoomLevels[map.zoomLevels.length - 1]
            }}, {{ formatBytes(map.bytes) }}
          </p>
        </div>
        <div class="flex">
          <v-icon icon="ri-calendar-line" scale="0.9" class="mt-[3px] mr-2" />
          <p class="mb-0! fr-text--sm text-stone-600">
            {{ map.tiles.toLocaleString("fr-FR") }} tuiles
          </p>
        </div>
      </div>
      <div class="flex gap-4 justify-end">
        <DsfrButton
          secondary
          size="sm"
          label="Aperçu"
          icon="ri-eye-line"
          @click="() => emit('open-actions')"
        />
        <DsfrButton
          secondary
          size="sm"
          label="Modifier"
          icon="ri-pencil-line"
          @click="() => emit('open-actions')"
        />
      </div>
    </div>
  </div>
</template>
