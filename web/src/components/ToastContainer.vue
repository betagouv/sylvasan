<script setup lang="ts">
import { useToastStore } from "../stores/toast"
const store = useToastStore()
</script>

<template>
  <div
    class="fixed top-1 right-1 d-flex flex-col gap-2 z-9999 bg-white"
    aria-live="polite"
  >
    <TransitionGroup name="toast">
      <DsfrAlert
        v-for="toast in store.toasts"
        :key="toast.id"
        :type="toast.type"
        role="status"
        :description="toast.message"
        :closeable="true"
        @close="store.dismiss(toast.id)"
      />
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateY(-10px);
}
.toast-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
