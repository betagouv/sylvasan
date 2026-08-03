<script setup lang="ts">
import { computed } from "vue"
import type { ResponseFull, LocalResponse } from "@shared-types/response"
import type { Survey, SurveyField, ImageItem } from "@shared-types/survey"
import ResponseBadge from "./ResponseBadge.vue"
import SummaryImage from "./SummaryImage.vue"
import { formatDate } from "../composables/offlineMapMetadata"
import { resolveFieldValue, evaluateCondition } from "@shared-utils/survey"
import { validateResponse, validateField } from "@shared-utils/validateField"
import { useVocabulariesStore } from "../stores/vocabularies"

const { response, data, survey } = defineProps<{
  response?: ResponseFull | LocalResponse
  data?: Record<string, unknown>
  survey: Survey
}>()

const { vocabularySets } = useVocabulariesStore()

const isRemote = (res: LocalResponse | ResponseFull): res is ResponseFull =>
  (<ResponseFull>res).id !== undefined

const resolvedData = computed(() => response?.data ?? data ?? {})

const resolveValue = (fieldId: string, raw: unknown): string => {
  const field = survey.jsonSchema.fields.find((f) => f.id === fieldId)
  return resolveFieldValue(field, raw, vocabularySets)
}

const isArrayField = (fieldId: string): boolean =>
  survey.jsonSchema.fields.find((f) => f.id === fieldId)?.ui?.widget === "array"

const isImageField = (fieldId: string): boolean =>
  survey.jsonSchema.fields.find((f) => f.id === fieldId)?.ui?.widget === "image"

const getSubFields = (fieldId: string): SurveyField[] =>
  survey.jsonSchema.fields.find((f) => f.id === fieldId)?.fields ?? []

const visibleFields = computed(() =>
  survey.jsonSchema.fields.filter(
    (f) => !f.condition || evaluateCondition(f.condition, resolvedData.value)
  )
)

const visibleFieldIds = computed(
  () => new Set(visibleFields.value.map((f) => f.id))
)

// On montre la validation seulement lors que la réponse n'est pas sauvegardé dans le backend
const validationErrors = computed(() =>
  response
    ? {}
    : validateResponse(
        survey.jsonSchema.fields,
        resolvedData.value,
        visibleFieldIds.value
      )
)

const getSubFieldError = (
  subField: SurveyField,
  value: unknown
): string | null => {
  if (response) return null
  return validateField(subField, value ?? null)
}

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

    <div class="p-4">
      <div v-for="field in visibleFields" :key="field.id">
        <p class="fr-text--sm font-bold text-stone-500 mb-0!">
          {{ field.label }}
        </p>

        <!-- Array field -->
        <template
          v-if="isArrayField(field.id) && Array.isArray(resolvedData[field.id])"
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
            <div v-for="subField in getSubFields(field.id)" :key="subField.id">
              <p class="fr-text--sm text-stone-400 mb-0!">
                {{ subField.label }}
              </p>
              <!-- Image sub-field -->
              <template v-if="subField.ui?.widget === 'image'">
                <SummaryImage
                  v-if="Array.isArray(item[subField.id]) && (item[subField.id] as unknown[]).length"
                  :images="(item[subField.id] as ImageItem[])"
                />
                <p v-else class="italic mb-0! text-stone-500">Non renseigné</p>
              </template>
              <!-- Other sub-fields -->
              <template v-else>
                <div class="flex gap-4">
                  <p
                    class="font-medium mb-0!"
                    v-if="resolveFieldValue(subField, item[subField.id], vocabularySets)"
                  >
                    {{ resolveFieldValue(subField, item[subField.id], vocabularySets) }}
                  </p>
                  <p class="italic mb-0! text-stone-500" v-else>Non renseigné</p>
                </div>
                <p
                  v-if="getSubFieldError(subField, item[subField.id])"
                  class="fr-error-text fr-text--sm mt-0! mb-2!"
                >
                  {{ getSubFieldError(subField, item[subField.id]) }}
                </p>
              </template>
            </div>
          </div>
        </template>

        <!-- Champ images -->
        <template
          v-else-if="
            isImageField(field.id) && Array.isArray(resolvedData[field.id])
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
        <!-- All other fields -->
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
