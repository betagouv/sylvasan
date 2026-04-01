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

const moveFieldUp = (fieldId: string) => {
  const fields = [...schema.value.fields]
  const index = fields.findIndex((f) => f.id === fieldId)
  if (index <= 0) return
  ;[fields[index - 1], fields[index]] = [fields[index], fields[index - 1]]
  schema.value = { ...schema.value, fields }
}

const moveFieldDown = (fieldId: string) => {
  const fields = [...schema.value.fields]
  const index = fields.findIndex((f) => f.id === fieldId)
  if (index === -1 || index >= fields.length - 1) return
  ;[fields[index], fields[index + 1]] = [fields[index + 1], fields[index]]
  schema.value = { ...schema.value, fields }
}

const closeModal = () => (modalOpened.value = false)
</script>

<template>
  <div class="border border-slate-300 bg-slate-100 rounded p-6">
    <TransitionGroup tag="div" name="field-list">
      <FieldCard
        v-for="field in schema.fields"
        :key="field.id"
        :field="field"
        @move-up="moveFieldUp(field.id)"
        @move-down="moveFieldDown(field.id)"
        @delete="removeField(field.id)"
        class="mb-1"
      />
    </TransitionGroup>
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
.field-list-move {
  transition: transform 0.25s ease;
}
</style>
