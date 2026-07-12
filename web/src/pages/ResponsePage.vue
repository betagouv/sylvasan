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
import { ref, computed, watch } from "vue"
import { useRoute } from "vue-router"
import { useApiFetch } from "../utils/data-fetching.ts"
import type { SurveyField, ImageItem } from "@shared-types/survey"
import SurveyRenderer from "@shared-components/SurveyRenderer.vue"
import ImageViewer from "@shared-components/ImageViewer.vue"
import { storeToRefs } from "pinia"
import { useRootStore } from "../stores/root.ts"
import MapField from "../components/MapField.vue"
import ProgressSpinner from "../components/ProgressSpinner.vue"
import ConfirmDeleteModal from "../components/SurveyBuilder/ConfirmDeleteModal.vue"
import { useToastStore } from "../stores/toast"
import { useRouter } from "vue-router"
import FollowUpsTable from "../components/ResponsePage/FollowUpsTable.vue"
import ResponseFieldsSection from "../components/ResponsePage/ResponseFieldsSection.vue"

const router = useRouter()
const route = useRoute()
const rootStore = useRootStore()
const { vocabularyDetails } = storeToRefs(rootStore)

const { data: response, isFetching } = useApiFetch(
  `/responses/${route.params.id}`
).json()

// Codes des vocabulaires utilisés dans cette enquête (sous-ensemble de tous les vocabulaires)
const surveyCodes = ref<string[]>([])

// Vocabulaires avec leurs entrées, limités à ceux référencés dans l'enquête.
// isReady bloque le rendu jusqu'à ce que les entrées soient disponibles.
const isReady = ref(false)

const surveyVocabularies = computed(() =>
  surveyCodes.value.map((code) => vocabularyDetails.value[code]).filter(Boolean)
)

// On surveille aussi isFetching pour débloquer la page si la requête échoue
// (response resterait null et le watch sur response seul ne se déclencherait pas)
watch([response, isFetching], async ([val, fetching]) => {
  if (fetching) return
  if (!val) {
    isReady.value = true
    return
  }
  const schema = val.survey?.jsonSchema
  const allFields: SurveyField[] = [
    ...(schema?.fields ?? []),
    ...(schema?.fields ?? []).flatMap((f: SurveyField) => f.fields ?? []),
  ]
  surveyCodes.value = [
    ...new Set(
      allFields.filter((f) => f.vocabulary).map((f) => f.vocabulary as string)
    ),
  ]
  // Récupération en best-effort : un échec individuel n'empêche pas l'affichage
  await Promise.allSettled(
    surveyCodes.value.map((code) => rootStore.fetchVocabularyDetail(code))
  )
  isReady.value = true
})

const confirmDeleteOpened = ref(false)
const toast = useToastStore()

const viewerOpen = ref(false)
const viewerImages = ref<ImageItem[]>([])
const viewerIndex = ref(0)

const openViewer = (images: ImageItem[], index: number) => {
  viewerImages.value = images
  viewerIndex.value = index
  viewerOpen.value = true
}

const respondantName = computed(() => {
  const respondant = response.value.respondant
  if (!respondant) return "—"
  return `${respondant.firstName} ${respondant.lastName || ""}`
})

const {
  execute: deleteResponse,
  isFetching: isDeleting,
  statusCode,
} = useApiFetch(`/responses/${route.params.id}`, { immediate: false }).delete()

const onConfirmDelete = async () => {
  await deleteResponse()
  confirmDeleteOpened.value = false
  if (statusCode.value === 204) {
    toast.show("La réponse a été supprimée.", "success")
    router.push({ name: "/ResponseListPage" })
  } else {
    toast.show("Une erreur s'est produite.", "error")
  }
}
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/dashboard', text: 'Dashboard' },
        { to: '/reponses', text: 'Réponses' },
        { text: `Réponse « ${response?.survey?.title || ''} »` },
      ]"
    />
    <div v-if="isFetching || !isReady" class="flex justify-center my-20">
      <ProgressSpinner />
    </div>
    <div v-else-if="response">
      <div class="flex border border-gray-200 p-4 mb-4 items-center">
        <h1 class="fr-h4 mb-0!">
          Réponse à l'enquête « {{ response.survey.title }} »
        </h1>
        <div class="grow"></div>
      </div>
      <div class="mb-6">
        <p class="font-medium fr-badge">
          <v-icon name="ri-user-line" scale="0.8" class="mr-2" />
          {{ respondantName }}
        </p>
      </div>

      <div class="grid grid-cols-12 gap-4">
        <div class="col-span-12 sm:col-span-6 md:col-span-7 lg:col-span-8">
          <ResponseFieldsSection
            :response="response"
            @open-viewer="openViewer"
          />
        </div>
        <!-- Preview -->
        <div class="col-span-12 sm:col-span-6 md:col-span-5 lg:col-span-4 mb-4">
          <div
            v-if="response.survey.jsonSchema"
            class="border rounded border-slate-300 p-4"
          >
            <SurveyRenderer
              :schema="response.survey.jsonSchema"
              :allowSubmit="false"
              :readonly="true"
              :prefillData="response.data"
              :vocabularies="surveyVocabularies"
              :mapComponent="MapField"
            />
          </div>
        </div>
      </div>

      <FollowUpsTable
        v-if="response?.followUpResponses?.length"
        :follow-up-responses="response.followUpResponses"
      />

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
      </div>
    </div>
  </div>

  <ImageViewer
    :images="viewerImages"
    :startIndex="viewerIndex"
    :opened="viewerOpen"
    @close="viewerOpen = false"
  />
  <ConfirmDeleteModal
    :opened="confirmDeleteOpened"
    title="Supprimer la réponse ?"
    @confirm="onConfirmDelete"
    @close="confirmDeleteOpened = false"
  />
</template>
