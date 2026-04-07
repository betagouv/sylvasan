<script setup lang="ts">
import { ref } from "vue"
import * as z from "zod"

const optionText = ref<string>()
const optionValue = ref<string>()
const emit = defineEmits(["add"])

const validator = z.object({
  text: z.string().min(1, "Ce champ ne peut pas être vide"),
  value: z.string().min(1, "Ce champ ne peut pas être vide"),
})
const formErrors = ref<any>()

const addOption = () => {
  const result = validator.safeParse({
    text: optionText.value,
    value: optionValue.value,
  })
  if (!result.success) {
    formErrors.value = z.flattenError(result.error)
    return
  }
  formErrors.value = undefined
  emit("add", result.data)
  optionText.value = ""
  optionValue.value = ""
}
</script>

<template>
  <div class="flex gap-4 items-end p-4 bg-slate-50 rounded">
    <div>
      <DsfrInputGroup :error-message="formErrors?.fieldErrors?.text?.[0]">
        <DsfrInput
          v-model="optionText"
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
