<script setup lang="ts">
import type { SurveyField } from "../types/survey"
import FieldRenderer from "./FieldRenderer.vue"
import { getEmptyValue } from "../utils/survey"

const createEmptyItem = () =>
  Object.fromEntries(
    (props.field.fields ?? []).map((f) => [f.id, getEmptyValue(f)])
  )

const props = defineProps<{
  field: SurveyField
  disabled?: boolean
}>()

const modelValue = defineModel<Record<string, unknown>[]>({ default: () => [] })

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
  <fieldset class="border border-slate-200 rounded p-3 mb-4 bg-[#f8fafc]">
    <legend class="fr-label px-2">{{ field.label }}</legend>

    <p
      v-if="!modelValue || !modelValue.length"
      class="font-medium fr-text--sm text-gray-500"
    >
      Aucun élément ajouté. Pour ajouter des éléments cliquez sur le bouton
      ci-dessous.
    </p>

    <div
      v-for="(item, index) in modelValue"
      :key="`item ${index}`"
      class="border border-slate-200 rounded p-3 mb-3 relative bg-white"
    >
      <div class="flex justify-end">
        <DsfrButton
          @click="removeItem(index)"
          tertiary
          icon-only
          :disabled="disabled"
          size="sm"
          no-outline
          :icon="{ name: 'ri-close-circle-fill' }"
        />
      </div>

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
      class="fr-info-text"
    >
      Minimum {{ field.validation.minItems }} élément(s) requis
    </p>

    <p
      v-if="
        field.validation?.maxItems &&
        modelValue.length >= field.validation.maxItems
      "
      class="fr-info-text"
    >
      Maximum de {{ field.validation.maxItems }} éléments atteint
    </p>
  </fieldset>
</template>
