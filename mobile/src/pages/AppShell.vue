<script setup lang="ts">
import {
  IonPage,
  IonTabs,
  IonTabBar,
  IonTabButton,
  IonIcon,
  IonLabel,
  IonRouterOutlet,
  IonModal,
} from "@ionic/vue"
import {
  mapOutline,
  clipboardOutline,
  addOutline,
  cloudDownloadOutline,
  personOutline,
} from "ionicons/icons"
import { ref } from "vue"
import SurveyListPage from "./SurveyListPage.vue"
import SurveyPage from "./SurveyPage.vue"

const surveyListOpen = ref(false)
const selectedSurveyId = ref<number | null>(null)

const onSurveySelected = (id: number) => {
  surveyListOpen.value = false
  selectedSurveyId.value = id
}
</script>

<template>
  <ion-page>
    <ion-tabs>
      <ion-router-outlet />
      <ion-tab-bar slot="bottom">
        <ion-tab-button tab="carte" href="/carte">
          <ion-icon :icon="mapOutline" />
          <ion-label>Ma position</ion-label>
        </ion-tab-button>

        <ion-tab-button tab="observations" href="/observations">
          <ion-icon :icon="clipboardOutline" />
          <ion-label>Observations</ion-label>
        </ion-tab-button>

        <!-- Espace réservé pour le bouton central positionné en dehors de la tab bar -->
        <div class="tab-center-spacer" />

        <ion-tab-button tab="cartes" href="/cartes">
          <ion-icon :icon="cloudDownloadOutline" />
          <ion-label>Cartes</ion-label>
        </ion-tab-button>

        <ion-tab-button tab="profil" href="/profil">
          <ion-icon :icon="personOutline" />
          <ion-label>Profil</ion-label>
        </ion-tab-button>
      </ion-tab-bar>
    </ion-tabs>

    <!-- Bouton central en dehors de ion-tab-bar pour éviter le clipping du shadow DOM -->
    <button
      class="tab-center-button fixed rounded-full flex"
      @click="surveyListOpen = true"
    >
      <ion-icon :icon="addOutline" />
    </button>

    <!-- Modal liste des enquêtes -->
    <ion-modal
      :is-open="surveyListOpen"
      @did-dismiss="surveyListOpen = false"
      :breakpoints="[0, 1]"
      :initial-breakpoint="1"
      handle
    >
      <SurveyListPage @select="onSurveySelected" />
    </ion-modal>

    <!-- Modal détail d'une enquête -->
    <ion-modal
      :is-open="selectedSurveyId !== null"
      @did-dismiss="selectedSurveyId = null"
    >
      <SurveyPage
        v-if="selectedSurveyId !== null"
        :id="selectedSurveyId"
        :is-modal="true"
        @close="selectedSurveyId = null"
      />
    </ion-modal>
  </ion-page>
</template>

<style scoped>
.tab-center-spacer {
  flex: 1;
}

.tab-center-button {
  bottom: calc(var(--ion-safe-area-bottom, 0px) + 12px);
  left: 50%;
  transform: translateX(-50%);
  width: 56px;
  height: 56px;
  background: var(--ion-color-primary, #3880ff);
  color: white;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  border: none;
  cursor: pointer;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
  z-index: 999;
}
</style>
