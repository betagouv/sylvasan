<script setup lang="ts">
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonTitle,
  IonRefresher,
  IonRefresherContent,
  IonModal,
} from "@ionic/vue"
import { useResponsesStore } from "../../stores/responses"
import { useSurveysStore } from "../../stores/surveys"
import ResponseCard from "./ResponseCard.vue"
import SurveyPage from "../SurveyPage.vue"
import { computed, ref } from "vue"
import type { ResponseFull, LocalResponse } from "@shared-types/response"

const responsesStore = useResponsesStore()
const surveysStore = useSurveysStore()

const draftResponses = computed(() => responsesStore.drafts)
const allResponses = computed(() => responsesStore.allResponses)
const nondraftResponses = computed(() =>
  allResponses.value.filter((x) => x.status !== "draft")
)

const selectedDraftSurveyId = ref<number | null>(null)

const handleRefresh = async (event: CustomEvent) => {
  await surveysStore.sync()
  await responsesStore.sync()
  ;(event.target as HTMLIonRefresherElement).complete()
}

const isLocal = (res: LocalResponse | ResponseFull): res is LocalResponse =>
  (<LocalResponse>res).localId !== undefined
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>Mes observations</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <ion-refresher slot="fixed" @ionRefresh="handleRefresh($event)">
        <ion-refresher-content />
      </ion-refresher>
      <div v-if="draftResponses.length" class="bg-amber-100 py-4">
        <p class="px-4 fr-text--sm font-semibold text-stone-600 mb-3!">
          En cours ({{ draftResponses.length }})
        </p>
        <div class="flex flex-row gap-3 overflow-x-auto px-4 pb-1">
          <div
            v-for="response in draftResponses"
            :key="response.localId"
            class="w-72 shrink-0"
          >
            <ResponseCard
              :response="response"
              @open-draft="selectedDraftSurveyId = $event.surveyId"
            />
          </div>
        </div>
      </div>
      <div class="p-4 grid grid-cols-1 gap-3! text-left">
        <ResponseCard
          v-for="response in nondraftResponses"
          :key="isLocal(response) ? response.localId : response.id"
          :response="response"
          @open-draft="selectedDraftSurveyId = $event.surveyId"
        />
      </div>
    </ion-content>

    <ion-modal
      :is-open="selectedDraftSurveyId !== null"
      @did-dismiss="selectedDraftSurveyId = null"
    >
      <SurveyPage
        v-if="selectedDraftSurveyId !== null"
        :id="selectedDraftSurveyId"
        :is-modal="true"
        @close="selectedDraftSurveyId = null"
      />
    </ion-modal>
  </ion-page>
</template>

<style scoped>
ion-content,
ion-content::part(background),
ion-refresher {
  background: #f4f4ff;
}
ion-refresher.refresher-active {
  z-index: 999;
}
ion-content::part(scroll) {
  z-index: 9999;
}
ion-content {
  --padding-top: 0;
  --padding-bottom: 0;
  --padding-start: 0;
  --padding-end: 0;
}
</style>
