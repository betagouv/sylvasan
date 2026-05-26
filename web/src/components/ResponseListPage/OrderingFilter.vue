<script setup lang="ts">
const ordering = defineModel()
const emit = defineEmits(["update:modelValue"])
const options = [
  { text: "Date de création (desc)", value: "-creation_date" },
  { text: "Date de création (asc)", value: "creation_date" },
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
      :modelValue="ordering"
      class="text-sm!"
    />
  </DsfrInputGroup>
</template>
