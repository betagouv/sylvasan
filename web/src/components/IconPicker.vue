<script setup lang="ts">
const icon = defineModel()

const options = [
  { text: "Ajout note", value: "ri-sticky-note-add-line" },
  { text: "Croix", value: "ri-close-line" },
  { text: "Information", value: "ri-information-line" },
  { text: "Alerte", value: "ri-error-warning-line" },
  { text: "Œil", value: "ri-eye-line" },
  { text: "Laboratoire", value: "ri-flask-line" },
  { text: "Check", value: "ri-check-line" },
]
</script>

<template>
  <DsfrSelect :options="options" v-model="icon" label="Icône" />
</template>
