<script setup lang="ts">
import { computed } from "vue"
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
import { useResponsesStore } from "../stores/responses"
import { useSurveysStore } from "../stores/surveys"
import { useAuthStore } from "../stores/auth"
import { canRespondToFollowUp } from "../composables/useCanAddFollowUp"

const route = useRoute()
const router = useIonRouter()
const responsesStore = useResponsesStore()
const surveysStore = useSurveysStore()
const authStore = useAuthStore()

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
    : response.value.survey?.id ?? null
})

const survey = computed(() =>
  surveyId.value != null
    ? surveysStore.getSurveyById(surveyId.value)
    : undefined
)

const accessibleFollowUps = computed(() => {
  if (!survey.value) return []
  const memberships = authStore.loggedUser?.memberships ?? []
  return survey.value.followUps.filter((fu) =>
    canRespondToFollowUp(fu, memberships)
  )
})

const labelFor = (followUp: (typeof accessibleFollowUps.value)[number]) =>
  followUp.actionLabel?.trim() || followUp.title

const navigateToFollowUp = (followUp: (typeof accessibleFollowUps.value)[number]) => {
  router.navigate(
    {
      name: "FollowUpSurveyPage",
      params: { responseId, followUpId: String(followUp.id) },
    },
    "forward",
    "push"
  )
}
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button
            :default-href="{
              name: 'ResponseSummaryPage',
              params: { responseId },
            }"
          />
        </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <div class="flex flex-col gap-4 pr-4">
        <button
          v-for="followUp in accessibleFollowUps"
          :key="followUp.id"
          class="w-full text-left border! border-slate-200! bg-white rounded-lg px-2 py-3 flex items-center gap-4 active:bg-slate-50"
          @click="navigateToFollowUp(followUp)"
        >
          <div
            class="shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
            :style="{ background: followUp.actionColor }"
          >
            <v-icon :name="followUp.actionIcon" scale="1.2" />
          </div>
          <span class="font-medium">{{ labelFor(followUp) }}</span>
          <v-icon
            name="ri-arrow-right-s-line"
            scale="1.2"
            class="ml-auto shrink-0"
          />
        </button>

        <p
          v-if="!accessibleFollowUps.length"
          class="text-stone-500 text-sm text-center mt-8"
        >
          Aucun suivi disponible pour cette observation.
        </p>
      </div>
    </ion-content>
  </ion-page>
</template>
