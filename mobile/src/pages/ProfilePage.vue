<script setup lang="ts">
import { IonPage, IonHeader, IonToolbar, IonContent } from "@ionic/vue"
import { computed } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "../stores/auth"
import { storeToRefs } from "pinia"

const authStore = useAuthStore()
const { loggedUser } = storeToRefs(authStore)
const router = useRouter()

const membershipTypeLabels: Record<string, string> = {
  admin: "Administrateur",
  manager: "Responsable",
  responder: "Répondant",
}

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
      <ion-toolbar />
    </ion-header>
    <ion-content class="ion-padding">
      <h1 class="fr-h3">Mon profil</h1>

      <DsfrTag
        icon="ri-links-line"
        v-if="loggedUser?.source !== 'local'"
        :label="`Compte ${loggedUser?.source?.toUpperCase()}`"
        class="mb-6!"
      />

      <section class="fr-mb-6w">
        <h2 class="fr-h5">Informations personnelles</h2>
        <dl class="pl-0!">
          <div v-for="info in personalInformation" :key="info.key" class="fr-mb-2w">
            <dt class="font-bold fr-text--sm mb-0!">{{ info.key }}</dt>
            <dd class="ml-0! pl-0!">{{ info.value }}</dd>
          </div>
        </dl>
      </section>

      <section class="fr-mb-6w">
        <h2 class="fr-h5">Rôles</h2>
        <p v-if="!loggedUser?.memberships.length" class="fr-text--sm text-gray-500">
          Aucun rôle assigné.
        </p>
        <div v-else class="flex flex-col gap-3">
          <div
            v-for="(m, i) in loggedUser?.memberships"
            :key="i"
            class="fr-p-3w border border-gray-200 rounded"
          >
            <p class="font-bold fr-text--sm mb-1!">{{ m.organisation.name }}</p>
            <p class="fr-text--sm mb-1!">{{ m.pole?.name ?? "Tous les pôles" }}</p>
            <DsfrBadge
              :label="membershipTypeLabels[m.membershipType] ?? m.membershipType"
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
