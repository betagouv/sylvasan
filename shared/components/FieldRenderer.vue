<script setup lang="ts">
import { computed, useId } from "vue"
import type { SurveyField, VocabularySet } from "@shared-types/survey"
import ArrayField from "./ArrayField.vue"

const props = defineProps<{
  field: SurveyField
  disabled?: boolean
  vocabularies?: VocabularySet[]
}>()

const localId = useId()

const modelValue = defineModel<unknown>()

const arrayModelValue = computed({
  get: () => (modelValue.value as Record<string, unknown>[] | undefined) ?? [],
  set: (val: Record<string, unknown>[]) => {
    modelValue.value = val
  },
})

const resolvedVocab = computed(() =>
  props.field.vocabulary
    ? props.vocabularies?.find((v) => v.code === props.field.vocabulary)
    : undefined
)

const selectOptions = computed(() =>
  resolvedVocab.value
    ? resolvedVocab.value.entries.map((e) => ({ text: e.label, value: e.code }))
    : props.field.ui?.choices
)

const radioOptions = computed(() =>
  resolvedVocab.value
    ? resolvedVocab.value.entries.map((e) => ({ label: e.label, value: e.code }))
    : props.field.ui?.choices
)
</script>

<template>
  <DsfrInputGroup v-if="field.ui?.widget === 'input'">
    <!-- Champ texte -->
    <DsfrInput
      v-model="modelValue"
      :label="field.label"
      :required="field.required ?? false"
      :label-visible="true"
      :hint="field.ui?.hint"
      :placeholder="field.ui?.placeholder"
      :isTextarea="field.ui?.textarea"
      :disabled="disabled"
    />
  </DsfrInputGroup>

  <!-- Champ numérique -->
  <DsfrInputGroup v-else-if="field.ui?.widget === 'number'">
    <DsfrInput
      v-model="modelValue"
      :label="field.label"
      :required="field.required ?? false"
      :label-visible="true"
      :hint="field.ui?.hint"
      type="number"
      :placeholder="field.ui?.placeholder"
      :min="field.validation?.min"
      :max="field.validation?.max"
      :disabled="disabled"
    />
  </DsfrInputGroup>

  <!-- Champ select -->
  <DsfrInputGroup v-else-if="field.ui?.widget === 'select'">
    <DsfrSelect
      :options="selectOptions"
      :label="field.label"
      :required="field.required ?? false"
      v-model="modelValue"
      :disabled="disabled"
    />
  </DsfrInputGroup>

  <!-- Champ checkboxes -->
  <DsfrInputGroup v-else-if="field.ui?.widget === 'checkboxes'">
    <DsfrCheckboxSet
      :options="field.ui?.choices"
      :legend="field.label"
      :required="field.required ?? false"
      v-model="modelValue"
      :disabled="disabled"
    />
  </DsfrInputGroup>

  <!-- Champ switch / interrupteur -->
  <DsfrInputGroup v-else-if="field.ui?.widget === 'switch'">
    <DsfrToggleSwitch
      :label="field.label"
      :required="field.required ?? false"
      :hint="field.ui?.hint"
      :activeText="field.ui?.activeText"
      :inactiveText="field.ui?.inactiveText"
      v-model="modelValue"
      :disabled="disabled"
    />
  </DsfrInputGroup>

  <!-- Champ radio -->
  <DsfrInputGroup v-else-if="field.ui?.widget === 'radio'">
    <DsfrRadioButtonSet
      :name="`radio-${field.id}-${localId}`"
      :options="radioOptions"
      :legend="field.label"
      :required="field.required ?? false"
      v-model="modelValue"
      :disabled="disabled"
    />
  </DsfrInputGroup>

  <!-- Champ date -->
  <DsfrInputGroup v-else-if="field.ui?.widget === 'date'">
    <DsfrInput
      v-model="modelValue"
      :label="field.label"
      :required="field.required ?? false"
      :label-visible="true"
      :hint="field.ui?.hint"
      type="date"
      :min="field.validation?.min"
      :max="field.validation?.max"
      :disabled="disabled"
    />
  </DsfrInputGroup>

  <ArrayField
    v-else-if="field.ui?.widget === 'array'"
    :field="field"
    v-model="arrayModelValue"
    :disabled="disabled"
    :vocabularies="props.vocabularies"
  />

  <hr v-if="field.ui?.widget === 'switch'" />
</template>
