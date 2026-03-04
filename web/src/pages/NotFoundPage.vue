<route lang="json">
{
  "path": "/page-non-trouvée",
  "meta": {
    "title": "Page non trouvée"
  }
}
</route>

<script setup lang="ts"></script>

<template>
  <div class="fr-container my-10">
    <DsfrErrorPage
      title="Page non trouvée"
      subtitle="Erreur 404"
      description="La page que vous recherchez est introuvable."
      class="p-0!"
    >
      <template v-slot:default>
        <router-link
          :to="{ name: '/HomePage' }"
          class="fr-btn fr-btn--md mt-0 mb-8"
          >Page d'accueil</router-link
        >
      </template>
    </DsfrErrorPage>
  </div>
</template>
