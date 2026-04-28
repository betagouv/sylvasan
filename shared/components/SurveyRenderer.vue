<script setup lang="ts">
import { reactive, ref, computed, watch } from "vue"
import type { SurveySchema, SurveyField, VocabularySet } from "../types/survey"
import FieldRenderer from "./FieldRenderer.vue"
import { getEmptyValue } from "../utils/survey"

const props = withDefaults(
  defineProps<{
    schema: SurveySchema
    allowSubmit?: boolean
    prefillData?: Record<string, unknown>
    readonly?: boolean
    vocabularies?: VocabularySet[]
  }>(),
  { vocabularies: () => [] }
)

const emit = defineEmits<{
  done: [data: Record<string, unknown>]
  change: [data: Record<string, unknown>]
}>()

const hasPages = computed(
  () => props.schema.pages && props.schema.pages.length > 1
)

const currentStep = ref(1)

const stepTitles = computed(
  () => props.schema.pages?.map((p) => p.title ?? `Page ${p.id}`) ?? []
)

const currentPageFields = computed(() => {
  if (!hasPages.value) return props.schema.fields
  const page = props.schema.pages?.[currentStep.value - 1]
  if (!page) return []
  return page.fields
    .map((fid) => props.schema.fields.find((f) => f.id === fid))
    .filter((f): f is SurveyField => f !== undefined)
})

const isLastStep = computed(
  () => !hasPages.value || currentStep.value === stepTitles.value.length
)

const goNext = () => {
  if (currentStep.value < stepTitles.value.length) currentStep.value++
}

const goPrev = () => {
  if (currentStep.value > 1) currentStep.value--
}
const formData = reactive<Record<string, string>>(
  Object.fromEntries(
    props.schema.fields.map((field: SurveyField) => {
      const hasPrefillValue = props.prefillData?.hasOwnProperty(field.id)
      const value =
        props.prefillData && hasPrefillValue
          ? props.prefillData[field.id]
          : getEmptyValue(field)
      return [field.id, value]
    })
  )
)

function handleDone() {
  if (!props.allowSubmit) return
  emit("done", { ...formData })
}

watch(formData, (newData) => emit("change", { ...newData }), { deep: true })
</script>

<template>
  <div>
    <!-- Le Stepper est rendu seulement lors qu'il y a des pages -->
    <DsfrStepper
      v-if="hasPages"
      :steps="stepTitles"
      :current-step="currentStep"
      class="mb-6"
    />

    <!-- Champs pour la page actuelle (ou tous les champs s'il n'y a pas de pages) -->
    <TransitionGroup
      tag="div"
      name="field-area"
      v-if="currentPageFields.length"
    >
      <FieldRenderer
        v-for="field in currentPageFields"
        :key="`render-${field.id}`"
        :field="field"
        v-model="formData[field.id]"
        :disabled="readonly"
        :vocabularies="props.vocabularies"
      />
    </TransitionGroup>

    <!-- Boutons de navigation -->
    <div class="flex justify-between nav-buttons" v-if="hasPages">
      <DsfrButton
        label="Précédent"
        secondary
        type="button"
        :disabled="currentStep === 1"
        @click="goPrev"
        size="lg"
      />
      <DsfrButton
        v-if="!isLastStep"
        label="Suivant"
        type="button"
        icon="ri-arrow-right-s-line"
        @click="goNext"
        size="lg"
      />
      <DsfrButton
        v-if="isLastStep && allowSubmit"
        icon="ri-arrow-right-s-line"
        label="Suivant"
        @click="handleDone"
        size="lg"
      />
    </div>

    <!-- S'il n'y a pas de pages, un seul bouton pour soumettre -->
    <div class="flex justify-end nav-buttons" v-if="!hasPages && allowSubmit">
      <DsfrButton
        @click="handleDone"
        icon="ri-arrow-right-s-line"
        label="Suivant"
        size="lg"
      />
    </div>
  </div>
</template>

<style scoped>
.field-area-move {
  transition: transform 0.25s ease;
}
div :deep(.fr-input-group) {
  margin-bottom: 24px;
}
.nav-buttons {
  margin-top: 16px;
}
</style>
