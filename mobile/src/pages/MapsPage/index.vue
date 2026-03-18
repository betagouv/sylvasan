<script setup lang="ts">
import { addOutline, pencilOutline, trashBinOutline } from "ionicons/icons"
import { ref } from "vue"
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonTitle,
  IonContent,
  IonButtons,
  IonMenuButton,
  IonActionSheet,
  alertController,
  IonIcon,
  IonButton,
  onIonViewDidEnter,
} from "@ionic/vue"
import { useOfflineMaps } from "../../composables/useOfflineMaps"
import MapListItem from "./MapListItem.vue"
import MapListLoading from "./MapListLoading.vue"
import MapListError from "./MapListError.vue"
import MapListEmpty from "./MapListEmpty.vue"
import {
  formatBytes,
  type OfflineMapRecord,
} from "../../composables/offlineMapMetadata"
import { useIonRouter } from "@ionic/vue"

const router = useIonRouter()
const { maps, loading, error, loadMaps, deleteMap, renameMap } =
  useOfflineMaps()

const actionSheetOpen = ref(false)
const selectedMap = ref<OfflineMapRecord | null>(null)

function openActions(map: OfflineMapRecord) {
  selectedMap.value = map
  actionSheetOpen.value = true
}

const actionSheetButtons = [
  {
    text: "Renommer",
    icon: pencilOutline,
    handler: () => {
      if (selectedMap.value) promptRename(selectedMap.value)
    },
  },
  {
    text: "Supprimer",
    icon: trashBinOutline,
    role: "destructive",
    handler: () => {
      if (selectedMap.value) confirmDelete(selectedMap.value)
    },
  },
  {
    text: "Annuler",
    role: "cancel",
  },
]

async function promptRename(map: OfflineMapRecord) {
  const alert = await alertController.create({
    header: "Renommer la carte",
    inputs: [
      {
        name: "name",
        type: "text",
        value: map.name,
        placeholder: "Nom de la carte",
      },
    ],
    buttons: [
      { text: "Annuler", role: "cancel" },
      {
        text: "Enregistrer",
        handler: (data) => {
          const name = data.name?.trim()
          if (name) renameMap(map.id, name)
        },
      },
    ],
  })
  await alert.present()
}

async function confirmDelete(map: OfflineMapRecord) {
  const alert = await alertController.create({
    header: "Êtes-vous sur de vouloir supprimer la carte ?",
    message: `"${map.name}" sera définitivement supprimée (${formatBytes(
      map.bytes
    )}).`,
    buttons: [
      { text: "Annuler", role: "cancel" },
      {
        text: "Supprimer",
        role: "destructive",
        handler: () => deleteMap(map.id),
      },
    ],
  })
  await alert.present()
}

// Nécessaire d'utiliser cette fontion pour re-rendre les cartes quand on revient
// de la page de téléchargement
onIonViewDidEnter(loadMaps)
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-buttons slot="start">
          <ion-menu-button />
        </ion-buttons>
        <ion-title>Mes cartes</ion-title>
        <ion-buttons slot="end">
          <ion-button @click="router.push({ name: 'MapDownloadPage' })">
            <ion-icon slot="start" :icon="addOutline"></ion-icon>
            Ajouter
          </ion-button>
        </ion-buttons>
      </ion-toolbar>
    </ion-header>

    <ion-content class="ion-padding">
      <MapListLoading v-if="loading" />

      <MapListError v-else-if="error" :error="error" />

      <MapListEmpty v-else-if="maps.length === 0" />

      <div v-else class="grid grid-cols-1 gap-3 p-2">
        <div v-for="map in maps" :key="map.id">
          <MapListItem :map="map" @open-actions="openActions(map)" />
        </div>
      </div>
    </ion-content>

    <ion-action-sheet
      :is-open="actionSheetOpen"
      :header="selectedMap?.name"
      :buttons="actionSheetButtons"
      @did-dismiss="actionSheetOpen = false"
    />
  </ion-page>
</template>

<style scoped>
ion-content::part(background) {
  background: #ececfe;
}
</style>
