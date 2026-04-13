<script setup lang="ts">
import type { Survey } from "@shared-types/survey"

const { survey } = defineProps<{
  survey: Survey
}>()

const emit = defineEmits(["select"])
</script>

<template>
  <DsfrTile :title="survey.title" @click="emit('select')"> </DsfrTile>
</template>
