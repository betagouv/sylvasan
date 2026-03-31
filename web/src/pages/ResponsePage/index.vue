<route lang="json">
{
  "path": "/response/:id",
  "meta": {
    "authenticationRequired": true,
    "title": "Réponse"
  }
}
</route>

<script setup lang="ts">
import { useRoute } from "vue-router"
const route = useRoute()
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/dashboard', text: 'Dashboard' },
        { to: '/reponses', text: 'Réponses' },
        { text: `Réponse ${route.params.id}` },
      ]"
    />
    <h1>Réponse ID {{ route.params.id }}</h1>
  </div>
</template>
