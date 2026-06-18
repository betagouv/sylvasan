<script setup lang="ts">
import { useToastStore } from "../stores/toast"
const store = useToastStore()
</script>

<template>
  <div
    class="fixed top-1 right-1 flex flex-col gap-2 z-9999 ml-1"
    id="main-toast-container"
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
        class="bg-white"
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
#main-toast-container {
  padding-top: env(safe-area-inset-top);
  padding-right: env(safe-area-inset-right);
  padding-left: env(safe-area-inset-left);
}
</style>
