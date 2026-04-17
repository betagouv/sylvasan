<script setup lang="ts">
import type { ResponseFull, LocalResponse } from "@shared-types/response"
import ResponseBadge from "../../components/ResponseBadge.vue"

const { response } = defineProps<{
  response: ResponseFull | LocalResponse
}>()

const emit = defineEmits<{
  open: [response: LocalResponse | ResponseFull]
}>()

const isLocal = (res: LocalResponse | ResponseFull): res is LocalResponse =>
  (<LocalResponse>res).localId !== undefined

const openResponse = () => {
  emit("open", response)
}

const surveyTitle = () => {
  if (isLocal(response)) return response.surveyTitle
  else return response.survey.title
}

const formatDate = (isoString: string): string => {
  return new Date(isoString).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "short",
    year: "numeric",
  })
}
</script>

<template>
  <div class="border border-slate-200 p-4 bg-white">
    <div class="mb-2">
      <ResponseBadge :response="response" />
    </div>
    <h2 class="fr-h6 mb-3!">{{ surveyTitle() }}</h2>
    <div>
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
