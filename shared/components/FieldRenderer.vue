<script setup lang="ts">
import { computed, ref, useId, watchEffect } from "vue"
import type { Component } from "vue"
import type {
  SurveyField,
  VocabularySet,
  VocabularyEntry,
  MapValue,
  ImageItem,
} from "@shared-types/survey"
import ArrayField from "./ArrayField.vue"
import AutocompleteField from "./AutocompleteField.vue"
import ImagesField from "./ImagesField.vue"
import { validateField } from "@shared-utils/validateField"

const props = defineProps<{
  field: SurveyField
  disabled?: boolean
  forceValidate?: boolean
  vocabularies?: VocabularySet[]
  mapComponent?: Component
  resolveImagePath?: (path: string) => Promise<string | null>
}>()

const localId = useId()

const emit = defineEmits<{
  busyChange: [value: boolean]
}>()

const modelValue = defineModel<unknown>()

const arrayModelValue = computed({
  get: () => (modelValue.value as Record<string, unknown>[] | undefined) ?? [],
  set: (val: Record<string, unknown>[]) => {
    modelValue.value = val
  },
})

const imagesModelValue = computed({
  get: () => (modelValue.value as ImageItem[] | undefined) ?? [],
  set: (val: ImageItem[]) => {
    modelValue.value = val
  },
})

const resolvedVocab = computed(() =>
  props.field.vocabulary
    ? props.vocabularies?.find((v) => v.code === props.field.vocabulary)
    : undefined
)

const selectOptions = computed(() =>
  resolvedVocab.value && resolvedVocab.value.entries
    ? resolvedVocab.value.entries.map((e) => ({ text: e.label, value: e.code }))
    : props.field.ui?.choices
)

const radioOptions = computed(() =>
  resolvedVocab.value && resolvedVocab.value.entries
    ? resolvedVocab.value.entries.map((e) => ({
        label: e.label,
        value: e.code,
      }))
    : props.field.ui?.choices
)

const autocompleteEntries = computed((): VocabularyEntry[] => {
  if (resolvedVocab.value?.entries) return resolvedVocab.value.entries
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

const rootRef = ref<HTMLElement | null>(null)
const touched = ref(false)
watchEffect(() => {
  if (props.forceValidate) touched.value = true
})

const onFocusOut = (e: FocusEvent) => {
  if (!rootRef.value?.contains(e.relatedTarget as Node)) {
    touched.value = true
  }
}

const errorMessage = computed(() =>
  touched.value && !props.disabled
    ? validateField(props.field, modelValue.value)
    : null
)

if (
  props.field.ui?.widget === "date" &&
  props.field.default === "today" &&
  !modelValue.value
) {
  const d = new Date()
  const mm = String(d.getMonth() + 1).padStart(2, "0")
  const dd = String(d.getDate()).padStart(2, "0")
  modelValue.value = `${d.getFullYear()}-${mm}-${dd}`
}
</script>

<template>
  <div ref="rootRef" @focusout="onFocusOut">
    <DsfrInputGroup
      v-if="field.ui?.widget === 'input'"
      :error-message="errorMessage ?? undefined"
    >
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
        :is-invalid="!!errorMessage"
      />
    </DsfrInputGroup>

    <!-- Champ numérique -->
    <DsfrInputGroup
      v-else-if="field.ui?.widget === 'number'"
      :error-message="errorMessage ?? undefined"
    >
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
        :step="
          field.validation?.numberType === 'integer'
            ? 1
            : field.validation?.numberType === 'float'
            ? 'any'
            : undefined
        "
        :is-invalid="!!errorMessage"
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
        :defaultUnselectedText="field.ui?.unselectedText"
        :error-message="errorMessage ?? undefined"
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
        :error-message="errorMessage ?? undefined"
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
        :error-message="errorMessage ?? undefined"
      />
    </DsfrInputGroup>

    <!-- Champ date -->
    <DsfrInputGroup
      v-else-if="field.ui?.widget === 'date'"
      :error-message="errorMessage ?? undefined"
    >
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
        :is-invalid="!!errorMessage"
      />
    </DsfrInputGroup>

    <ArrayField
      v-else-if="field.ui?.widget === 'array'"
      :field="field"
      v-model="arrayModelValue"
      :disabled="disabled"
      :force-validate="forceValidate"
      :vocabularies="props.vocabularies"
      :map-component="mapComponent"
    />

    <AutocompleteField
      v-else-if="field.ui?.widget === 'autocomplete'"
      :entries="autocompleteEntries"
      :label="field.label"
      :required="field.required ?? false"
      :hint="field.ui?.hint"
      :disabled="disabled"
      :placeholder="field.ui?.placeholder"
      :error-message="errorMessage ?? undefined"
      v-model="autocompleteValue"
    />

    <ImagesField
      v-else-if="field.ui?.widget === 'image'"
      :field="field"
      v-model="imagesModelValue as ImageItem[]"
      :disabled="disabled"
      :resolveImagePath="resolveImagePath"
      @busyChange="(val) => emit('busyChange', val)"
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
