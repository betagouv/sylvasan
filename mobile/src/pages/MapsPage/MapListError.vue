<script setup lang="ts">
const { error } = defineProps<{ error: string }>()
</script>

<template>
  <div class="fr-alert fr-alert--error fr-mt-2w">
    <p>{{ error }}</p>
  </div>
</template>
