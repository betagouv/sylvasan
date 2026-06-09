<script setup lang="ts">
import { computed, ref } from "vue"
import type { ResponseFull, LocalResponse } from "@shared-types/response"
import type { Survey, SurveyField, ImageItem } from "@shared-types/survey"
import ResponseBadge from "./ResponseBadge.vue"
import { formatDate } from "../composables/offlineMapMetadata"
import { resolveFieldValue } from "@shared-utils/survey"
import { validateResponse, validateField } from "@shared-utils/validateField"
import { useVocabulariesStore } from "../stores/vocabularies"
import ImageViewer from "@shared-components/ImageViewer.vue"

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

const imageSrc = (item: ImageItem): string | null => {
  if ("type" in item)
    return (window as any).Capacitor?.convertFileSrc(item.path) ?? null
  if ("file" in item) return `data:image/jpeg;base64,${item.file}`
  if (item.thumbnail) return `data:image/jpeg;base64,${item.thumbnail}`
  return null
}

// On montre la validation seulement lors que la réponse n'est pas sauvegardé dans le backend
const validationErrors = computed(() =>
  response ? {} : validateResponse(survey.jsonSchema.fields, resolvedData.value)
)

const getSubFieldError = (
  subField: SurveyField,
  value: unknown
): string | null => {
  if (response) return null
  return validateField(subField, value ?? null)
}

const viewerOpen = ref(false)
const viewerImages = ref<ImageItem[]>([])
const viewerIndex = ref(0)

const openViewer = (images: ImageItem[], index: number) => {
  viewerImages.value = images
  viewerIndex.value = index
  viewerOpen.value = true
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
      <div v-for="field in survey.jsonSchema.fields" :key="field.id">
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
              <div class="flex gap-4">
                <p class="fr-text--sm text-stone-400 mb-0!">
                  {{ subField.label }}
                </p>
                <p
                  class="font-medium mb-0!"
                  v-if="
                    resolveFieldValue(
                      subField,
                      item[subField.id],
                      vocabularySets
                    )
                  "
                >
                  {{
                    resolveFieldValue(
                      subField,
                      item[subField.id],
                      vocabularySets
                    )
                  }}
                </p>
                <p class="italic mb-0! text-stone-500" v-else>Non renseigné</p>
              </div>
              <p
                v-if="getSubFieldError(subField, item[subField.id])"
                class="fr-error-text fr-text--sm mt-0! mb-2!"
              >
                {{ getSubFieldError(subField, item[subField.id]) }}
              </p>
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
          <div v-else class="grid grid-cols-4 gap-2 my-2">
            <div
              v-for="(img, idx) in (resolvedData[field.id] as ImageItem[])"
              :key="idx"
              class="aspect-square rounded overflow-hidden border border-slate-200 cursor-pointer"
              @click="openViewer(resolvedData[field.id] as ImageItem[], idx)"
            >
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
            </div>
          </div>
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

  <ImageViewer
    :images="viewerImages"
    :startIndex="viewerIndex"
    :opened="viewerOpen"
    @close="viewerOpen = false"
  />
</template>
