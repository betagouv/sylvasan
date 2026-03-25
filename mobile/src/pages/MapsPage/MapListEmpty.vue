<script setup lang="ts">
import { mapOutline } from "ionicons/icons"

import { useIonRouter, IonIcon } from "@ionic/vue"

const router = useIonRouter()
</script>

<template>
  <div
    class="flex flex-col items-center justify-center gap-4 h-64 text-center text-stone-500"
  >
    <ion-icon :icon="mapOutline" />
    <div>
      <p class="fr-text--lg font-semibold fr-mb-1w">Aucune carte téléchargée</p>
      <p class="fr-text--sm">
        Utilisez le téléchargement pour enregistrer une zone et la consulter
        sans connexion.
      </p>
    </div>
    <DsfrButton
      label="Télécharger une zone"
      icon="ri-download-line"
      @click="router.push({ name: 'MapDownloadPage' })"
    />
  </div>
</template>
