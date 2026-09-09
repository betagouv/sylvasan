<route lang="json">
{
  "path": "/stats",
  "meta": {
    "title": "Mesures d'impact",
    "sitemap": true
  }
}
</route>

<script setup lang="ts">
import { useApiFetch } from "../utils/data-fetching.ts"
import ProgressSpinner from "../components/ProgressSpinner.vue"

const { data, isFetching } = useApiFetch("/stats").get().json()

const chartTag = (type: string) => `${type}-chart`
const chartX = (stat: any) => JSON.stringify([stat.data.labels])
const chartY = (stat: any) => JSON.stringify(stat.data.datasets.map((d: any) => d.data))
const chartName = (stat: any) => JSON.stringify(stat.data.datasets.map((d: any) => d.label))
</script>

<template>
  <div class="fr-container my-10">
    <DsfrBreadcrumb
      :links="[{ to: '/', text: 'Accueil' }, { text: 'Mesures d\'impact' }]"
    />
    <h1>Mesures d'impact</h1>

    <div v-if="isFetching" class="flex justify-center my-20">
      <ProgressSpinner />
    </div>

    <div v-else class="flex flex-col gap-10">
      <div v-for="stat in data" :key="stat.id">
        <h2>{{ stat.title }}</h2>
        <p class="fr-text--lead">{{ stat.description }}</p>
        <component
          :is="chartTag(stat.type)"
          :x="chartX(stat)"
          :y="chartY(stat)"
          :name="chartName(stat)"
          selected-palette="categorical"
        />
      </div>
    </div>
  </div>
</template>
