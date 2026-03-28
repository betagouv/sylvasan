<script setup lang="ts">
import { computed } from "vue"
import { useRoute } from "vue-router"
import { useSurveysStore } from "../stores/surveys"
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonButtons,
  IonBackButton,
} from "@ionic/vue"
import SurveyRenderer from "../components/SurveyRenderer.vue"

const route = useRoute()
const store = useSurveysStore()

const survey = computed(() => store.getSurveyById(Number(route.params.id)))
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button :default-href="{ name: 'SurveyListPage' }" />
        </ion-buttons>

        <ion-buttons slot="end"> </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <div v-if="!survey">Enquête introuvable.</div>
      <div v-else class="box-border! p-4!">
        <h1>{{ survey.title }}</h1>
        <SurveyRenderer :schema="survey.jsonSchema" />
      </div>
    </ion-content>
  </ion-page>
</template>
