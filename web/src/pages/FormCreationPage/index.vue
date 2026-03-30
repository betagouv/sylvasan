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
import type { SurveySchema } from "@shared-types/survey"
import { DsfrBreadcrumb } from "@gouvminint/vue-dsfr"
import { useApiFetch } from "../../utils/data-fetching"
import { useToastStore } from "../../stores/toast"
import { useRouter } from "vue-router"
import { useRootStore } from "../../stores/root"
import * as z from "zod"
import { ZodError } from "zod"

const store = useRootStore()
const router = useRouter()
const toast = useToastStore()

const title = ref("")

const adminMemberships = computed(() =>
  store.loggedUser?.memberships.filter((x) => x.membershipType === "admin")
)

const orgOptions = computed(
  () =>
    adminMemberships.value?.map((m) => ({
      text: m.organisation.name,
      value: m.organisation.id,
    })) ?? []
)

const selectedOrganisationId = ref<number | undefined>()

const organisation = computed(() =>
  adminMemberships.value?.length === 1
    ? adminMemberships.value[0].organisation.id
    : selectedOrganisationId.value
)

const validator = z.object({
  title: z.string().min(1, "Le titre est obligatoire"),
  fields: z.array(z.any()).min(1, "L'enquête doit contenir au moins un champ"),
  organisation: z.coerce.number("L'organisation est obligatoire"),
})

const formErrors = ref<{
  formErrors: string[]
  fieldErrors: Record<string, string[]>
}>({
  formErrors: [],
  fieldErrors: {},
})

function clearFieldError(field: string) {
  if (formErrors.value.fieldErrors[field])
    delete formErrors.value.fieldErrors[field]
}

const schema = ref<SurveySchema>({
  version: "1.0",
  fields: [],
})

const payload = computed(() => ({
  organisation: organisation.value,
  pole: null,
  title: title.value,
  jsonSchema: schema.value,
  campaign: null,
  createdBy: store.loggedUser?.id,
}))

const createSurvey = async () => {
  // TODO : add schema validation with Json schema
  try {
    validator.parse({
      title: title.value,
      fields: schema.value.fields,
      organisation: organisation.value,
    })
  } catch (error) {
    if (error instanceof ZodError) formErrors.value = z.flattenError(error)
    return
  }
  const { response } = await useApiFetch("/surveys/").post(payload).json()
  if (response.value?.ok) {
    toast.show("Enquête créée", "success")
    router.push({ name: "/DashboardPage" })
  } else {
    toast.show("Une erreur s'est produite", "error")
  }
}
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/dashboard', text: 'Dashboard' },
        { text: 'Création d\'enquête' },
      ]"
    />
    <h1 class="fr-h4">
      Créer une nouvelle enquête
      <span v-if="adminMemberships?.length === 1"
        >pour {{ adminMemberships[0].organisation.name }}</span
      >
    </h1>
    <div class="flex gap-8">
      <DsfrInputGroup :error-message="formErrors?.fieldErrors?.title?.[0]">
        <DsfrInput
          class="max-w-sm"
          label="Titre de l'enquête"
          :required="true"
          label-visible
          v-model="title"
          @update:modelValue="clearFieldError('title')"
        />
      </DsfrInputGroup>
      <DsfrSelect
        v-if="adminMemberships && adminMemberships.length > 1"
        v-model="selectedOrganisationId"
        class="max-w-sm"
        label="Organisation"
        :options="orgOptions"
        :required="true"
        :error-message="formErrors?.fieldErrors?.organisation?.[0]"
        @update:modelValue="clearFieldError('organisation')"
      />
    </div>
    <div class="my-6">
      <FormBuilder
        v-model="schema"
        @update:modelValue="clearFieldError('fields')"
      />
      <p v-if="formErrors?.fieldErrors?.fields?.[0]" class="fr-error-text">
        {{ formErrors.fieldErrors.fields[0] }}
      </p>
    </div>
    <div class="flex justify-end my-6">
      <DsfrButton
        label="Sauvegarder"
        icon="ri-cloud-line"
        size="large"
        @click="createSurvey"
      />
    </div>
  </div>
</template>
