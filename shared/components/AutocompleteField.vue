<script setup lang="ts">
import { ref, computed } from "vue"
import type { VocabularyEntry } from "@shared-types/survey"

const props = defineProps<{
  entries: VocabularyEntry[]
  label: string
  required?: boolean
  disabled?: boolean
  hint?: string
  placeholder?: string
  errorMessage?: string
}>()

const modelValue = defineModel<string>()

const query = ref("")
const isOpen = ref(false)
const highlightedIndex = ref(-1)
const listRef = ref<HTMLUListElement | null>(null)
const containerRef = ref<HTMLElement | null>(null)
const dropdownStyle = ref({ top: "0px", left: "0px", width: "0px" })

const updateDropdownPosition = () => {
  const rect = containerRef.value?.getBoundingClientRect()
  if (!rect) return
  dropdownStyle.value = {
    top: `${rect.bottom}px`,
    left: `${rect.left}px`,
    width: `${rect.width}px`,
  }
}

const normalize = (s: string) =>
  s
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")

const filtered = computed(() => {
  if (!query.value) return props.entries.slice(0, 20)
  const q = normalize(query.value)
  return props.entries
    .filter(
      (e) => normalize(e.label).includes(q) || normalize(e.code).includes(q)
    )
    .slice(0, 20)
})

const selectedLabel = computed(
  () => props.entries.find((e) => e.code === modelValue.value)?.label ?? ""
)

const select = (entry: VocabularyEntry) => {
  modelValue.value = entry.code
  query.value = entry.label
  isOpen.value = false
  highlightedIndex.value = -1
}

// Si le modelValue est pre-rempli on selectionne l'option
if (modelValue.value) {
  const selectedEntry = props.entries.find((x) => x.code === modelValue.value)
  if (selectedEntry) select(selectedEntry)
}

const onFocus = () => {
  query.value = selectedLabel.value
  isOpen.value = true
  updateDropdownPosition()
}

// @mousedown.prevent dans la liste maintient le focus dans l'input, blur n'est
// déclenché que quand l'utilisateur clique ailleurs ou fait Tab
const onBlur = () => {
  isOpen.value = false
  highlightedIndex.value = -1
  if (!query.value) {
    modelValue.value = undefined
  } else {
    query.value = selectedLabel.value
  }
}

const scrollToHighlighted = () => {
  if (!listRef.value || highlightedIndex.value < 0) return
  const item = listRef.value.children[highlightedIndex.value] as HTMLElement
  item?.scrollIntoView({ block: "nearest" })
}

const onKeydown = (e: KeyboardEvent) => {
  if (e.key === "ArrowDown") {
    e.preventDefault()
    if (!isOpen.value) {
      isOpen.value = true
      return
    }
    highlightedIndex.value = Math.min(
      highlightedIndex.value + 1,
      filtered.value.length - 1
    )
    scrollToHighlighted()
  } else if (e.key === "ArrowUp") {
    e.preventDefault()
    if (highlightedIndex.value > 0) {
      highlightedIndex.value--
      scrollToHighlighted()
    }
  } else if (e.key === "Enter" && isOpen.value) {
    e.preventDefault()
    const entry = filtered.value[highlightedIndex.value]
    if (entry) select(entry)
  } else if (e.key === "Escape") {
    ;(e.target as HTMLElement).blur()
  }
}
</script>

<template>
  <div>
    <DsfrInputGroup :class="errorMessage ? 'fr-input-group--error' : ''">
      <div ref="containerRef" class="relative">
        <div class="flex items-end">
          <div class="grow">
            <DsfrInput
              v-model="query"
              :label="label"
              :required="required ?? false"
              :label-visible="true"
              :hint="hint"
              :disabled="disabled"
              :placeholder="placeholder"
              autocomplete="off"
              @focus="onFocus"
              @blur="onBlur"
              @keydown="onKeydown"
              @update:model-value="
                () => {
                  isOpen = true
                  highlightedIndex = -1
                }
              "
            />
          </div>
          <v-icon icon="ri-search-line" class="mb-3 mx-2" />
        </div>
      </div>
      <p v-if="errorMessage" class="fr-error-text">{{ errorMessage }}</p>
    </DsfrInputGroup>

    <Teleport to="body">
      <ul
        v-if="isOpen && filtered.length"
        ref="listRef"
        :style="dropdownStyle"
        class="fixed z-[9999] bg-white border border-slate-200 rounded shadow-md max-h-60 overflow-y-auto pl-0!"
        role="listbox"
      >
        <li
          v-for="(entry, i) in filtered"
          :key="entry.code"
          class="px-4 pt-4! pb-4! cursor-pointer fr-text--sm mb-0! list-none"
          :class="i === highlightedIndex ? 'bg-blue-50' : 'hover:bg-slate-100'"
          role="option"
          :aria-selected="i === highlightedIndex"
          @mousedown.prevent="select(entry)"
        >
          <span class="font-medium">{{ entry.label }}</span>
          <span class="text-gray-400 ml-2 font-mono text-xs">{{
            entry.code
          }}</span>
        </li>
      </ul>
    </Teleport>
  </div>
</template>
