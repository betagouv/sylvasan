<script setup lang="ts">
import { computed } from "vue"
import { useIonRouter } from "@ionic/vue"
import type { PinData } from "../composables/useMapPins"
import ResponseBadge from "./ResponseBadge.vue"

const props = defineProps<{ pin: PinData }>()
const emit = defineEmits<{ close: [] }>()

const router = useIonRouter()

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
</script>

<template>
  <div
    class="absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl p-4 pb-16 z-10 shadow-drawer"
  >
    <div class="flex justify-between items-start mb-3">
      <h3 class="font-semibold text-stone-800 text-base mb-0! pr-4">
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
      <span>{{ formattedDate }}</span>
      <ResponseBadge :response="({ status: pin.status } as any)" />
    </div>
    <DsfrButton
      label="Voir le détail"
      @click="navigate"
      secondary
      size="sm"
      icon="ri-arrow-right-line"
    />
  </div>
</template>

<style scoped>
.shadow-drawer {
  box-shadow: 0px 0px 7px -1px #25252591;
}
</style>
