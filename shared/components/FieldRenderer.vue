<script setup lang="ts">
import { computed, useId } from "vue"
import type { Component } from "vue"
import type {
  SurveyField,
  VocabularySet,
  VocabularyEntry,
  MapValue,
} from "@shared-types/survey"
import ArrayField from "./ArrayField.vue"
import AutocompleteField from "./AutocompleteField.vue"

const props = defineProps<{
  field: SurveyField
  disabled?: boolean
  vocabularies?: VocabularySet[]
  mapComponent?: Component
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
    ? resolvedVocab.value.entries.map((e) => ({
        label: e.label,
        value: e.code,
      }))
    : props.field.ui?.choices
)

const autocompleteEntries = computed((): VocabularyEntry[] => {
  if (resolvedVocab.value) return resolvedVocab.value.entries
  if (props.field.ui?.choices) {
    return (props.field.ui.choices as any[]).map((c) => ({
      code: String(c.value ?? ""),
      label: String(c.text ?? c.label ?? c.value ?? ""),
      position: null,
    }))
  }
  return []
})

const autocompleteValue = computed({
  get: () => (modelValue.value as string | undefined) ?? "",
  set: (val: string) => {
    modelValue.value = val
  },
})

const mapValue = computed({
  get: () => modelValue.value as MapValue | undefined,
  set: (val: MapValue | undefined) => {
    modelValue.value = val
  },
})
</script>

<template>
  <div>
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

    <AutocompleteField
      v-else-if="field.ui?.widget === 'autocomplete'"
      :entries="autocompleteEntries"
      :label="field.label"
      :required="field.required ?? false"
      :hint="field.ui?.hint"
      :disabled="disabled"
      v-model="autocompleteValue"
    />

    <component
      v-else-if="field.ui?.widget === 'map'"
      :is="mapComponent ?? 'div'"
      :label="field.label"
      :required="field.required ?? false"
      :hint="field.ui?.hint"
      :disabled="disabled"
      v-model="mapValue"
    />

    <hr v-if="field.ui?.widget === 'switch'" />
  </div>
</template>
