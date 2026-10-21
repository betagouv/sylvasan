<script setup lang="ts">
import * as z from "zod"
import { ref, watch } from "vue"
import { ZodError } from "zod"
import { useApiFetch } from "../../utils/data-fetching"
import { useToastStore } from "../../stores/toast"
import type { VocabularyEntry } from "@shared-types/survey"

const props = defineProps<{
  opened: boolean
  entry: VocabularyEntry
  vocabularysetId: string | number
}>()

const emit = defineEmits<{ close: []; saved: [] }>()

const toast = useToastStore()

const payload = ref({
  code: props.entry.code,
  label: props.entry.label,
  position: props.entry.position as number | null | string,
})

watch(
  () => props.opened,
  (isOpen) => {
    if (isOpen) {
      payload.value = {
        code: props.entry.code,
        label: props.entry.label,
        position: props.entry.position,
      }
      formErrors.value = { formErrors: [], fieldErrors: {} }
    }
  }
)

const validator = z.object({
  code: z.string().min(1, "Le code est obligatoire"),
  label: z.string().min(1, "Le libellé est obligatoire"),
  position: z.preprocess(
    (v) => (v === "" || v === null || v === undefined ? null : Number(v)),
    z.number().int("La position doit être un entier").nullable()
  ),
})

const formErrors = ref<{
  formErrors: string[]
  fieldErrors: Record<string, string[]>
}>({ formErrors: [], fieldErrors: {} })

const clearFieldError = (field: string) => {
  if (formErrors.value.fieldErrors[field])
    delete formErrors.value.fieldErrors[field]
}

const {
  execute: executePatch,
  isFetching: isSaving,
  statusCode,
} = useApiFetch(
  () =>
    `/admin/vocabularies/${props.vocabularysetId}/entries/${props.entry.id}/`,
  { immediate: false }
)
  .patch(payload)
  .json()

const onSave = async () => {
  formErrors.value = { formErrors: [], fieldErrors: {} }
  try {
    validator.parse(payload.value)
  } catch (error) {
    if (error instanceof ZodError) formErrors.value = z.flattenError(error)
    return
  }
  await executePatch()
  if (statusCode.value === 200) {
    toast.show("L'entrée a été modifiée.", "success")
    emit("saved")
    emit("close")
  } else {
    toast.show("Une erreur s'est produite.", "error")
  }
}
</script>

<template>
  <DsfrModal
    :opened="opened"
    :title="`Modifier l'entrée « ${entry.code} »`"
    @close="emit('close')"
  >
    <form @submit.prevent="onSave">
      <DsfrInputGroup :error-message="formErrors.fieldErrors.code?.[0]">
        <DsfrInput
          v-model="payload.code"
          label="Code"
          label-visible
          :required="true"
          @update:model-value="clearFieldError('code')"
        />
      </DsfrInputGroup>
      <DsfrInputGroup :error-message="formErrors.fieldErrors.label?.[0]">
        <DsfrInput
          v-model="payload.label"
          label="Libellé"
          label-visible
          :required="true"
          @update:model-value="clearFieldError('label')"
        />
      </DsfrInputGroup>
      <DsfrInputGroup :error-message="formErrors.fieldErrors.position?.[0]">
        <DsfrInput
          v-model="payload.position"
          label="Position"
          label-visible
          type="number"
          @update:model-value="clearFieldError('position')"
        />
      </DsfrInputGroup>
    </form>
    <template #footer>
      <div class="flex justify-end gap-2 w-full">
        <DsfrButton label="Fermer" secondary @click="emit('close')" />
        <DsfrButton
          label="Sauvegarder"
          icon="ri-save-line"
          :disabled="isSaving"
          @click="onSave"
        />
      </div>
    </template>
  </DsfrModal>
</template>
