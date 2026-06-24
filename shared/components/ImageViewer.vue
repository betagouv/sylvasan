<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue"
import type { ImageItem } from "@shared-types/survey"

const props = withDefaults(
  defineProps<{
    images: ImageItem[]
    startIndex?: number
    opened: boolean
    resolvedSrcs?: Record<string, string>
  }>(),
  { startIndex: 0 }
)

const emit = defineEmits<{ close: [] }>()

const currentIndex = ref(props.startIndex)

watch(
  () => props.startIndex,
  (val) => {
    currentIndex.value = val
  }
)

const current = computed(() => props.images[currentIndex.value])

const fullSrc = (item: ImageItem): string => {
  if ("type" in item) return props.resolvedSrcs?.[item.path] ?? ""
  if ("id" in item) {
    if (item.fileUrl) return item.fileUrl
    if (item.thumbnail) return `data:image/jpeg;base64,${item.thumbnail}`
    return ""
  }
  return `data:image/jpeg;base64,${item.file}`
}

const direction = ref<"left" | "right">("left")

const prev = () => {
  if (currentIndex.value > 0) {
    direction.value = "right"
    currentIndex.value--
  }
}

const next = () => {
  if (currentIndex.value < props.images.length - 1) {
    direction.value = "left"
    currentIndex.value++
  }
}

const onKeydown = (e: KeyboardEvent) => {
  if (!props.opened) return
  if (e.key === "ArrowLeft") prev()
  if (e.key === "ArrowRight") next()
}

onMounted(() => window.addEventListener("keydown", onKeydown))
onUnmounted(() => window.removeEventListener("keydown", onKeydown))

const touchStartX = ref(0)

const onTouchStart = (e: TouchEvent) => {
  touchStartX.value = e.touches[0].clientX
}

const onTouchEnd = (e: TouchEvent) => {
  const delta = e.changedTouches[0].clientX - touchStartX.value
  if (Math.abs(delta) < 50) return
  if (delta > 0) prev()
  else next()
}
</script>

<template>
  <Teleport to="body">
    <DsfrModal
      :opened="opened"
      :title="`Photo ${currentIndex + 1} / ${images.length}`"
      size="xl"
      @close="emit('close')"
    >
      <div
        class="relative overflow-hidden flex items-center justify-center min-h-64"
        @touchstart.passive="onTouchStart"
        @touchend.passive="onTouchEnd"
      >
        <Transition :name="`slide-${direction}`">
          <img
            v-if="current && fullSrc(current)"
            :key="currentIndex"
            :src="fullSrc(current)"
            class="max-w-full max-h-[70vh] object-contain rounded"
            alt=""
          />
        </Transition>
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

<style scoped>
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
  position: absolute;
}

.slide-left-enter-from  { transform: translateX(100%);  opacity: 0; }
.slide-left-leave-to    { transform: translateX(-100%); opacity: 0; }
.slide-right-enter-from { transform: translateX(-100%); opacity: 0; }
.slide-right-leave-to   { transform: translateX(100%);  opacity: 0; }
</style>
