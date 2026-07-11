<script setup lang="ts">
import { computed, onMounted } from "vue"
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonButtons,
  IonBackButton,
  IonButton,
  IonIcon,
  useIonRouter,
  alertController,
  modalController,
} from "@ionic/vue"
import { trashOutline } from "ionicons/icons"
import { useRoute } from "vue-router"
import { useResponsesStore } from "../stores/responses"
import { useSurveysStore } from "../stores/surveys"
import SurveySummary from "../components/SurveySummary.vue"
import { useCanAddFollowUp } from "../composables/useCanAddFollowUp"
import FollowUpChooserPage from "./FollowUpChooserPage.vue"
import type { ResponseFull, LocalResponse } from "@shared-types/response"
import type { Survey } from "@shared-types/survey"

const route = useRoute()
const router = useIonRouter()
const responsesStore = useResponsesStore()
const surveysStore = useSurveysStore()

onMounted(() => responsesStore.loadFromStorage())

const responseId = route.params.responseId as string

const response = computed(
  () =>
    responsesStore.getByLocalId(responseId) ??
    responsesStore.getResponseById(Number(responseId))
)

const surveyId = computed(() => {
  if (!response.value) return null
  return "surveyId" in response.value
    ? response.value.surveyId
    : response.value.survey?.id
})

const survey = computed(() =>
  surveyId.value != null
    ? surveysStore.getSurveyById(surveyId.value)
    : undefined
)

const isLocal = computed(() => {
  const r = response.value
  return !r || "localId" in r
})

const followUp = computed(() => {
  const r = response.value
  if (!r) return undefined
  if ("localId" in r) return (r as LocalResponse).surveyFollowUp ?? undefined
  const id = (r as ResponseFull).surveyFollowUp?.id
  return id != null ? surveysStore.getFollowUpById(id) : undefined
})

const parentResponse = computed(() => {
  const r = response.value
  if (!r) return undefined
  const id = "localId" in r
    ? (r as LocalResponse).parentResponse
    : (r as ResponseFull).parentResponse
  return id != null ? responsesStore.getResponseById(id) : undefined
})

const surveyForSummary = computed((): Survey | undefined => {
  if (survey.value) return survey.value
  const fu = followUp.value
  if (!fu?.jsonSchema) return undefined
  return {
    id: fu.id,
    title: fu.title,
    jsonSchema: fu.jsonSchema,
    surveyType: "",
    followUps: [],
  }
})

const isDeletable = computed(
  () =>
    response.value != null &&
    "localId" in response.value &&
    response.value.status !== "synced"
)

const confirmDelete = async () => {
  if (!response.value || !("localId" in response.value)) return
  const localId = response.value.localId
  const alert = await alertController.create({
    header: "Supprimer cette observation ?",
    message: "Cette observation sera définitivement supprimée.",
    buttons: [
      { text: "Annuler", role: "cancel" },
      {
        text: "Supprimer",
        role: "destructive",
        handler: async () => {
          await responsesStore.deleteDraft(localId)
          router.navigate({ name: "ResponseListPage" }, "back", "replace")
        },
      },
    ],
  })
  await alert.present()
}
const canAddFollowUp = useCanAddFollowUp(survey)
const addFollowUp = async () => {
  const modal = await modalController.create({
    component: FollowUpChooserPage,
    componentProps: { responseId },
  })
  await modal.present()
}
const isFollowUp = computed(() => followUp.value != null)
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button :default-href="{ name: 'ResponseListPage' }" />
        </ion-buttons>
        <ion-buttons slot="end">
          <ion-button
            v-if="isDeletable"
            color="danger"
            class="pr-2"
            @click="confirmDelete"
          >
            <ion-icon slot="icon-only" :icon="trashOutline" />
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <div v-if="canAddFollowUp" class="p-4 bg-blue-france-975">
        <DsfrButton
          label="Ajouter une étape de suivi"
          icon="ri-arrow-right-line"
          size="sm"
          @click="addFollowUp"
        />
      </div>
      <div v-if="isFollowUp" class="flex items-center gap-2 p-4">
        <div
          class="shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
          :style="{ background: followUp?.actionColor }"
        >
          <v-icon :name="followUp?.actionIcon" scale="1.2" />
        </div>
        <div class="flex flex-col">
          <span class="fr-text--sm mb-0! text-gray-500"
            >Suivi effectué pour l'observation</span
          >
          <span class="font-medium">{{ parentResponse?.survey?.title }}</span>
        </div>
      </div>
      <div v-if="!response || !surveyForSummary">Observation introuvable.</div>
      <SurveySummary v-else :survey="surveyForSummary" :response="response" />
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
