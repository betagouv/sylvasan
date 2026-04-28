<script setup lang="ts">
import { computed, ref, onMounted } from "vue"
import { useRoute } from "vue-router"
import { useSurveysStore } from "../stores/surveys"
import { useToastStore } from "../stores/toast"

const toast = useToastStore()

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
  alertController,
} from "@ionic/vue"
import { closeOutline, trashOutline } from "ionicons/icons"
import SurveyRenderer from "@shared-components/SurveyRenderer.vue"
import SurveySummary from "../components/SurveySummary.vue"
import { useResponsesStore } from "../stores/responses"
import { storeToRefs } from "pinia"
import { useVocabulariesStore } from "../stores/vocabularies"

const props = defineProps<{
  id?: number
  isModal?: boolean
  localId?: string
}>()
const emit = defineEmits<{ close: [] }>()

const responsesStore = useResponsesStore()
const { vocabularySets } = storeToRefs(useVocabulariesStore())
const currentLocalId = ref<string | undefined>(undefined)
const currentFormData = ref<Record<string, unknown>>({})
const prefillData = ref<Record<string, unknown> | undefined>(undefined)
const dataReady = ref(false)
const showSummary = ref(false)
const summaryData = ref<Record<string, unknown>>({})

const router = useIonRouter()
const route = useRoute()
const store = useSurveysStore()

const surveyId = computed(() => props.id ?? Number(route.params.id))
const survey = computed(() => store.getSurveyById(surveyId.value))

// s'il y a un draft avec cet ID on pre-rempli le formulaire
onMounted(async () => {
  await responsesStore.loadFromStorage()
  const draftLocalId =
    props.localId ?? (route.params.localId as string | undefined)

  if (draftLocalId) {
    const existingDraft = responsesStore.getByLocalId(draftLocalId)
    if (existingDraft) {
      currentLocalId.value = existingDraft.localId
      prefillData.value = existingDraft.data
    }
  }
  dataReady.value = true
})

const saveDraftIfNeeded = async () => {
  if (Object.keys(currentFormData.value).length === 0) return
  const localId = await responsesStore.upsertDraft(
    surveyId.value,
    survey.value?.title ?? "",
    currentFormData.value,
    currentLocalId.value
  )
  currentLocalId.value = localId
}

const handleFormChange = (data: Record<string, unknown>) => {
  currentFormData.value = data
}

const onSurveyDone = (data: Record<string, unknown>) => {
  currentFormData.value = data
  summaryData.value = data
  showSummary.value = true
}

const confirmDelete = async () => {
  if (!currentLocalId.value) return
  const alert = await alertController.create({
    header: "Supprimer l'observation en cours ?",
    message: "Cette observation sera définitivement supprimée.",
    buttons: [
      { text: "Annuler", role: "cancel" },
      {
        text: "Supprimer",
        role: "destructive",
        handler: async () => {
          await responsesStore.deleteDraft(currentLocalId.value!)
          emit("close")
        },
      },
    ],
  })
  await alert.present()
}

const saveResponse = async (data: Record<string, unknown>) => {
  currentFormData.value = data

  const localId = await responsesStore.upsertDraft(
    surveyId.value,
    survey.value?.title ?? "",
    data,
    currentLocalId.value
  )

  currentLocalId.value = localId
  const success = await responsesStore.submitResponse(localId)

  if (success) {
    toast.show("Votre réponse a été envoyée", "success")
    if (props.isModal) emit("close")
    else router.navigate({ name: "SurveyListPage" }, "back", "replace")
  } else {
    toast.show(
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
        <ion-buttons slot="end">
          <ion-button
            v-if="currentLocalId"
            color="danger"
            @click="confirmDelete"
            class="pr-2"
          >
            <ion-icon slot="icon-only" :icon="trashOutline" />
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <ion-content>
      <div v-if="!survey">Enquête introuvable.</div>
      <template v-else-if="dataReady">
        <div v-show="!showSummary" class="box-border! p-4!">
          <SurveyRenderer
            :allowSubmit="true"
            :schema="survey.jsonSchema"
            :prefillData="prefillData"
            :vocabularies="vocabularySets"
            @done="onSurveyDone"
            @change="handleFormChange"
          />
        </div>
        <template v-if="showSummary">
          <SurveySummary :survey="survey" :data="summaryData" />
          <div class="flex justify-between p-4">
            <DsfrButton
              label="Modifier"
              secondary
              icon="ri-edit-line"
              @click="showSummary = false"
            />
            <DsfrButton
              label="Sauvegarder"
              icon="ri-cloud-line"
              @click="saveResponse(summaryData)"
            />
          </div>
        </template>
      </template>
    </ion-content>
  </ion-page>
</template>

<style scoped>
ion-content {
  --padding-top: 0;
  --padding-bottom: 0;
  --padding-start: 0;
  --padding-end: 0;
}
</style>
