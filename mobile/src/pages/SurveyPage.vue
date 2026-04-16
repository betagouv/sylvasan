<script setup lang="ts">
import { computed, ref, onMounted } from "vue"
import { useRoute } from "vue-router"
import { useSurveysStore } from "../stores/surveys"

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
  onIonViewWillLeave,
} from "@ionic/vue"
import { closeOutline } from "ionicons/icons"
import SurveyRenderer from "@shared-components/SurveyRenderer.vue"
import { useResponsesStore } from "../stores/responses"

const props = defineProps<{ id?: number; isModal?: boolean }>()
const emit = defineEmits<{ close: [] }>()

const responsesStore = useResponsesStore()
const currentLocalId = ref<string | undefined>(undefined)
const currentFormData = ref<Record<string, unknown>>({})
const prefillData = ref<Record<string, unknown> | undefined>(undefined)
const dataReady = ref(false)

const router = useIonRouter()
const route = useRoute()
const store = useSurveysStore()

const surveyId = computed(() => props.id ?? Number(route.params.id))
const survey = computed(() => store.getSurveyById(surveyId.value))

// s'il y a un draft avec cet ID on pre-rempli le formulaire
onMounted(async () => {
  await responsesStore.loadFromStorage()
  const existingDraft = responsesStore.getDraftBySurveyId(surveyId.value)
  if (existingDraft) {
    currentLocalId.value = existingDraft.localId
    prefillData.value = existingDraft.data
  }
  dataReady.value = true
})

const saveDraftIfNeeded = async () => {
  if (Object.keys(currentFormData.value).length === 0) return
  await responsesStore.upsertDraft(
    surveyId.value,
    survey.value?.title ?? "",
    currentFormData.value,
    currentLocalId.value
  )
}

// Sauvegarde lors qu'on sort de la page (navigation Ionic)
onIonViewWillLeave(saveDraftIfNeeded)

const handleFormChange = (data: Record<string, unknown>) => {
  currentFormData.value = data
}

const saveResponse = async (data: Record<string, unknown>) => {
  currentFormData.value = data

  await responsesStore.upsertDraft(
    surveyId.value,
    survey.value?.title ?? "",
    data,
    currentLocalId.value
  )

  // Trouver la réponse locale (soit déjà existante soit à peine créée)
  const localResponse = currentLocalId.value
    ? responsesStore.getByLocalId(currentLocalId.value)
    : responsesStore.getDraftBySurveyId(surveyId.value)

  if (!localResponse) return

  currentLocalId.value = localResponse.localId
  const success = await responsesStore.submitResponse(localResponse.localId)

  if (success) {
    alert("Votre réponse a été envoyée")
    if (props.isModal) emit("close")
    else router.navigate({ name: "SurveyListPage" }, "back", "replace")
  } else {
    alert(
      "Votre réponse a été sauvegardée localement et sera envoyée dès que possible"
    )
    if (props.isModal) emit("close")
    else router.navigate({ name: "SurveyListPage" }, "back", "replace")
  }
}
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title v-if="!isModal">
          {{ survey?.title }}
        </ion-title>
        <ion-buttons slot="start">
          <ion-back-button
            v-if="!isModal"
            :default-href="{ name: 'CartePage' }"
          />
          <ion-button
            v-else
            @click="saveDraftIfNeeded().then(() => emit('close'))"
          >
            <ion-icon slot="start" :icon="closeOutline" />
            Enregistrer et quitter
          </ion-button>
        </ion-buttons>
        <ion-buttons slot="end" />
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <div v-if="!survey">Enquête introuvable.</div>
      <div v-else-if="dataReady" class="box-border! p-4!">
        <SurveyRenderer
          :allowSubmit="true"
          :schema="survey.jsonSchema"
          :prefillData="prefillData"
          @submit="saveResponse"
          @change="handleFormChange"
        />
      </div>
    </ion-content>
  </ion-page>
</template>
