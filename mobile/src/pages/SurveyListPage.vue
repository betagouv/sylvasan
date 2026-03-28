<script setup lang="ts">
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonButtons,
  IonMenuButton,
} from "@ionic/vue"
import { storeToRefs } from "pinia"
import { useSurveysStore } from "../stores/surveys"
import { useIonRouter } from "@ionic/vue"

const router = useIonRouter()
const surveysStore = useSurveysStore()
const { surveys, syncing } = storeToRefs(surveysStore)

function openSurvey(id: number) {
  router.push({ name: "SurveyPage", params: { id } })
}
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-menu-button />
        </ion-buttons>

        <ion-buttons slot="end"> </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <div class="grid grid-cols-1 p-3 gap-3! text-left">
        <DsfrCard
          v-for="survey in surveys"
          :key="survey.id"
          :title="survey.title"
          @click="openSurvey(survey.id)"
        >
        </DsfrCard>
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
ion-content::part(background) {
  background: #ececfe;
}
</style>
