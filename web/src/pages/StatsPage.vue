<route lang="json">
{
  "path": "/stats",
  "meta": {
    "title": "Mesures d'impact",
    "sitemap": true
  }
}
</route>

<script setup lang="ts"></script>

<template>
  <div class="fr-container my-10">
    <DsfrBreadcrumb
      :links="[{ to: '/', text: 'Accueil' }, { text: 'Mesures d\'impact' }]"
    />
    <h1>Mesures d'impact</h1>

    <bar-chart
      x='[["2025", "2030", "2035", "2040"]]'
      y="[[10, 20, 30, 40]]"
      selected-palette="categorical"
    ></bar-chart>
  </div>
</template>
