<script setup lang="ts">
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonTitle,
} from "@ionic/vue"
import { storeToRefs } from "pinia"
import { useSurveysStore } from "../../stores/surveys"
import SurveyCard from "./SurveyCard.vue"

const emit = defineEmits<{ select: [id: number] }>()

const surveysStore = useSurveysStore()
const { surveys } = storeToRefs(surveysStore)
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar><ion-title>Mes enquêtes</ion-title> </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <div class="grid grid-cols-2 gap-2! text-left">
        <SurveyCard
          :survey="survey"
          v-for="survey in surveys"
          :key="survey.id"
          @select="emit('select', survey.id)"
        />
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
ion-content::part(background) {
  background: #ececfe;
}
</style>
