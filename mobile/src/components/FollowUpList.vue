<script setup lang="ts">
import { computed } from "vue"
import type { GeoFollowUp } from "@shared-types/response"

const MAX_VISIBLE = 7

const props = defineProps<{ followUps: GeoFollowUp[] }>()

const visibleFollowUps = computed(() => props.followUps.slice(0, MAX_VISIBLE))
const hiddenCount = computed(() =>
  Math.max(0, props.followUps.length - MAX_VISIBLE)
)

function followUpDate(creationDate: string): string {
  return new Date(creationDate).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
}
</script>

<template>
  <ul
    v-if="followUps.length > 0"
    class="flex flex-col gap-1.5 list-none p-0 border border-gray-300 p-2! rounded"
  >
    <li
      v-for="followUp in visibleFollowUps"
      :key="followUp.id"
      class="flex items-center gap-2 text-sm"
    >
      <span
        v-if="followUp.survey"
        class="shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs"
        :style="{ backgroundColor: followUp.survey.actionColor || '#e3e3fd' }"
      >
        <v-icon
          v-if="followUp.survey.actionIcon"
          :name="followUp.survey.actionIcon"
          scale="0.75"
        />
      </span>
      <span class="text-stone-700 truncate">
        {{ followUp.survey?.title }}
      </span>
      <span class="ml-auto shrink-0 text-stone-400 text-xs">
        {{ followUpDate(followUp.creationDate) }}
      </span>
    </li>
    <li v-if="hiddenCount > 0" class="text-xs text-stone-500 mt-0.5 list-none">
      ... et {{ hiddenCount }} autre{{ hiddenCount > 1 ? "s" : "" }} suivi{{
        hiddenCount > 1 ? "s" : ""
      }}
    </li>
  </ul>
</template>
