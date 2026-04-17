<script setup lang="ts">
import { computed } from "vue"
import type { ResponseFull, LocalResponse } from "@shared-types/response"
import type { Survey } from "@shared-types/survey"
import ResponseBadge from "./ResponseBadge.vue"
import { formatDate } from "../composables/offlineMapMetadata"

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

  if (field?.ui?.widget === "switch") {
    if (raw === true) return field.ui.activeText ?? "Oui"
    if (raw === false) return field.ui.inactiveText ?? "Non"
    return ""
  }

  const choices = field?.ui?.choices
  if (!choices || !choices.length) return String(raw)

  if (field?.ui?.widget === "select") {
    const match = choices.find((c: any) => c.value === raw)
    return match ? (match as any).text ?? String(raw) : String(raw)
  }

  if (field?.ui?.widget === "radio") {
    const match = choices.find((c: any) => c.value === raw)
    return match ? (match as any).label ?? String(raw) : String(raw)
  }

  if (field?.ui?.widget === "checkboxes" && Array.isArray(raw)) {
    const labels = raw.map((v) => {
      const match = choices.find((c: any) => c.value === v)
      return match ? (match as any).label ?? String(v) : String(v)
    })
    return labels.join(", ") || ""
  }

  return String(raw)
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
      <div v-for="entry in Object.entries(resolvedData)" :key="entry[0]">
        <p class="fr-text--sm font-bold text-stone-500 mb-0!">
          {{ fieldLabel(entry[0]) }}
        </p>
        <p class="font-medium mb-0!" v-if="resolveValue(entry[0], entry[1])">
          {{ resolveValue(entry[0], entry[1]) }}
        </p>
        <p class="italic mb-0! text-stone-500" v-else>Non renseigné</p>
        <hr class="p-1! mt-2!" />
      </div>
    </div>
  </div>
</template>
