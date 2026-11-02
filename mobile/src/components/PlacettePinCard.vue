<script setup lang="ts">
import { computed, ref } from "vue"
import { modalController, useIonRouter } from "@ionic/vue"
import { useSurveysStore } from "../stores/surveys"
import { usePlacetteStore } from "../stores/placette"
import type { PlacetteData } from "../composables/useGeoPins"
import PlacetteObservationList from "./PlacetteObservationList.vue"
import PlacetteChooserPage from "../pages/PlacetteChooserPage.vue"

const props = defineProps<{ placette: PlacetteData }>()
const emit = defineEmits<{ close: [] }>()

const router = useIonRouter()
const surveysStore = useSurveysStore()
const placetteStore = usePlacetteStore()

const hasSurveys = computed(() =>
  surveysStore.surveys.some(
    (s) => s.placetteGroupId === props.placette.groupId,
  ),
)

const openingChooser = ref(false)

const navigate = () => {
  emit("close")
  placetteStore.currentPlacette = props.placette
  router.navigate(
    { name: "PlacetteInfoPage", params: { placetteId: String(props.placette.placetteId) } },
    "forward",
    "push",
  )
}

const addObservation = async () => {
  if (openingChooser.value) return
  openingChooser.value = true
  emit("close")
  try {
    const modal = await modalController.create({
      component: PlacetteChooserPage,
      componentProps: {
        placetteId: props.placette.placetteId,
        groupId: props.placette.groupId,
      },
    })
    await modal.present()
  } finally {
    openingChooser.value = false
  }
}
</script>

<template>
  <div
    class="absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl p-4 pb-16 z-10 shadow-drawer"
  >
    <div class="flex justify-between items-start mb-2">
      <h3 class="font-semibold text-stone-800 fr-h5 text-base mb-0! pr-4">
        {{ placette.label }}
      </h3>
      <button
        @click="emit('close')"
        class="shrink-0 text-stone-400 p-1 -mt-1 -mr-1"
      >
        <v-icon name="ri-close-line" scale="1.2" />
      </button>
    </div>

    <p class="text-sm text-stone-500 mb-3">{{ placette.groupName }}</p>

    <PlacetteObservationList class="mb-4!" :observations="placette.responses" />

    <p class="text-xs text-stone-400 break-all mb-3">
      {{ JSON.stringify(placette.characteristics) }}
    </p>

    <div class="flex gap-2">
      <DsfrButton
        v-if="hasSurveys"
        label="Ajouter une observation"
        size="sm"
        icon="ri-add-line"
        @click="addObservation"
      />
      <DsfrButton
        label="Voir le détail"
        size="sm"
        secondary
        icon="ri-arrow-right-line"
        @click="navigate"
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
