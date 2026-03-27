<route lang="json">
{
  "path": "/creation-enquete",
  "meta": {
    "authenticationRequired": true,
    "title": "Création d'enquête"
  }
}
</route>

<script setup lang="ts">
import { ref } from "vue"
import FormBuilder from "../../components/FormBuilder/index.vue"
import type { SurveySchema } from "../../types/survey"
import { DsfrBreadcrumb } from "@gouvminint/vue-dsfr"

const schema = ref<SurveySchema>({
  version: "1.0",
  fields: [],
})
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/DashboardPage', text: 'Dashboard' },
        { text: 'Création d\'enquête' },
      ]"
    />
    <h1 class="fr-h4">Créer une nouvelle enquête</h1>
    <div class="my-6">
      <FormBuilder v-model="schema" />
    </div>
    <div v-if="schema.fields.length" class="flex justify-end my-6">
      <DsfrButton label="Sauvegarder" icon="ri-cloud-line" size="large" />
    </div>
  </div>
</template>
