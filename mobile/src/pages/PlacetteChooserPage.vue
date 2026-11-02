<script setup lang="ts">
import { computed } from "vue"
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonButtons,
  IonButton,
  IonIcon,
  modalController,
} from "@ionic/vue"
import { closeOutline } from "ionicons/icons"
import { useSurveysStore } from "../stores/surveys"

const props = defineProps<{ placetteId: number; groupId: number }>()

const surveysStore = useSurveysStore()

const surveys = computed(() =>
  surveysStore.surveys.filter((s) => s.placetteGroupId === props.groupId)
)

const selectSurvey = (_surveyId: number) => {
  // TODO : ouvrir PlacetteSurveyPage avec placetteId + surveyId
  modalController.dismiss()
}
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-button @click="modalController.dismiss()">
            <ion-icon slot="icon-only" :icon="closeOutline" />
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <div class="flex flex-col gap-4 pr-4">
        <button
          v-for="survey in surveys"
          :key="survey.id"
          class="w-full text-left border! border-slate-200! bg-white rounded-lg px-2 py-3 flex items-center gap-4 active:bg-slate-50"
          @click="selectSurvey(survey.id)"
        >
          <span class="font-medium">{{ survey.title }}</span>
          <v-icon
            name="ri-arrow-right-s-line"
            scale="1.2"
            class="ml-auto shrink-0"
          />
        </button>

        <p
          v-if="!surveys.length"
          class="text-stone-500 text-sm text-center mt-8"
        >
          Aucune enquête disponible pour ce groupe de placettes.
        </p>
      </div>
    </ion-content>
  </ion-page>
</template>
