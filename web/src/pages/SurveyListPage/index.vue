<route lang="json">
{
  "path": "/enquetes",
  "meta": {
    "authenticationRequired": true,
    "title": "Mes enquête"
  }
}
</route>

<script setup lang="ts">
import { useApiFetch } from "../../utils/data-fetching"
import { computed } from "vue"
import type { SurveyDisplay } from "@shared-types/api"

const { data: surveys } = useApiFetch("/surveys/").get().json()

const rows = computed(() =>
  surveys.value?.map((survey: SurveyDisplay) => ({
    rowData: [
      survey.id,
      {
        component: "router-link",
        text: survey.title,
        class: "font-bold",
        to: { name: "/SurveyPage/", params: { id: survey.id } },
      },
      survey.organisationName,
      survey.poleName,
      `${new Date(survey.creationDate).toLocaleDateString("fr-FR", {
        day: "numeric",
        month: "long",
      })}`,
    ],
  }))
)

const headers = [
  { text: "ID", headerAttrs: { id: "th-id" } },
  { text: "Titre", headerAttrs: { id: "th-title" } },
  { text: "Organisation", headerAttrs: { id: "th-organisation" } },
  { text: "Pole", headerAttrs: { id: "th-pole" } },
  { text: "Date de création", headerAttrs: { id: "th-creation-date" } },
]
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/dashboard', text: 'Dashboard' },
        { text: 'Mes enquêtes' },
      ]"
    />
    <div
      v-if="surveys && !surveys.length"
      class="border rounded border-slate-200 p-10 mb-10"
    >
      <p class="text-stone-500 italic mb-0!">Aucune enquête n'a été créée</p>
    </div>
    <DsfrTable v-else :rows="rows" :headers="headers" />
  </div>
</template>

<style scoped>
.fr-table :deep(table) {
  @apply table!;
}
</style>
