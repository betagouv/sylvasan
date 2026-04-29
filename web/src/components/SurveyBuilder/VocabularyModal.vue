<script setup lang="ts">
import { ref } from "vue"
import type { VocabularySet } from "@shared-types/survey"

const props = defineProps<{
  vocabulary: VocabularySet
}>()

const opened = ref(false)
</script>

<template>
  <div>
    <DsfrButton
      icon="ri-information-line"
      icon-only
      tertiary
      size="sm"
      :title="`Voir le référentiel ${props.vocabulary.code}`"
      @click="opened = true"
    />
    <Teleport to="body">
      <DsfrModal
        :opened="opened"
        :title="props.vocabulary.name"
        @close="opened = false"
      >
        <p class="fr-text--sm text-gray-500 mb-4">
          Code :
          <code class="bg-slate-100 px-1 rounded">{{
            props.vocabulary.code
          }}</code>
          · {{ props.vocabulary.entries.length }} entrée(s)
        </p>
        <div class="overflow-y-auto max-h-96 border border-slate-200 rounded">
          <div
            v-for="entry in props.vocabulary.entries"
            :key="entry.code"
            class="flex gap-3 px-3 py-2 border-b border-slate-100 last:border-b-0"
          >
            <span class="font-mono text-gray-400 text-sm shrink-0">{{
              entry.code
            }}</span>
            <span class="text-sm">{{ entry.label }}</span>
          </div>
          <p
            v-if="!props.vocabulary.entries.length"
            class="px-3 py-2 text-sm text-gray-400 italic"
          >
            Aucune entrée active
          </p>
        </div>
      </DsfrModal>
    </Teleport>
  </div>
</template>
