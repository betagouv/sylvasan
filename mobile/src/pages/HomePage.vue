<template>
  <ion-tabs>
    <ion-tab tab="home">
      <ion-page id="home-page">
        <ion-header>
          <ion-toolbar>
            <ion-title>Formulaires</ion-title>
          </ion-toolbar>
        </ion-header>
        <ion-content>
          <div class="m-2">
            <DsfrAlert title="Alerte DSFR" />
          </div>
        </ion-content>
      </ion-page>
    </ion-tab>
    <ion-tab tab="radio">
      <ion-page id="radio-page">
        <ion-header>
          <ion-toolbar>
            <ion-title>Mes réponses</ion-title>
          </ion-toolbar>
        </ion-header>
        <ion-content>
          <div class="example-content">Mes réponses</div>
        </ion-content>
      </ion-page>
    </ion-tab>
    <ion-tab tab="library">
      <ion-page id="library-page">
        <ion-header>
          <ion-toolbar>
            <ion-title>Paramètres</ion-title>
          </ion-toolbar>
        </ion-header>
        <ion-content>
          <div class="example-content">Paramètres</div>
        </ion-content>
      </ion-page>
    </ion-tab>

    <ion-tab-bar slot="bottom">
      <ion-tab-button tab="home">
        <ion-icon :icon="createOutline" />
        Formulaires
      </ion-tab-button>
      <ion-tab-button tab="radio">
        <ion-icon :icon="documentTextOutline" />
        Mes réponses
      </ion-tab-button>
      <ion-tab-button tab="library">
        <ion-icon :icon="settingsOutline" />
        Paramètres
      </ion-tab-button>
    </ion-tab-bar>
  </ion-tabs>
</template>

<script setup lang="ts">
import {
  IonContent,
  IonHeader,
  IonIcon,
  IonPage,
  IonTab,
  IonTabs,
  IonTabBar,
  IonTabButton,
  IonTitle,
  IonToolbar,
} from "@ionic/vue"
import {
  documentTextOutline,
  createOutline,
  settingsOutline,
} from "ionicons/icons"
</script>

<style scoped>
.example-content {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>
