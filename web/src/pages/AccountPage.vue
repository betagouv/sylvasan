<route lang="json">
{
  "path": "/mon-compte",
  "meta": {
    "authenticationRequired": true,
    "title": "Mon compte"
  }
}
</route>

<script setup lang="ts">
import { computed } from "vue"
import { useRootStore } from "../stores/root"
import { storeToRefs } from "pinia"

const { loggedUser } = storeToRefs(useRootStore())

const membershipTypeLabels: Record<string, string> = {
  admin: "Administrateur",
  manager: "Responsable",
  responder: "Répondant",
}

const membershipTypeDescriptions: Record<string, string> = {
  admin: "Création d'enquêtes, accès aux réponses, gestion des usagers.",
  manager: "Accès aux réponses de son pôle ou organisation",
  responder: "Réponse aux enquêtes de son pôle ou organisation",
}

const membershipRows = computed(
  () =>
    loggedUser.value?.memberships.map((m) => [
      m.organisation.name,
      m.pole?.name ?? "Tous les pôles",
      membershipTypeLabels[m.membershipType] ?? m.membershipType,
      membershipTypeDescriptions[m.membershipType] ?? m.membershipType,
    ]) ?? []
)

const personalInformation = computed(() => {
  return [
    {
      key: "Prénom",
      label: loggedUser?.value?.firstName,
    },
    {
      key: "Nom",
      label: loggedUser?.value?.lastName || "-",
    },
    {
      key: "Identifiant",
      label: loggedUser?.value?.username,
    },
  ]
})
</script>

<template>
  <div class="fr-container my-6">
    <DsfrBreadcrumb
      :links="[{ to: '/', text: 'Accueil' }, { text: 'Mon compte' }]"
    />

    <h1 class="fr-h3">Mon compte</h1>

    <DsfrTag
      icon="ri-links-line"
      v-if="loggedUser?.source !== 'local'"
      :label="`Compte ${loggedUser?.source?.toUpperCase()}`"
      class="mb-6!"
    />

    <section class="mb-8">
      <h2 class="fr-h5">Informations personnelles</h2>
      <dl class="grid grid-cols-1 sm:grid-cols-3 gap-4 pl-0!">
        <div v-for="info in personalInformation" :key="info.key">
          <dt class="font-bold fr-text--sm mb-0!">{{ info.key }}</dt>
          <dd class="ml-0! pl-0!">{{ info.label }}</dd>
        </div>
      </dl>
    </section>

    <section>
      <h2 class="fr-h5">Rôles</h2>
      <p
        v-if="!loggedUser?.memberships.length"
        class="fr-text--sm text-gray-500"
      >
        Aucun rôle assigné.
      </p>
      <DsfrTable
        v-else
        title="Rôles"
        :no-caption="true"
        :headers="['Organisation', 'Pôle', 'Rôle', 'Actions']"
        :rows="membershipRows"
      />
    </section>
  </div>
</template>

<style scoped>
.fr-table :deep(table) {
  @apply table!;
}
</style>
