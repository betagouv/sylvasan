<script setup lang="ts">
import { computed, ref } from "vue"
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonButtons,
  IonBackButton,
  modalController,
} from "@ionic/vue"
import { useRoute } from "vue-router"
import { useSurveysStore } from "../stores/surveys"
import { usePlacetteStore } from "../stores/placette"
import PlacetteChooserPage from "./PlacetteChooserPage.vue"

const route = useRoute()
const surveysStore = useSurveysStore()
const placetteStore = usePlacetteStore()

const placetteId = Number(route.params.placetteId)

const placette = computed(() => placetteStore.currentPlacette)

const hasSurveys = computed(() =>
  placette.value
    ? surveysStore.surveys.some((s) => s.placetteGroupId === placette.value!.groupId)
    : false
)

const openingChooser = ref(false)

const addObservation = async () => {
  if (!placette.value || openingChooser.value) return
  openingChooser.value = true
  try {
    const modal = await modalController.create({
      component: PlacetteChooserPage,
      componentProps: {
        placetteId: placette.value.placetteId,
        groupId: placette.value.groupId,
      },
    })
    await modal.present()
  } finally {
    openingChooser.value = false
  }
}
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-back-button default-href="/carte" />
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <template v-if="placette">
        <h2 class="fr-h4 mb-1">{{ placette.label }}</h2>
        <p class="text-sm text-stone-500 mb-4">{{ placette.groupName }}</p>

        <p class="text-xs text-stone-400 break-all mb-6">
          {{ JSON.stringify(placette.characteristics) }}
        </p>

        <DsfrButton
          v-if="hasSurveys"
          label="Ajouter une observation"
          icon="ri-add-line"
          @click="addObservation"
        />
      </template>

      <p v-else class="text-stone-500 text-sm text-center mt-8">
        Placette introuvable (id : {{ placetteId }}).
      </p>
    </ion-content>
  </ion-page>
</template>
