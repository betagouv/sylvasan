<script setup lang="ts">
import { computed } from "vue"
import { useIonRouter, modalController } from "@ionic/vue"
import type { PinData } from "../composables/useMapPins"
import { useSurveysStore } from "../stores/surveys"
import { useAuthStore } from "../stores/auth"
import { useCanAddFollowUp } from "../composables/useCanAddFollowUp"
import ResponseBadge from "./ResponseBadge.vue"
import FollowUpChooserPage from "../pages/FollowUpChooserPage.vue"
import FollowUpList from "./FollowUpList.vue"

const props = defineProps<{ pin: PinData }>()
const emit = defineEmits<{ close: [] }>()

const router = useIonRouter()
const surveysStore = useSurveysStore()
const authStore = useAuthStore()

const isOwnResponse = computed(
  () =>
    !props.pin.respondant ||
    props.pin.respondant.id === authStore.loggedUser?.id
)

const formattedDate = computed(() =>
  new Date(props.pin.date).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  })
)

const navigate = () => {
  emit("close")
  router.navigate(
    {
      name: "ResponseSummaryPage",
      params: { responseId: String(props.pin.responseId) },
    },
    "forward",
    "push"
  )
}

const addFollowUp = async () => {
  if (!survey.value) return
  emit("close")
  const modal = await modalController.create({
    component: FollowUpChooserPage,
    componentProps: {
      responseId: String(props.pin.responseId),
      survey: survey.value,
    },
  })
  await modal.present()
}

const survey = computed(() =>
  props.pin.surveyId != null
    ? surveysStore.getSurveyById(props.pin.surveyId)
    : undefined
)
const canAddFollowUp = useCanAddFollowUp(survey)
</script>

<template>
  <div
    class="absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl p-4 pb-16 z-10 shadow-drawer"
  >
    <div class="flex justify-between items-start mb-2">
      <h3 class="font-semibold text-stone-800 fr-h5 text-base mb-0! pr-4">
        {{ pin.surveyTitle }}
      </h3>
      <button
        @click="emit('close')"
        class="shrink-0 text-stone-400 p-1 -mt-1 -mr-1"
      >
        <v-icon name="ri-close-line" scale="1.2" />
      </button>
    </div>
    <div class="flex flex-col gap-1 text-sm text-stone-500 mb-4">
      <div>
        <span>{{ formattedDate }}</span>
        <span class="pl-3" v-if="!isOwnResponse && pin.respondant">
          {{ pin.respondant.firstName }} {{ pin.respondant.lastName }}
        </span>
      </div>
      <ResponseBadge :response="({ status: pin.status } as any)" />
    </div>
    <FollowUpList class="mb-4!" :follow-ups="pin.followUps" />

    <div class="flex gap-2">
      <DsfrButton
        v-if="canAddFollowUp"
        label="Ajouter une étape de suivi"
        size="sm"
        @click="addFollowUp"
        icon="ri-add-line"
      />

      <DsfrButton
        v-if="isOwnResponse"
        label="Voir le détail"
        @click="navigate"
        secondary
        size="sm"
        icon="ri-arrow-right-line"
      />
    </div>
  </div>
</template>

<style scoped>
.shadow-drawer {
  box-shadow: 0px 0px 7px -1px #25252591;
  z-index: 999999;
}
</style>
