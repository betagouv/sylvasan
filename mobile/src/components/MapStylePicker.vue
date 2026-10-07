<script setup lang="ts">
import { MAP_STYLE_OPTIONS } from "../composables/useMapStyle"
import type { MapStyleKey } from "../composables/useMapStyle"

const props = defineProps<{ modelValue: MapStyleKey }>()
const emit = defineEmits<{
  (e: "update:modelValue", value: MapStyleKey): void
  (e: "close"): void
}>()

const select = (key: MapStyleKey) => {
  emit("update:modelValue", key)
  emit("close")
}
</script>

<template>
  <div
    class="bg-white rounded-xl shadow-xl border border-slate-100 overflow-hidden"
  >
    <button
      v-for="(option, key) in MAP_STYLE_OPTIONS"
      :key="key"
      class="flex items-center gap-3 w-full px-4 py-3 text-sm hover:bg-slate-50 active:bg-slate-100 transition-colors"
      :class="{ 'text-[#000091] font-semibold': modelValue === key }"
      @click="select(key as MapStyleKey)"
    >
      <v-icon :name="option.icon" scale="1.1" />
      <span>{{ option.label }}</span>
      <v-icon
        v-if="modelValue === key"
        name="ri-check-line"
        class="ml-auto"
      />
    </button>
  </div>
</template>
