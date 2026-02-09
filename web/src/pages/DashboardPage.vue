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
import { useRootStore } from "../stores/root"
import { storeToRefs } from "pinia"
import { useFetch } from "../utils/data-fetching"
import { useRouter } from "vue-router"

const router = useRouter()

const { loggedUser } = storeToRefs(useRootStore())

const logout = async () => {
  await useFetch("/auth/logout/").post()
  router.push({ name: "/" })
}
</script>

<template>
  <div class="fr-container my-10">
    <h1>Dashboard</h1>
    <p>Bienvenue {{ loggedUser?.firstName }}</p>
    <DsfrButton label="Se déconnecter" secondary @click="logout" />
  </div>
</template>
