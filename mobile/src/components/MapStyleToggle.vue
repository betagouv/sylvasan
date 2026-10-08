<script setup lang="ts">
import { ref } from "vue"
import type { MapStyleKey } from "../composables/useMapStyle"
import MapStylePicker from "./MapStylePicker.vue"

defineProps<{ modelValue: MapStyleKey }>()
const emit = defineEmits<{
  (e: "update:modelValue", value: MapStyleKey): void
}>()

const pickerOpen = ref(false)

const onSelect = (key: MapStyleKey) => {
  pickerOpen.value = false
  emit("update:modelValue", key)
}
</script>

<template>
  <div class="relative">
    <button
      class="toggle-btn flex items-center justify-center rounded-full shadow-lg bg-white! border border-slate-200"
      :aria-expanded="pickerOpen"
      aria-label="Choisir le style de carte"
      @click="pickerOpen = !pickerOpen"
    >
      <v-icon name="ri-stack-line" scale="1.2" />
    </button>

    <Transition name="drop">
      <MapStylePicker
        v-if="pickerOpen"
        :model-value="modelValue"
        class="picker absolute"
        @update:model-value="onSelect"
        @close="pickerOpen = false"
      />
    </Transition>
  </div>
</template>

<style scoped>
.toggle-btn {
  width: 44px;
  height: 44px;
}

.picker {
  top: 0;
  right: calc(100% + 0.5rem);
}

.drop-enter-active,
.drop-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.drop-enter-from,
.drop-leave-to {
  transform: translateY(-0.5rem);
  opacity: 0;
}
</style>
