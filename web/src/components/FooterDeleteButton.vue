<script setup lang="ts">
import { ref } from "vue"
import { useApiFetch } from "../utils/data-fetching"
import { useToastStore } from "../stores/toast"
import ConfirmDeleteModal from "./SurveyBuilder/ConfirmDeleteModal.vue"

const props = withDefaults(
  defineProps<{
    url: string
    modalTitle: string
    successMessage: string
    modalBody?: string
  }>(),
  { modalBody: "" }
)

const emit = defineEmits<{ deleted: [] }>()

const toast = useToastStore()
const confirmDeleteOpened = ref(false)

const {
  execute: executeDelete,
  isFetching: isDeleting,
  statusCode,
} = useApiFetch(() => props.url, { immediate: false }).delete()

const onConfirmDelete = async () => {
  await executeDelete()
  confirmDeleteOpened.value = false
  if (statusCode.value === 204) {
    toast.show(props.successMessage, "success")
    emit("deleted")
  } else {
    toast.show("Une erreur s'est produite.", "error")
  }
}
</script>

<template>
  <div class="flex border border-gray-200 p-4 mb-4 items-center">
    <div class="grow"></div>
    <DsfrButton
      label="Supprimer"
      secondary
      :icon="{
        name: 'ri-delete-bin-line',
        fill: '#c9191e',
      }"
      :disabled="isDeleting"
      @click="confirmDeleteOpened = true"
    />
    <ConfirmDeleteModal
      :opened="confirmDeleteOpened"
      :title="modalTitle"
      @confirm="onConfirmDelete"
      @close="confirmDeleteOpened = false"
    >
      {{ modalBody }}
    </ConfirmDeleteModal>
  </div>
</template>
