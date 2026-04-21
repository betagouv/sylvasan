<script setup lang="ts">
import { computed, ref } from "vue"
import type { DsfrButtonProps } from "@gouvminint/vue-dsfr"
import type { SurveyField } from "@shared-types/survey"
import { typeWidgetMapping } from "./mappings"
import type { WidgetData } from "./mappings"
import NewFieldModal from "./NewFieldModal.vue"

const widgetData = computed(() =>
  field.ui?.widget
    ? (typeWidgetMapping[field.ui.widget] as WidgetData)
    : undefined
)
const icon = computed(() => widgetData.value?.icon)
const label = computed(() => widgetData.value?.label)

const { field } = defineProps<{ field: SurveyField }>()
const emit = defineEmits([
  "delete",
  "moveUp",
  "moveDown",
  "addSubField",
  "removeSubField",
])

const confirmDeleteOpened = ref(false)
const subFieldModalOpened = ref(false)

const confirmDeleteActions: DsfrButtonProps[] = [
  {
    label: "Supprimer",
    onClick() {
      emit("delete")
      confirmDeleteOpened.value = false
    },
  },
  {
    label: "Annuler",
    secondary: true,
    onClick() {
      confirmDeleteOpened.value = false
    },
  },
]

const handleAddSubField = (subField: SurveyField) => {
  emit("addSubField", subField)
  subFieldModalOpened.value = false
}

const formatDate = (isoString: string): string => {
  return new Date(isoString).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  })
}
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
        <div
          :class="`border border-slate-100 px-1 rounded-full pt-1 field-${widgetData?.widget}`"
        >
          <v-icon :icon="icon" />
        </div>
        <h3 class="fr-text--sm mb-0!">{{ field.label }}</h3>
        <p class="fr-text--sm mb-0! text-gray-500">{{ label }}</p>
        <p class="mb-0! fr-text--sm italic text-gray-500" v-if="field.required">
          *Champ requis
        </p>
        <div class="grow"></div>
        <div class="font-mono text-gray-400">{{ field.id }}</div>
      </div>

      <!-- Champ text / numérique -->
      <div v-if="field.ui?.widget === 'input' || field.ui?.widget === 'number'">
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
      </div>

      <!-- Champ select -->
      <div v-if="field.ui?.widget === 'select'">
        <div class="flex gap-2" v-if="field.ui?.choices">
          <div>{{ field.ui.choices.length }} options</div>
        </div>
      </div>

      <!-- Champ Checkbox -->
      <div v-if="field.ui?.widget === 'checkboxes'">
        <div class="flex gap-2" v-if="field.ui?.choices">
          <div>{{ field.ui.choices.length }} options</div>
        </div>
      </div>

      <!-- Champ Date -->
      <div v-if="field.ui?.widget === 'date'">
        <div class="flex gap-2" v-if="field.ui?.hint">
          <div class="text-gray-500 text-medium">Aide</div>
          <div>{{ field.ui.hint }}</div>
        </div>
        <div class="flex gap-2" v-if="field.validation?.min">
          <div class="text-gray-500 text-medium">Date min</div>
          <div v-if="typeof field.validation.min === 'string'">
            {{ formatDate(field.validation.min) }}
          </div>
        </div>
        <div class="flex gap-2" v-if="field.validation?.max">
          <div class="text-gray-500 text-medium">Date max</div>
          <div v-if="typeof field.validation.max === 'string'">
            {{ formatDate(field.validation.max) }}
          </div>
        </div>
      </div>

      <!-- Champ Liste d'objets -->
      <div v-if="field.ui?.widget === 'array'">
        <div class="flex gap-2 mb-1" v-if="field.ui?.addLabel">
          <div class="text-gray-500 text-medium">Titre du bouton d'ajout</div>
          <div>{{ field.ui.addLabel }}</div>
        </div>
        <div class="flex gap-2 mb-1" v-if="field.validation?.minItems">
          <div class="text-gray-500 text-medium">No. min d'éléments</div>
          <div>{{ field.validation.minItems }}</div>
        </div>
        <div class="flex gap-2 mb-1" v-if="field.validation?.maxItems">
          <div class="text-gray-500 text-medium">No. max d'éléments</div>
          <div>{{ field.validation.maxItems }}</div>
        </div>

        <!-- Sub-fields list -->
        <div class="bg-slate-50 rounded border border-slate-200 p-3 mt-2">
          <p class="fr-text--sm text-gray-500 mb-2!">
            Sous-champs ({{ field.fields?.length ?? 0 }})
          </p>

          <div v-if="field.fields?.length" class="flex flex-col gap-2 mb-3">
            <div
              v-for="subField in field.fields"
              :key="subField.id"
              class="flex items-center justify-between bg-white border border-slate-100 rounded px-3 py-2"
            >
              <div class="flex items-center gap-2">
                <div
                  :class="`border border-slate-100 px-1 rounded-full pt-1 field-${subField.ui?.widget}`"
                >
                  <v-icon
                    :icon="
                      typeWidgetMapping[subField.ui?.widget ?? 'input']?.icon
                    "
                  />
                </div>
                <span class="fr-text--sm font-medium">{{
                  subField.label
                }}</span>
                <span class="fr-text--sm text-gray-400">
                  {{ typeWidgetMapping[subField.ui?.widget ?? "input"]?.label }}
                </span>
                <span class="font-mono text-xs text-gray-400">{{
                  subField.id
                }}</span>
              </div>
              <DsfrButton
                icon="ri-delete-bin-line"
                tertiary
                icon-only
                size="sm"
                @click="emit('removeSubField', subField.id)"
              />
            </div>
          </div>

          <DsfrButton
            label="Ajouter un sous-champ"
            icon="ri-add-circle-line"
            secondary
            size="sm"
            @click="subFieldModalOpened = true"
          />
        </div>

        <!-- NewFieldModal restricted to non-array types -->
        <NewFieldModal
          :opened="subFieldModalOpened"
          :exclude-widgets="['array']"
          @add="handleAddSubField"
          @close="subFieldModalOpened = false"
        />
      </div>
    </div>

    <div class="self-center end">
      <DsfrButton
        icon="ri-delete-bin-line"
        @click="confirmDeleteOpened = true"
        secondary
        icon-only
      />
    </div>

    <DsfrModal
      :opened="confirmDeleteOpened"
      title="Supprimer le champ ?"
      :is-alert="true"
      :actions="confirmDeleteActions"
      @close="confirmDeleteOpened = false"
    >
      <p>
        Êtes-vous sûr de vouloir supprimer le champ «
        <strong>{{ field.label }}</strong> » ?
      </p>
    </DsfrModal>
  </div>
</template>
