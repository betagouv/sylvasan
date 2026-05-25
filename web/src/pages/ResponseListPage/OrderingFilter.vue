<script setup lang="ts">
const limit = defineModel()
const emit = defineEmits(["update:modelValue"])
const options = [
  { text: "Date de cŕeation (desc)", value: "-creation_date" },
  { text: "Date de cŕeation (asc)", value: "creation_date" },
  { text: "ID (desc)", value: "-id" },
  { text: "ID (asc)", value: "id" },
]
</script>

<template>
  <DsfrInputGroup>
    <DsfrSelect
      label="Triage"
      :options="options"
      @update:modelValue="(val: string) => emit('update:modelValue', val)"
      :modelValue="limit"
      class="text-sm!"
    />
  </DsfrInputGroup>
</template>
