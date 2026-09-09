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
import { ref } from "vue"
import { useApiFetch } from "../utils/data-fetching.ts"
import ProgressSpinner from "../components/ProgressSpinner.vue"

const { data, isFetching } = useApiFetch("/stats").get().json()
const activeAccordion = ref("")

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

    <DsfrAccordionsGroup v-else v-model="activeAccordion">
      <DsfrAccordion
        v-for="stat in data"
        :key="stat.id"
        :id="stat.id"
        :title="stat.title"
      >
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
      </DsfrAccordion>
    </DsfrAccordionsGroup>
  </div>
</template>
