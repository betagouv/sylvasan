<route lang="json">
{
  "path": "/enquetes",
  "meta": {
    "authenticationRequired": true,
    "title": "Mes enquête"
  }
}
</route>

<script setup lang="ts">
import { useApiFetch } from "../../utils/data-fetching"

const { data: surveys } = useApiFetch("/surveys/").get().json()
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/dashboard', text: 'Dashboard' },
        { text: 'Mes enquêtes' },
      ]"
    />
    <h1 class="fr-h4">Mes enquêtes</h1>
    <div class="flex flex-col gap-6 my-2">
      <div
        v-for="survey in surveys"
        :key="`survey-${survey.id}`"
        class="border p-4 rounded border-slate-200"
      >
        <h5 class="mb-0!">{{ survey.title }}</h5>

        <ul>
          <li
            v-for="field in survey.jsonSchema.fields"
            :key="`field-${survey.id}-${field.id}`"
          >
            {{ field.label }} (type « {{ field.type }} »)
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
