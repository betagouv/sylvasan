<script setup lang="ts">
import { ref } from "vue"
import type { SurveySchema, SurveyField } from "@shared-types/survey"
import NewFieldModal from "./NewFieldModal.vue"
import FieldCard from "./FieldCard.vue"

const schema = defineModel<SurveySchema>({ required: true })

const modalOpened = ref(false)

const addField = (field: SurveyField) => {
  schema.value = { ...schema.value, fields: [...schema.value.fields, field] }
  closeModal()
}
const removeField = (fieldId: string) => {
  schema.value = {
    ...schema.value,
    fields: schema.value.fields.filter((x) => x.id !== fieldId),
  }
}
const closeModal = () => (modalOpened.value = false)
</script>

<template>
  <div class="border border-slate-300 bg-slate-100 rounded p-6">
    <div v-for="field in schema.fields" :key="field.id">
      <FieldCard :field="field" @delete="removeField(field.id)" class="mb-1" />
    </div>
    <hr v-if="schema.fields.length" />
    <div class="flex items-center justify-center">
      <DsfrButton
        label="Ajouter un champ"
        icon="ri-add-circle-line"
        @click="modalOpened = true"
        secondary
      />
    </div>
    <DsfrModal :opened="modalOpened" @close="closeModal">
      <NewFieldModal @add="(f) => addField(f)" />
    </DsfrModal>
  </div>
</template>

<style scoped>
.license-logo {
  height: 1em;
  margin-right: 0.125em;
  display: inline;
}
</style>
