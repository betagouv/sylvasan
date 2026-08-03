<script setup lang="ts">
import { computed, watch } from "vue"
import type { ResponseFull } from "@shared-types/response"
import { resolveFieldValue } from "@shared-utils/survey"
import type { SurveyField, ImageItem } from "@shared-types/survey"
import { storeToRefs } from "pinia"
import { useRootStore } from "../../stores/root.ts"
import SummaryImage from "./SummaryImage.vue"

const rootStore = useRootStore()
const { response } = defineProps<{
  response: ResponseFull
}>()

const jsonSchema = computed(
  () => response.survey?.jsonSchema ?? response.surveyFollowUp?.jsonSchema
)

const surveyCodes = computed(() => {
  const schema = jsonSchema.value
  const allFields: SurveyField[] = [
    ...(schema?.fields ?? []),
    ...(schema?.fields ?? []).flatMap((f: SurveyField) => f.fields ?? []),
  ]
  const codes = [
    ...new Set(
      allFields.filter((f) => f.vocabulary).map((f) => f.vocabulary as string)
    ),
  ]
  return codes
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

const resolveSubFieldValue = (subField: SurveyField, raw: unknown): string =>
  resolveFieldValue(subField, raw, surveyVocabularies.value)

const isArrayField = (fieldId: string): boolean =>
  jsonSchema.value?.fields.find((f: SurveyField) => f.id === fieldId)
    ?.ui?.widget === "array"

const isImageField = (fieldId: string): boolean =>
  jsonSchema.value?.fields.find((f: SurveyField) => f.id === fieldId)
    ?.ui?.widget === "image"

const getSubFields = (fieldId: string): SurveyField[] =>
  jsonSchema.value?.fields.find((f: SurveyField) => f.id === fieldId)
    ?.fields ?? []

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
            <div v-for="subField in getSubFields(entry[0])" :key="subField.id">
              <p class="fr-text--sm text-stone-400 mb-0!">
                {{ subField.label }}
              </p>
              <!-- Image sub-field -->
              <template v-if="subField.ui?.widget === 'image'">
                <SummaryImage
                  v-if="Array.isArray(item[subField.id]) && (item[subField.id] as unknown[]).length"
                  :images="(item[subField.id] as ImageItem[])"
                  @open-viewer="(imgs, idx) => emit('open-viewer', imgs, idx)"
                />
                <p v-else class="italic text-stone-500 mb-0!">Non renseigné</p>
              </template>
              <!-- Other sub-fields -->
              <template v-else>
                <p
                  class="font-medium mb-0!"
                  v-if="resolveSubFieldValue(subField, item[subField.id])"
                >
                  {{ resolveSubFieldValue(subField, item[subField.id]) }}
                </p>
                <p class="italic text-stone-500 mb-0!" v-else>Non renseigné</p>
              </template>
            </div>
          </div>
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
