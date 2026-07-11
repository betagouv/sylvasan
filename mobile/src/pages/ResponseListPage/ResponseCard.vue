<script setup lang="ts">
import { computed } from "vue"
import type { ResponseFull, LocalResponse } from "@shared-types/response"
import ResponseBadge from "../../components/ResponseBadge.vue"
import { useSurveysStore } from "../../stores/surveys"
import { useResponsesStore } from "../../stores/responses"

const { response } = defineProps<{
  response: ResponseFull | LocalResponse
}>()

const emit = defineEmits<{
  open: [response: LocalResponse | ResponseFull]
}>()

const surveysStore = useSurveysStore()
const responsesStore = useResponsesStore()

const isLocal = (res: LocalResponse | ResponseFull): res is LocalResponse =>
  (<LocalResponse>res).localId !== undefined

const openResponse = () => {
  emit("open", response)
}

const surveyTitle = () => {
  if (isLocal(response)) return response.surveyTitle
  else return response.survey?.title
}

const formatDate = (isoString: string): string => {
  return new Date(isoString).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
}

const followUp = computed(() => {
  if (isLocal(response)) return undefined
  const id = (response as ResponseFull).surveyFollowUp?.id
  return id != null ? surveysStore.getFollowUpById(id) : undefined
})

const parentResponse = computed(() => {
  if (isLocal(response)) return undefined
  const id = (response as ResponseFull).parentResponse
  return id != null ? responsesStore.getResponseById(id) : undefined
})

const isFollowUp = computed(() => followUp.value != null)
</script>

<template>
  <div class="border border-slate-200 p-4 bg-white">
    <div class="mb-2">
      <ResponseBadge :response="response" />
    </div>
    <div v-if="isFollowUp" class="flex items-center gap-2">
      <div
        class="shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
        :style="{ background: followUp?.actionColor }"
      >
        <v-icon :name="followUp?.actionIcon" scale="1.2" />
      </div>
      <div class="flex flex-col">
        <span class="font-medium">{{ followUp?.title }}</span>
        <span class="fr-text--sm mb-0! text-gray-500"
          >Observation « {{ parentResponse?.survey?.title }} »</span
        >
      </div>
    </div>
    <h2 v-else class="fr-h6 mb-2!">{{ surveyTitle() }}</h2>
    <div class="mt-2">
      <div class="flex">
        <v-icon icon="ri-calendar-line" scale="0.9" class="mt-[3px] mr-2" />
        <p class="mb-0! fr-text--sm text-stone-600">
          {{ formatDate(response.creationDate) }}
        </p>
      </div>
    </div>
    <div class="flex justify-end">
      <DsfrButton
        secondary
        size="sm"
        icon-only
        icon="ri-arrow-right-line"
        @click="openResponse"
      />
    </div>
  </div>
</template>
