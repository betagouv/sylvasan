<route lang="json">
{
  "path": "/email-de-confirmation-envoye",
  "meta": {
    "title": "Confirmez votre adresse email",
    "omitIfLoggedIn": true,
    "sitemap": true
  }
}
</route>

<script setup lang="ts"></script>

<template>
  <div class="fr-container mb-10">
    <DsfrBreadcrumb
      :links="[
        { to: '/', text: 'Accueil' },
        { to: '/s-identifier', text: 'S\'identifier' },
        { text: 'Confirmez votre adresse email' },
      ]"
    />
    <div>
      <h1 class="fr-h3">
        <v-icon name="ri-mail-send-line" scale="2" class="mr-2" />Vérifiez votre
        adresse email
      </h1>

      <p class="fr-text--lg mb-1!">
        Un email de confirmation vous a été envoyé.
      </p>

      <p class="fr-text--lg">
        Cliquez sur le lien qu'il contient pour activer votre compte.
      </p>

      <p class="fr-text--sm text-stone-500">
        Pensez à vérifier votre dossier spam ou courrier indésirable.
      </p>

      <DsfrButton
        label="Revenir à l'accueil"
        secondary
        class="mt-6"
        @click="$router.push('/')"
      />
    </div>
  </div>
</template>
