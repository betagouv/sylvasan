<route lang="json">
{
  "path": "/enquetes/:surveyId/creation-suivi",
  "meta": {
    "authenticationRequired": true,
    "title": "Création de sous-enquête de suivi"
  }
}
</route>

<script setup lang="ts">
import { computed, nextTick, ref } from "vue"
import SurveyBuilder from "../components/SurveyBuilder/index.vue"
import { useApiFetch } from "../utils/data-fetching.ts"
import { useToastStore } from "../stores/toast.ts"
import { useRouter, useRoute } from "vue-router"
import { useRootStore } from "../stores/root.ts"
import ColorPicker from "../components/ColorPicker.vue"
import * as z from "zod"
import { ZodError } from "zod"
import ProgressSpinner from "../components/ProgressSpinner.vue"
import type { SurveySchema } from "@shared-types/survey"
import IconPicker from "../components/IconPicker.vue"
import EmptyPageTitleModal from "../components/SurveyBuilder/EmptyPageTitleModal.vue"
import { useAdminScopeSelection } from "../composables/useAdminScopeSelection.ts"

const store = useRootStore()
const router = useRouter()
const toast = useToastStore()

const title = ref("")
const actionLabel = ref("")
const color = ref("#e3e3fd")
const icon = ref("ri-information-line")

const pageTitleModalOpened = ref(false)

const schema = ref<SurveySchema>({
  version: "1.0",
  fields: [],
  pages: [{ id: "page_1", title: "Page 1", fields: [] }],
})

const formErrors = ref<{
  formErrors: string[]
  fieldErrors: Record<string, string[]>
}>({
  formErrors: [],
  fieldErrors: {},
})

////////////////////////////////////////////////
//////////////// MODIFICATION //////////////////
// Si on est dans le cas d'une modification d'une
// enquête existante, on doit fetch les données et
// initializer les refs pour rendre l'enquête
/////////////////////////////////////////////////
const route = useRoute()
const isFetchingFollowUp = ref(true)
const surveyId = computed(() => route.params.surveyId)
const existingFollowUpId = computed(() => route.params.followUpId)
const {
  execute: executeFollowUpQuery,
  data: existingFollowUp,
  onFetchError: onFetchFollowUpError,
  onFetchResponse: onFetchFollowUpResponse,
} = useApiFetch(
  `/surveys/${surveyId.value}/follow-ups/${existingFollowUpId.value}`,
  {
    immediate: false,
  }
).json()

onFetchFollowUpError(() => {
  toast.show("Sous-enquête de suivi introuvable", "error")
  router.push({ name: "/SurveyPage", params: { id: surveyId.value } })
})

onFetchFollowUpResponse(async () => {
  schema.value = existingFollowUp.value.jsonSchema
  selectedOrganisationId.value = existingFollowUp.value.organisation?.id
    ? String(existingFollowUp.value.organisation.id)
    : ""
  await nextTick()
  selectedPoleOption.value = existingFollowUp.value.pole?.id
    ? String(existingFollowUp.value.pole?.id)
    : ""

  color.value = existingFollowUp.value.actionColor
  icon.value = existingFollowUp.value.actionIcon
  actionLabel.value = existingFollowUp.value.actionLabel
  title.value = existingFollowUp.value.title

  isFetchingFollowUp.value = false
})

if (existingFollowUpId.value) {
  executeFollowUpQuery()
} else {
  isFetchingFollowUp.value = false
}
/////////////////////////////////////////
/////////////////////////////////////////

const isFetchingSurvey = ref(true)
const {
  execute: executeSurveyQuery,
  data: survey,
  onFetchError: onFetchSurveyError,
  onFetchResponse: onFetchSurveyResponse,
  onFetchFinally: onFetchSurveyFinally,
} = useApiFetch(`/surveys/${surveyId.value}`, {
  immediate: false,
}).json()

onFetchSurveyError(() => {
  toast.show("Enquête introuvable", "error")
  router.push({ name: "/SurveyListPage" })
})

onFetchSurveyResponse(async () => {
  selectedOrganisationId.value = survey.value.organisation?.id
    ? String(survey.value.organisation.id)
    : ""
  await nextTick()
  selectedPoleOption.value = survey.value.pole?.id
    ? String(survey.value.pole?.id)
    : ""
})

onFetchSurveyFinally(() => {
  isFetchingSurvey.value = false
})

executeSurveyQuery()

const isFetching = computed(
  () => isFetchingFollowUp.value || isFetchingSurvey.value
)

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
} = useAdminScopeSelection()

const createOrUpdateFollowUp = async () => {
  const hasPageWithoutTitle = schema.value.pages?.some(
    (p) => !p.title || p.title.trim() === ""
  )
  if (hasPageWithoutTitle) {
    pageTitleModalOpened.value = true
    return
  }

  try {
    validator.parse({
      title: title.value,
      fields: schema.value.fields,
      organisation: organisation.value,
      pole: pole.value,
    })
  } catch (error) {
    if (error instanceof ZodError) formErrors.value = z.flattenError(error)
    return
  }
  const saveFunction = existingFollowUpId.value
    ? useApiFetch(
        `/surveys/${surveyId.value}/follow-ups/${existingFollowUpId.value}`
      ).put
    : useApiFetch(`/surveys/${surveyId.value}/follow-ups`).post

  const { response } = await saveFunction(payload).json()
  if (response.value?.ok) {
    const message = existingFollowUpId.value
      ? `Sous-enquête « ${title.value} » modifiée`
      : "Sous-enquête de suivi créée"
    toast.show(message, "success")
    router.push({ name: "/SurveyPage", params: { id: survey.value.id } })
  } else {
    toast.show("Une erreur s'est produite", "error")
  }
}

const payload = computed(() => ({
  organisation: organisation.value,
  pole: pole.value,
  title: title.value,
  actionColor: color.value,
  actionIcon: icon.value,
  actionLabel: actionLabel.value,
  jsonSchema: schema.value,
  campaign: null,
  createdBy: store.loggedUser?.id,
}))

const clearFieldError = (field: string) => {
  if (formErrors.value.fieldErrors[field])
    delete formErrors.value.fieldErrors[field]
}

// Validators

const validator = z
  .object({
    title: z.string().min(1, "Le titre est obligatoire"),
    fields: z
      .array(z.any())
      .min(1, "L'enquête doit contenir au moins un champ"),
    organisation: z.coerce.number("L'organisation est obligatoire"),
    pole: z.number().nullable(),
  })
  .superRefine(({ pole }, ctx) => {
    if (!hasOrgLevelAdmin.value && pole === null) {
      ctx.addIssue({
        code: "custom",
        message: "Le pôle est obligatoire",
        path: ["pole"],
      })
    }
  })
</script>

<template>
  <div class="fr-container mb-10">
    <DsfrBreadcrumb
      :links="[
        { to: '/dashboard', text: 'Dashboard' },
        { to: '/enquetes', text: 'Enquêtes' },
        { to: `/enquete/${survey?.id}`, text: `Enquête « ${survey?.title} »` },
        { text: 'Sous-enquête de suivi' },
      ]"
    />
    <div v-if="isFetching" class="flex justify-center my-20">
      <ProgressSpinner />
    </div>
    <div v-if="survey">
      <div class="flex">
        <div class="border border-gray-300 rounded p-4">
          <p class="mb-0! font-bold">Enquête « {{ survey?.title }} »</p>
        </div>
      </div>
      <div class="flex gap-1 mt-2">
        <div>
          <v-icon scale="1.9" icon="ri-corner-down-right-line"></v-icon>
        </div>
        <div class="bg-gray-50 p-4 border border-gray-300 rounded">
          <h1 class="fr-h4 flex gap-2 items-center mb-2!">
            <div
              class="aspect-square border border-gray-300 w-10 h-10 rounded-full flex justify-center items-center"
              :style="`background: ${color}`"
            >
              <v-icon scale="1.2" :icon="icon"></v-icon>
            </div>
            <span v-if="existingFollowUp"
              >Sous-enquête de suivi « {{ existingFollowUp.title }} »</span
            >
            <span v-else>Nouvelle sous-enquête de suivi</span>
          </h1>
          <div class="pl-4 ml-8">
            <div class="flex gap-8">
              <ColorPicker v-model="color" />
              <IconPicker v-model="icon" />
              <DsfrInputGroup>
                <DsfrInput
                  class="max-w-sm"
                  label="Texte du bouton"
                  label-visible
                  placeholder="Ajouter une étape de suivi.."
                  v-model="actionLabel"
                />
              </DsfrInputGroup>
            </div>

            <div class="flex gap-8">
              <DsfrInputGroup
                :error-message="formErrors?.fieldErrors?.title?.[0]"
              >
                <DsfrInput
                  class="max-w-sm"
                  label="Titre"
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
          </div>
        </div>
      </div>
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
        @click="createOrUpdateFollowUp"
      />
    </div>
  </div>
  <EmptyPageTitleModal v-model="pageTitleModalOpened" />
</template>
