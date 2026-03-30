<script setup lang="ts">
import { computed } from "vue"
import { useRoute } from "vue-router"
import { useSurveysStore } from "../stores/surveys"
import { useAuthStore } from "../stores/auth"
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonButtons,
  IonBackButton,
  IonTitle,
  useIonRouter,
} from "@ionic/vue"
import SurveyRenderer from "../components/SurveyRenderer.vue"
import { useApiFetch } from "../utils/data-fetching"
import { storeToRefs } from "pinia"

const router = useIonRouter()
const route = useRoute()
const store = useSurveysStore()
const authStore = useAuthStore()

const { loggedUser } = storeToRefs(authStore)
const survey = computed(() => store.getSurveyById(Number(route.params.id)))

const saveResponse = async (data: object) => {
  const { response } = await useApiFetch("/responses/")
    .post({
      survey: Number(route.params.id),
      respondant: loggedUser.value?.id,
      data,
    })
    .json()
  if (response.value?.ok) {
    alert("Votre réponse a été envoyée")
    router.navigate({ name: "SurveyListPage" }, "back", "replace")
  } else {
    alert("Une erreur s'est produite")
  }
}
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>
          {{ survey?.title }}
        </ion-title>
        <ion-buttons slot="start">
          <ion-back-button :default-href="{ name: 'SurveyListPage' }" />
        </ion-buttons>

        <ion-buttons slot="end"> </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <div v-if="!survey">Enquête introuvable.</div>
      <div v-else class="box-border! p-4!">
        <SurveyRenderer :schema="survey.jsonSchema" @submit="saveResponse" />
      </div>
    </ion-content>
  </ion-page>
</template>
