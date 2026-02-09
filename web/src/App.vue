<script setup lang="ts">
import { useRoute } from "vue-router"
import { useTitle } from "@vueuse/core"
import { computed } from "vue"
import { fr } from "zod/locales"
import * as z from "zod"

z.config(fr())

const environment = window.ENVIRONMENT
const logoText = [
  "Ministère",
  "de l'Agriculture,",
  "de l'Agro-alimentaire",
  "et de la Souveraineté",
  "Alimentaire",
]

const currentRoute = useRoute()
useTitle(computed(() => `${currentRoute.meta.title || ""} - SylvaSan`))
</script>

<template>
  <DsfrSkipLinks
    :links="[
      { id: 'main-content', text: 'Aller au contenu principal' },
      { id: 'navigation', text: 'Aller au menu' },
      { id: 'footer', text: 'Aller au pied de page' },
    ]"
  />

  <p
    v-if="environment && environment !== 'prod'"
    id="env-banner"
    :class="`${environment} mb-0 sm:hidden`"
  >
    Environnement de {{ environment }}
  </p>

  <DsfrHeader :logo-text="logoText" id="navigation" />
  <main id="main-content">
    <router-view></router-view>
  </main>
  <DsfrFooter :logo-text="logoText" id="footer">
    <template v-slot:description>
      <p>SylvaSan</p>
    </template>
  </DsfrFooter>
</template>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
</style>
