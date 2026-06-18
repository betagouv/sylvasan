<route lang="json">
{
  "path": "/compte-non-active",
  "meta": {
    "title": "Compte non activé",
    "omitIfLoggedIn": true
  }
}
</route>

<script setup lang="ts">
import { ref } from "vue"
import { useRoute } from "vue-router"
import { useApiFetch } from "../utils/data-fetching"

const route = useRoute()

const identifier = ref((route.query.identifier as string) ?? "")
const sent = ref(false)

const { execute, isFetching } = useApiFetch("/auth/resend-verification/", {
  immediate: false,
}).post(identifier.value ? { identifier: identifier.value } : {})

const resend = async () => {
  await execute()
  sent.value = true
}
</script>

<template>
  <div class="fr-container mb-10">
    <DsfrBreadcrumb
      :links="[
        { to: '/', text: 'Accueil' },
        { to: '/s-identifier', text: 'S\'identifier' },
        { text: 'Compte non activé' },
      ]"
    />

    <div class="max-w-lg">
      <h1 class="fr-h3">
        <v-icon name="ri-mail-close-line" scale="1.5" class="mr-2" />
        Compte non activé
      </h1>

      <p class="fr-text--lg">
        Vous n'avez pas encore confirmé votre adresse email. Veuillez cliquer
        sur le lien envoyé lors de votre inscription pour activer votre compte.
      </p>

      <p class="fr-text--sm text-stone-500">
        Pensez à vérifier votre dossier spam ou courrier indésirable.
      </p>

      <DsfrAlert
        v-if="sent"
        type="success"
        title="Email renvoyé"
        description="Un nouvel email de vérification vous a été envoyé. Vérifiez votre boîte de réception."
        class="mb-4"
      />

      <DsfrButton
        label="Renvoyer l'email de vérification"
        icon="ri-send-plane-line"
        :disabled="isFetching || sent"
        v-if="!sent"
        @click="resend"
      />
    </div>
  </div>
</template>
