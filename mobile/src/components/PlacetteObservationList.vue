<script setup lang="ts">
import { computed } from "vue"
import type { PlacetteObservation } from "@shared-types/response"

const MAX_VISIBLE = 7

const props = defineProps<{ observations: PlacetteObservation[] }>()

const visible = computed(() => props.observations.slice(0, MAX_VISIBLE))
const hiddenCount = computed(() => Math.max(0, props.observations.length - MAX_VISIBLE))

function formatDate(date: string): string {
  return new Date(date).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
}
</script>

<template>
  <ul
    v-if="observations.length > 0"
    class="flex flex-col gap-1.5 list-none p-0 border border-gray-300 p-2! rounded"
  >
    <li
      v-for="obs in visible"
      :key="obs.id"
      class="flex items-center gap-2 text-sm"
    >
      <span class="text-stone-700 truncate">{{ obs.surveyTitle }}</span>
      <span v-if="obs.respondant" class="text-stone-500 truncate text-xs">
        {{ obs.respondant.firstName }} {{ obs.respondant.lastName }}
      </span>
      <span class="ml-auto shrink-0 text-stone-400 text-xs">
        {{ formatDate(obs.creationDate) }}
      </span>
    </li>
    <li v-if="hiddenCount > 0" class="text-xs text-stone-500 mt-0.5">
      ... et {{ hiddenCount }} autre{{ hiddenCount > 1 ? "s" : "" }}
    </li>
  </ul>
</template>
