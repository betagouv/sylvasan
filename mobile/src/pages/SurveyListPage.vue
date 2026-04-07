<script setup lang="ts">
import { IonPage, IonHeader, IonToolbar, IonContent } from "@ionic/vue"
import { storeToRefs } from "pinia"
import { useSurveysStore } from "../stores/surveys"

const emit = defineEmits<{ select: [id: number] }>()

const surveysStore = useSurveysStore()
const { surveys } = storeToRefs(surveysStore)
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar />
    </ion-header>
    <ion-content class="ion-padding">
      <div class="grid grid-cols-1 p-3 gap-3! text-left">
        <DsfrCard
          v-for="survey in surveys"
          :key="survey.id"
          :title="survey.title"
          @click="emit('select', survey.id)"
        >
        </DsfrCard>
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
ion-content::part(background) {
  background: #ececfe;
}
</style>
