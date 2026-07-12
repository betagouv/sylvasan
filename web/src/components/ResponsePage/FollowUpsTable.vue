<script setup lang="ts">
import { ref, computed } from "vue"
import type { ResponseFull } from "@shared-types/response"
import FollowUpIconName from "./FollowUpIconName.vue"
import ResponseFieldsSection from "./ResponseFieldsSection.vue"

const props = defineProps<{
  followUpResponses: ResponseFull[]
}>()

const headers = ["Suivi", "Auteur", "Date de création", ""]

const formatDate = (iso: string) =>
  new Date(iso).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  })

const respondantName = (r: ResponseFull) => {
  if (!r.respondant) return "—"
  return `${r.respondant.firstName} ${r.respondant.lastName}`.trim() || "—"
}

const rows = computed(() => {
  return props.followUpResponses.map((x) => ({
    rowData: [
      {
        component: FollowUpIconName,
        followUpResponse: x,
      },
      respondantName(x),
      formatDate(x.creationDate),
      {
        component: "DsfrButton",
        label: "Visualiser",
        secondary: true,
        size: "sm",
        icon: "ri-eye-line",
        onClick: () => openModal(x),
      },
    ],
  }))
})
const selectedFollowUp = ref<ResponseFull | null>(null)
const modalOpened = ref(false)

const openModal = (r: ResponseFull) => {
  selectedFollowUp.value = r
  modalOpened.value = true
}

const closeModal = () => {
  modalOpened.value = false
  selectedFollowUp.value = null
}
</script>

<template>
  <div class="mb-4">
    <DsfrTable
      title="Étapes de suivi"
      :headers="headers"
      :no-caption="false"
      :rows="rows"
    >
    </DsfrTable>
  </div>

  <Teleport to="body">
    <DsfrModal
      v-if="selectedFollowUp"
      :opened="modalOpened"
      :title="selectedFollowUp.surveyFollowUp?.title || 'Étape de suivi'"
      @close="closeModal"
    >
      <ResponseFieldsSection :response="selectedFollowUp" />
    </DsfrModal>
  </Teleport>
</template>

<style scoped>
.fr-table :deep(table) {
  @apply table!;
}
</style>
