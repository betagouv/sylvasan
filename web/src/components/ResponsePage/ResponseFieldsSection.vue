<script setup lang="ts">
import { computed, watch } from "vue"
import type { ResponseFull } from "@shared-types/response"
import { resolveFieldValue } from "@shared-utils/survey"
import type { SurveyField, ImageItem } from "@shared-types/survey"
import { storeToRefs } from "pinia"
import { useRootStore } from "../../stores/root.ts"

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

const imageSrc = (item: ImageItem): string | null => {
  if ("type" in item) return null
  if ("file" in item) return `data:image/jpeg;base64,${item.file}`
  if (item.thumbnail) return `data:image/jpeg;base64,${item.thumbnail}`
  return null
}
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
              <p
                class="font-medium mb-0!"
                v-if="resolveSubFieldValue(subField, item[subField.id])"
              >
                {{ resolveSubFieldValue(subField, item[subField.id]) }}
              </p>
              <p class="italic text-stone-500 mb-0!" v-else>Non renseigné</p>
            </div>
          </div>
        </div>
      </template>

      <!-- Champ images -->
      <template v-else-if="isImageField(entry[0]) && Array.isArray(entry[1])">
        <p v-if="!entry[1].length" class="italic text-stone-500 mb-0!">
          Non renseigné
        </p>
        <div v-else class="grid grid-cols-7 gap-2 my-2">
          <div
            v-for="(img, idx) in (entry[1] as ImageItem[])"
            :key="idx"
            class="group aspect-square rounded overflow-hidden border border-slate-200 cursor-pointer relative"
            @click="emit('open-viewer', entry[1] as ImageItem[], idx)"
          >
            <!-- @click="openViewer(entry[1] as ImageItem[], idx)" -->
            <img
              v-if="imageSrc(img)"
              :src="imageSrc(img)!"
              class="w-full h-full object-cover"
              alt=""
            />
            <div
              v-else
              class="w-full h-full bg-slate-100 flex items-center justify-center"
            >
              <v-icon name="ri-image-line" scale="2" class="text-slate-400" />
            </div>
            <div
              class="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center"
            >
              <v-icon
                name="ri-search-eye-line"
                color="white"
                scale="1.5"
                class="text-white opacity-0 group-hover:opacity-100 transition-opacity"
              />
            </div>
          </div>
        </div>
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
