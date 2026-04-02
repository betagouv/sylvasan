<script setup lang="ts">
import type { SurveyField } from "@shared-types/survey"

const { field } = defineProps<{ field: SurveyField }>()
const emit = defineEmits(["delete", "moveUp", "moveDown"])
</script>

<template>
  <div class="rounded bg-white border border-slate-50 p-6 flex gap-6">
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
    <div class="flex flex-col grow border-r border-slate-300 pr-4">
      <h3 class="fr-text--sm mb-0!">{{ field.id }}</h3>
      <p class="fr-text--sm mb-0!">Type : {{ field.type }}</p>
      <p class="fr-text--sm mb-0!" v-if="field.required">Champ obligatoire</p>
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
