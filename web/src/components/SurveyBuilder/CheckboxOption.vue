<script setup lang="ts">
import { ref } from "vue"

// TODO - Vérifier si on garde ID et nom (est-ce nécessaire ?)

const optionLabel = ref<string>()
const optionValue = ref<string>()
// const optionId = ref<string>()
// const optionName = ref<string>()
const optionHint = ref<string>()

const emit = defineEmits(["add"])

const addOption = () => {
  emit("add", {
    label: optionLabel.value,
    value: optionValue.value,
    // id: optionId.value,
    // name: optionName.value,
    hint: optionHint.value,
  })
  optionLabel.value = ""
  optionValue.value = ""
  // optionId.value = ""
  // optionName.value = ""
  optionHint.value = ""
}
</script>

<template>
  <div>
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
        <DsfrInput
          v-model="optionValue"
          label="Valeur"
          label-visible
          :required="true"
        />
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
    <!-- <div class="flex gap-4 items-end p-4 bg-slate-50 rounded">
      <div>
        <DsfrInput
          v-model="optionId"
          label="Id"
          label-visible
          :required="true"
        />
      </div>
      <div>
        <DsfrInput
          v-model="optionName"
          label="Nom"
          label-visible
          :required="true"
        />
      </div>
    </div> -->
  </div>
</template>
