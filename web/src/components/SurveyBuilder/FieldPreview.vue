<script setup lang="ts">
import type { SurveyField } from "@shared-types/survey"

const { field } = defineProps<{ field: SurveyField }>()
</script>

<template>
  <div>
    <div>
      <DsfrInput
        v-if="field.type === 'text'"
        :label="field.label"
        :required="field.required"
        label-visible
      />
    </div>
  </div>
</template>
