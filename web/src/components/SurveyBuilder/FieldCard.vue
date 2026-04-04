<script setup lang="ts">
import { computed } from "vue"
import type { SurveyField } from "@shared-types/survey"
import { typeWidgetMapping } from "./mappings"
import type { WidgetData } from "./mappings"

const widgetData = computed(() =>
  field.ui?.widget
    ? (typeWidgetMapping[field.ui.widget] as WidgetData)
    : undefined
)
const icon = computed(() => widgetData.value?.icon)
const color = computed(() => widgetData.value?.color)
const label = computed(() => widgetData.value?.label)

const { field } = defineProps<{ field: SurveyField }>()
const emit = defineEmits(["delete", "moveUp", "moveDown"])
</script>

<template>
  <div class="rounded bg-white border border-slate-50 p-4 flex gap-6">
    <div class="flex flex-col gap-2 items-center justify-center">
      <DsfrButton
        icon-only
        @click="emit('moveUp')"
        tertiary
        icon="ri-arrow-up-line"
      />
      <DsfrButton
        icon-only
        @click="emit('moveDown')"
        tertiary
        icon="ri-arrow-down-line"
      />
    </div>
    <div class="flex flex-col grow border-r border-slate-300 pr-4">
      <div class="flex gap-2 items-end mb-4">
        <h3
          :class="`fr-text--sm mb-0! border border-slate-100 px-1 rounded pt-1 field-${widgetData?.widget}`"
        >
          <v-icon :icon="icon" /> {{ field.label }}
        </h3>

        <p class="fr-text--sm mb-0!">{{ widgetData?.label }}</p>
        <p class="mb-0! fr-text--sm italic text-gray-500" v-if="field.required">
          *Champ requis
        </p>
        <div class="grow"></div>
        <div class="font-mono text-gray-400">{{ field.id }}</div>
      </div>

      <!-- Champ text / numérique -->

      <div
        v-if="field.ui?.widget === 'input' || field.ui?.widget === 'number'"
      ></div>
      <div class="flex gap-2" v-if="field.ui?.placeholder">
        <div class="text-gray-500 text-medium">Placeholder</div>
        <div>{{ field.ui.placeholder }}</div>
      </div>
      <div class="flex gap-2" v-if="field.ui?.hint">
        <div class="text-gray-500 text-medium">Aide</div>
        <div>{{ field.ui.hint }}</div>
      </div>
      <div v-if="field.ui?.widget === 'number'">
        <div class="flex gap-2" v-if="field.validation?.min">
          <div class="text-gray-500 text-medium">Valeur min.</div>
          <div>{{ field.validation.min }}</div>
        </div>

        <div class="flex gap-2" v-if="field.validation?.max">
          <div class="text-gray-500 text-medium">Valeur max.</div>
          <div>{{ field.validation.max }}</div>
        </div>
      </div>
      <!-- Champ select -->
      <div v-if="field.ui?.widget === 'select'">
        <div class="flex gap-2" v-if="field.ui?.choices">
          <div>{{ field.ui.choices.length }} options</div>
        </div>
      </div>
    </div>

    <div class="self-center end">
      <DsfrButton
        icon="ri-delete-bin-line"
        @click="emit('delete')"
        secondary
        icon-only
      />
    </div>
  </div>
</template>

<style scoped>
@reference "../../styles.css";

.field-input {
  @apply bg-[#ececfe];
}
.field-number {
  @apply bg-[#fee9e9];
}
.field-select {
  @apply bg-[#dffee6];
}
.field-checkbox {
  @apply bg-slate-50;
}
.field-textarea {
  @apply bg-slate-50;
}
.field-radio {
  @apply bg-slate-50;
}
.field-date {
  @apply bg-slate-50;
}
</style>
