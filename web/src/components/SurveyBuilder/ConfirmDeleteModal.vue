<script setup lang="ts">
import type { DsfrButtonProps } from "@gouvminint/vue-dsfr"

defineProps<{
  opened: boolean
  title: string
}>()

const emit = defineEmits(["confirm", "close"])

const actions: DsfrButtonProps[] = [
  {
    label: "Supprimer",
    onClick() {
      emit("confirm")
    },
  },
  {
    label: "Annuler",
    secondary: true,
    onClick() {
      emit("close")
    },
  },
]
</script>

<template>
  <DsfrModal
    :opened="opened"
    :title="title"
    :is-alert="true"
    :actions="actions"
    @close="emit('close')"
  >
    <slot />
  </DsfrModal>
</template>
