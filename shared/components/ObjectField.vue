<script setup lang="ts">
import { watch } from "vue"
import type { Component } from "vue"
import type {
  SurveyField,
  VocabularySet,
  LocalImageItem,
} from "../types/survey"
import FieldRenderer from "./FieldRenderer.vue"
import { getEmptyValue, evaluateCondition } from "../utils/survey"

const props = defineProps<{
  field: SurveyField
  disabled?: boolean
  forceValidate?: boolean
  vocabularies?: VocabularySet[]
  mapComponent?: Component
  resolveImagePath?: (path: string) => Promise<string | null>
  captureImage?: () => Promise<LocalImageItem | null>
}>()

const emit = defineEmits<{ busyChange: [value: boolean] }>()

const modelValue = defineModel<Record<string, unknown>>({ default: () => ({}) })

const isSubFieldVisible = (subField: SurveyField): boolean => {
  if (!subField.condition) return true
  return evaluateCondition(subField.condition, modelValue.value)
}

const updateField = (fieldId: string, value: unknown) => {
  modelValue.value = { ...modelValue.value, [fieldId]: value }
}

// Efface la valeur d'un sous-champ quand il devient invisible
watch(
  () => (props.field.fields ?? []).map((f) => isSubFieldVisible(f)),
  (newVisibility, oldVisibility) => {
    let needsUpdate = false
    let result = modelValue.value
    ;(props.field.fields ?? []).forEach((subField, j) => {
      if ((oldVisibility?.[j] ?? true) && !newVisibility[j]) {
        result = { ...result, [subField.id]: getEmptyValue(subField) }
        needsUpdate = true
      }
    })
    if (needsUpdate) modelValue.value = result
  },
  { immediate: true },
)
</script>

<template>
  <fieldset class="border border-slate-200 rounded p-3 mb-4 bg-[#f8fafc]">
    <legend class="fr-label px-2">{{ field.label }}</legend>

    <template v-for="subField in field.fields" :key="subField.id">
      <FieldRenderer
        v-if="isSubFieldVisible(subField)"
        :field="subField"
        :model-value="modelValue[subField.id]"
        :disabled="disabled"
        :force-validate="forceValidate"
        :vocabularies="props.vocabularies"
        :map-component="props.mapComponent"
        :resolve-image-path="props.resolveImagePath"
        :captureImage="props.captureImage"
        @update:model-value="updateField(subField.id, $event)"
        @busy-change="emit('busyChange', $event)"
      />
    </template>
  </fieldset>
</template>
