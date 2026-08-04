<script setup lang="ts">
import { computed, onUnmounted, ref, useId, watch } from "vue"
import type {
  SurveyField,
  ImageItem,
  LocalImageItem,
} from "@shared-types/survey"
import ImageViewer from "./ImageViewer.vue"

const props = defineProps<{
  field: SurveyField
  required?: boolean
  disabled?: boolean
  resolveImagePath?: (path: string) => Promise<string | null>
}>()

const emit = defineEmits<{
  busyChange: [value: boolean]
}>()

const modelValue = defineModel<ImageItem[]>({ default: () => [] })
const inputId = useId()
const fileInput = ref<HTMLInputElement | null>(null)

const openFilePicker = () => fileInput.value?.click()

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

const MAX_DIM = 2000
const MAX_BYTES = 2 * 1024 * 1024

const compressImage = (file: File): Promise<LocalImageItem> =>
  new Promise((resolve, reject) => {
    const img = new Image()
    const objectUrl = URL.createObjectURL(file)

    img.onerror = () => {
      URL.revokeObjectURL(objectUrl)
      reject(new Error("Lecture image échouée"))
    }
    img.onload = async () => {
      URL.revokeObjectURL(objectUrl)

      // D'abord on redimensione l'image pour s'assurer que le côté le plus grand est ≤ MAX_DIM
      let { width, height } = img
      if (Math.max(width, height) > MAX_DIM) {
        if (width >= height) {
          height = Math.round((height / width) * MAX_DIM)
          width = MAX_DIM
        } else {
          width = Math.round((width / height) * MAX_DIM)
          height = MAX_DIM
        }
      }

      const canvas = document.createElement("canvas")
      canvas.width = width
      canvas.height = height
      canvas.getContext("2d")!.drawImage(img, 0, 0, width, height)

      // Puis on réduit graduellement la qualité jusqu'à arriver sous la taille MAX_BYTES
      let quality = 0.85
      let blob: Blob
      while (true) {
        blob = await new Promise<Blob>((res, rej) =>
          canvas.toBlob(
            (b) => (b ? res(b) : rej(new Error("Compression échouée"))),
            "image/jpeg",
            quality
          )
        )
        if (blob.size <= MAX_BYTES || quality <= 0.1) break
        quality = Math.max(0.1, quality - 0.1)
      }

      const reader = new FileReader()
      reader.onerror = reject
      reader.onload = () =>
        resolve({ file: (reader.result as string).split(",")[1] })
      reader.readAsDataURL(blob)
    }

    img.src = objectUrl
  })

const compressing = ref(false)
watch(compressing, (val) => emit("busyChange", val))
onUnmounted(() => {
  if (compressing.value) emit("busyChange", false)
})

const handleChange = async (event: Event) => {
  const files = (event.target as HTMLInputElement).files
  if (!files) return
  const remaining = maxImages.value - modelValue.value.length
  const toProcess = Array.from(files).slice(0, remaining)
  compressing.value = true
  try {
    const newItems = await Promise.all(toProcess.map(compressImage))
    modelValue.value = [...modelValue.value, ...newItems]
  } finally {
    compressing.value = false
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
        @click="openFilePicker"
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
