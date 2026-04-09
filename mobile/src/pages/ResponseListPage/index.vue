<script setup lang="ts">
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonTitle,
  IonRefresher,
  IonRefresherContent,
} from "@ionic/vue"
import { storeToRefs } from "pinia"
import { useResponsesStore } from "../../stores/responses"
import { useSurveysStore } from "../../stores/surveys"
import ResponseCard from "./ResponseCard.vue"

const responsesStore = useResponsesStore()
const { responses } = storeToRefs(responsesStore)

const surveysStore = useSurveysStore()

const handleRefresh = async (event: CustomEvent) => {
  await surveysStore.sync()
  await responsesStore.sync()
  ;(event.target as HTMLIonRefresherElement).complete()
}
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
      <div class="grid grid-cols-1 gap-3! text-left">
        <ResponseCard
          v-for="response in responses"
          :key="response.id"
          :response="response"
        />
      </div>
    </ion-content>
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
</style>
