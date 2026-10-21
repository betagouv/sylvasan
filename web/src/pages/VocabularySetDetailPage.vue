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
import { computed, ref } from "vue"
import { useRouter, useRoute } from "vue-router"
import ProgressSpinner from "../components/ProgressSpinner.vue"
import FooterDeleteButton from "../components/FooterDeleteButton.vue"
import { useApiFetch } from "../utils/data-fetching"
import type { VocabularyEntry } from "@shared-types/survey"
import EntryActionButtons from "../components/VocabularySetDetailPage/EntryActionButtons.vue"
import EntryModificationModal from "../components/VocabularySetDetailPage/EntryModificationModal.vue"

const router = useRouter()
const route = useRoute()

const vocabularySetId = route.params.id as string

const {
  data: vocabularySet,
  isFetching,
  execute: refetchVocabularySet,
} = useApiFetch(`/admin/vocabularies/${vocabularySetId}/`).json()

const rows = computed(() =>
  (vocabularySet.value?.entries ?? []).map((entry: VocabularyEntry) => ({
    rowData: [
      entry.code,
      entry.label,
      entry.position,
      {
        component: EntryActionButtons,
        entry: entry,
        vocabularysetId: vocabularySetId,
        onRefreshed: () => refetchVocabularySet(),
      },
    ],
  }))
)

const headers = [
  { text: "Code", headerAttrs: { id: "th-code" } },
  { text: "Label", headerAttrs: { id: "th-label" } },
  { text: "Position", headerAttrs: { id: "th-position" } },
  { text: "Actions", headerAttrs: { id: "th-actions" } },
]

const addModalOpen = ref(false)
const newEntry: VocabularyEntry = { id: 0, code: "", label: "", position: null }
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
    <div v-if="isFetching && !vocabularySet" class="flex justify-center my-20">
      <ProgressSpinner />
    </div>
    <div v-if="vocabularySet" class="mb-4">
      <h1 class="fr-h4">{{ vocabularySet.code }} - {{ vocabularySet.name }}</h1>

      <div class="flex">
        <h2 class="fr-h5 mb-0! grow">Entrées</h2>
        <DsfrButton
          label="Ajouter une entrée"
          size="md"
          icon="ri-add-line"
          @click="addModalOpen = true"
        />
      </div>
      <DsfrTable :rows="rows" :headers="headers" />
    </div>

    <EntryModificationModal
      :opened="addModalOpen"
      :entry="newEntry"
      :vocabularyset-id="vocabularySetId"
      @close="addModalOpen = false"
      @saved="refetchVocabularySet()"
    />

    <FooterDeleteButton
      :url="`/admin/vocabularies/${vocabularySetId}/`"
      modal-title="Supprimer le référentiel ?"
      :modal-body="`Cette action supprimera également toutes les ${vocabularySet?.entries?.length} entrées du référentiel « ${vocabularySet?.code} »`"
      success-message="Le référentiel a été supprimé."
      @deleted="router.push({ name: '/VocabularySetPage' })"
    />
  </div>
</template>

<style scoped>
.fr-table :deep(table) {
  @apply table!;
}
</style>
