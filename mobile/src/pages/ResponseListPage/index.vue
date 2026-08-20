<script setup lang="ts">
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonTitle,
  IonRefresher,
  IonRefresherContent,
  IonModal,
  useIonRouter,
} from "@ionic/vue"
import { useResponsesStore } from "../../stores/responses"
import { useSyncStore } from "../../stores/sync"
import ResponseCard from "./ResponseCard.vue"
import SurveyPage from "../SurveyPage.vue"
import FollowUpSurveyPage from "../FollowUpSurveyPage.vue"
import { computed, ref } from "vue"
import type { ResponseFull, LocalResponse } from "@shared-types/response"

const responsesStore = useResponsesStore()
const syncStore = useSyncStore()

const byDateDesc = (
  a: LocalResponse | ResponseFull,
  b: LocalResponse | ResponseFull
) => new Date(b.creationDate).getTime() - new Date(a.creationDate).getTime()

const draftResponses = computed(() =>
  [...responsesStore.drafts].sort(byDateDesc)
)
const allResponses = computed(() =>
  [...responsesStore.allResponses].sort(byDateDesc)
)
const nondraftResponses = computed(() =>
  allResponses.value.filter((x) => x.status !== "draft")
)

const selectedDraft = ref<LocalResponse | null>(null)
const selectedFollowUpDraft = ref<LocalResponse | null>(null)
const surveyPageRef = ref<InstanceType<typeof SurveyPage> | null>(null)
const followUpPageRef = ref<InstanceType<typeof FollowUpSurveyPage> | null>(null)
const ionRouter = useIonRouter()

const onOpen = (response: LocalResponse | ResponseFull) => {
  if (isLocal(response) && response.status === "draft") {
    if (response.surveyFollowUp) {
      selectedFollowUpDraft.value = response
    } else {
      selectedDraft.value = response
    }
  } else {
    const responseId = isLocal(response)
      ? response.localId
      : String(response.id)
    ionRouter.navigate(
      { name: "ResponseSummaryPage", params: { responseId } },
      "forward",
      "push"
    )
  }
}

const handleRefresh = async (event: CustomEvent) => {
  try {
    await syncStore.syncAll()
  } finally {
    ;(event.target as HTMLIonRefresherElement).complete()
  }
}

const isLocal = (res: LocalResponse | ResponseFull): res is LocalResponse =>
  (<LocalResponse>res).localId !== undefined

const responseKey = (res: LocalResponse | ResponseFull): string =>
  "localId" in res ? res.localId : String(res.id)
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>Mes observations</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <ion-refresher slot="fixed" @ionRefresh="handleRefresh($event)">
        <ion-refresher-content />
      </ion-refresher>
      <div v-if="draftResponses.length" class="bg-amber-100 py-4">
        <p class="px-4 fr-text--sm font-semibold text-stone-600 mb-3!">
          En cours ({{ draftResponses.length }})
        </p>
        <div class="flex flex-row gap-3 overflow-x-auto px-4 pb-1">
          <div
            v-for="response in draftResponses"
            :key="response.localId"
            class="w-72 shrink-0"
          >
            <ResponseCard :response="response" @open="onOpen($event)" />
          </div>
        </div>
      </div>
      <div
        v-if="allResponses.length > 0"
        class="p-4 grid grid-cols-1 gap-3! text-left"
      >
        <ResponseCard
          v-for="response in nondraftResponses"
          :key="responseKey(response)"
          :response="response"
          @open="onOpen($event)"
        />
      </div>
      <div
        v-else
        class="flex flex-col items-center justify-center h-full gap-3 text-center px-8 text-stone-400"
      >
        <v-icon icon="ri-clipboard-line" scale="3" />
        <p class="fr-text--lg font-semibold mb-0!">Aucune observation</p>
        <p class="fr-text--sm mb-0!">
          Vos observations apparaîtront ici une fois que vous aurez répondu à
          une enquête.
        </p>
      </div>
    </ion-content>

    <ion-modal
      :is-open="selectedDraft !== null"
      :can-dismiss="() => surveyPageRef?.canDismiss() ?? true"
      @did-dismiss="selectedDraft = null"
    >
      <SurveyPage
        v-if="selectedDraft !== null"
        ref="surveyPageRef"
        :id="selectedDraft.surveyId"
        :local-id="selectedDraft.localId"
        :is-modal="true"
        @close="selectedDraft = null"
      />
    </ion-modal>

    <ion-modal
      :is-open="selectedFollowUpDraft !== null"
      :can-dismiss="() => followUpPageRef?.canDismiss() ?? true"
      @did-dismiss="selectedFollowUpDraft = null"
    >
      <FollowUpSurveyPage
        v-if="selectedFollowUpDraft !== null"
        ref="followUpPageRef"
        :response-id="String(selectedFollowUpDraft.parentResponse)"
        :follow-up-id="selectedFollowUpDraft.surveyFollowUp?.id"
        :local-id="selectedFollowUpDraft.localId"
        :is-modal="true"
        @close="selectedFollowUpDraft = null"
      />
    </ion-modal>
  </ion-page>
</template>

<style scoped>
ion-content,
ion-content::part(background) {
  background: #f4f4ff;
}
ion-refresher {
  --background: #f4f4ff;
}
ion-content {
  --padding-top: 0;
  --padding-bottom: 0;
  --padding-start: 0;
  --padding-end: 0;
}
</style>
