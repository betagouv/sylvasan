<script setup lang="ts">
const emit = defineEmits(["delete"])
const { choice } = defineProps(["choice"])
</script>

<template>
  <div>
    <div class="grow pl-2">
      <p class="mb-0!">
        {{ choice.label || choice.text }} ({{ choice.value }})
      </p>
      <p class="mb-0! italic text-slate-500" v-if="choice.hint">
        {{ choice.hint }}
      </p>
    </div>
    <DsfrButton
      type="button"
      tertiary
      size="sm"
      icon-only
      icon="ri-delete-bin-line"
      @click.stop.prevent="() => emit('delete', choice)"
    />
  </div>
</template>
