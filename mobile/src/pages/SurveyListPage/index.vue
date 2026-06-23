<script setup lang="ts">
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonTitle,
} from "@ionic/vue"
import { computed, ref, onUnmounted } from "vue"
import { storeToRefs } from "pinia"
import { useSurveysStore } from "../../stores/surveys"
import { useSyncStore } from "../../stores/sync"
import { timeAgo } from "@shared-utils/date"
import SurveyCard from "./SurveyCard.vue"

const emit = defineEmits<{ select: [id: number] }>()

const surveysStore = useSurveysStore()
const { surveys } = storeToRefs(surveysStore)

const syncStore = useSyncStore()
const { syncedAt, syncing } = storeToRefs(syncStore)

const sync = async () => {
  await syncStore.syncAll().catch(() => {})
}

const now = ref(Date.now())
const ticker = setInterval(() => {
  now.value = Date.now()
}, 60000)
onUnmounted(() => clearInterval(ticker))

const syncedAtLabel = computed(() => {
  void now.value
  return syncedAt.value ? timeAgo(syncedAt.value) : "Jamais synchronisé"
})
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar
        ><ion-title class="box-border!">Mes enquêtes</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <div>
        <div class="flex items-center">
          <p class="mb-0! grow fr-text--sm text-stone-600">
            Dernière màj {{ syncedAtLabel }}
          </p>
          <DsfrButton
            size="sm"
            tertiary
            label="Actualiser"
            :icon="
              syncing
                ? { name: 'ri-refresh-line', animation: 'spin' }
                : 'ri-refresh-line'
            "
            :disabled="syncing"
            @click="sync"
          />
        </div>
        <hr class="pb-2! mt-2!" />
      </div>
      <div class="grid grid-cols-2 gap-2! text-left">
        <SurveyCard
          :survey="survey"
          v-for="survey in surveys"
          :key="survey.id"
          @select="emit('select', survey.id)"
        />
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
ion-content::part(background) {
  background: #ececfe;
}
</style>
