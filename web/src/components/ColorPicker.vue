<script setup lang="ts">
const color = defineModel()

const options = [
  { text: "Bleu", value: "#e3e3fd" },
  { text: "Gris", value: "#ededed" },
  { text: "Rouge", value: "#ffc5c5" },
  { text: "Vert", value: "#c9fcac" },
  { text: "Jaune", value: "#fde39c" },
]
</script>

<template>
  <DsfrSelect :options="options" v-model="color" label="Couleur" />
</template>
