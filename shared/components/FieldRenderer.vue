<script setup lang="ts">
import { computed } from "vue"
import type { SurveyField } from "@shared-types/survey"
import ArrayField from "./ArrayField.vue"

const props = defineProps<{
  field: SurveyField
  disabled?: boolean
}>()

const modelValue = defineModel<unknown>()

const arrayModelValue = computed({
  get: () => (modelValue.value as Record<string, unknown>[] | undefined) ?? [],
  set: (val: Record<string, unknown>[]) => {
    modelValue.value = val
  },
})
</script>

<template>
  <DsfrInputGroup v-if="field.ui?.widget === 'input'">
    <!-- Champ texte -->
    <DsfrInput
      v-model="field.id"
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
  <DsfrInputGroup v-if="field.ui?.widget === 'number'">
    <DsfrInput
      v-model="field.id"
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
  <DsfrInputGroup v-if="field.ui?.widget === 'select'">
    <DsfrSelect
      :options="field.ui?.choices"
      :label="field.label"
      :required="field.required ?? false"
      v-model="field.id"
      :disabled="disabled"
    />
  </DsfrInputGroup>

  <!-- Champ checkboxes -->
  <DsfrInputGroup v-if="field.ui?.widget === 'checkboxes'">
    <DsfrCheckboxSet
      :options="field.ui?.choices"
      :legend="field.label"
      :required="field.required ?? false"
      v-model="field.id"
      :disabled="disabled"
    />
  </DsfrInputGroup>

  <!-- Champ switch / interrupteur -->
  <DsfrInputGroup v-if="field.ui?.widget === 'switch'">
    <DsfrToggleSwitch
      :label="field.label"
      :required="field.required ?? false"
      :hint="field.ui?.hint"
      :activeText="field.ui?.activeText"
      :inactiveText="field.ui?.inactiveText"
      v-model="field.id"
      :disabled="disabled"
    />
  </DsfrInputGroup>
  <hr v-if="field.ui?.widget === 'switch'" />

  <!-- Champ radio -->
  <DsfrInputGroup v-if="field.ui?.widget === 'radio'">
    <DsfrRadioButtonSet
      :name="`radio-${field.id}`"
      :options="field.ui?.choices"
      :legend="field.label"
      :required="field.required ?? false"
      v-model="field.id"
      :disabled="disabled"
    />
  </DsfrInputGroup>

  <!-- Champ date -->
  <DsfrInputGroup v-if="field.ui?.widget === 'date'">
    <DsfrInput
      v-model="field.id"
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
  />
</template>
