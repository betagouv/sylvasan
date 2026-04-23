<route lang="json">
{
  "path": "/reponses",
  "meta": {
    "authenticationRequired": true,
    "title": "Réponses à mes enquêtes"
  }
}
</route>

<script setup lang="ts">
import { useApiFetch } from "../../utils/data-fetching"
import { computed } from "vue"
import type { ResponseDisplay } from "@shared-types/response"

const { data: responses } = useApiFetch("/responses/").get().json()

const rows = computed(() =>
  responses.value?.map((response: ResponseDisplay) => ({
    rowData: [
      response.id,
      {
        component: "router-link",
        text: `${response.survey.title}`,
        class: "font-bold",
        to: { name: "/ResponsePage/", params: { id: response.id } },
      },
      `${response.respondant?.firstName} ${response.respondant?.lastName}`,
      `${new Date(response.creationDate).toLocaleDateString("fr-FR", {
        day: "numeric",
        month: "long",
      })}`,
    ],
  }))
)

const headers = [
  { text: "ID", headerAttrs: { id: "th-id" } },
  { text: "Enquête", headerAttrs: { id: "th-survey" } },
  { text: "Répondant", headerAttrs: { id: "th-respondent" } },
  { text: "Date de création", headerAttrs: { id: "th-creation-date" } },
]
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[{ to: '/dashboard', text: 'Dashboard' }, { text: 'Réponses' }]"
    />
    <div
      v-if="responses && !responses.length"
      class="border rounded border-slate-200 p-10 mb-10"
    >
      <p class="text-stone-500 italic mb-0!">
        Aucune réponse reçue pour le moment.
      </p>
    </div>
    <DsfrTable v-else :rows="rows" :headers="headers" />
  </div>
</template>

<style scoped>
.fr-table :deep(table) {
  @apply table!;
}
</style>
