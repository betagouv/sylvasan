<script setup lang="ts">
import { ref } from "vue"

const optionText = ref<string>()
const optionValue = ref<string>()
const emit = defineEmits(["add"])

const addOption = () => {
  emit("add", { text: optionText.value, value: optionValue.value })
  optionText.value = ""
  optionValue.value = ""
}
</script>

<template>
  <div class="flex gap-4 items-end p-4 bg-slate-50 rounded">
    <div>
      <DsfrInput
        v-model="optionText"
        label="Texte"
        label-visible
        :required="true"
      />
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
