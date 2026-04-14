<script setup lang="ts">
import { reactive, ref, computed } from "vue"
import type {
  SurveySchema,
  SurveyField,
  FieldWidget,
} from "@shared-types/survey"

const props = defineProps<{
  schema: SurveySchema
  allowSubmit?: boolean
  prefillData?: Record<string, unknown>
  readonly?: boolean
}>()

const emit = defineEmits<{
  submit: [data: Record<string, unknown>]
}>()

const hasPages = computed(
  () => props.schema.pages && props.schema.pages.length > 0
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

const getEmptyValue = (field: SurveyField): any => {
  if (!field.ui?.widget) return ""
  const mapping: Record<FieldWidget, any> = {
    input: "",
    number: "",
    select: "",
    checkboxes: Array(),
    switch: false,
    radio: Array(),
    date: "",
  }
  return mapping[field.ui.widget]
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

function handleSubmit() {
  if (!props.allowSubmit) return
  emit("submit", { ...formData })
}
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
      <div
        v-for="(field, index) in currentPageFields"
        :key="`render-${field.id}`"
      >
        <DsfrInputGroup v-if="field.ui?.widget === 'input'">
          <!-- Champ texte -->
          <DsfrInput
            v-model="formData[field.id]"
            :label="field.label"
            :required="field.required ?? false"
            :label-visible="true"
            :hint="field.ui?.hint"
            :placeholder="field.ui?.placeholder"
            :isTextarea="field.ui?.textarea"
            :disabled="props.readonly"
          />
        </DsfrInputGroup>

        <!-- Champ numérique -->
        <DsfrInputGroup v-if="field.ui?.widget === 'number'">
          <DsfrInput
            v-model="formData[field.id]"
            :label="field.label"
            :required="field.required ?? false"
            :label-visible="true"
            :hint="field.ui?.hint"
            type="number"
            :placeholder="field.ui?.placeholder"
            :min="field.validation?.min"
            :max="field.validation?.max"
            :disabled="props.readonly"
          />
        </DsfrInputGroup>

        <!-- Champ select -->
        <DsfrInputGroup v-if="field.ui?.widget === 'select'">
          <DsfrSelect
            :options="field.ui?.choices"
            :label="field.label"
            :required="field.required ?? false"
            v-model="formData[field.id]"
            :disabled="props.readonly"
          />
        </DsfrInputGroup>

        <!-- Champ checkboxes -->
        <DsfrInputGroup v-if="field.ui?.widget === 'checkboxes'">
          <DsfrCheckboxSet
            :options="field.ui?.choices"
            :legend="field.label"
            :required="field.required ?? false"
            v-model="formData[field.id]"
            :disabled="props.readonly"
          />
        </DsfrInputGroup>

        <!-- Champ switch / interrupteur -->
        <DsfrInputGroup v-if="field.ui?.widget === 'switch'">
          <DsfrToggleSwitch
            :label="field.label"
            :required="field.required ?? false"
            :hint="field.ui?.hint"
            :activeText="field.ui?.activeText"
            :inactiveText="field.ui?.inactiveText"
            v-model="formData[field.id]"
            :disabled="props.readonly"
          />
        </DsfrInputGroup>
        <hr v-if="field.ui?.widget === 'switch'" />

        <!-- Champ radio -->
        <DsfrInputGroup v-if="field.ui?.widget === 'radio'">
          <DsfrRadioButtonSet
            :name="`radio-${index}`"
            :options="field.ui?.choices"
            :legend="field.label"
            :required="field.required ?? false"
            v-model="formData[field.id]"
            :disabled="props.readonly"
          />
        </DsfrInputGroup>

        <!-- Champ date -->
        <DsfrInputGroup v-if="field.ui?.widget === 'date'">
          <DsfrInput
            v-model="formData[field.id]"
            :label="field.label"
            :required="field.required ?? false"
            :label-visible="true"
            :hint="field.ui?.hint"
            type="date"
            :min="field.validation?.min"
            :max="field.validation?.max"
            :disabled="props.readonly"
          />
        </DsfrInputGroup>
      </div>
    </TransitionGroup>

    <!-- Boutons de navigation -->
    <div class="flex justify-between mt-6" v-if="hasPages">
      <DsfrButton
        label="Précédent"
        secondary
        type="button"
        :disabled="currentStep === 1"
        @click="goPrev"
      />
      <DsfrButton
        v-if="!isLastStep"
        label="Suivant"
        type="button"
        icon="ri-arrow-right-s-line"
        @click="goNext"
      />
      <DsfrButton
        v-if="isLastStep && allowSubmit"
        label="Soumettre"
        @click="handleSubmit"
        icon="ri-check-line"
      />
    </div>

    <!-- S'il n'y a pas de pages, un seul bouton pour soumettre -->
    <DsfrButton
      v-if="!hasPages && allowSubmit"
      @click="handleSubmit"
      label="Soumettre"
      icon="ri-check-line"
    />
  </div>
</template>

<style scoped>
.field-area-move {
  transition: transform 0.25s ease;
}
div :deep(.fr-input-group) {
  margin-bottom: 24px;
}
</style>
