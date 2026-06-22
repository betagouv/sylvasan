<script setup lang="ts">
import { ref, computed, onUnmounted, nextTick } from "vue"
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
const dropdownStyle = ref<Record<string, string>>({})
const dropdownPositioned = ref(false)

const MAX_DROPDOWN_HEIGHT = 240

const updateDropdownPosition = () => {
  const rect = containerRef.value?.getBoundingClientRect()
  if (!rect) return

  const viewportHeight = window.visualViewport?.height ?? window.innerHeight
  const spaceBelow = viewportHeight - rect.bottom

  // Certaines plateformes (comme iOS) déplacent le document vers le haut lorsque
  // le clavier est affiché. Ce déplacement est donné par getBoundingClientRect (en
  // négatif) et doit être pris en compte pour la mesure de l'espace
  const bodyRectTop = Math.abs(document.body.getBoundingClientRect().top)

  // Petit espace approximatif per s'approcher de l'input en se mettant au dessus
  // du label
  const labelOffsetHeight = 24


  if ((spaceBelow + bodyRectTop) < MAX_DROPDOWN_HEIGHT) {
    dropdownStyle.value = {
      bottom: `${window.innerHeight - rect.top - labelOffsetHeight}px`,
      left: `${rect.left}px`,
      width: `${rect.width}px`,
    }
  } else {
    dropdownStyle.value = {
      top: `${rect.bottom + bodyRectTop}px`,
      left: `${rect.left}px`,
      width: `${rect.width}px`,
    }
  }
  dropdownPositioned.value = true
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

const addPositionListeners = () => {
  window.visualViewport?.addEventListener("resize", updateDropdownPosition)
  window.visualViewport?.addEventListener("scroll", updateDropdownPosition)
  window.addEventListener("resize", updateDropdownPosition)
}

const removePositionListeners = () => {
  window.visualViewport?.removeEventListener("resize", updateDropdownPosition)
  window.visualViewport?.removeEventListener("scroll", updateDropdownPosition)
  window.removeEventListener("resize", updateDropdownPosition)
}

const openDropdown = async () => {
  dropdownPositioned.value = false
  isOpen.value = true
  await nextTick()
  addPositionListeners()
  // Delai pour résoudre certaines lenteurs du render dans les téléphones
  setTimeout(updateDropdownPosition, navigator.maxTouchPoints > 0 ? 500 : 0)
}

const closeDropdown = () => {
  isOpen.value = false
  dropdownPositioned.value = false
  removePositionListeners()
}

onUnmounted(() => {
  removePositionListeners()
})

const select = (entry: VocabularyEntry) => {
  modelValue.value = entry.code
  query.value = entry.label
  closeDropdown()
  highlightedIndex.value = -1
}

// Si le modelValue est pre-rempli on selectionne l'option
if (modelValue.value) {
  const selectedEntry = props.entries.find((x) => x.code === modelValue.value)
  if (selectedEntry) select(selectedEntry)
}

const onFocus = async () => {
  query.value = selectedLabel.value
  await openDropdown()
}

// @mousedown.prevent dans la liste maintient le focus dans l'input, blur n'est
// déclenché que quand l'utilisateur clique ailleurs ou fait Tab
const onBlur = () => {
  closeDropdown()
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
      openDropdown()
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
                  openDropdown()
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
        :class="{ invisible: !dropdownPositioned }"
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
