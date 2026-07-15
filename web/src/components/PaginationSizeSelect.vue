<script setup lang="ts">
const limit = defineModel()
const emit = defineEmits(["update:modelValue"])
const options = [10, 20, 30, 40, 50, 100]
</script>

<template>
  <DsfrInputGroup>
    <DsfrSelect
      label="Réponses par page"
      :options="options"
      @update:modelValue="(val: string | number) => emit('update:modelValue', Number(val))"
      :modelValue="limit"
      class="text-sm!"
    />
  </DsfrInputGroup>
</template>
