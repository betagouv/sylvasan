<route lang="json">
{
  "path": "/enquete/:id",
  "meta": {
    "authenticationRequired": true,
    "title": "Enquête"
  }
}
</route>

<script setup lang="ts">
import { ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useApiFetch } from "../utils/data-fetching"
import { useToastStore } from "../stores/toast"
import ProgressSpinner from "../components/ProgressSpinner.vue"
import ConfirmDeleteModal from "../components/SurveyBuilder/ConfirmDeleteModal.vue"

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const { data: survey, isFetching } = useApiFetch(
  `/surveys/${route.params.id}`
).json()

const activeAccordion = ref<number>()
const confirmDeleteOpened = ref(false)

const { execute: deleteSurvey, isFetching: isDeleting } = useApiFetch(
  `/surveys/${route.params.id}`,
  { immediate: false }
).delete()

const onConfirmDelete = async () => {
  await deleteSurvey()
  confirmDeleteOpened.value = false
  toast.show("L'enquête a été supprimée.", "success")
  router.push({ name: "/SurveyListPage" })
}
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/dashboard', text: 'Dashboard' },
        { to: '/enquetes', text: 'Enquêtes' },
        { text: `Enquête ${route.params.id}` },
      ]"
    />
    <div v-if="isFetching" class="flex justify-center my-20">
      <ProgressSpinner />
    </div>
    <div v-else-if="survey" class="mb-4">
      <h1 class="fr-h4">Enquête « {{ survey.title }} »</h1>
      <div class="mb-4 flex gap-2 border border-gray-200 p-4">
        <DsfrBadge type="none" :label="survey.organisation.name" />
        <DsfrBadge type="none" :label="survey.pole?.name || 'Tous les pôles'" />
        <div class="grow"></div>
        <DsfrButton
          label="Supprimer"
          secondary
          icon="ri-delete-bin-line"
          :disabled="isDeleting"
          @click="confirmDeleteOpened = true"
        />
      </div>

      <router-link
        :to="{ name: '/ResponseListPage', query: { survey: route.params.id } }"
      >
        <v-icon icon="ri-file-list-line"></v-icon> Voir les réponses
      </router-link>

      <DsfrAccordionsGroup v-model="activeAccordion" class="mt-10">
        <DsfrAccordion id="accordion-1" title="Schema JSON">
          <div>
            <pre>
<code>
  {{ survey.jsonSchema }}
</code>
            </pre>
          </div>
        </DsfrAccordion>
      </DsfrAccordionsGroup>
    </div>
  </div>

  <ConfirmDeleteModal
    :opened="confirmDeleteOpened"
    title="Supprimer l'enquête ?"
    @confirm="onConfirmDelete"
    @close="confirmDeleteOpened = false"
  >
    <p>
      Êtes-vous sûr de vouloir supprimer l'enquête
      <strong>« {{ survey?.title }} »</strong> ?
    </p>
    <p class="fr-text--sm text-orange-600">
      <v-icon name="ri-alert-line" class="mr-1" />
      Cette action supprimera également toutes les réponses associées à cette
      enquête.
    </p>
  </ConfirmDeleteModal>
</template>
