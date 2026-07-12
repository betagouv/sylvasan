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
import { computed, ref } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useApiFetch } from "../utils/data-fetching"
import { useToastStore } from "../stores/toast"
import ProgressSpinner from "../components/ProgressSpinner.vue"
import ConfirmDeleteModal from "../components/SurveyBuilder/ConfirmDeleteModal.vue"
import FollowUpRow from "../components/FollowUpRow.vue"

const route = useRoute()
const router = useRouter()
const toast = useToastStore()

const { data: survey, isFetching } = useApiFetch(
  `/surveys/${route.params.id}`
).json()

const sortedFollowUps = computed(() =>
  [...(survey.value?.followUps ?? [])].sort((a, b) =>
    a.title.localeCompare(b.title, "fr")
  )
)

const activeAccordion = ref<number>()
const confirmDeleteOpened = ref(false)

const {
  execute: deleteSurvey,
  isFetching: isDeleting,
  statusCode,
} = useApiFetch(`/surveys/${route.params.id}`, { immediate: false }).delete()

const followUpToDelete = ref<{ id: number; title: string } | null>(null)
const confirmDeleteFollowUpOpened = ref(false)

const { execute: executeDeleteFollowUp, statusCode: deleteFollowUpStatusCode } =
  useApiFetch(
    () =>
      `/surveys/${route.params.id}/follow-ups/${followUpToDelete.value?.id}`,
    { immediate: false }
  ).delete()

const onDeleteFollowUp = (followUp: { id: number; title: string }) => {
  followUpToDelete.value = followUp
  confirmDeleteFollowUpOpened.value = true
}

const onConfirmDeleteFollowUp = async () => {
  await executeDeleteFollowUp()
  confirmDeleteFollowUpOpened.value = false
  if (deleteFollowUpStatusCode.value === 204) {
    survey.value.followUps = survey.value.followUps.filter(
      (f: { id: number }) => f.id !== followUpToDelete.value?.id
    )
    toast.show("Le suivi a été supprimé.", "success")
    followUpToDelete.value = null
  } else {
    toast.show("Une erreur s'est produite.", "error")
  }
}

const onConfirmDelete = async () => {
  await deleteSurvey()
  confirmDeleteOpened.value = false
  if (statusCode.value === 204) {
    toast.show("L'enquête a été supprimée.", "success")
    router.push({ name: "/SurveyListPage" })
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
        { to: '/enquetes', text: 'Enquêtes' },
        { text: `Enquête « ${survey?.title || ''} »` },
      ]"
    />
    <div v-if="isFetching" class="flex justify-center my-20">
      <ProgressSpinner />
    </div>
    <div v-else-if="survey" class="mb-4">
      <h1 class="fr-h4">Enquête « {{ survey.title }} »</h1>
      <div class="mb-4 flex gap-2">
        <DsfrBadge type="none" :label="survey.organisation.name" />
        <DsfrBadge type="none" :label="survey.pole?.name || 'Tous les pôles'" />
        <div class="grow"></div>
        <DsfrButton
          label="Dupliquer"
          icon="ri-file-copy-line"
          secondary
          @click="
            router.push({
              name: '/SurveyCreationModificationPage',
              query: { source: survey.id },
            })
          "
        />
        <DsfrButton
          label="Modifier"
          icon="ri-pencil-line"
          :disabled="isDeleting"
          @click="
            router.push({
              name: 'SurveyModification',
              params: { surveyId: survey.id },
            })
          "
        />
      </div>

      <div>
        <router-link
          :to="{
            name: '/ResponseListPage',
            query: { survey: route.params.id },
          }"
        >
          <v-icon icon="ri-file-list-line"></v-icon> Voir les réponses
        </router-link>
      </div>
      <div class="border rounded border-gray-200 bg-gray-50 p-4 mt-8">
        <div class="flex gap-4 mb-4 items-baseline">
          <h3 class="fr-h6 mb-2!">Sous-enquêtes de suivi</h3>
          <div class="grow"></div>
          <DsfrButton
            secondary
            label="Ajouter un suivi"
            icon="ri-add-line"
            size="sm"
            @click="
              router.push({
                name: '/FollowUpCreationModificationPage',
                params: { surveyId: survey.id },
              })
            "
          />
        </div>
        <p>
          Les sous-enquêtes de suivi vous permettent d'ajouter des actions liées
          aux réponses de l'enquête « {{ survey.title }} ».
        </p>

        <div
          v-if="!survey.followUps?.length"
          class="border rounded border-gray-200 p-4 bg-gray-50"
        >
          Vous n'avez pas encore ajouté de sous-enquêtes de suivi.
        </div>
        <div v-else>
          <FollowUpRow
            v-for="followUp in sortedFollowUps"
            :key="`followup-${followUp.id}`"
            :followUp="followUp"
            @delete="onDeleteFollowUp(followUp)"
            @edit="
              () =>
                router.push({
                  name: 'FollowUpModification',
                  params: { surveyId: survey.id, followUpId: followUp.id },
                })
            "
          />
        </div>
      </div>

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

      <div class="mb-4 flex gap-2 border border-gray-200 p-4">
        <div class="grow"></div>

        <DsfrButton
          label="Supprimer l'enquête"
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
    <p class="fr-text--sm text-red-600">
      <v-icon name="ri-alert-line" class="mr-1" />
      Cette action supprimera également toutes les réponses associées à cette
      enquête.
    </p>
  </ConfirmDeleteModal>

  <ConfirmDeleteModal
    :opened="confirmDeleteFollowUpOpened"
    title="Supprimer le suivi ?"
    @confirm="onConfirmDeleteFollowUp"
    @close="confirmDeleteFollowUpOpened = false"
  >
    <p>
      Êtes-vous sûr de vouloir supprimer le suivi
      <strong>« {{ followUpToDelete?.title }} »</strong> ?
    </p>
    <p class="fr-text--sm text-red-600">
      <v-icon name="ri-alert-line" class="mr-1" />
      Cette action supprimera également toutes les réponses associées à ce
      suivi.
    </p>
  </ConfirmDeleteModal>
</template>
