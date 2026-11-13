<script setup lang="ts">
import type { SurveyField, VocabularySet, ImageItem } from "@shared-types/survey"
import { resolveFieldValue } from "@shared-utils/survey"
import SummaryImage from "./SummaryImage.vue"

const props = defineProps<{
  item: Record<string, unknown>
  subFields: SurveyField[]
  vocabularies?: VocabularySet[]
}>()

const emit = defineEmits<{
  "open-viewer": [images: ImageItem[], index: number]
}>()

const resolveValue = (subField: SurveyField, value: unknown): string =>
  resolveFieldValue(subField, value, props.vocabularies)
</script>

<template>
  <div v-for="subField in subFields" :key="subField.id">
    <p class="fr-text--sm text-stone-400 mb-0!">{{ subField.label }}</p>

    <!-- Sous-champ image -->
    <template v-if="subField.ui?.widget === 'image'">
      <SummaryImage
        v-if="Array.isArray(item[subField.id]) && (item[subField.id] as unknown[]).length"
        :images="(item[subField.id] as ImageItem[])"
        @open-viewer="(imgs, idx) => emit('open-viewer', imgs, idx)"
      />
      <p v-else class="italic text-stone-500 mb-0!">Non renseigné</p>
    </template>

    <!-- Sous-champ liste (récursif) -->
    <template v-else-if="subField.ui?.widget === 'array'">
      <p
        v-if="!Array.isArray(item[subField.id]) || !(item[subField.id] as unknown[]).length"
        class="italic text-stone-500 mb-0!"
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
          <ResponseSubFields
            :item="subItem"
            :sub-fields="subField.fields ?? []"
            :vocabularies="vocabularies"
            @open-viewer="(imgs, idx) => emit('open-viewer', imgs, idx)"
          />
        </div>
      </template>
    </template>

    <!-- Sous-champ objet (récursif) -->
    <template
      v-else-if="
        subField.ui?.widget === 'object' &&
        item[subField.id] !== null &&
        typeof item[subField.id] === 'object'
      "
    >
      <div class="border border-slate-200 rounded p-2 mb-1 bg-white">
        <ResponseSubFields
          :item="(item[subField.id] as Record<string, unknown>)"
          :sub-fields="subField.fields ?? []"
          :vocabularies="vocabularies"
          @open-viewer="(imgs, idx) => emit('open-viewer', imgs, idx)"
        />
      </div>
    </template>

    <!-- Autres sous-champs -->
    <template v-else>
      <p class="font-medium mb-0!" v-if="resolveValue(subField, item[subField.id])">
        {{ resolveValue(subField, item[subField.id]) }}
      </p>
      <p class="italic text-stone-500 mb-0!" v-else>Non renseigné</p>
    </template>
  </div>
</template>
