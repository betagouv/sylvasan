<script setup lang="ts">
import { ref } from "vue"
import * as z from "zod"

const optionLabel = ref<string>()
const optionValue = ref<string>()
const optionHint = ref<string>()
const emit = defineEmits(["add"])

const validator = z.object({
  label: z.string().min(1, "Ce champ ne peut pas être vide"),
  value: z.string().min(1, "Ce champ ne peut pas être vide"),
})
const formErrors = ref<any>()

const addOption = () => {
  const result = validator.safeParse({
    label: optionLabel.value,
    value: optionValue.value,
  })
  if (!result.success) {
    formErrors.value = z.flattenError(result.error)
    return
  }
  formErrors.value = undefined
  emit("add", {
    label: optionLabel.value,
    value: optionValue.value,
    hint: optionHint.value,
  })
  optionLabel.value = ""
  optionValue.value = ""
  optionHint.value = ""
}
</script>

<template>
  <div class="flex gap-4 items-end p-4 bg-slate-50 rounded">
    <div>
      <DsfrInputGroup :error-message="formErrors?.fieldErrors?.label?.[0]">
        <DsfrInput
          v-model="optionLabel"
          label="Texte"
          label-visible
          :required="true"
        />
      </DsfrInputGroup>
    </div>
    <div>
      <DsfrInputGroup :error-message="formErrors?.fieldErrors?.value?.[0]">
        <DsfrInput
          v-model="optionValue"
          label="Valeur"
          label-visible
          :required="true"
        />
      </DsfrInputGroup>
    </div>
    <div>
      <DsfrInput v-model="optionHint" label="Aide" label-visible />
    </div>
    <div>
      <DsfrButton
        tertiary
        no-outline
        label="Ajouter"
        @click="addOption"
        icon="ri-add-line"
      />
    </div>
  </div>
</template>
