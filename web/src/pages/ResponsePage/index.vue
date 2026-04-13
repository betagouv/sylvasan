<route lang="json">
{
  "path": "/response/:id",
  "meta": {
    "authenticationRequired": true,
    "title": "Réponse"
  }
}
</route>

<script setup lang="ts">
import { useRoute } from "vue-router"
import { useApiFetch } from "../../utils/data-fetching"
import { computed } from "vue"
import SurveyRenderer from "@shared-components/SurveyRenderer.vue"

const route = useRoute()

const { data: response } = useApiFetch(`/responses/${route.params.id}`).json()

const rows = computed(() => {
  if (!response) return {}

  return Object.entries(response.value.data).map((x: any) => ({
    rowData: [x[0], `${x[1]}`],
  }))
})

const headers = [
  { text: "ID du champ", headerAttrs: { id: "th-id" } },
  { text: "Réponse", headerAttrs: { id: "th-response" } },
]
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/dashboard', text: 'Dashboard' },
        { to: '/reponses', text: 'Réponses' },
        { text: `Réponse « ${response?.survey.title} »` },
      ]"
    />
    <div v-if="response">
      <h1 class="fr-h4">Réponse à l'enquête « {{ response.survey.title }} »</h1>
      <p class="m-0! font-medium fr-badge">
        <v-icon name="ri-user-line" scale="0.8" class="mr-2" />
        {{ response.respondant?.firstName }} {{ response.respondant?.lastName }}
      </p>
      <div class="grid grid-cols-12 gap-4">
        <div class="col-span-12 sm:col-span-6 md:col-span-7 lg:col-span-8">
          <DsfrTable :rows="rows" :headers="headers" />
        </div>
        <!-- Preview -->
        <div class="col-span-12 sm:col-span-6 md:col-span-5 lg:col-span-4">
          <div
            v-if="response.survey.jsonSchema"
            class="border rounded border-slate-300 p-4"
          >
            <SurveyRenderer
              :schema="response.survey.jsonSchema"
              :allowSubmit="false"
              :readonly="true"
              :prefillData="response.data"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fr-table :deep(table) {
  @apply table!;
}
</style>
