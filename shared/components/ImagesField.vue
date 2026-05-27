<script setup lang="ts">
import { computed, ref, useId } from "vue"
import type { SurveyField } from "@shared-types/survey"

type LocalImageItem = { file: string }
type RemoteImageItem = { id: number; thumbnail: string | null }
type ImageItem = LocalImageItem | RemoteImageItem

const props = defineProps<{
  field: SurveyField
  disabled?: boolean
}>()

const modelValue = defineModel<ImageItem[]>({ default: () => [] })
const inputId = useId()
const fileInput = ref<HTMLInputElement | null>(null)

const openFilePicker = () => fileInput.value?.click()

const maxImages = computed(() => props.field.validation?.maxItems ?? 5)
const atMax = computed(() => modelValue.value.length >= maxImages.value)

const previewSrc = (item: ImageItem): string | null => {
  if ("file" in item) return `data:image/jpeg;base64,${item.file}`
  if (item.thumbnail) return `data:image/jpeg;base64,${item.thumbnail}`
  return null
}

const fileToBase64 = (file: File): Promise<LocalImageItem> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const dataUrl = reader.result as string
      resolve({ file: dataUrl.split(",")[1] })
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })

const handleChange = async (event: Event) => {
  const files = (event.target as HTMLInputElement).files
  if (!files) return
  const remaining = maxImages.value - modelValue.value.length
  const toProcess = Array.from(files).slice(0, remaining)
  const newItems = await Promise.all(toProcess.map(fileToBase64))
  modelValue.value = [...modelValue.value, ...newItems]
  if (fileInput.value) fileInput.value.value = ""
}

const removeItem = (index: number) => {
  modelValue.value = modelValue.value.filter((_, i) => i !== index)
}
</script>

<template>
  <div class="mb-6">
    <p class="fr-label mb-1!">{{ field.label }}</p>
    <p v-if="field.ui?.hint" class="fr-hint-text mb-2">{{ field.ui.hint }}</p>

    <div v-if="modelValue.length" class="grid grid-cols-2 gap-2 mb-4">
      <div
        v-for="(item, index) in modelValue"
        :key="index"
        class="relative rounded overflow-hidden border border-slate-200 aspect-square"
      >
        <img
          v-if="previewSrc(item)"
          :src="previewSrc(item)!"
          class="w-full h-full object-cover"
          alt=""
        />
        <div
          v-else
          class="w-full h-full bg-slate-100 flex items-center justify-center"
        >
          <v-icon name="ri-image-line" scale="2" class="text-slate-400" />
        </div>
        <DsfrButton
          v-if="!disabled"
          icon-only
          icon="ri-close-circle-fill"
          class="absolute top-1 right-1 bg-white/80!"
          secondary
          @click="removeItem(index)"
          :aria-label="`Supprimer la photo ${index + 1}`"
        />
      </div>
    </div>

    <template v-if="!atMax && !disabled">
      <input
        :id="inputId"
        ref="fileInput"
        type="file"
        accept="image/*"
        multiple
        class="sr-only"
        @change="handleChange"
      />
      <DsfrButton
        type="button"
        secondary
        icon="ri-image-add-line"
        :label="`Ajouter une photo (${modelValue.length} / ${maxImages})`"
        @click="openFilePicker"
      />
    </template>

    <p v-if="atMax" class="fr-info-text">
      Maximum de {{ maxImages }} photo(s) atteint
    </p>
  </div>
</template>
