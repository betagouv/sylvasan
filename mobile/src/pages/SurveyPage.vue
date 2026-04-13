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
  IonButton,
  IonIcon,
  IonTitle,
  useIonRouter,
} from "@ionic/vue"
import { closeOutline } from "ionicons/icons"
import SurveyRenderer from "@shared-components/SurveyRenderer.vue"
import { useApiFetch } from "../utils/data-fetching"
import { storeToRefs } from "pinia"

const props = defineProps<{ id?: number; isModal?: boolean }>()
const emit = defineEmits<{ close: [] }>()

const router = useIonRouter()
const route = useRoute()
const store = useSurveysStore()
const authStore = useAuthStore()

const { loggedUser } = storeToRefs(authStore)

const surveyId = computed(() => props.id ?? Number(route.params.id))
const survey = computed(() => store.getSurveyById(surveyId.value))

const saveResponse = async (data: object) => {
  const { response } = await useApiFetch("/responses/")
    .post({
      survey: surveyId.value,
      respondant: loggedUser.value?.id,
      data,
    })
    .json()
  if (response.value?.ok) {
    alert("Votre réponse a été envoyée")
    if (props.isModal) emit("close")
    else router.navigate({ name: "CartePage" }, "back", "replace")
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
          <ion-back-button
            v-if="!isModal"
            :default-href="{ name: 'CartePage' }"
          />
          <ion-button v-else @click="emit('close')">
            <ion-icon slot="icon-only" :icon="closeOutline" />
          </ion-button>
        </ion-buttons>
        <ion-buttons slot="end" />
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <div v-if="!survey">Enquête introuvable.</div>
      <div v-else class="box-border! p-4!">
        <SurveyRenderer
          :allowSubmit="true"
          :schema="survey.jsonSchema"
          @submit="saveResponse"
        />
      </div>
    </ion-content>
  </ion-page>
</template>
