<script setup lang="ts">
import { ref } from "vue"

const optionLabel = ref<string>()
const optionValue = ref<string>()
const optionHint = ref<string>()
const emit = defineEmits(["add"])

const addOption = () => {
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
      <DsfrInput
        v-model="optionLabel"
        label="Texte"
        label-visible
        :required="true"
      />
    </div>
    <div>
      <DsfrInput v-model="optionHint" label="Aide" label-visible />
    </div>
    <div>
      <DsfrInput
        v-model="optionValue"
        label="Valeur"
        label-visible
        :required="true"
      />
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
