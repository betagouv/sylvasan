<route lang="json">
{
  "path": "/dashboard",
  "meta": {
    "authenticationRequired": true,
    "title": "Tableau de bord"
  }
}
</route>

<script setup lang="ts">
import { computed } from "vue"
import { useRootStore } from "../stores/root"
import { storeToRefs } from "pinia"
const { loggedUser } = storeToRefs(useRootStore())

const userIsAdmin = computed(() =>
  loggedUser.value?.memberships.find((x) => x.membershipType === "admin")
)

const adminActions = [
  {
    title: "Créer une enquête",
    description: "Créez une nouvelle enquête",
    link: { name: "/FormCreationPage/" },
  },
  {
    title: "Mes enquêtes",
    description: "Toutes mes enquêtes",
    link: { name: "/SurveyListPage/" },
  },
]

const userActions = [
  {
    title: "Mon compte",
    description: "Mettez à jour vos informations",
    link: { name: "/HomePage" },
  },
  {
    title: "Guide utilisateur",
    description: "",
    link: { name: "/HomePage" },
  },
]
</script>

<template>
  <div class="bg-blue-france-975 relative inset-shadow-sm">
    <div class="fr-container py-3">
      <p class="m-0! font-medium">
        <v-icon name="ri-user-line" class="mr-2" /> Bienvenue
        {{ loggedUser?.firstName }}
      </p>
    </div>
  </div>
  <div class="fr-container my-6">
    <h1 class="fr-h6">Mon tableau de bord</h1>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <DsfrCard
        v-for="(action, index) in adminActions"
        v-if="userIsAdmin"
        :key="`${action.title}-${index}`"
        :title="action.title"
        :description="action.description"
        :link="action.link"
      />
    </div>

    <h2 class="fr-h6 mt-8!">Réglages</h2>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <DsfrCard
        v-for="(action, index) in userActions"
        :key="`${action.title}-${index}`"
        :title="action.title"
        :description="action.description"
        :link="action.link"
      />
    </div>
  </div>
</template>
