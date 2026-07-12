<script setup lang="ts">
import type { ResponseFull } from "@shared-types/response"
const { followUpResponse } = defineProps<{
  followUpResponse: ResponseFull
}>()
</script>

<template>
  <div>
    <span
      class="inline-flex items-center gap-1 px-3 py-1 rounded-full font-bold"
      :style="{
        background: followUpResponse.surveyFollowUp?.actionColor ?? '#e3e3fd',
      }"
    >
      <v-icon
        v-if="followUpResponse.surveyFollowUp?.actionIcon"
        :name="followUpResponse.surveyFollowUp.actionIcon"
        scale="1.2"
      />
      {{ followUpResponse.surveyFollowUp?.title }}
    </span>
  </div>
</template>
