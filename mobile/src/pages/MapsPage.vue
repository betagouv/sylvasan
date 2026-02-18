<script setup lang="ts">
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonButtons,
  IonMenuButton,
} from "@ionic/vue"
import imgUrl1 from "../assets/images/thumbnail-1.jpg"
import imgUrl2 from "../assets/images/thumbnail-2.jpg"
import imgUrl3 from "../assets/images/thumbnail-3.jpg"
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>Cartes</ion-title>
        <ion-buttons slot="start">
          <ion-menu-button />
        </ion-buttons>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <div class="p-2!">
        <div class="grid grid-cols-1 gap-3! text-left">
          <DsfrCard
            title="Carte régionale - 257 ko."
            description="Téléchargée le 18 février"
            link="/"
            :imgSrc="imgUrl1"
          />
          <DsfrCard
            title="Auvergne - 412 ko."
            description="Téléchargée le 5 février"
            link="/"
            :imgSrc="imgUrl2"
          />
          <DsfrCard
            title="Ouest - 188 ko."
            description="Téléchargée le 5 février"
            link="/"
            :imgSrc="imgUrl3"
          />
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
ion-content::part(background) {
  background: #ececfe;
}
</style>
