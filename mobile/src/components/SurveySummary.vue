<script setup lang="ts">
import { computed } from "vue"
import type { ResponseFull, LocalResponse } from "@shared-types/response"
import type { Survey, SurveyField, ImageItem } from "@shared-types/survey"
import ResponseBadge from "./ResponseBadge.vue"
import SummaryImage from "./SummaryImage.vue"
import SummarySubFields from "./SummarySubFields.vue"
import { formatDate } from "../composables/offlineMapMetadata"
import { resolveFieldValue, evaluateCondition } from "@shared-utils/survey"
import { validateResponse, validateField } from "@shared-utils/validateField"
import { useVocabulariesStore } from "../stores/vocabularies"
import { DsfrButton } from "@gouvminint/vue-dsfr"

const { response, data, survey } = defineProps<{
  response?: ResponseFull | LocalResponse
  data?: Record<string, unknown>
  survey: Survey
}>()

const emit = defineEmits<{ goToPage: [page: number] }>()

const { vocabularySets } = useVocabulariesStore()

const isRemote = (res: LocalResponse | ResponseFull): res is ResponseFull =>
  (<ResponseFull>res).id !== undefined

// On montre la validation seulement quand la réponse n'est pas encore sauvegardée dans le backend
const showValidation = computed(() => !response)

const resolvedData = computed(() => response?.data ?? data ?? {})

const resolveValue = (fieldId: string, raw: unknown): string => {
  const field = survey.jsonSchema.fields.find((f) => f.id === fieldId)
  return resolveFieldValue(field, raw, vocabularySets)
}

const isArrayField = (fieldId: string): boolean =>
  survey.jsonSchema.fields.find((f) => f.id === fieldId)?.ui?.widget === "array"

const isObjectField = (fieldId: string): boolean =>
  survey.jsonSchema.fields.find((f) => f.id === fieldId)?.ui?.widget === "object"

const isImageField = (fieldId: string): boolean =>
  survey.jsonSchema.fields.find((f) => f.id === fieldId)?.ui?.widget === "image"

const getSubFields = (fieldId: string): SurveyField[] =>
  survey.jsonSchema.fields.find((f) => f.id === fieldId)?.fields ?? []

const getObjectValue = (fieldId: string): Record<string, unknown> =>
  (resolvedData.value[fieldId] as Record<string, unknown>) ?? {}

const visibleFields = computed(() =>
  survey.jsonSchema.fields.filter(
    (f) => !f.condition || evaluateCondition(f.condition, resolvedData.value)
  )
)

const visibleFieldIds = computed(
  () => new Set(visibleFields.value.map((f) => f.id))
)

const validationErrors = computed(() =>
  showValidation.value
    ? validateResponse(
        survey.jsonSchema.fields,
        resolvedData.value,
        visibleFieldIds.value
      )
    : {}
)

const getSubFieldError = (
  subField: SurveyField,
  value: unknown
): string | null => {
  if (!showValidation.value) return null
  return validateField(subField, value ?? null)
}

// Liste de sections — une par page si le schéma a des pages, sinon une seule section plate.
// Chaque section avec `pageNumber` est une vraie page (en-tête affiché).
const sections = computed(() => {
  const schema = survey.jsonSchema
  if (!schema.pages || schema.pages.length <= 1) {
    return [
      {
        pageNumber: null as number | null,
        title: null as string | null,
        fields: visibleFields.value,
        errorCount: 0,
      },
    ]
  }
  return schema.pages.map((page, index) => {
    const fields = page.fields
      .map((fid) => schema.fields.find((f) => f.id === fid))
      .filter((f): f is SurveyField => f !== undefined)
      .filter((f) => visibleFieldIds.value.has(f.id))
    const errorCount = fields.filter((f) => validationErrors.value[f.id]).length
    return {
      pageNumber: index + 1,
      title: page.title ?? `Page ${index + 1}`,
      fields,
      errorCount,
    }
  })
})
</script>

<template>
  <div>
    <div class="p-4 bg-blue-france-975">
      <ResponseBadge v-if="response" :response="response" />
      <h1 class="fr-h3 mb-3!">{{ survey.title }}</h1>
      <p
        v-if="response && isRemote(response) && response.creationDate"
        class="mb-0! fr-text--sm font-bold text-stone-600"
      >
        <v-icon scale="0.8" icon="ri-calendar-line" class="mr-1"></v-icon
        >Envoyée le
        {{ formatDate(response.creationDate) }}
      </p>
    </div>

    <div>
      <template v-for="(section, si) in sections" :key="`${si}-sections`">
        <!-- En-tête de page (seulement quand il y a plusieurs pages) -->
        <div
          v-if="section.pageNumber !== null"
          class="flex items-center justify-between gap-2 border-b-[8px] border-slate-200 px-4 py-2"
        >
          <h2 class="fr-h6 mb-0!">{{ si + 1 }}. {{ section.title }}</h2>
          <div
            v-if="showValidation && section.errorCount > 0"
            class="flex items-center gap-2 shrink-0"
          >
            <span class="fr-error-text fr-text--sm">
              {{ section.errorCount }}
              erreur{{ section.errorCount > 1 ? "s" : "" }}
            </span>
            <DsfrButton
              size="small"
              tertiary
              @click="emit('goToPage', section.pageNumber!)"
              label="Modifier"
            />
          </div>
        </div>

        <div class="bg-slate-200 pb-4">
          <div class="mx-2 bg-white px-4 py-2 rounded">
            <!-- Champs de la section -->
            <div v-for="field in section.fields" :key="field.id">
              <p class="fr-text--sm font-bold text-stone-500 mb-0!">
                {{ field.label }}
              </p>

              <!-- Array field -->
              <template
                v-if="
                  isArrayField(field.id) &&
                  Array.isArray(resolvedData[field.id])
                "
              >
                <p
                  v-if="!(resolvedData[field.id] as unknown[]).length"
                  class="italic mb-0! text-stone-500"
                >
                  Non renseigné
                </p>
                <p v-else class="font-medium mb-2! text-stone-500">
                  {{ (resolvedData[field.id] as unknown[]).length }} entrée(s) :
                </p>
                <div
                  v-for="(item, idx) in (resolvedData[field.id] as Record<string, unknown>[])"
                  :key="`${field.id}-${idx}`"
                  class="border border-slate-200 rounded p-3 mb-2 bg-slate-50"
                >
                  <SummarySubFields
                    :item="item"
                    :sub-fields="getSubFields(field.id)"
                    :vocabularies="vocabularySets"
                    :show-validation="showValidation"
                  />
                </div>
              </template>

              <!-- Champ objet (groupe de champs) -->
              <template
                v-else-if="
                  isObjectField(field.id) &&
                  resolvedData[field.id] != null &&
                  typeof resolvedData[field.id] === 'object' &&
                  !Array.isArray(resolvedData[field.id])
                "
              >
                <div class="border border-slate-200 rounded p-3 mb-2 bg-slate-50">
                  <SummarySubFields
                    :item="getObjectValue(field.id)"
                    :sub-fields="getSubFields(field.id)"
                    :vocabularies="vocabularySets"
                    :show-validation="showValidation"
                  />
                </div>
              </template>

              <!-- Champ images -->
              <template
                v-else-if="
                  isImageField(field.id) &&
                  Array.isArray(resolvedData[field.id])
                "
              >
                <p
                  v-if="!(resolvedData[field.id] as unknown[]).length"
                  class="italic mb-0! text-stone-500"
                >
                  Non renseigné
                </p>
                <SummaryImage
                  v-else
                  :images="(resolvedData[field.id] as ImageItem[])"
                />
              </template>

              <!-- Tous les autres champs -->
              <template v-else>
                <p
                  class="font-medium mb-0!"
                  v-if="resolveValue(field.id, resolvedData[field.id])"
                >
                  {{ resolveValue(field.id, resolvedData[field.id]) }}
                </p>
                <p class="italic mb-0! text-stone-500" v-else>Non renseigné</p>
              </template>

              <p
                v-if="validationErrors[field.id]"
                class="fr-error-text fr-text--sm mt-1! mb-0!"
              >
                {{ validationErrors[field.id] }}
              </p>

              <hr class="p-1! mt-2!" />
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>
