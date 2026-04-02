<script setup lang="ts">
import { reactive } from "vue"
import type { SurveySchema, SurveyField } from "@shared-types/survey"

const props = defineProps<{
  schema: SurveySchema
  allowSubmit: boolean
}>()

const emit = defineEmits<{
  submit: [data: Record<string, unknown>]
}>()

const formData = reactive<Record<string, string>>(
  Object.fromEntries(
    props.schema.fields.map((field: SurveyField) => [field.id, ""])
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
      <DsfrInputGroup
        v-for="field in schema.fields"
        :key="`render-${field.id}`"
      >
        <!-- Champ texte -->
        <DsfrInput
          v-model="formData[field.id]"
          :label="field.label"
          :required="field.required ?? false"
          :label-visible="true"
          :hint="field.ui?.hint"
          :placeholder="field.ui?.placeholder"
          v-if="field.ui?.widget === 'input'"
        />

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
          v-else-if="field.ui?.widget === 'number'"
        />
      </DsfrInputGroup>
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
</style>
