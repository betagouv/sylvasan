<route lang="json">
{
  "path": "/creation-enquete",
  "meta": {
    "authenticationRequired": true,
    "title": "Création d'enquête"
  }
}
</route>

<script setup lang="ts">
import { computed, ref } from "vue"
import FormBuilder from "../../components/FormBuilder/index.vue"
import type { SurveySchema } from "../../types/survey"
import { DsfrBreadcrumb } from "@gouvminint/vue-dsfr"
import { useApiFetch } from "../../utils/data-fetching"
import { useToastStore } from "../../stores/toast"
import { useRouter } from "vue-router"
import { useRootStore } from "../../stores/root"

const store = useRootStore()
const router = useRouter()
const toast = useToastStore()

const title = ref("")

const schema = ref<SurveySchema>({
  version: "1.0",
  fields: [],
})

const adminMemberships = computed(() =>
  store.loggedUser?.memberships.filter((x) => x.membershipType === "admin")
)

const payload = computed(() => ({
  organisation: adminMemberships.value?.[0].organisation.id, // TODO handle multiple orgs
  pole: null,
  title: title.value,
  jsonSchema: schema.value,
  campaign: null,
  createdBy: store.loggedUser?.id,
}))

const createSurvey = async () => {
  // TODO : add schema validation with Json schema
  const { response } = await useApiFetch("/surveys/").post(payload).json()
  if (response.value?.ok) {
    toast.show("Enquête créée", "success")
    router.push({ name: "/HomePage" })
  } else {
    toast.show("Une erreur s'est produite", "error")
  }
}
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/DashboardPage', text: 'Dashboard' },
        { text: 'Création d\'enquête' },
      ]"
    />
    <h1 class="fr-h4">
      Créer une nouvelle enquête
      <span v-if="adminMemberships?.length === 1"
        >pour {{ adminMemberships[0].organisation.name }}</span
      >
    </h1>
    <DsfrInputGroup>
      <DsfrInput
        class="max-w-sm"
        label="Titre de l'enquête"
        label-visible
        v-model="title"
      />
    </DsfrInputGroup>
    <div class="my-6">
      <FormBuilder v-model="schema" />
    </div>
    <div v-if="schema.fields.length" class="flex justify-end my-6">
      <DsfrButton
        label="Sauvegarder"
        icon="ri-cloud-line"
        size="large"
        @click="createSurvey"
      />
    </div>
  </div>
</template>
