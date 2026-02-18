<script setup lang="ts">
import {
  IonPage,
  IonMenu,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonList,
  IonItem,
  IonLabel,
  IonIcon,
  IonRouterOutlet,
  IonMenuToggle,
} from "@ionic/vue"
import {
  documentTextOutline,
  navigateCircleOutline,
  personOutline,
  logOutOutline,
  helpCircleOutline,
} from "ionicons/icons"

import { useRouter } from "vue-router"
import { useAuthStore } from "../stores/auth"
import { useApiFetch } from "../utils/data-fetching"

const displayUserInfo = async () => {
  const { data } = await useApiFetch("/auth/me/").get().json()
  alert(`Je suis ${data.value.firstName} ${data.value.lastName}`)
}

const router = useRouter()
const auth = useAuthStore()

const logout = async () => {
  await auth.logout()
  router.replace({ name: "LoginPage" })
}
</script>

<template>
  <ion-page>
    <ion-menu content-id="main">
      <ion-header>
        <ion-toolbar>
          <ion-title>SylvaSan</ion-title>
        </ion-toolbar>
      </ion-header>

      <ion-content>
        <ion-list>
          <ion-menu-toggle :auto-hide="true">
            <ion-item button router-link="/projets" router-direction="root">
              <ion-icon slot="start" :icon="documentTextOutline" />
              <ion-label>Projets</ion-label>
            </ion-item>
          </ion-menu-toggle>

          <ion-menu-toggle :auto-hide="true">
            <ion-item
              button
              router-link="/gestion-des-cartes"
              router-direction="root"
            >
              <ion-icon slot="start" :icon="navigateCircleOutline" />
              <ion-label>Cartes</ion-label>
            </ion-item>
          </ion-menu-toggle>

          <ion-menu-toggle :auto-hide="true">
            <ion-item button router-link="/mon-profil" router-direction="root">
              <ion-icon slot="start" :icon="personOutline" />
              <ion-label>Profil</ion-label>
            </ion-item>
          </ion-menu-toggle>

          <ion-item @click="displayUserInfo"
            ><ion-icon
              aria-hidden="true"
              :icon="helpCircleOutline"
              slot="start"
            ></ion-icon>
            <ion-label> Qui suis-je ? </ion-label></ion-item
          >

          <ion-menu-toggle :auto-hide="true">
            <ion-item button @click="logout">
              <ion-icon slot="start" :icon="logOutOutline" />
              <ion-label>Déconnexion</ion-label>
            </ion-item>
          </ion-menu-toggle>
        </ion-list>
      </ion-content>
    </ion-menu>

    <ion-page id="main">
      <ion-router-outlet />
    </ion-page>
  </ion-page>
</template>
