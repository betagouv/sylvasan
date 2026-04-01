<script setup lang="ts">
import type { SurveyField } from "@shared-types/survey"

const { field } = defineProps<{ field: SurveyField }>()
const emit = defineEmits(["delete", "moveUp", "moveDown"])
</script>

<template>
  <div class="rounded bg-white border border-slate-50 p-6 flex gap-10">
    <div class="flex flex-col gap-2 items-center justify-center">
      <DsfrButton
        icon-only
        @click="emit('moveUp')"
        tertiary
        icon="ri-arrow-up-line"
      />
      <DsfrButton
        icon-only
        @click="emit('moveDown')"
        tertiary
        icon="ri-arrow-down-line"
      />
    </div>
    <div
      class="flex items-center justify-end w-32 border-r border-slate-300 pr-4"
    >
      <h3 class="fr-text--sm mb-0!">{{ field.id }}</h3>
    </div>
    <div class="grow">
      <div class="w-80">
        <DsfrInput
          v-if="field.type === 'text'"
          :label="field.label"
          :required="field.required"
          label-visible
        />
      </div>
    </div>
    <div class="self-center end">
      <DsfrButton
        icon="ri-delete-bin-line"
        @click="emit('delete')"
        secondary
        icon-only
      />
    </div>
  </div>
</template>
