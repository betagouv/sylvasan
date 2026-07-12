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
import { computed, nextTick, ref } from "vue"
import SurveyBuilder from "../components/SurveyBuilder/index.vue"
import type { SurveySchema } from "@shared-types/survey"
import { useApiFetch } from "../utils/data-fetching.ts"
import { useToastStore } from "../stores/toast.ts"
import { useRouter, useRoute } from "vue-router"
import { useRootStore } from "../stores/root.ts"
import * as z from "zod"
import ProgressSpinner from "../components/ProgressSpinner.vue"
import EmptyPageTitleModal from "../components/SurveyBuilder/EmptyPageTitleModal.vue"
import { useAdminScopeSelection } from "../composables/useAdminScopeSelection.ts"

////////////////////////////////////////////////
//////// MODIFICATION / DUPLICATION ////////////
// Si on est dans le cas d'une modification d'une
// enquête existante, on doit fetch les données et
// initializer les refs pour rendre l'enquête
/////////////////////////////////////////////////
const route = useRoute()
const isFetching = ref(true)
const duplicateId = computed(() => route.query?.source)
const existingSurveyId = computed(() => route.params.surveyId)
const {
  execute,
  data: existingSurvey,
  onFetchError,
  onFetchResponse,
} = useApiFetch(`/surveys/${existingSurveyId.value || duplicateId.value}`, {
  immediate: false,
}).json()

onFetchError(() => {
  toast.show("Enquête introuvable", "error")
  router.push({ name: "/SurveyListPage" })
})

onFetchResponse(async () => {
  schema.value = existingSurvey.value.jsonSchema
  selectedOrganisationId.value = existingSurvey.value.organisation?.id
    ? String(existingSurvey.value.organisation.id)
    : ""
  await nextTick()
  selectedPoleOption.value = existingSurvey.value.pole?.id
    ? String(existingSurvey.value.pole?.id)
    : ""
  if (!duplicateId.value) {
    title.value = existingSurvey.value.title
  }

  isFetching.value = false
})

if (existingSurveyId.value || duplicateId.value) {
  execute()
} else {
  isFetching.value = false
}
/////////////////////////////////////////
/////////////////////////////////////////

const store = useRootStore()
const router = useRouter()
const toast = useToastStore()

const title = ref("")

const {
  selectedOrganisationId,
  selectedPoleOption,
  organisation,
  pole,
  orgOptions,
  poleOptions,
  showPoleSelect,
  hasOrgLevelAdmin,
  uniqueAdminOrgs,
  scopeValidator,
} = useAdminScopeSelection()

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
  pages: [{ id: "page_1", title: "Page 1", fields: [] }],
})

const pageTitleModalOpened = ref(false)

const payload = computed(() => ({
  organisation: organisation.value,
  pole: pole.value,
  title: title.value,
  jsonSchema: schema.value,
  campaign: null,
  createdBy: store.loggedUser?.id,
}))

const createOrUpdateSurvey = async () => {
  const hasPageWithoutTitle = schema.value.pages?.some(
    (p) => !p.title || p.title.trim() === ""
  )
  if (hasPageWithoutTitle) {
    pageTitleModalOpened.value = true
    return
  }
  try {
    scopeValidator.parse({
      title: title.value,
      fields: schema.value.fields,
      organisation: organisation.value,
      pole: pole.value,
    })
  } catch (error) {
    if (error instanceof z.ZodError) formErrors.value = z.flattenError(error)
    return
  }
  const saveFunction = existingSurveyId.value
    ? useApiFetch(`/surveys/${existingSurveyId.value}`).put
    : useApiFetch("/surveys/").post

  const { response } = await saveFunction(payload).json()
  if (response.value?.ok) {
    const message = existingSurveyId.value
      ? "Enquête modifiée"
      : "Enquête créée"
    toast.show(message, "success")
    router.push({ name: "/SurveyListPage" })
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
        { text: 'Mon enquête' },
      ]"
    />
    <div
      v-if="(existingSurveyId || duplicateId) && isFetching"
      class="flex justify-center my-20"
    >
      <ProgressSpinner />
    </div>
    <div v-else>
      <h1 class="fr-h4">
        <span v-if="existingSurveyId">Modifiez votre enquête </span>
        <span v-else>Créer une nouvelle enquête </span>
        <span v-if="uniqueAdminOrgs.length === 1"
          >pour {{ uniqueAdminOrgs[0].name }}</span
        >
      </h1>
      <div v-if="existingSurveyId" class="flex mb-6">
        <DsfrAlert
          type="warning"
          description="La modification d'une enquête existante peut entraîner des jeux de
        données incompatibles"
          :small="true"
        />
      </div>
      <div v-if="duplicateId" class="flex mb-6">
        <DsfrAlert
          type="info"
          :description="`Dupliquée à patir de l'enquête « ${existingSurvey?.title} »`"
          :small="true"
        />
      </div>
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
          v-if="uniqueAdminOrgs.length > 1"
          v-model="selectedOrganisationId"
          class="max-w-sm"
          label="Organisation"
          :options="orgOptions"
          :required="true"
          :error-message="formErrors?.fieldErrors?.organisation?.[0]"
          @update:modelValue="clearFieldError('organisation')"
        />
        <DsfrSelect
          v-if="showPoleSelect"
          v-model="selectedPoleOption"
          class="max-w-sm"
          label="Pôle"
          :options="poleOptions"
          :required="!hasOrgLevelAdmin"
          :error-message="formErrors?.fieldErrors?.pole?.[0]"
          @update:modelValue="clearFieldError('pole')"
        />
      </div>
      <div class="my-6">
        <SurveyBuilder
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
          @click="createOrUpdateSurvey"
        />
      </div>
    </div>
  </div>

  <EmptyPageTitleModal v-model="pageTitleModalOpened" />
</template>
