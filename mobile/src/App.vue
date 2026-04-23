<script setup lang="ts">
import { IonApp, IonRouterOutlet } from "@ionic/vue"
import ToastContainer from "./components/ToastContainer.vue"
</script>

<template>
  <ion-app>
    <ToastContainer />
    <ion-router-outlet></ion-router-outlet>
  </ion-app>
</template>
