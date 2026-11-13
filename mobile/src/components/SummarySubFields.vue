<script setup lang="ts">
import type { SurveyField, VocabularySet, ImageItem } from "@shared-types/survey"
import { resolveFieldValue } from "@shared-utils/survey"
import { validateField } from "@shared-utils/validateField"
import SummaryImage from "./SummaryImage.vue"

const props = defineProps<{
  item: Record<string, unknown>
  subFields: SurveyField[]
  vocabularies?: VocabularySet[]
  showValidation?: boolean
}>()

const resolveValue = (subField: SurveyField, value: unknown): string =>
  resolveFieldValue(subField, value, props.vocabularies)

const getSubFieldError = (subField: SurveyField, value: unknown): string | null => {
  if (!props.showValidation) return null
  return validateField(subField, value ?? null)
}
</script>

<template>
  <div v-for="subField in subFields" :key="subField.id">
    <p class="fr-text--sm text-stone-400 mb-0!">{{ subField.label }}</p>

    <!-- Sous-champ image -->
    <template v-if="subField.ui?.widget === 'image'">
      <SummaryImage
        v-if="Array.isArray(item[subField.id]) && (item[subField.id] as unknown[]).length"
        :images="(item[subField.id] as ImageItem[])"
      />
      <p v-else class="italic mb-0! text-stone-500">Non renseigné</p>
    </template>

    <!-- Sous-champ liste (récursif) -->
    <template v-else-if="subField.ui?.widget === 'array'">
      <p
        v-if="!Array.isArray(item[subField.id]) || !(item[subField.id] as unknown[]).length"
        class="italic mb-0! text-stone-500"
      >
        Non renseigné
      </p>
      <template v-else>
        <p class="font-medium mb-1! text-stone-500">
          {{ (item[subField.id] as unknown[]).length }} entrée(s) :
        </p>
        <div
          v-for="(subItem, subIdx) in (item[subField.id] as Record<string, unknown>[])"
          :key="subIdx"
          class="border border-slate-200 rounded p-2 mb-1 bg-white"
        >
          <SummarySubFields
            :item="subItem"
            :sub-fields="subField.fields ?? []"
            :vocabularies="vocabularies"
            :show-validation="showValidation"
          />
        </div>
      </template>
    </template>

    <!-- Sous-champ objet (récursif) -->
    <template
      v-else-if="
        subField.ui?.widget === 'object' &&
        item[subField.id] != null &&
        typeof item[subField.id] === 'object' &&
        !Array.isArray(item[subField.id])
      "
    >
      <div class="border border-slate-200 rounded p-2 mb-1 bg-white">
        <SummarySubFields
          :item="(item[subField.id] as Record<string, unknown>)"
          :sub-fields="subField.fields ?? []"
          :vocabularies="vocabularies"
          :show-validation="showValidation"
        />
      </div>
    </template>

    <!-- Autres sous-champs -->
    <template v-else>
      <p class="font-medium mb-0!" v-if="resolveValue(subField, item[subField.id])">
        {{ resolveValue(subField, item[subField.id]) }}
      </p>
      <p class="italic mb-0! text-stone-500" v-else>Non renseigné</p>
      <p
        v-if="getSubFieldError(subField, item[subField.id])"
        class="fr-error-text fr-text--sm mt-0! mb-2!"
      >
        {{ getSubFieldError(subField, item[subField.id]) }}
      </p>
    </template>
  </div>
</template>
