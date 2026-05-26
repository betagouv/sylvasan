<script setup lang="ts">
const props = defineProps<{
  createdAfter: string
  createdBefore: string
}>()

const emit = defineEmits<{
  "update:createdAfter": [value: string]
  "update:createdBefore": [value: string]
}>()
</script>

<template>
  <div class="flex gap-4">
    <DsfrInputGroup class="mb-0!">
      <DsfrInput
        label="Créée après le"
        label-visible
        type="date"
        :model-value="props.createdAfter"
        @update:model-value="(v: string) => emit('update:createdAfter', v)"
      />
    </DsfrInputGroup>
    <DsfrInputGroup class="mb-0!">
      <DsfrInput
        label="Créée avant le"
        label-visible
        type="date"
        :model-value="props.createdBefore"
        @update:model-value="(v: string) => emit('update:createdBefore', v)"
      />
    </DsfrInputGroup>
  </div>
</template>
