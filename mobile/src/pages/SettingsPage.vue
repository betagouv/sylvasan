<script setup lang="ts">
import { personOutline } from "ionicons/icons"
import {
  IonPage,
  IonHeader,
  IonToolbar,
  IonContent,
  IonTitle,
  IonIcon,
} from "@ionic/vue"
import { computed } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "../stores/auth"
import { useSyncStore } from "../stores/sync"
import { useToastStore } from "../stores/toast"
import { storeToRefs } from "pinia"
import { timeAgo } from "@shared-utils/date"

const authStore = useAuthStore()
const { loggedUser } = storeToRefs(authStore)
const syncStore = useSyncStore()
const { syncedAt, syncing } = storeToRefs(syncStore)
const toast = useToastStore()

const sync = async () => {
  try {
    await syncStore.syncAll()
    toast.show("Données mises à jour", "success")
  } catch {
    toast.show("Échec de la synchronisation", "error")
  }
}

const syncedAtLabel = computed(() =>
  syncedAt.value ? timeAgo(syncedAt.value) : "Jamais synchronisé"
)
const router = useRouter()

const membershipTypeLabels: Record<string, string> = {
  admin: "Administrateur",
  responder: "Répondant",
}
const fullName = computed(() => {
  return `${loggedUser.value?.firstName ?? ""} ${
    loggedUser.value?.lastName || "-"
  }`
})

const personalInformation = computed(() => [
  { key: "Prénom", value: loggedUser.value?.firstName ?? "-" },
  { key: "Nom", value: loggedUser.value?.lastName || "-" },
  { key: "Identifiant", value: loggedUser.value?.username ?? "-" },
])

const logout = async () => {
  await authStore.logout()
  router.replace({ name: "LoginPage" })
}
</script>

<template>
  <ion-page>
    <ion-header>
      <ion-toolbar>
        <ion-title>Paramètres</ion-title>
      </ion-toolbar>
    </ion-header>
    <ion-content class="ion-padding">
      <section class="mb-4 flex items-center gap-3">
        <div class="flex flex-col items-center gap-0">
          <ion-icon
            :icon="personOutline"
            class="p-2 bg-slate-100 rounded-full border border-slate-300"
          />
          <p
            v-if="loggedUser?.source !== 'local'"
            class="mb-0! fr-text--xs font-medium text-emerald-700"
          >
            {{ `${loggedUser?.source?.toUpperCase()}` }}
          </p>
        </div>
        <div>
          <p class="font-bold mb-0!">
            {{ fullName }}
          </p>
          <p class="fr-text--sm text-gray-500 font-bold mb-0!">
            {{ loggedUser?.username ?? "-" }}
          </p>
        </div>
      </section>

      <hr />
      <section class="mb-8">
        <h2 class="fr-h6 mb-1!">Gestion des données</h2>
        <p class="fr-text--sm text-gray-500 mb-2!">
          Dernière synchronisation {{ syncedAtLabel }}
        </p>
        <DsfrButton
          label="Synchroniser"
          size="sm"
          secondary
          icon="ri-refresh-line"
          :disabled="syncing"
          @click="sync"
        />
      </section>

      <hr />
      <section class="mb-8">
        <h2 class="fr-h6 mb-1!">Rôles</h2>
        <p
          v-if="!loggedUser?.memberships.length"
          class="fr-text--sm text-gray-500"
        >
          Aucun rôle assigné.
        </p>

        <div v-else class="flex flex-col gap-3">
          <div
            v-for="(m, i) in loggedUser?.memberships"
            :key="i"
            class="p-3 border border-gray-200 rounded"
          >
            <p class="font-bold fr-text--sm mb-1!">{{ m.organisation.name }}</p>
            <p class="fr-text--sm mb-1!">
              {{ m.pole?.name ?? "Tous les pôles" }}
            </p>
            <DsfrBadge
              :label="
                membershipTypeLabels[m.membershipType] ?? m.membershipType
              "
              type="info"
              no-icon
            />
          </div>
        </div>
      </section>

      <DsfrButton label="Se déconnecter" secondary @click="logout" />
    </ion-content>
  </ion-page>
</template>
