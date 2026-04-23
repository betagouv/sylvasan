<script setup lang="ts">
import { computed } from "vue"
import type { ResponseFull, LocalResponse } from "@shared-types/response"
import type { Survey, SurveyField } from "@shared-types/survey"
import ResponseBadge from "./ResponseBadge.vue"
import { formatDate } from "../composables/offlineMapMetadata"
import { resolveFieldValue } from "@shared-utils/survey"

const { response, data, survey } = defineProps<{
  response?: ResponseFull | LocalResponse
  data?: Record<string, unknown>
  survey: Survey
}>()

const isRemote = (res: LocalResponse | ResponseFull): res is ResponseFull =>
  (<ResponseFull>res).id !== undefined

const resolvedData = computed(() => response?.data ?? data ?? {})

const fieldLabel = (fieldId: string): string =>
  survey.jsonSchema.fields.find((f) => f.id === fieldId)?.label ?? fieldId

const resolveValue = (fieldId: string, raw: unknown): string => {
  const field = survey.jsonSchema.fields.find((f) => f.id === fieldId)
  return resolveFieldValue(field, raw)
}

const isArrayField = (fieldId: string): boolean =>
  survey.jsonSchema.fields.find((f) => f.id === fieldId)?.ui?.widget === "array"

const getSubFields = (fieldId: string): SurveyField[] =>
  survey.jsonSchema.fields.find((f) => f.id === fieldId)?.fields ?? []
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
      <div v-for="entry in Object.entries(resolvedData)" :key="entry[0]">
        <p class="fr-text--sm font-bold text-stone-500 mb-0!">
          {{ fieldLabel(entry[0]) }}
        </p>

        <!-- Array field -->
        <template v-if="isArrayField(entry[0]) && Array.isArray(entry[1])">
          <p v-if="!entry[1].length" class="italic mb-0! text-stone-500">
            Non renseigné
          </p>
          <p v-else class="font-medium mb-2! text-stone-500">
            {{ entry[1].length }} entrée(s) :
          </p>
          <div
            v-for="(item, idx) in (entry[1] as Record<string, unknown>[])"
            :key="`${entry[0]}-${idx}`"
            class="border border-slate-200 rounded p-3 mb-2 bg-slate-50"
          >
            <div
              v-for="subField in getSubFields(entry[0])"
              :key="subField.id"
              class="flex gap-4"
            >
              <p class="fr-text--sm text-stone-400 mb-0!">
                {{ subField.label }}
              </p>
              <p
                class="font-medium mb-0!"
                v-if="resolveFieldValue(subField, item[subField.id])"
              >
                {{ resolveFieldValue(subField, item[subField.id]) }}
              </p>
              <p class="italic mb-0! text-stone-500" v-else>Non renseigné</p>
            </div>
          </div>
        </template>

        <!-- All other fields -->
        <template v-else>
          <p class="font-medium mb-0!" v-if="resolveValue(entry[0], entry[1])">
            {{ resolveValue(entry[0], entry[1]) }}
          </p>
          <p class="italic mb-0! text-stone-500" v-else>Non renseigné</p>
        </template>

        <hr class="p-1! mt-2!" />
      </div>
    </div>
  </div>
</template>
