<script setup lang="ts">
import type { ResponseFull, ResponseStatus } from "@shared-types/response"
import { computed } from "vue"

const { response } = defineProps<{
  response: ResponseFull
}>()

const displayStatus = computed(() => {
  const mapping: Record<ResponseStatus, string> = {
    draft: "envoyée", //  TODO change once the state management is ready
    submitted: "envoyée",
    exported: "exportée",
  }
  return mapping[response.status]
})

// import { useIonRouter } from "@ionic/vue"

// const router = useIonRouter()

const openResponse = () => {
  // TODO : ouvrir la page avec la réponse
  console.log(`Ouvrir ${response.id}`)
  // router.push({ name: "ResponsePage", params: { id } })
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
  <div class="border border-slate-200 p-4">
    <div class="mb-1">
      <DsfrBadge :small="true" :label="displayStatus" />
    </div>
    <h2 class="fr-h6 mb-3!">{{ response.survey.title }}</h2>
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
