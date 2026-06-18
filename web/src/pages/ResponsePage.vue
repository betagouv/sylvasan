<route lang="json">
{
  "path": "/response/:id",
  "meta": {
    "authenticationRequired": true,
    "title": "Réponse"
  }
}
</route>

<script setup lang="ts">
import { ref, computed } from "vue"
import { useRoute } from "vue-router"
import { useApiFetch } from "../utils/data-fetching.ts"
import type { SurveyField, ImageItem } from "@shared-types/survey"
import SurveyRenderer from "@shared-components/SurveyRenderer.vue"
import ImageViewer from "@shared-components/ImageViewer.vue"
import { resolveFieldValue } from "@shared-utils/survey"
import { storeToRefs } from "pinia"
import { useRootStore } from "../stores/root.ts"
import MapField from "../components/MapField.vue"
import ProgressSpinner from "../components/ProgressSpinner.vue"

const route = useRoute()
const { vocabularies } = storeToRefs(useRootStore())

const { data: response, isFetching } = useApiFetch(
  `/responses/${route.params.id}`
).json()

const fieldLabel = (fieldId: string): string =>
  response.value?.survey.jsonSchema.fields.find(
    (f: SurveyField) => f.id === fieldId
  )?.label ?? fieldId

const resolveValue = (fieldId: string, raw: unknown): string => {
  const field = response.value?.survey.jsonSchema.fields.find(
    (f: SurveyField) => f.id === fieldId
  )
  return resolveFieldValue(field, raw, vocabularies.value)
}

const isArrayField = (fieldId: string): boolean =>
  response.value?.survey.jsonSchema.fields.find(
    (f: SurveyField) => f.id === fieldId
  )?.ui?.widget === "array"

const isImageField = (fieldId: string): boolean =>
  response.value?.survey.jsonSchema.fields.find(
    (f: SurveyField) => f.id === fieldId
  )?.ui?.widget === "image"

const getSubFields = (fieldId: string): SurveyField[] =>
  response.value?.survey.jsonSchema.fields.find(
    (f: SurveyField) => f.id === fieldId
  )?.fields ?? []

const imageSrc = (item: ImageItem): string | null => {
  if ("type" in item) return null
  if ("file" in item) return `data:image/jpeg;base64,${item.file}`
  if (item.thumbnail) return `data:image/jpeg;base64,${item.thumbnail}`
  return null
}

const viewerOpen = ref(false)
const viewerImages = ref<ImageItem[]>([])
const viewerIndex = ref(0)

const openViewer = (images: ImageItem[], index: number) => {
  viewerImages.value = images
  viewerIndex.value = index
  viewerOpen.value = true
}

const respondantName = computed(() => {
  const respondant = response.value.respondant
  if (!respondant) return "—"
  return `${respondant.firstName} ${respondant.lastName || ""}`
})
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/dashboard', text: 'Dashboard' },
        { to: '/reponses', text: 'Réponses' },
        { text: `Réponse « ${response?.survey?.title || ''} »` },
      ]"
    />
    <div v-if="isFetching" class="flex justify-center my-20">
      <ProgressSpinner />
    </div>
    <div v-else-if="response">
      <h1 class="fr-h4">Réponse à l'enquête « {{ response.survey.title }} »</h1>
      <div class="mb-6">
        <p class="font-medium fr-badge">
          <v-icon name="ri-user-line" scale="0.8" class="mr-2" />
          {{ respondantName }}
        </p>
      </div>

      <div class="grid grid-cols-12 gap-4">
        <div class="col-span-12 sm:col-span-6 md:col-span-7 lg:col-span-8">
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
                  <div
                    v-for="subField in getSubFields(entry[0])"
                    :key="subField.id"
                  >
                    <p class="fr-text--sm text-stone-400 mb-0!">
                      {{ subField.label }}
                    </p>
                    <p
                      class="font-medium mb-0!"
                      v-if="
                        resolveFieldValue(
                          subField,
                          item[subField.id],
                          vocabularies
                        )
                      "
                    >
                      {{
                        resolveFieldValue(
                          subField,
                          item[subField.id],
                          vocabularies
                        )
                      }}
                    </p>
                    <p class="italic text-stone-500 mb-0!" v-else>
                      Non renseigné
                    </p>
                  </div>
                </div>
              </div>
            </template>

            <!-- Champ images -->
            <template
              v-else-if="isImageField(entry[0]) && Array.isArray(entry[1])"
            >
              <p v-if="!entry[1].length" class="italic text-stone-500 mb-0!">
                Non renseigné
              </p>
              <div v-else class="grid grid-cols-7 gap-2 my-2">
                <div
                  v-for="(img, idx) in (entry[1] as ImageItem[])"
                  :key="idx"
                  class="group aspect-square rounded overflow-hidden border border-slate-200 cursor-pointer relative"
                  @click="openViewer(entry[1] as ImageItem[], idx)"
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
                    <v-icon
                      name="ri-image-line"
                      scale="2"
                      class="text-slate-400"
                    />
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
              <p
                class="font-medium mb-0!"
                v-if="resolveValue(entry[0], entry[1])"
              >
                {{ resolveValue(entry[0], entry[1]) }}
              </p>
              <p class="italic text-stone-500 mb-0!" v-else>Non renseigné</p>
            </template>

            <hr class="mt-2! mb-0!" />
          </div>
        </div>
        <!-- Preview -->
        <div class="col-span-12 sm:col-span-6 md:col-span-5 lg:col-span-4 mb-4">
          <div
            v-if="response.survey.jsonSchema"
            class="border rounded border-slate-300 p-4"
          >
            <SurveyRenderer
              :schema="response.survey.jsonSchema"
              :allowSubmit="false"
              :readonly="true"
              :prefillData="response.data"
              :vocabularies="vocabularies"
              :mapComponent="MapField"
            />
          </div>
        </div>
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
