<script setup lang="ts">
import type { SurveyField } from "@shared-types/survey"
import FieldRenderer from "./FieldRenderer.vue"

const props = defineProps<{
  field: SurveyField
  disabled?: boolean
}>()

const emit = defineEmits<{
  "update:modelValue": [value: Record<string, unknown>[]]
}>()

const modelValue = defineModel<Record<string, unknown>[]>({ default: () => [] })

const createEmptyItem = () =>
  Object.fromEntries((props.field.fields ?? []).map((f) => [f.id, ""]))

const addItem = () => {
  if (
    props.field.validation?.maxItems &&
    modelValue.value.length >= props.field.validation.maxItems
  )
    return
  modelValue.value = [...modelValue.value, createEmptyItem()]
}

const removeItem = (index: number) => {
  modelValue.value = modelValue.value.filter((_, i) => i !== index)
}

const updateItem = (index: number, fieldId: string, value: unknown) => {
  modelValue.value = modelValue.value.map((item, i) =>
    i === index ? { ...item, [fieldId]: value } : item
  )
}
</script>

<template>
  <fieldset class="border border-slate-300 rounded p-4 mb-4">
    <legend class="fr-label px-2">{{ field.label }}</legend>

    <div
      v-for="(item, index) in modelValue"
      :key="index"
      class="border border-slate-200 rounded p-3 mb-3 relative"
    >
      <button
        type="button"
        class="absolute top-2 right-2 text-red-500 text-xs"
        @click="removeItem(index)"
        :disabled="disabled"
      >
        Supprimer
      </button>

      <FieldRenderer
        v-for="subField in field.fields"
        :key="subField.id"
        :field="subField"
        :model-value="item[subField.id]"
        :disabled="disabled"
        @update:model-value="updateItem(index, subField.id, $event)"
      />
    </div>

    <DsfrButton
      type="button"
      secondary
      :label="field.ui?.addLabel ?? 'Ajouter'"
      icon="ri-add-circle-line"
      :disabled="
        disabled ||
        (!!field.validation?.maxItems &&
          modelValue.length >= field.validation.maxItems)
      "
      @click="addItem"
    />

    <p
      v-if="
        field.validation?.minItems &&
        modelValue.length < field.validation.minItems
      "
      class="fr-error-text"
    >
      Minimum {{ field.validation.minItems }} élément(s) requis
    </p>
  </fieldset>
</template>
