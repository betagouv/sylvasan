<script setup lang="ts">
import { ref } from "vue"
import type { SurveyField } from "@shared-types/survey"
import * as z from "zod"
import { ZodError } from "zod"
import { DsfrInputGroup } from "@gouvminint/vue-dsfr"

const emit = defineEmits(["add"])

const payload = ref<SurveyField>({
  type: "text",
  label: "",
  required: false,
  id: "",
  hint: undefined,
  placeholder: undefined,
})

const validator = z.object({
  type: z.string().min(1, "Ce champ ne peut pas être vide"),
  label: z.string().min(1, "Ce champ ne peut pas être vide"),
  id: z.string().min(1, "Ce champ ne peut pas être vide"),
})
const formErrors = ref<any>()

const typeOptions = [{ text: "Texte", value: "text" }]

const addField = () => {
  try {
    validator.parse(payload.value)
    emit("add", { ...payload.value })
    payload.value.type = "text"
    payload.value.label = ""
    payload.value.required = false
    payload.value.id = ""
    payload.value.hint = ""
    payload.value.placeholder = ""
  } catch (error) {
    if (error instanceof ZodError) formErrors.value = z.flattenError(error)
  }
}
</script>

<template>
  <div>
    <h3>Nouveau champ</h3>
    <DsfrSelect
      v-model="payload.type"
      :error-message="formErrors?.fieldErrors?.type?.[0]"
      label="Type"
      :options="typeOptions"
      :required="true"
    />
    <DsfrInputGroup :error-message="formErrors?.fieldErrors?.label?.[0]">
      <DsfrInput label-visible v-model="payload.label" label="Titre" />
    </DsfrInputGroup>
    <DsfrInputGroup :error-message="formErrors?.fieldErrors?.hint?.[0]">
      <DsfrInput label-visible v-model="payload.hint" label="Aide" />
    </DsfrInputGroup>
    <DsfrInputGroup :error-message="formErrors?.fieldErrors?.placeholder?.[0]">
      <DsfrInput
        label-visible
        v-model="payload.placeholder"
        label="Placeholder"
      />
    </DsfrInputGroup>
    <DsfrToggleSwitch
      v-model="payload.required"
      label="Champ obligatoire ?"
      activeText="Oui"
      inactiveText="Non"
      class="my-4"
    />
    <hr />
    <DsfrInputGroup :error-message="formErrors?.fieldErrors?.id?.[0]">
      <DsfrInput label-visible v-model="payload.id" label="Id du champ" />
    </DsfrInputGroup>
    <hr />
    <div class="flex items-center justify-center">
      <DsfrButton label="Ajouter" @click="addField" />
    </div>
  </div>
</template>
