<script setup lang="ts">
import { ref, computed } from "vue"
import type { SurveyField, FieldWidget, FieldType } from "@shared-types/survey"
import * as z from "zod"
import { ZodError } from "zod"
import { DsfrInputGroup } from "@gouvminint/vue-dsfr"
import SelectOption from "./SelectOption.vue"
import RadioOption from "./RadioOption.vue"
import type { DsfrSelectOption } from "@gouvminint/vue-dsfr"
import CheckboxOption from "./CheckboxOption.vue"
import { typeWidgetMapping } from "./mappings"
import ChoiceCard from "./ChoiceCard.vue"
import { useRootStore } from "../../stores/root"

const emit = defineEmits(["add", "close"])

const props = defineProps(["opened"])

const rootStore = useRootStore()

const makeEmptyPayload = (
  type: FieldType = "string",
  widget: FieldWidget = "input"
): SurveyField => ({
  type: type,
  label: "",
  required: false,
  id: "",
  ui: {
    hint: undefined,
    placeholder: undefined,
    widget: widget,
    textarea: false,
    choices: [],
  },
  validation: {},
})

const payload = ref<SurveyField>(makeEmptyPayload())

const optionsSource = ref<"manual" | "vocabulary">("manual")
const selectedVocabularyCode = ref<string>("")

const optionsSourceOptions = [
  { label: "Saisie manuelle", value: "manual" },
  { label: "Référentiel", value: "vocabulary" },
]

const vocabularySelectOptions = computed(() =>
  rootStore.vocabularies?.map((v) => ({
    text: `${v.code} — ${v.name}`,
    value: v.code,
  }))
)

const validator = z
  .object({
    type: z.string().min(1, "Ce champ ne peut pas être vide"),
    label: z.string().min(1, "Ce champ ne peut pas être vide"),
    id: z.string().min(1, "Ce champ ne peut pas être vide"),
    validation: z.object({ min: z.any(), max: z.any() }).optional(),
  })
  .superRefine((data, ctx) => {
    // Validation que min est inférieur à max pour les champs numériques
    if (data.type === "number") {
      const min = data.validation?.min
      const max = data.validation?.max
      const minFilled = min !== undefined && min !== null && min !== ""
      const maxFilled = max !== undefined && max !== null && max !== ""
      if (minFilled && maxFilled && Number(min) >= Number(max)) {
        ctx.addIssue({
          code: "custom",
          message: "Le minimum doit être inférieur au maximum",
          path: ["validationNumericLimits"],
        })
      }
    }
  })
const formErrors = ref<any>()

const typeOptions = computed(() =>
  Object.entries(typeWidgetMapping).map((x) => ({
    text: x[1].label,
    value: x[0],
  }))
)

const assignWidgetAndType = (option: FieldWidget) => {
  const mapping = typeWidgetMapping[option]
  if (!mapping) return
  optionsSource.value = "manual"
  selectedVocabularyCode.value = ""
  payload.value = makeEmptyPayload(mapping.type, mapping.widget)
}

const onOptionsSourceChange = (source: string | number | boolean) => {
  optionsSource.value = source as "manual" | "vocabulary"
  if (source === "manual") {
    payload.value.vocabulary = undefined
    selectedVocabularyCode.value = ""
  } else {
    if (payload.value.ui) payload.value.ui.choices = []
  }
}

const onVocabularyChange = (code: string) => {
  selectedVocabularyCode.value = code
  payload.value.vocabulary = code || undefined
}

const addField = () => {
  try {
    validator.parse(payload.value)
    const emitValue = { ...payload.value }
    payload.value = makeEmptyPayload()
    optionsSource.value = "manual"
    selectedVocabularyCode.value = ""
    emit("add", emitValue)
  } catch (error) {
    if (error instanceof ZodError) formErrors.value = z.flattenError(error)
  }
}

const addOption = (option: DsfrSelectOption) => {
  if (!payload.value.ui) return
  if (!payload.value.ui.choices) {
    payload.value.ui.choices = [option]
    return
  }
  payload.value.ui.choices.push(option)
}

const removeOption = (option: DsfrSelectOption) => {
  if (!payload.value.ui?.choices) return
  payload.value.ui.choices = payload.value.ui?.choices.filter(
    (x: DsfrSelectOption) => x !== option
  )
}

const close = () => {
  if (formErrors.value?.fieldErrors) formErrors.value.fieldErrors = undefined
  emit("close")
}
</script>

<template>
  <DsfrModal :opened="props.opened" @close="close" size="xl">
    <h3 class="fr-text--md">Nouveau champ</h3>
    <div class="md:flex gap-6">
      <DsfrSelect
        @update:modelValue="(value: FieldWidget) => assignWidgetAndType(value)"
        value="input"
        :error-message="formErrors?.fieldErrors?.type?.[0]"
        label="Type"
        :options="typeOptions"
        :required="true"
      />
      <DsfrInputGroup :error-message="formErrors?.fieldErrors?.label?.[0]">
        <DsfrInput
          label-visible
          v-model="payload.label"
          :required="true"
          label="Titre"
        />
      </DsfrInputGroup>
      <DsfrInputGroup :error-message="formErrors?.fieldErrors?.id?.[0]">
        <DsfrInput
          label-visible
          v-model="payload.id"
          :required="true"
          label="Id du champ"
        />
      </DsfrInputGroup>
      <DsfrToggleSwitch
        v-model="payload.required"
        label="Champ obligatoire ?"
        activeText="Oui"
        inactiveText="Non"
        class="my-4"
      />
    </div>
    <hr />

    <!-- Options pour widget "input" / number -->
    <div
      class="flex gap-6"
      v-if="payload.ui?.widget === 'input' || payload.ui?.widget === 'number'"
    >
      <DsfrInputGroup>
        <DsfrInput
          label-visible
          v-model="payload.ui.hint"
          v-if="payload.ui"
          label="Aide"
        />
      </DsfrInputGroup>
      <DsfrInputGroup>
        <DsfrInput
          label-visible
          v-model="payload.ui.placeholder"
          label="Placeholder"
        />
      </DsfrInputGroup>

      <div
        class="grow"
        v-if="payload.validation && payload.ui.widget === 'input'"
      ></div>
      <DsfrToggleSwitch
        v-if="payload.validation && payload.ui.widget === 'input'"
        label="Champ multiligne"
        activeText="Oui"
        inactiveText="Non"
        v-model="payload.ui.textarea"
      />

      <!-- Validation min/max pour les chiffres -->
      <div v-if="payload.validation && payload.ui.widget === 'number'">
        <DsfrInputGroup
          :error-message="formErrors?.fieldErrors?.validationNumericLimits?.[0]"
        >
          <div class="flex gap-4">
            <div>
              <DsfrInput
                type="number"
                v-model="payload.validation.min"
                label="Valeur minimale"
                label-visible
              />
            </div>
            <div>
              <DsfrInput
                type="number"
                v-model="payload.validation.max"
                label="Valeur maximale"
                label-visible
              />
            </div>
          </div>
        </DsfrInputGroup>
      </div>
    </div>

    <div v-else-if="payload.ui?.widget === 'select'">
      <h6 class="fr-text--md">Options</h6>
      <DsfrRadioButtonSet
        name="options-source-select"
        :options="optionsSourceOptions"
        :model-value="optionsSource"
        :inline="true"
        @update:model-value="onOptionsSourceChange"
        class="mb-4"
      />
      <div v-if="optionsSource === 'vocabulary'">
        <DsfrSelect
          class="max-w-lg"
          label="Référentiel"
          :options="vocabularySelectOptions"
          :model-value="selectedVocabularyCode"
          @update:model-value="onVocabularyChange"
        />
      </div>
      <template v-else>
        <div v-if="payload.ui.choices" class="grid grid-cols grid-cols-3 gap-4">
          <ChoiceCard
            v-for="choice in payload.ui.choices"
            :key="`choice-${choice.value}`"
            class="col-span-1 p-2 border border-slate-300 flex items-center gap-4"
            :choice="choice"
            @delete="removeOption(choice)"
          />
        </div>
        <SelectOption class="mt-4" @add="addOption" />
      </template>
    </div>

    <div v-else-if="payload.ui?.widget === 'checkboxes'">
      <h6 class="fr-text--md">Options</h6>
      <div v-if="payload.ui.choices" class="grid grid-cols grid-cols-3 gap-4">
        <ChoiceCard
          v-for="choice in payload.ui.choices"
          :key="`checkbox-choice-${choice.value}`"
          class="col-span-1 p-2 border border-slate-300 flex items-center gap-4"
          :choice="choice"
          @delete="removeOption(choice)"
        />
      </div>
      <CheckboxOption class="mt-4" @add="addOption" />
    </div>

    <div
      v-else-if="payload.ui?.widget === 'switch'"
      class="flex gap-4 items-end switch-fields"
    >
      <!-- TODO : automatically add ID et nom, verifier à quoi ils servent -->
      <DsfrInputGroup>
        <DsfrInput
          label-visible
          v-model="payload.ui.hint"
          v-if="payload.ui"
          label="Aide"
        />
      </DsfrInputGroup>
      <DsfrInputGroup>
        <DsfrInput
          label-visible
          v-model="payload.ui.activeText"
          label="Text actif"
          hint="Texte à afficher lorsqu'il est activé"
        />
      </DsfrInputGroup>
      <DsfrInputGroup>
        <DsfrInput
          label-visible
          v-model="payload.ui.inactiveText"
          label="Text inactif"
          hint="Texte à afficher lorsqu'il est desactivé"
        />
      </DsfrInputGroup>
    </div>

    <div v-else-if="payload.ui?.widget === 'radio'">
      <h6>Options</h6>
      <DsfrRadioButtonSet
        name="options-source-radio"
        :options="optionsSourceOptions"
        :model-value="optionsSource"
        :inline="true"
        @update:model-value="onOptionsSourceChange"
        class="mb-4"
      />
      <div v-if="optionsSource === 'vocabulary'">
        <DsfrSelect
          class="max-w-lg"
          label="Référentiel"
          :options="vocabularySelectOptions"
          :model-value="selectedVocabularyCode"
          @update:model-value="onVocabularyChange"
        />
      </div>
      <template v-else>
        <div v-if="payload.ui.choices" class="grid grid-cols grid-cols-3 gap-4">
          <div
            v-for="choice in payload.ui.choices"
            :key="`choice-${choice.value}`"
            class="col-span-1 p-2 border border-slate-300 flex items-center gap-4"
          >
            <DsfrButton
              tertiary
              size="sm"
              icon-only
              icon="ri-delete-bin-line"
              @click="() => removeOption(choice)"
            />
            <p class="mb-0!">{{ choice.label }} ({{ choice.value }})</p>
          </div>
        </div>
        <RadioOption class="mt-4" @add="addOption" />
      </template>
    </div>

    <div class="flex gap-6" v-else-if="payload.ui?.widget === 'date'">
      <DsfrInputGroup>
        <DsfrInput
          label-visible
          v-model="payload.ui.hint"
          v-if="payload.ui"
          label="Aide"
        />
      </DsfrInputGroup>
      <div v-if="payload.validation">
        <DsfrInput
          type="date"
          v-model="payload.validation.min"
          label="Valeur minimale"
          label-visible
        />
      </div>
      <div v-if="payload.validation">
        <DsfrInput
          type="date"
          v-model="payload.validation.max"
          label="Valeur maximale"
          label-visible
        />
      </div>
    </div>

    <div v-else-if="payload.ui?.widget === 'array'">
      <div class="flex gap-6">
        <DsfrInputGroup>
          <DsfrInput
            label-visible
            v-model="payload.ui.addLabel"
            v-if="payload.ui"
            placeholder="Ajouter un élément"
            label="Titre du bouton pour l'ajout"
          />
        </DsfrInputGroup>
        <DsfrInputGroup>
          <DsfrInput
            type="number"
            v-model="payload.validation.minItems"
            label="No. min d'éléments"
            label-visible
            v-if="payload.validation"
          />
        </DsfrInputGroup>
        <DsfrInputGroup>
          <DsfrInput
            type="number"
            v-model="payload.validation.maxItems"
            label="No. max d'éléments"
            label-visible
            v-if="payload.validation"
          />
        </DsfrInputGroup>
      </div>
      <DsfrHighlight
        class="ml-0!"
        text="Vous pourrez ajouter des champs de l'objet par la suite"
      />
    </div>

    <!-- Pas encore gérés -->
    <div v-else>
      <DsfrNotice type="warning" title="Pas encore disponible" />
    </div>

    <!-- Footer -->
    <template v-slot:footer>
      <div class="flex justify-end w-full">
        <DsfrButton label="Ajouter" @click="addField" />
      </div>
    </template>
  </DsfrModal>
</template>

<style scoped>
.switch-fields :deep(.fr-input-group) {
  margin-bottom: 0;
}
</style>
