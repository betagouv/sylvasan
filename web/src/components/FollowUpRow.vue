<script setup lang="ts">
import { DsfrButton } from "@gouvminint/vue-dsfr"
import type { SurveyFollowUp } from "@shared-types/survey"

const { followUp } = defineProps<{ followUp: SurveyFollowUp }>()
const emit = defineEmits(["delete", "edit"])
</script>

<template>
  <div
    class="grid grid-cols-12 gap-2 items-center p-4 border border-gray-300 bg-white"
  >
    <div class="col-span-4 flex">
      <div
        class="border border-gray-100 px-4 h-10 rounded-full flex justify-center items-center"
        :style="`background: ${followUp.actionColor}`"
      >
        <v-icon scale="1.2" :icon="followUp.actionIcon" class="mr-1"></v-icon>
        <span class="font-medium">{{ followUp.actionLabel }}</span>
      </div>
    </div>

    <div class="col-span-5">
      <p class="mb-0! font-medium">{{ followUp.title }}</p>
    </div>

    <div class="col-span-3 flex gap-4 justify-end">
      <DsfrButton
        tertiary
        size="sm"
        label="Modifier"
        icon="ri-pencil-line"
        @click="emit('edit')"
      />
      <DsfrButton
        tertiary
        size="sm"
        label="Supprimer"
        :icon="{
          name: 'ri-delete-bin-line',
          fill: '#c9191e',
        }"
        @click="emit('delete')"
      />
    </div>
  </div>
</template>
