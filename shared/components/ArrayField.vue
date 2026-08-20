<script setup lang="ts">
import { ref, watch } from "vue"
import type { Component } from "vue"
import type { SurveyField, VocabularySet } from "../types/survey"
import FieldRenderer from "./FieldRenderer.vue"
import { getEmptyValue, evaluateCondition } from "../utils/survey"
import { getDefaultValue } from "../utils/defaultValues"

const createEmptyItem = () =>
  Object.fromEntries(
    (props.field.fields ?? []).map((f) => [
      f.id,
      getDefaultValue(f) ?? getEmptyValue(f),
    ])
  )

const props = defineProps<{
  field: SurveyField
  disabled?: boolean
  forceValidate?: boolean
  vocabularies?: VocabularySet[]
  mapComponent?: Component
}>()

const modelValue = defineModel<Record<string, unknown>[]>({ default: () => [] })

// Clés stables par item pour que TransitionGroup puisse animer les déplacements.
// On maintient ce tableau en parallèle de modelValue via chaque mutation.
let nextKey = 0
const itemKeys = ref<number[]>(
  Array.from({ length: modelValue.value.length }, () => nextKey++)
)

const addItem = () => {
  if (
    props.field.validation?.maxItems &&
    modelValue.value.length >= props.field.validation.maxItems
  )
    return
  modelValue.value = [...modelValue.value, createEmptyItem()]
  itemKeys.value = [...itemKeys.value, nextKey++]
}

const removeItem = (index: number) => {
  modelValue.value = modelValue.value.filter((_, i) => i !== index)
  itemKeys.value = itemKeys.value.filter((_, i) => i !== index)
}

const moveItem = (index: number, direction: -1 | 1) => {
  const target = index + direction
  if (target < 0 || target >= modelValue.value.length) return
  const copy = [...modelValue.value]
  ;[copy[index], copy[target]] = [copy[target], copy[index]]
  modelValue.value = copy
  const keyCopy = [...itemKeys.value]
  ;[keyCopy[index], keyCopy[target]] = [keyCopy[target], keyCopy[index]]
  itemKeys.value = keyCopy
}

const updateItem = (index: number, fieldId: string, value: unknown) => {
  modelValue.value = modelValue.value.map((item, i) =>
    i === index ? { ...item, [fieldId]: value } : item
  )
}

const isSubFieldVisible = (
  subField: SurveyField,
  item: Record<string, unknown>
): boolean => {
  if (!subField.condition) return true
  return evaluateCondition(subField.condition, item)
}

watch(
  () =>
    modelValue.value.map((item) =>
      (props.field.fields ?? []).map((f) => isSubFieldVisible(f, item))
    ),
  (newVisibility, oldVisibility) => {
    let needsUpdate = false
    const updated = modelValue.value.map((item, i) => {
      const newVis = newVisibility[i]
      const oldVis = oldVisibility?.[i]
      let result = item
      ;(props.field.fields ?? []).forEach((subField, j) => {
        if ((!oldVis || oldVis[j]) && !newVis[j]) {
          result = { ...result, [subField.id]: getEmptyValue(subField) }
          needsUpdate = true
        }
      })
      return result
    })
    if (needsUpdate) modelValue.value = updated
  },
  { immediate: true }
)
</script>

<template>
  <fieldset class="border border-slate-200 rounded p-3 mb-4 bg-[#f8fafc]">
    <legend class="fr-label px-2">{{ field.label }}</legend>

    <p
      v-if="!modelValue || !modelValue.length"
      class="font-medium fr-text--sm text-gray-500"
    >
      Aucun élément ajouté. Pour en ajouter cliquez sur le bouton ci-dessous.
    </p>

    <TransitionGroup tag="div" name="array-item">
      <div
        v-for="(item, index) in modelValue"
        :key="itemKeys[index]"
        class="border border-slate-300 rounded p-3 mb-3 relative bg-white"
      >
        <div class="flex justify-between border-b mb-2 pb-1 border-gray-200">
          <div v-if="modelValue.length > 1" class="flex gap-1">
            <DsfrButton
              @click="moveItem(index, -1)"
              tertiary
              icon-only
              :disabled="disabled || index === 0"
              size="sm"
              no-outline
              :icon="{ name: 'ri-arrow-up-line' }"
            />
            <DsfrButton
              @click="moveItem(index, 1)"
              tertiary
              icon-only
              :disabled="disabled || index === modelValue.length - 1"
              size="sm"
              no-outline
              :icon="{ name: 'ri-arrow-down-line' }"
            />
          </div>
          <div v-else></div>
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

        <template v-for="subField in field.fields" :key="subField.id">
          <FieldRenderer
            v-if="isSubFieldVisible(subField, item)"
            :field="subField"
            :model-value="item[subField.id]"
            :disabled="disabled"
            :force-validate="forceValidate"
            :vocabularies="props.vocabularies"
            :map-component="props.mapComponent"
            @update:model-value="updateItem(index, subField.id, $event)"
          />
        </template>
      </div>
    </TransitionGroup>

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

<style scoped>
.array-item-move {
  transition: transform 0.25s ease;
}
</style>
