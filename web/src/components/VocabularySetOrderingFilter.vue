<script setup lang="ts">
const ordering = defineModel()
const emit = defineEmits(["update:modelValue"])
const options = [
  { text: "Label (desc)", value: "-name" },
  { text: "Label (asc)", value: "name" },
  { text: "Code (desc)", value: "-code" },
  { text: "Code (asc)", value: "code" },
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
