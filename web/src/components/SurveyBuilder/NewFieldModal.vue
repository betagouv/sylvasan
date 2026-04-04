<script setup lang="ts">
import { ref, computed } from "vue"
import type { FieldType, SurveyField, FieldWidget } from "@shared-types/survey"
import * as z from "zod"
import { ZodError } from "zod"
import { DsfrInputGroup } from "@gouvminint/vue-dsfr"
import SelectOption from "./SelectOption.vue"
import type { DsfrSelectOption } from "@gouvminint/vue-dsfr"
import { typeWidgetMapping } from "./mappings"

const emit = defineEmits(["add", "close"])

const props = defineProps(["opened"])

const makeEmptyPayload = (): SurveyField => ({
  type: "string",
  label: "",
  required: false,
  id: "",
  ui: {
    hint: undefined,
    placeholder: undefined,
    widget: "input",
  },
  validation: {},
})

const payload = ref<SurveyField>(makeEmptyPayload())

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
  payload.value.type = mapping.type
  if (payload.value.ui) payload.value.ui.widget = mapping.widget
}

const addField = () => {
  try {
    validator.parse(payload.value)
    const emitValue = { ...payload.value }
    payload.value = makeEmptyPayload()
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
  formErrors.value.fieldErrors = undefined
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
      <DsfrInputGroup :error-message="formErrors?.fieldErrors?.hint?.[0]">
        <DsfrInput
          label-visible
          v-model="payload.ui.hint"
          v-if="payload.ui"
          label="Aide"
        />
      </DsfrInputGroup>
      <DsfrInputGroup
        :error-message="formErrors?.fieldErrors?.placeholder?.[0]"
      >
        <DsfrInput
          label-visible
          v-model="payload.ui.placeholder"
          label="Placeholder"
        />
      </DsfrInputGroup>

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
      <h6>Options</h6>
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
          <p class="mb-0!">{{ choice.text }} ({{ choice.value }})</p>
        </div>
      </div>
      <SelectOption class="mt-4" @add="addOption" />
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
