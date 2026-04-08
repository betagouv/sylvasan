<script setup lang="ts">
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonTitle,
} from "@ionic/vue"
import { storeToRefs } from "pinia"
import { useResponsesStore } from "../../stores/responses"
import ResponseCard from "./ResponseCard.vue"

const responsesStore = useResponsesStore()
const { responses } = storeToRefs(responsesStore)
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>Mes observations</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
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
