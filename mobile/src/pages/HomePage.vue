<script setup lang="ts">
import {
  addOutline,
  documentTextOutline,
  navigateCircleOutline,
  personOutline,
  logOutOutline,
} from "ionicons/icons"
import {
  IonIcon,
  IonButtons,
  IonContent,
  IonHeader,
  IonMenu,
  IonMenuButton,
  IonPage,
  IonTitle,
  IonToolbar,
  IonButton,
  IonLabel,
  IonItem,
  IonList,
} from "@ionic/vue"

import { useRouter } from "vue-router"
import { useLightTheme } from "../utils/ui"
import { useAuthStore } from "../stores/auth"

import { useApiFetch } from "../utils/data-fetching"

useLightTheme()

const authStore = useAuthStore()
const router = useRouter()
const logOut = async () => {
  await authStore.logout()
  router.push({ name: "LoginPage" })
}

const testPost = async () => useApiFetch("/auth/test/").post().json()

useApiFetch("/auth/test/").post().json()
useApiFetch("/auth/test/").get().json()
</script>

<template>
  <ion-menu content-id="main-content">
    <ion-header>
      <ion-toolbar>
        <ion-title>SylvaSan</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <ion-list>
        <ion-item>
          <ion-icon
            aria-hidden="true"
            :icon="documentTextOutline"
            slot="start"
            class="mr-2"
          ></ion-icon>
          <ion-label>
            <h2>Projets</h2>
            <p class="pb-2">Mes formulaires et réponses</p>
          </ion-label>
        </ion-item>
        <ion-item>
          <ion-icon
            aria-hidden="true"
            :icon="navigateCircleOutline"
            slot="start"
            class="mr-2"
          ></ion-icon>
          <ion-label>
            <h2>Cartes hors ligne</h2>
            <p class="pb-2">Gerez le stockage de la cartographie</p>
          </ion-label>
        </ion-item>
        <ion-item>
          <ion-icon
            aria-hidden="true"
            :icon="personOutline"
            slot="start"
            class="mr-2"
          ></ion-icon>
          <ion-label>
            <h2>Mes informations</h2>
            <p class="pb-2">Gerez votre profil</p>
          </ion-label>
        </ion-item>
        <ion-item @click="testPost"
          ><ion-icon
            aria-hidden="true"
            :icon="logOutOutline"
            slot="start"
            class="mr-2"
          ></ion-icon>
          <ion-label>
            <h2>Test POST</h2>
          </ion-label></ion-item
        >
        <ion-item @click="logOut"
          ><ion-icon
            aria-hidden="true"
            :icon="logOutOutline"
            slot="start"
            class="mr-2"
          ></ion-icon>
          <ion-label>
            <h2>Déconnexion</h2>
          </ion-label></ion-item
        >
      </ion-list>
    </ion-content>
  </ion-menu>
  <ion-page id="main-content">
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-menu-button></ion-menu-button>
        </ion-buttons>
        <ion-buttons slot="end">
          <ion-button>
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
