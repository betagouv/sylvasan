<script setup lang="ts">
import { computed, ref, watch, onMounted } from "vue"
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonButtons,
  IonBackButton,
  useIonRouter,
} from "@ionic/vue"
import { useRoute } from "vue-router"
import { storeToRefs } from "pinia"
import SurveyRenderer from "@shared-components/SurveyRenderer.vue"
import SurveySummary from "../components/SurveySummary.vue"
import MapField from "../components/MapField.vue"
import type { Survey } from "@shared-types/survey"
import type { ResponseFull } from "@shared-types/response"
import { useResponsesStore } from "../stores/responses"
import { useSurveysStore } from "../stores/surveys"
import { useAuthStore } from "../stores/auth"
import { useToastStore } from "../stores/toast"
import { useVocabulariesStore } from "../stores/vocabularies"
import { useApiFetch } from "../utils/data-fetching"
import {
  loadImagesFromFilesystem,
  resolveLocalImageSrc,
} from "../utils/imageStorage"
import { validateResponse } from "@shared-utils/validateField"
import { evaluateCondition } from "@shared-utils/survey"

const route = useRoute()
const router = useIonRouter()
const responsesStore = useResponsesStore()
const surveysStore = useSurveysStore()
const authStore = useAuthStore()
const toast = useToastStore()
const { vocabularySets } = storeToRefs(useVocabulariesStore())

const responseId = route.params.responseId as string
const followUpId = Number(route.params.followUpId)

onMounted(() => responsesStore.loadFromStorage())

const response = computed(
  () =>
    responsesStore.getByLocalId(responseId) ??
    responsesStore.getResponseById(Number(responseId))
)

const surveyId = computed(() => {
  const r = response.value
  if (!r) return null
  return "surveyId" in r ? r.surveyId : r.survey?.id ?? null
})

const survey = computed(() =>
  surveyId.value != null ? surveysStore.getSurveyById(surveyId.value) : undefined
)

const followUp = computed(() =>
  survey.value?.followUps.find((fu) => fu.id === followUpId)
)

const parentBackendId = computed<number | null>(() => {
  const r = response.value
  if (!r || !("id" in r)) return null
  return (r as ResponseFull).id
})

const label = computed(
  () => followUp.value?.actionLabel?.trim() || followUp.value?.title || ""
)

const followUpAsSurvey = computed((): Survey | undefined => {
  const fu = followUp.value
  if (!fu?.jsonSchema) return undefined
  return {
    id: fu.id,
    title: label.value,
    jsonSchema: fu.jsonSchema,
    surveyType: "",
    followUps: [],
  }
})

// Form state
const currentFormData = ref<Record<string, unknown>>({})
const showSummary = ref(false)
const summaryData = ref<Record<string, unknown>>({})
const saving = ref(false)
const forceValidate = ref(false)

watch(showSummary, (val, prev) => {
  if (!val && prev) forceValidate.value = true
})

const summaryHasErrors = computed(() => {
  const fields = followUp.value?.jsonSchema?.fields ?? []
  const visibleFieldIds = new Set(
    fields
      .filter(
        (f) => !f.condition || evaluateCondition(f.condition, summaryData.value)
      )
      .map((f) => f.id)
  )
  return (
    Object.keys(validateResponse(fields, summaryData.value, visibleFieldIds))
      .length > 0
  )
})

const onSurveyDone = (data: Record<string, unknown>) => {
  currentFormData.value = data
  summaryData.value = data
  showSummary.value = true
}

const saveResponse = async () => {
  const fu = followUp.value
  const parentId = parentBackendId.value
  if (!fu || !parentId) return
  saving.value = true
  try {
    const submissionData = await loadImagesFromFilesystem(summaryData.value)
    const { response: apiResponse } = await useApiFetch("/responses/")
      .post({
        survey_follow_up: fu.id,
        parent_response: parentId,
        data: submissionData,
        respondant: authStore.loggedUser?.id,
      })
      .json()

    if (apiResponse.value?.ok) {
      toast.show("Votre suivi a été envoyé", "success")
      router.navigate(
        { name: "ResponseSummaryPage", params: { responseId } },
        "back",
        "replace"
      )
    } else {
      toast.show("Une erreur est survenue. Veuillez réessayer.")
    }
  } catch {
    toast.show("Impossible d'envoyer le suivi. Vérifiez votre connexion.")
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button
            :default-href="{
              name: 'FollowUpChooserPage',
              params: { responseId },
            }"
          />
        </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <ion-content>
      <div v-if="!followUp || !followUp.jsonSchema" class="p-4 text-stone-500">
        Suivi introuvable.
      </div>
      <div v-else-if="!parentBackendId" class="p-4 text-stone-500">
        Cette observation n'a pas encore été synchronisée. Synchronisez-la
        avant d'ajouter un suivi.
      </div>
      <template v-else>
        <!-- Contextual banner -->
        <div
          class="p-4 flex items-center gap-4 border-b border-slate-200"
          :style="{ background: (followUp.actionColor ?? '#000091') + '20' }"
        >
          <div
            class="shrink-0 w-12 h-12 rounded-full flex items-center justify-center"
            :style="{ background: followUp.actionColor ?? '#000091' }"
          >
            <v-icon :name="followUp.actionIcon" scale="1.4" class="text-white" />
          </div>
          <div>
            <p class="fr-text--sm text-stone-500 mb-0!">Ajout d'un suivi</p>
            <h2 class="fr-h6 mb-0!">{{ label }}</h2>
          </div>
        </div>

        <!-- Form -->
        <div v-show="!showSummary" class="box-border! p-4!">
          <SurveyRenderer
            :allowSubmit="true"
            :schema="followUp.jsonSchema"
            :forceValidate="forceValidate"
            :vocabularies="vocabularySets"
            :mapComponent="MapField"
            :resolveImagePath="resolveLocalImageSrc"
            @done="onSurveyDone"
            @change="currentFormData = $event"
          />
        </div>

        <!-- Summary -->
        <template v-if="showSummary && followUpAsSurvey">
          <SurveySummary :survey="followUpAsSurvey" :data="summaryData" />
          <div class="flex justify-between p-4">
            <DsfrButton
              label="Modifier"
              secondary
              icon="ri-edit-line"
              :disabled="saving"
              @click="showSummary = false"
            />
            <DsfrButton
              label="Sauvegarder"
              :icon="
                saving
                  ? { name: 'ri-refresh-line', animation: 'spin' }
                  : 'ri-cloud-line'
              "
              :disabled="saving || summaryHasErrors"
              @click="saveResponse"
            />
          </div>
        </template>
      </template>
    </ion-content>
  </ion-page>
</template>

<style scoped>
ion-content {
  --padding-top: 0;
  --padding-bottom: 0;
  --padding-start: 0;
  --padding-end: 0;
}
</style>
