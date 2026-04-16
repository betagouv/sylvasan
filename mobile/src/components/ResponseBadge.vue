<script setup lang="ts">
import type {
  ResponseFull,
  LocalResponseStatus,
  BackendResponseStatus,
  LocalResponse,
} from "@shared-types/response"
import { computed } from "vue"

const { response } = defineProps<{
  response: ResponseFull | LocalResponse
}>()

const displayStatus = computed(() => {
  const mapping: Record<LocalResponseStatus | BackendResponseStatus, string> = {
    draft: "en cours",
    pending: "Envoi en cours",
    synced: "envoyée",
    submitted: "envoyée",
    exported: "exportée",
  }
  return mapping[response.status]
})

const badgeType = computed(() => {
  const mapping: Record<LocalResponseStatus | BackendResponseStatus, string> = {
    draft: "warning",
    pending: "none",
    synced: "info",
    submitted: "info",
    exported: "success",
  }
  return mapping[response.status]
})

const hideIcon = computed(() => response.status !== "pending")
</script>

<template>
  <DsfrBadge
    :small="true"
    :label="displayStatus"
    :no-icon="hideIcon"
    :type="badgeType"
  />
</template>
