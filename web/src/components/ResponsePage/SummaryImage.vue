<script setup lang="ts">
import type { ImageItem } from "@shared-types/survey"

const { images } = defineProps<{
  images: ImageItem[]
}>()

const emit = defineEmits<{
  "open-viewer": [images: ImageItem[], index: number]
}>()

const imageSrc = (item: ImageItem): string | null => {
  if ("type" in item) return null
  if ("file" in item) return `data:image/jpeg;base64,${item.file}`
  if (item.thumbnail) return `data:image/jpeg;base64,${item.thumbnail}`
  return null
}
</script>

<template>
  <div class="grid grid-cols-4 gap-2 my-2">
    <div
      v-for="(img, idx) in images"
      :key="idx"
      class="group aspect-square rounded overflow-hidden border border-slate-200 cursor-pointer relative"
      @click="emit('open-viewer', images, idx)"
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
      <div
        class="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center"
      >
        <v-icon
          name="ri-search-eye-line"
          color="white"
          scale="1.5"
          class="text-white opacity-0 group-hover:opacity-100 transition-opacity"
        />
      </div>
    </div>
  </div>
</template>
