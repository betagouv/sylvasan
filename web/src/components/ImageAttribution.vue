<script setup lang="ts">
defineProps({
  licenseName: String,
  licenseUrl: String,
  sourceUrl: String,
  author: String,
  authorUrl: String,
  creativeCommons: Boolean,
})
</script>

<template>
  <p class="attribution text-xs!">
    <a rel="noopener noreferrer" :href="sourceUrl">Image</a>
    de
    <a rel="noopener noreferrer" :href="authorUrl">{{ author }}</a>
    sous licence
    <a rel="noopener noreferrer" :href="licenseUrl"
      >{{ licenseName }}
      <img
        v-if="creativeCommons"
        src="https://mirrors.creativecommons.org/presskit/icons/cc.svg"
        class="license-logo"
      />
      <img
        v-if="creativeCommons"
        src="https://mirrors.creativecommons.org/presskit/icons/by.svg"
        class="license-logo"
      /> </a
    >.
  </p>
</template>

<style scoped>
.license-logo {
  height: 1em;
  margin-right: 0.125em;
  display: inline;
}
</style>
