<script setup lang="ts">
import type { ResponseFull } from "@shared-types/response"
import { computed } from "vue"
import FollowUpIconName from "./FollowUpIconName.vue"

const props = defineProps<{
  followUpResponses: ResponseFull[]
}>()

const headers = ["Suivi", "Auteur", "Date de création"]

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
    ],
  }))
})
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
</template>

<style scoped>
.fr-table :deep(table) {
  @apply table!;
}
</style>
