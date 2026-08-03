<script setup lang="ts">
import { computed, ref, watch, onMounted } from "vue"
import { closeOutline, trashOutline } from "ionicons/icons"
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonButtons,
  IonButton,
  IonIcon,
  alertController,
  modalController,
  useIonRouter,
} from "@ionic/vue"
import { useRoute } from "vue-router"
import { storeToRefs } from "pinia"
import SurveyRenderer from "@shared-components/SurveyRenderer.vue"
import SurveySummary from "../components/SurveySummary.vue"
import MapField from "../components/MapField.vue"
import type { Survey } from "@shared-types/survey"
import type { ResponseFull } from "@shared-types/response"
import { useResponsesStore } from "../stores/responses"
import { useSurveysStore } from "../stores/surveys"
import { useToastStore } from "../stores/toast"
import { useVocabulariesStore } from "../stores/vocabularies"
import {
  saveImagesToFilesystem,
  resolveLocalImageSrc,
} from "../utils/imageStorage"
import { validateResponse } from "@shared-utils/validateField"
import { evaluateCondition } from "@shared-utils/survey"

const props = defineProps<{
  responseId?: string
  followUpId?: number
  localId?: string
}>()

const route = useRoute()
const router = useIonRouter()
const responsesStore = useResponsesStore()
const surveysStore = useSurveysStore()
const toast = useToastStore()
const { vocabularySets } = storeToRefs(useVocabulariesStore())
const prefillData = ref<Record<string, unknown> | undefined>(undefined)
const dataReady = ref(false)

// Force validation immediately when a draft is opened (user already saw/filled the form)
watch(prefillData, (val) => {
  if (val) forceValidate.value = true
})

const responseId = props.responseId ?? (route.params.responseId as string)
const followUpId = props.followUpId ?? Number(route.params.followUpId)

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

const response = computed(
  () =>
    responsesStore.getByLocalId(responseId) ??
    responsesStore.getResponseById(Number(responseId))
)

const surveyId = computed(() => {
  const r = response.value
  if (!r) return null
  return "surveyId" in r ? r.surveyId : r.survey?.id ?? null
})

const survey = computed(() =>
  surveyId.value != null
    ? surveysStore.getSurveyById(surveyId.value)
    : undefined
)

const followUp = computed(
  () =>
    survey.value?.followUps.find((fu) => fu.id === followUpId) ??
    surveysStore.getFollowUpById(followUpId)
)

const parentBackendId = computed<number | null>(() => {
  const r = response.value
  if (r && "id" in r) return (r as ResponseFull).id
  if (!r) {
    // Réponse d'un collègue non présente dans le store local : responseId est l'id backend
    const numericId = Number(responseId)
    return !isNaN(numericId) && numericId > 0 ? numericId : null
  }
  return null
})

const label = computed(
  () => followUp.value?.actionLabel?.trim() || followUp.value?.title || ""
)

const followUpAsSurvey = computed((): Survey | undefined => {
  const fu = followUp.value
  if (!fu?.jsonSchema) return undefined
  return {
    id: fu.id,
    title: label.value,
    jsonSchema: fu.jsonSchema,
    surveyType: "",
    followUps: [],
  }
})

// Form state
const currentLocalId = ref<string | undefined>(undefined)
const currentFormData = ref<Record<string, unknown>>({})
const showSummary = ref(false)
const summaryData = ref<Record<string, unknown>>({})
const saving = ref(false)
const forceValidate = ref(false)

watch(showSummary, (val, prev) => {
  if (!val && prev) forceValidate.value = true
})

const summaryHasErrors = computed(() => {
  const fields = followUp.value?.jsonSchema?.fields ?? []
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

const onSurveyDone = (data: Record<string, unknown>) => {
  currentFormData.value = data
  summaryData.value = data
  showSummary.value = true
}

const saveDraftIfNeeded = async () => {
  const parentId = parentBackendId.value
  if (
    Object.keys(currentFormData.value).length === 0 ||
    !followUp.value ||
    !parentId
  )
    return
  const schema = followUp.value.jsonSchema
  const draftData = schema
    ? await saveImagesToFilesystem(currentFormData.value, schema)
    : currentFormData.value
  const localId = await responsesStore.upsertFollowUpDraft(
    followUp.value,
    parentId,
    draftData,
    currentLocalId.value
  )
  currentLocalId.value = localId
}

const saveResponse = async () => {
  const parentId = parentBackendId.value
  if (!followUp.value || !parentId) return
  saving.value = true
  try {
    const schema = followUp.value.jsonSchema
    const draftData = schema
      ? await saveImagesToFilesystem(summaryData.value, schema)
      : summaryData.value

    const localId = await responsesStore.upsertFollowUpDraft(
      followUp.value,
      parentId,
      draftData,
      currentLocalId.value
    )
    currentLocalId.value = localId

    const success = await responsesStore.submitFollowUpResponse(localId)
    if (success) {
      toast.show("Votre suivi a été envoyé", "success")
    } else {
      toast.show(
        "Votre suivi a été sauvegardé localement et sera envoyé dès que possible"
      )
    }
    closeAndNavigateToObservations()
  } finally {
    saving.value = false
  }
}

const closeAndNavigateToObservations = () => {
  modalController.dismiss()
  router.navigate({ name: "ResponseListPage" }, "forward", "replace")
}
const formatDate = (isoString: string | undefined): string => {
  if (!isoString) return ""
  return new Date(isoString).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
}

const confirmDelete = async () => {
  const hasDraft = !!currentLocalId.value
  const alert = await alertController.create({
    header: hasDraft
      ? "Supprimer le suivi en cours ?"
      : "Abandonner le suivi ?",
    message: hasDraft
      ? "Ce suivi sera définitivement supprimé."
      : "Les données saisies ne seront pas sauvegardées.",
    buttons: [
      { text: "Continuer la saisie", role: "cancel" },
      {
        text: hasDraft ? "Supprimer" : "Abandonner",
        role: "destructive",
        handler: async () => {
          if (hasDraft) {
            await responsesStore.deleteDraft(currentLocalId.value!)
          }
          await modalController.dismiss()
        },
      },
    ],
  })
  await alert.present()
}
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-button
            @click="
              saveDraftIfNeeded().then(() => closeAndNavigateToObservations())
            "
          >
            <ion-icon slot="start" :icon="closeOutline" />
            Enregistrer en brouillon
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
      <div v-if="!followUp || !followUp.jsonSchema" class="p-4 text-stone-500">
        Suivi introuvable.
      </div>
      <div v-else-if="!parentBackendId" class="p-4 text-stone-500">
        Cette observation n'a pas encore été synchronisée. Synchronisez-la avant
        d'ajouter un suivi.
      </div>
      <template v-else>
        <!-- Contextual banner -->
        <div
          class="p-4 flex items-center gap-4 border-b border-slate-200"
          :style="{ background: (followUp.actionColor ?? '#000091') + '20' }"
        >
          <div
            class="shrink-0 w-12 h-12 rounded-full flex items-center justify-center"
            :style="{ background: followUp.actionColor ?? '#000091' }"
          >
            <v-icon
              :name="followUp.actionIcon"
              scale="1.4"
              class="text-white"
            />
          </div>
          <div>
            <h2 class="fr-h6 mb-0!">{{ label }}</h2>
            <p class="mb-0! fr-text--sm" v-if="survey?.title">
              <span class="italic">{{ survey?.title }}</span>
              {{ formatDate(response?.creationDate) }}
            </p>
          </div>
        </div>

        <!-- Form -->
        <div v-if="dataReady" v-show="!showSummary" class="box-border! p-4!">
          <SurveyRenderer
            :allowSubmit="true"
            :schema="followUp.jsonSchema"
            :forceValidate="forceValidate"
            :prefillData="prefillData"
            :vocabularies="vocabularySets"
            :mapComponent="MapField"
            :resolveImagePath="resolveLocalImageSrc"
            @done="onSurveyDone"
            @change="currentFormData = $event"
          />
        </div>

        <!-- Summary -->
        <template v-if="showSummary && followUpAsSurvey">
          <SurveySummary :survey="followUpAsSurvey" :data="summaryData" />
          <div class="flex justify-between p-4">
            <DsfrButton
              label="Modifier"
              secondary
              icon="ri-edit-line"
              :disabled="saving"
              @click="showSummary = false"
            />
            <DsfrButton
              label="Envoyer"
              :icon="
                saving
                  ? { name: 'ri-refresh-line', animation: 'spin' }
                  : 'ri-cloud-line'
              "
              :disabled="saving || summaryHasErrors"
              @click="saveResponse"
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
