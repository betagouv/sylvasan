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
    <div v-if="survey" class="mb-4">
      <h1 class="fr-h4">Enquête « {{ survey.title }} »</h1>
      <div class="mb-4">
        <p class="fr-badge">
          {{ survey.organisation.name }}
        </p>
        <p v-if="survey.pole" class="fr-badge">{{ survey.pole.name }}</p>
      </div>
      <h2>Schema JSON</h2>
      <div class="bg-stone-100 p-4 rounded border border-stone-200">
        <pre>
<code>
{{ survey.jsonSchema }}
</code>
        </pre>
      </div>
    </div>
  </div>
</template>
