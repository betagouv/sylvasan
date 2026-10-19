<route lang="json">
{
  "path": "/referentiels/:id",
  "meta": {
    "authenticationRequired": true,
    "title": "Mon référentiel"
  }
}
</route>

<script setup lang="ts">
import { computed } from "vue"
import { useRouter, useRoute } from "vue-router"
import { useToastStore } from "../stores/toast"
import ProgressSpinner from "../components/ProgressSpinner.vue"
import { useApiFetch } from "../utils/data-fetching"
import type { VocabularySet, VocabularyEntry } from "@shared-types/survey"

const toast = useToastStore()
const router = useRouter()
const route = useRoute()

const { data: vocabularySet, isFetching } = useApiFetch(
  `/admin/vocabularies/${route.params.id}/`
).json()

const rows = computed(() =>
  (vocabularySet.value?.entries ?? []).map((entry: VocabularyEntry) => ({
    rowData: [entry.code, entry.label, entry.position, ""],
  }))
)

const headers = [
  { text: "Code", headerAttrs: { id: "th-code" } },
  { text: "Label", headerAttrs: { id: "th-label" } },
  { text: "Position", headerAttrs: { id: "th-position" } },
  { text: "Actions", headerAttrs: { id: "th-actions" } },
]
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/dashboard', text: 'Dashboard' },
        { to: '/referentiels', text: 'Mes référentiels' },
        { text: `Référentiel « ${vocabularySet?.code || ''} »` },
      ]"
    />
    <div v-if="isFetching" class="flex justify-center my-20">
      <ProgressSpinner />
    </div>
    <div v-else-if="vocabularySet" class="mb-4">
      <h1 class="fr-h4">{{ vocabularySet.code }} - {{ vocabularySet.name }}</h1>

      <h2 class="fr-h5">Entrées</h2>
      <DsfrTable :rows="rows" :headers="headers" />
    </div>
  </div>
</template>

<style scoped>
.fr-table :deep(table) {
  @apply table!;
}
</style>
