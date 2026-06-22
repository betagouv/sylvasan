<script setup lang="ts">
import { computed, ref, watch, onMounted } from "vue"
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
  IonSpinner,
  IonTitle,
  useIonRouter,
  alertController,
} from "@ionic/vue"
import { closeOutline, trashOutline } from "ionicons/icons"
import SurveyRenderer from "@shared-components/SurveyRenderer.vue"
import SurveySummary from "../components/SurveySummary.vue"
import MapField from "../components/MapField.vue"
import { useResponsesStore } from "../stores/responses"
import { storeToRefs } from "pinia"
import { useVocabulariesStore } from "../stores/vocabularies"
import { saveImagesToFilesystem } from "../utils/imageStorage"
import { validateResponse } from "@shared-utils/validateField"
import { evaluateCondition } from "@shared-utils/survey"

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
const saving = ref(false)
const forceValidate = ref(false)

// Force validation immediately when a draft is opened (user already saw/filled the form)
watch(prefillData, (val) => {
  if (val) forceValidate.value = true
})
// Force validation when going back from summary (user clicked "Modifier")
watch(showSummary, (val, prev) => {
  if (!val && prev) forceValidate.value = true
})

const summaryHasErrors = computed(() => {
  const fields = survey.value?.jsonSchema?.fields ?? []
  const visibleFieldIds = new Set(
    fields
      .filter(
        (f) => !f.condition || evaluateCondition(f.condition, summaryData.value)
      )
      .map((f) => f.id)
  )
  return (
    Object.keys(validateResponse(fields, summaryData.value, visibleFieldIds))
      .length > 0
  )
})

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
  const schema = survey.value?.jsonSchema
  const data = schema
    ? await saveImagesToFilesystem(currentFormData.value, schema)
    : currentFormData.value
  const localId = await responsesStore.upsertDraft(
    surveyId.value,
    survey.value?.title ?? "",
    data,
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
  const hasDraft = !!currentLocalId.value
  const alert = await alertController.create({
    header: hasDraft
      ? "Supprimer l'observation en cours ?"
      : "Abandonner l'observation ?",
    message: hasDraft
      ? "Cette observation sera définitivement supprimée."
      : "Les données saisies ne seront pas sauvegardées.",
    buttons: [
      { text: "Contnuer la saisie", role: "cancel" },
      {
        text: hasDraft ? "Supprimer" : "Abandonner",
        role: "destructive",
        handler: async () => {
          if (hasDraft) {
            await responsesStore.deleteDraft(currentLocalId.value!)
          }
          emit("close")
        },
      },
    ],
  })
  await alert.present()
}

const saveResponse = async (data: Record<string, unknown>) => {
  saving.value = true
  try {
    currentFormData.value = data

    const schema = survey.value?.jsonSchema
    const draftData = schema ? await saveImagesToFilesystem(data, schema) : data

    const localId = await responsesStore.upsertDraft(
      surveyId.value,
      survey.value?.title ?? "",
      draftData,
      currentLocalId.value
    )

    currentLocalId.value = localId
    const success = await responsesStore.submitResponse(localId)

    if (success) {
      toast.show("Votre réponse a été envoyée", "success")
      if (props.isModal) emit("close")
      else router.navigate({ name: "ResponseListPage" }, "back", "replace")
    } else {
      toast.show(
        "Votre réponse a été sauvegardée localement et sera envoyée dès que possible"
      )
      if (props.isModal) emit("close")
      else router.navigate({ name: "ResponseListPage" }, "back", "replace")
    }
  } finally {
    saving.value = false
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
          <ion-button color="danger" @click="confirmDelete" class="pr-2">
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
            :forceValidate="forceValidate"
            :vocabularies="vocabularySets"
            :mapComponent="MapField"
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
              :disabled="saving"
              @click="showSummary = false"
            />
            <div class="flex items-center gap-3">
              <DsfrButton
                label="Sauvegarder"
                :icon="
                  saving
                    ? { name: 'ri-refresh-line', animation: 'spin' }
                    : 'ri-cloud-line'
                "
                :disabled="saving || summaryHasErrors"
                @click="saveResponse(summaryData)"
              />
            </div>
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
