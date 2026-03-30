<script setup lang="ts">
import { reactive, computed } from "vue"
import type { SurveySchema, SurveyField } from "@shared-types/survey"

const props = defineProps<{
  schema: SurveySchema
}>()

const emit = defineEmits<{
  submit: [data: Record<string, unknown>]
}>()

const formData = reactive<Record<string, string>>(
  Object.fromEntries(props.schema.fields.map((field) => [field.id, ""]))
)

const textFields = computed(() =>
  props.schema.fields.filter(
    (f): f is SurveyField & { type: "text" } => f.type === "text"
  )
)

function handleSubmit() {
  emit("submit", { ...formData })
}
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <DsfrInputGroup v-for="field in textFields" :key="field.id">
      <DsfrInput
        v-model="formData[field.id]"
        :label="field.label"
        :required="field.required ?? false"
        :label-visible="true"
      />
    </DsfrInputGroup>

    <DsfrButton type="submit" label="Soumettre" />
  </form>
</template>
