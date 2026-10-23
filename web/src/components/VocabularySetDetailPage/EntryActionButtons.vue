<script setup lang="ts">
import { ref } from "vue"
import { useApiFetch } from "../../utils/data-fetching"
import { useToastStore } from "../../stores/toast"
import ConfirmDeleteModal from "../SurveyBuilder/ConfirmDeleteModal.vue"
import EntryModificationModal from "./EntryModificationModal.vue"
import type { VocabularyEntry } from "@shared-types/survey"

const props = defineProps<{
  entry: VocabularyEntry
  vocabularysetId: string | number
}>()

const emit = defineEmits<{ refreshed: [] }>()

const toast = useToastStore()

const deleteModalOpen = ref(false)

const {
  execute: executeDelete,
  isFetching: isDeleting,
  statusCode: deleteStatusCode,
} = useApiFetch(
  `/admin/vocabularies/${props.vocabularysetId}/entries/${props.entry.id}/`,
  { immediate: false }
).delete()

const onConfirmDelete = async () => {
  await executeDelete()
  deleteModalOpen.value = false
  if (deleteStatusCode.value === 204) {
    toast.show("L'entrée a été supprimée.", "success")
    emit("refreshed")
  } else {
    toast.show("Une erreur s'est produite.", "error")
  }
}

const editModalOpen = ref(false)
</script>

<template>
  <div class="flex gap-2">
    <DsfrButton
      label="Modifier"
      icon="ri-pencil-line"
      tertiary
      size="sm"
      icon-only
      @click="editModalOpen = true"
    />
    <DsfrButton
      label="Supprimer"
      tertiary
      size="sm"
      icon-only
      :icon="{
        name: 'ri-delete-bin-line',
        fill: '#c9191e',
      }"
      :disabled="isDeleting"
      @click="deleteModalOpen = true"
    />

    <EntryModificationModal
      :opened="editModalOpen"
      :entry="entry"
      :vocabularyset-id="vocabularysetId"
      @close="editModalOpen = false"
      @saved="emit('refreshed')"
    />

    <ConfirmDeleteModal
      :opened="deleteModalOpen"
      title="Supprimer l'entrée ?"
      @confirm="onConfirmDelete"
      @close="deleteModalOpen = false"
    >
      Cette action concerne l'entrée
      <span class="font-bold">{{ entry.code }} - {{ entry.label }}</span>
    </ConfirmDeleteModal>
  </div>
</template>
