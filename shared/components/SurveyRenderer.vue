<script setup lang="ts">
import { reactive } from "vue"
import type {
  SurveySchema,
  SurveyField,
  FieldWidget,
} from "@shared-types/survey"

const props = defineProps<{
  schema: SurveySchema
  allowSubmit: boolean
}>()

const emit = defineEmits<{
  submit: [data: Record<string, unknown>]
}>()

const getEmptyValue = (field: SurveyField): any => {
  if (!field.ui?.widget) return ""
  const mapping: Record<FieldWidget, any> = {
    input: "",
    number: "",
    select: "",
    checkboxes: Array(),
    switch: false,
    radio: Array(),
    date: "",
  }
  return mapping[field.ui.widget]
}

const formData = reactive<Record<string, string>>(
  Object.fromEntries(
    props.schema.fields.map((field: SurveyField) => [
      field.id,
      getEmptyValue(field),
    ])
  )
)

function handleSubmit() {
  if (!props.allowSubmit) return
  emit("submit", { ...formData })
}
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <TransitionGroup tag="div" name="field-area" v-if="schema.fields?.length">
      <div v-for="(field, index) in schema.fields" :key="`render-${field.id}`">
        <DsfrInputGroup v-if="field.ui?.widget === 'input'">
          <!-- Champ texte -->
          <DsfrInput
            v-model="formData[field.id]"
            :label="field.label"
            :required="field.required ?? false"
            :label-visible="true"
            :hint="field.ui?.hint"
            :placeholder="field.ui?.placeholder"
            :isTextarea="field.ui?.textarea"
          />
        </DsfrInputGroup>
        <DsfrInputGroup v-if="field.ui?.widget === 'number'">
          <!-- Champ numérique -->
          <DsfrInput
            v-model="formData[field.id]"
            :label="field.label"
            :required="field.required ?? false"
            :label-visible="true"
            :hint="field.ui?.hint"
            type="number"
            :placeholder="field.ui?.placeholder"
            :min="field.validation?.min"
            :max="field.validation?.max"
          />
        </DsfrInputGroup>

        <!-- Champ select -->
        <DsfrInputGroup v-if="field.ui?.widget === 'select'">
          <DsfrSelect
            :options="field.ui?.choices"
            :label="field.label"
            :required="field.required ?? false"
            v-model="formData[field.id]"
          />
        </DsfrInputGroup>

        <!-- Champ checkboxes -->
        <DsfrInputGroup v-if="field.ui?.widget === 'checkboxes'">
          <DsfrCheckboxSet
            :options="field.ui?.choices"
            :legend="field.label"
            :required="field.required ?? false"
            v-model="formData[field.id]"
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
            v-model="formData[field.id]"
          />
        </DsfrInputGroup>
        <hr v-if="field.ui?.widget === 'switch'" />

        <!-- Champ radio -->
        <DsfrInputGroup v-if="field.ui?.widget === 'radio'">
          <DsfrRadioButtonSet
            :name="`radio-${index}`"
            :options="field.ui?.choices"
            :legend="field.label"
            :required="field.required ?? false"
            v-model="formData[field.id]"
          />
        </DsfrInputGroup>
      </div>
    </TransitionGroup>

    <DsfrButton
      v-if="allowSubmit"
      type="submit"
      label="Soumettre"
      id="submit-button"
    />
  </form>
</template>

<style scoped>
.field-area-move {
  transition: transform 0.25s ease;
}
#submit-button {
  margin-top: 16px;
}
div :deep(.fr-input-group) {
  margin-bottom: 24px;
}
</style>
