<script setup lang="ts">
import { computed, watch } from "vue"
import type { ResponseFull } from "@shared-types/response"
import { flattenFields, resolveFieldValue } from "@shared-utils/survey"
import type { SurveyField, ImageItem } from "@shared-types/survey"
import { storeToRefs } from "pinia"
import { useRootStore } from "../../stores/root.ts"
import SummaryImage from "./SummaryImage.vue"
import ResponseSubFields from "./ResponseSubFields.vue"

const rootStore = useRootStore()
const { response } = defineProps<{
  response: ResponseFull
}>()

const jsonSchema = computed(
  () => response.survey?.jsonSchema ?? response.surveyFollowUp?.jsonSchema
)

const surveyCodes = computed(() => {
  const allFields = flattenFields(jsonSchema.value?.fields ?? [])
  return [
    ...new Set(
      allFields.filter((f) => f.vocabulary).map((f) => f.vocabulary as string)
    ),
  ]
})

watch(surveyCodes, async () => {
  await Promise.allSettled(
    surveyCodes.value.map((code) => rootStore.fetchVocabularyDetail(code))
  )
})

const { vocabularyDetails } = storeToRefs(rootStore)

const emit = defineEmits(["open-viewer"])

const surveyVocabularies = computed(() =>
  surveyCodes.value.map((code) => vocabularyDetails.value[code]).filter(Boolean)
)
const fieldLabel = (fieldId: string): string =>
  jsonSchema.value?.fields.find((f: SurveyField) => f.id === fieldId)
    ?.label ?? fieldId

const resolveValue = (fieldId: string, raw: unknown): string => {
  const field = jsonSchema.value?.fields.find(
    (f: SurveyField) => f.id === fieldId
  )
  return resolveFieldValue(field, raw, surveyVocabularies.value)
}

const isArrayField = (fieldId: string): boolean =>
  jsonSchema.value?.fields.find((f: SurveyField) => f.id === fieldId)
    ?.ui?.widget === "array"

const isObjectField = (fieldId: string): boolean =>
  jsonSchema.value?.fields.find((f: SurveyField) => f.id === fieldId)
    ?.ui?.widget === "object"

const isImageField = (fieldId: string): boolean =>
  jsonSchema.value?.fields.find((f: SurveyField) => f.id === fieldId)
    ?.ui?.widget === "image"

const getSubFields = (fieldId: string): SurveyField[] =>
  jsonSchema.value?.fields.find((f: SurveyField) => f.id === fieldId)
    ?.fields ?? []

const getObjectValue = (fieldId: string): Record<string, unknown> =>
  (response.data[fieldId] as Record<string, unknown>) ?? {}

</script>

<template>
  <div>
    <div v-for="entry in Object.entries(response.data)" :key="entry[0]">
      <p class="fr-text--sm font-bold text-stone-500 mb-0!">
        {{ fieldLabel(entry[0]) }}
      </p>

      <!-- Array field -->
      <template v-if="isArrayField(entry[0]) && Array.isArray(entry[1])">
        <p v-if="!entry[1].length" class="italic text-stone-500 mb-0!">
          Non renseigné
        </p>
        <p v-else class="font-medium mb-2! text-stone-500">
          {{ entry[1].length }} entrée(s) :
        </p>
        <div class="grid grid-cols-12 gap-4">
          <div
            v-for="(item, idx) in (entry[1] as Record<string, unknown>[])"
            :key="idx"
            class="border border-slate-200 rounded p-3 bg-slate-50 col-span-12 md:col-span-6 lg:col-span-4"
          >
            <ResponseSubFields
              :item="item"
              :sub-fields="getSubFields(entry[0])"
              :vocabularies="surveyVocabularies"
              @open-viewer="(imgs, idx) => emit('open-viewer', imgs, idx)"
            />
          </div>
        </div>
      </template>

      <!-- Champ objet (groupe de champs) -->
      <template
        v-else-if="
          isObjectField(entry[0]) &&
          entry[1] !== null &&
          typeof entry[1] === 'object'
        "
      >
        <div class="border border-slate-200 rounded p-3 bg-slate-50">
          <ResponseSubFields
            :item="getObjectValue(entry[0])"
            :sub-fields="getSubFields(entry[0])"
            :vocabularies="surveyVocabularies"
            @open-viewer="(imgs, idx) => emit('open-viewer', imgs, idx)"
          />
        </div>
      </template>

      <!-- Champ images -->
      <template v-else-if="isImageField(entry[0]) && Array.isArray(entry[1])">
        <p v-if="!entry[1].length" class="italic text-stone-500 mb-0!">
          Non renseigné
        </p>
        <SummaryImage
          v-else
          :images="(entry[1] as ImageItem[])"
          @open-viewer="(imgs, idx) => emit('open-viewer', imgs, idx)"
        />
      </template>

      <!-- All other fields -->
      <template v-else>
        <p class="font-medium mb-0!" v-if="resolveValue(entry[0], entry[1])">
          {{ resolveValue(entry[0], entry[1]) }}
        </p>
        <p class="italic text-stone-500 mb-0!" v-else>Non renseigné</p>
      </template>

      <hr class="mt-2! mb-0!" />
    </div>
  </div>
</template>
