<script setup lang="ts">
import { addOutline } from "ionicons/icons"
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonIcon,
  IonButtons,
  IonMenuButton,
  IonButton,
} from "@ionic/vue"

const addProject = () => console.log("Add project")
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-menu-button />
        </ion-buttons>

        <ion-buttons slot="end">
          <ion-button @click="addProject">
            <ion-icon slot="start" :icon="addOutline"></ion-icon>
            Ajouter un projet
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <div class="grid grid-cols-1 p-3 gap-3! text-left">
        <DsfrCard
          title="Projet Ruche"
          description="Projet test pour le layout de l'application"
          link="/"
        >
          <template #end-details>
            <DsfrTags :tags="[{ label: '3 réponses' }]" />
          </template>
        </DsfrCard>
        <DsfrCard
          title="Projet Clermont-Ferrand"
          description="Le kickoff SylvaSan c'est bientôt !"
          link="/"
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
