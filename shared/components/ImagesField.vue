<script setup lang="ts">
import { computed, onUnmounted, ref, useId, watch } from "vue"
import type {
  SurveyField,
  ImageItem,
  LocalImageItem,
} from "@shared-types/survey"
import ImageViewer from "./ImageViewer.vue"
import { compressBase64Image, compressFileImage } from "@shared-utils/image"

const props = defineProps<{
  field: SurveyField
  required?: boolean
  disabled?: boolean
  resolveImagePath?: (path: string) => Promise<string | null>
  captureImage?: () => Promise<LocalImageItem | null>
}>()

const emit = defineEmits<{
  busyChange: [value: boolean]
}>()

const modelValue = defineModel<ImageItem[]>({ default: () => [] })
const inputId = useId()
const fileInput = ref<HTMLInputElement | null>(null)

const openFilePicker = () => fileInput.value?.click()

const handleAddPhoto = async () => {
  if (props.captureImage) {
    compressing.value = true
    emit("busyChange", true)
    try {
      const item = await props.captureImage()
      if (item) modelValue.value = [...modelValue.value, item]
    } finally {
      compressing.value = false
      emit("busyChange", false)
    }
  } else {
    openFilePicker()
  }
}

const maxImages = computed(() => props.field.validation?.maxItems ?? 5)
const atMax = computed(() => modelValue.value.length >= maxImages.value)

const resolvedSrcs = ref<Record<string, string>>({})

watch(
  modelValue,
  async (items) => {
    if (!props.resolveImagePath) return
    for (const item of items) {
      if (!("type" in item) || resolvedSrcs.value[item.path]) continue
      const src = await props.resolveImagePath(item.path).catch(() => null)
      if (src) resolvedSrcs.value[item.path] = src
    }
  },
  { immediate: true }
)

const previewSrc = (item: ImageItem): string | null => {
  if ("type" in item) return resolvedSrcs.value[item.path] ?? null
  if ("file" in item) return `data:image/jpeg;base64,${item.file}`
  if (item.thumbnail) return `data:image/jpeg;base64,${item.thumbnail}`
  return null
}

const compressImage = async (file: File): Promise<LocalImageItem> => ({
  file: await compressFileImage(file),
})

const compressing = ref(false)
onUnmounted(() => {
  if (compressing.value) emit("busyChange", false)
})

const handleChange = async (event: Event) => {
  const files = (event.target as HTMLInputElement).files
  if (!files) return
  const remaining = maxImages.value - modelValue.value.length
  const toProcess = Array.from(files).slice(0, remaining)
  compressing.value = true
  emit("busyChange", true)
  try {
    const newItems = await Promise.all(toProcess.map(compressImage))
    modelValue.value = [...modelValue.value, ...newItems]
  } finally {
    compressing.value = false
    emit("busyChange", false)
    if (fileInput.value) fileInput.value.value = ""
  }
}

const removeItem = (index: number) => {
  modelValue.value = modelValue.value.filter((_, i) => i !== index)
}

const viewerOpen = ref(false)
const viewerIndex = ref(0)

const openViewer = (index: number) => {
  viewerIndex.value = index
  viewerOpen.value = true
}
</script>

<template>
  <div class="mb-6">
    <p class="fr-label mb-1!">
      {{ field.label }}
      <span v-if="required" class="required"> *</span>
    </p>
    <p v-if="field.ui?.hint" class="fr-hint-text mb-2">{{ field.ui.hint }}</p>

    <div v-if="modelValue.length" class="grid grid-cols-3 gap-2 mb-4">
      <div
        v-for="(item, index) in modelValue"
        :key="index"
        class="relative rounded overflow-hidden border border-slate-200 aspect-square cursor-pointer"
        @click.stop="openViewer(index)"
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
          icon="ri-delete-bin-line"
          class="absolute top-1 right-1 bg-white/90! rounded-full"
          secondary
          @click.stop="removeItem(index)"
          :aria-label="`Supprimer la photo ${index + 1}`"
        />
      </div>
    </div>

    <template v-if="!atMax && !disabled">
      <input
        v-if="!captureImage"
        :id="inputId"
        ref="fileInput"
        type="file"
        accept="image/*"
        class="sr-only"
        :aria-required="required ?? false"
        @change="handleChange"
      />
      <DsfrButton
        type="button"
        secondary
        icon="ri-image-add-line"
        :label="`Ajouter une photo (${modelValue.length} / ${maxImages})`"
        :disabled="compressing"
        @click="handleAddPhoto"
      />
      <p v-if="compressing" class="fr-hint-text my-4!">
        Merci de patienter, l'image est en cours d'optimisation...
      </p>
    </template>

    <p v-if="atMax" class="fr-info-text">
      Maximum de {{ maxImages }} photo(s) atteint
    </p>
  </div>

  <ImageViewer
    :images="modelValue"
    :startIndex="viewerIndex"
    :opened="viewerOpen"
    :resolvedSrcs="resolvedSrcs"
    @close="viewerOpen = false"
  />
</template>
