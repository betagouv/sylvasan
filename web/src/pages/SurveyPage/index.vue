<route lang="json">
{
  "path": "/enquete/:id",
  "meta": {
    "authenticationRequired": true,
    "title": "Enquête"
  }
}
</route>

<script setup lang="ts">
import { useRoute } from "vue-router"
import { useApiFetch } from "../../utils/data-fetching"

const route = useRoute()

const { data: survey } = useApiFetch(`/surveys/${route.params.id}`).json()
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/dashboard', text: 'Dashboard' },
        { to: '/enquetes', text: 'Enquêtes' },
        { text: `Enquête ${route.params.id}` },
      ]"
    />
    <div v-if="survey">
      <h1>Enquête « {{ survey.title }} »</h1>
    </div>
  </div>
</template>
