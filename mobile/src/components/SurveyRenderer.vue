<script setup lang="ts">
import { reactive, computed } from "vue"
import { DsfrInput } from "@gouvminint/vue-dsfr"
import type { SurveySchema, SurveyField } from "@sylvasan/shared"

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
    <div class="fr-form-group">
      <DsfrInput
        v-for="field in textFields"
        :key="field.id"
        v-model="formData[field.id] as string"
        :label="field.label"
        :required="field.required ?? false"
        :label-visible="true"
      />
    </div>

    <DsfrButton type="submit" label="Soumettre" class="fr-mt-3w" />
  </form>
</template>
