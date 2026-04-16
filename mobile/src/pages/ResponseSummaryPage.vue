<script setup lang="ts">
import { computed, onMounted } from "vue"
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonButtons,
  IonBackButton,
  IonTitle,
} from "@ionic/vue"
import { useRoute } from "vue-router"
import { useResponsesStore } from "../stores/responses"
import { useSurveysStore } from "../stores/surveys"
import SurveySummary from "../components/SurveySummary.vue"

const route = useRoute()
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
    : response.value.survey.id
})

const survey = computed(() =>
  surveyId.value != null
    ? surveysStore.getSurveyById(surveyId.value)
    : undefined
)
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button :default-href="{ name: 'ResponseListPage' }" />
        </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <div v-if="!response || !survey">Observation introuvable.</div>
      <SurveySummary v-else :survey="survey" :response="response" />
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
