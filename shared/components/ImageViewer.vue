<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue"
import type { ImageItem } from "@shared-types/survey"

const props = withDefaults(
  defineProps<{
    images: ImageItem[]
    startIndex?: number
    opened: boolean
  }>(),
  { startIndex: 0 }
)

const emit = defineEmits<{ close: [] }>()

const currentIndex = ref(props.startIndex)

watch(
  () => props.startIndex,
  (val) => { currentIndex.value = val }
)

const current = computed(() => props.images[currentIndex.value])

const fullSrc = (item: ImageItem): string => {
  if ("id" in item) {
    if (item.fileUrl) return item.fileUrl
    if (item.thumbnail) return `data:image/jpeg;base64,${item.thumbnail}`
    return ""
  }
  return `data:image/jpeg;base64,${item.file}`
}

const prev = () => {
  if (currentIndex.value > 0) currentIndex.value--
}

const next = () => {
  if (currentIndex.value < props.images.length - 1) currentIndex.value++
}

const onKeydown = (e: KeyboardEvent) => {
  if (!props.opened) return
  if (e.key === "ArrowLeft") prev()
  if (e.key === "ArrowRight") next()
}

onMounted(() => window.addEventListener("keydown", onKeydown))
onUnmounted(() => window.removeEventListener("keydown", onKeydown))
</script>

<template>
  <Teleport to="body">
    <DsfrModal
      :opened="opened"
      :title="`Photo ${currentIndex + 1} / ${images.length}`"
      size="xl"
      @close="emit('close')"
    >
      <div class="flex items-center justify-center min-h-64">
        <img
          v-if="current && fullSrc(current)"
          :src="fullSrc(current)"
          class="max-w-full max-h-[70vh] object-contain rounded"
          alt=""
        />
      </div>

      <template v-if="images.length > 1" #footer>
        <div class="flex gap-3">
          <DsfrButton
            type="button"
            secondary
            icon="ri-arrow-left-s-line"
            label="Précédente"
            :disabled="currentIndex === 0"
            @click="prev"
          />
          <DsfrButton
            type="button"
            secondary
            icon="ri-arrow-right-s-line"
            icon-right
            label="Suivante"
            :disabled="currentIndex === images.length - 1"
            @click="next"
          />
        </div>
      </template>
    </DsfrModal>
  </Teleport>
</template>
