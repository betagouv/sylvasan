<script setup lang="ts">
import { ref, watch } from "vue"
import type { ImageItem } from "@shared-types/survey"
import ImageViewer from "@shared-components/ImageViewer.vue"
import { resolveLocalImageSrc } from "../utils/imageStorage"

const { images } = defineProps<{
  images: ImageItem[]
}>()

const resolvedSrcs = ref<Record<string, string>>({})

watch(
  () => images,
  async (imgs) => {
    for (const item of imgs) {
      if (!("type" in item) || resolvedSrcs.value[item.path]) continue
      const src = await resolveLocalImageSrc(item.path).catch(() => null)
      if (src) resolvedSrcs.value[item.path] = src
    }
  },
  { immediate: true }
)

const imageSrc = (item: ImageItem): string | null => {
  if ("type" in item) return resolvedSrcs.value[item.path] ?? null
  if ("file" in item) return `data:image/jpeg;base64,${item.file}`
  if (item.thumbnail) return `data:image/jpeg;base64,${item.thumbnail}`
  return null
}

const viewerOpen = ref(false)
const viewerIndex = ref(0)

const openViewer = (index: number) => {
  viewerIndex.value = index
  viewerOpen.value = true
}
</script>

<template>
  <div class="grid grid-cols-4 gap-2 my-2">
    <div
      v-for="(img, idx) in images"
      :key="idx"
      class="aspect-square rounded overflow-hidden border border-slate-200 cursor-pointer"
      @click="openViewer(idx)"
    >
      <img
        v-if="imageSrc(img)"
        :src="imageSrc(img)!"
        class="w-full h-full object-cover"
        alt=""
      />
      <div
        v-else
        class="w-full h-full bg-slate-100 flex items-center justify-center"
      >
        <v-icon name="ri-image-line" scale="2" class="text-slate-400" />
      </div>
    </div>
  </div>

  <ImageViewer
    :images="images"
    :startIndex="viewerIndex"
    :opened="viewerOpen"
    :resolvedSrcs="resolvedSrcs"
    @close="viewerOpen = false"
  />
</template>
