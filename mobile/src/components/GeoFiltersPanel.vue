<script setup lang="ts">
import { ref, computed, watch } from "vue"
import type { DsfrButtonProps } from "@gouvminint/vue-dsfr"
import type { Survey } from "@shared-types/survey"
import type { GeoFilters } from "../composables/useGeoPins"

const props = defineProps<{
  modelValue: GeoFilters
  surveys: Survey[]
}>()

const emit = defineEmits<{
  "update:modelValue": [value: GeoFilters]
  apply: []
  close: []
}>()

const draft = ref<GeoFilters>({
  ...props.modelValue,
  surveyIds: [...props.modelValue.surveyIds],
})

watch(
  () => props.modelValue,
  (v) => {
    draft.value = { ...v, surveyIds: [...v.surveyIds] }
  }
)

const periodGroupId = ref<string | undefined>("periode")
const typesGroupId = ref<string | undefined>("types")

const periodTitle = computed(() =>
  draft.value.period !== null ? "Période (1)" : "Période"
)
const typesTitle = computed(() =>
  draft.value.surveyIds.length > 0
    ? `Types d'observation (${draft.value.surveyIds.length})`
    : "Types d'observation"
)

const currentYear = new Date().getFullYear()
const yearOptions = Array.from({ length: 7 }, (_, i) => currentYear - i)

type PeriodOption = "12months" | number

const periodTags = computed(() => [
  {
    label: "12 derniers mois",
    selectable: true,
    value: "12months" as PeriodOption,
  },
  ...yearOptions.map((y) => ({
    label: String(y),
    selectable: true,
    value: y as PeriodOption,
  })),
])

// DsfrTags gère un tableau, mais la période est à choix unique.
// Le setter impose l'exclusivité : si deux options sont présentes, on garde
// uniquement la nouvelle (celle qui diffère de la sélection précédente).
const periodSelection = computed<PeriodOption[]>({
  get: () =>
    draft.value.period !== null ? [draft.value.period as PeriodOption] : [],
  set: (newVal) => {
    if (newVal.length === 0) {
      draft.value.period = null
    } else {
      draft.value.period =
        newVal.find((v) => v !== draft.value.period) ?? newVal[0]
    }
  },
})

const surveyOptions = computed(() =>
  props.surveys.map((s) => ({ label: s.title, value: s.id }))
)

const activeCount = computed(() => {
  let n = 0
  if (draft.value.onlyMine) n++
  if (draft.value.period !== null) n++
  if (draft.value.surveyIds.length > 0) n++
  return n
})

const hasDraftChanges = computed(() => {
  const m = props.modelValue
  if (draft.value.onlyMine !== m.onlyMine) return true
  if (draft.value.period !== m.period) return true
  const sortedDraft = [...draft.value.surveyIds].sort().join(",")
  const sortedModel = [...m.surveyIds].sort().join(",")
  return sortedDraft !== sortedModel
})

const confirmCloseOpen = ref(false)

const tryClose = () => {
  if (hasDraftChanges.value) {
    confirmCloseOpen.value = true
  } else {
    emit("close")
  }
}

const reset = () => {
  draft.value = { surveyIds: [], period: null, onlyMine: false }
}

const apply = () => {
  emit("update:modelValue", {
    ...draft.value,
    surveyIds: [...draft.value.surveyIds],
  })
  emit("apply")
  emit("close")
}

const confirmCloseActions: DsfrButtonProps[] = [
  {
    label: "Appliquer et fermer",
    onClick: () => {
      confirmCloseOpen.value = false
      apply()
    },
  },
  {
    label: "Fermer sans appliquer",
    secondary: true,
    onClick: () => {
      confirmCloseOpen.value = false
      emit("close")
    },
  },
]
</script>

<template>
  <div class="filters-panel absolute inset-0 z-50 flex flex-col bg-[#f0f0ff]">
    <!-- Header -->
    <div
      class="filters-header flex items-center justify-between px-5 pb-4 bg-[#f0f0ff]"
    >
      <h2 class="fr-h4 mb-0!">Filtres</h2>
      <button
        class="flex items-center gap-1 text-sm font-medium"
        @click="tryClose"
      >
        Fermer
        <v-icon name="ri-close-line" />
      </button>
    </div>

    <!-- Zone scrollable -->
    <div class="flex-1 overflow-y-auto px-4 pb-4 flex flex-col gap-3">
      <!-- Toggle: mes observations uniquement -->
      <div class="bg-white rounded-lg px-4 py-3">
        <DsfrToggleSwitch
          label="Ne voir que mes observations"
          v-model="draft.onlyMine"
        />
      </div>

      <div class="bg-white rounded-lg box-border!">
        <!-- Période -->
        <DsfrAccordionsGroup v-model="periodGroupId">
          <DsfrAccordion id="periode" :title="periodTitle">
            <div class="p-2 pb-0">
              <DsfrTags v-model="periodSelection" :tags="periodTags" />
            </div>
          </DsfrAccordion>
        </DsfrAccordionsGroup>

        <!-- Types d'observation -->
        <DsfrAccordionsGroup v-model="typesGroupId">
          <DsfrAccordion id="types" :title="typesTitle">
            <DsfrCheckboxSet
              class="p-2 pb-0"
              v-if="surveys.length > 0"
              v-model="draft.surveyIds"
              :options="surveyOptions"
              legend=""
            />
            <p v-else class="py-2 text-sm text-stone-400 italic">
              Aucun type d'observation disponible
            </p>
          </DsfrAccordion>
        </DsfrAccordionsGroup>
      </div>
    </div>

    <!-- Confirmation de fermeture sans appliquer -->
    <DsfrModal
      :opened="confirmCloseOpen"
      title="Modifications non appliquées"
      :is-alert="true"
      :actions="confirmCloseActions"
      @close="confirmCloseOpen = false"
      class="box-border!"
    >
      Des modifications ont été effectuées mais pas encore appliquées. Que
      souhaitez-vous faire ?
    </DsfrModal>

    <!-- Footer -->
    <div
      class="filters-footer flex gap-3 px-4 bg-white border-t border-slate-200"
    >
      <DsfrButton
        label="Réinitialiser"
        secondary
        class="flex-1"
        :disabled="activeCount === 0"
        @click="reset"
      />
      <DsfrButton label="Appliquer les filtres" class="flex-1" @click="apply" />
    </div>
  </div>
</template>

<style scoped>
.filters-panel {
  padding-top: env(safe-area-inset-top);
}

.filters-header {
  padding-top: max(1.25rem, env(safe-area-inset-top));
}

.filters-footer {
  padding-top: 1rem;
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
}
</style>
