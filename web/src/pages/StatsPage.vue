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

const flatX = (stat: any) => JSON.stringify(stat.data.labels)
const yLine = (stat: any) => JSON.stringify(stat.data.datasets[0].data)
const yBar = (stat: any) => {
  const cumulative: number[] = stat.data.datasets[0].data
  return JSON.stringify(cumulative.map((v: number, i: number) => (i === 0 ? v : v - cumulative[i - 1])))
}
const nameLine = (stat: any) => stat.data.datasets[0].label
const yMax = (stat: any) => {
  const cumulative: number[] = stat.data.datasets[0].data
  return cumulative.length ? cumulative[cumulative.length - 1] : undefined
}
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
        <bar-line-chart
          :x="flatX(stat)"
          :y-bar="yBar(stat)"
          :y-line="yLine(stat)"
          name-bar="Par mois"
          :name-line="nameLine(stat)"
          :y-bar-max="yMax(stat)"
          :y-line-max="yMax(stat)"
          selected-palette="categorical"
        />
      </div>
    </div>
  </div>
</template>
