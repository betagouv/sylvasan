<script setup lang="ts">
import type { ResponseFull, LocalResponse } from "@shared-types/response"
import type { Survey } from "@shared-types/survey"
import ResponseBadge from "./ResponseBadge.vue"

const { response, survey } = defineProps<{
  response: ResponseFull | LocalResponse
  survey: Survey
}>()

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
      <ResponseBadge :response="response" />
      <h1 class="fr-h3">{{ survey.title }}</h1>
    </div>

    <div class="p-4">
      <div v-for="entry in Object.entries(response.data)" :key="entry[0]">
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
