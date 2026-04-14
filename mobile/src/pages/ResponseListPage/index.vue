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
import { useResponsesStore } from "../../stores/responses"
import { useSurveysStore } from "../../stores/surveys"
import ResponseCard from "./ResponseCard.vue"
import { computed } from "vue"
import type { ResponseFull, LocalResponse } from "@shared-types/response"

const responsesStore = useResponsesStore()
const surveysStore = useSurveysStore()
const allResponses = computed(() => responsesStore.allResponses)

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
      <div class="grid grid-cols-1 gap-3! text-left">
        <ResponseCard
          v-for="response in allResponses"
          :key="isLocal(response) ? response.localId : response.id"
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
