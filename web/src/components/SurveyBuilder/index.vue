<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue"
import type {
  SurveySchema,
  SurveyField,
  SurveyPage,
} from "@shared-types/survey"
import SurveyRenderer from "@shared-components/SurveyRenderer.vue"
import NewFieldModal from "./NewFieldModal.vue"
import FieldCard from "./FieldCard.vue"

const schema = defineModel<SurveySchema>({ required: true })

const activeTab = ref(0)
const modalOpened = ref(false)
const tabsRef = ref<HTMLElement | null>(null)

// S'il n'y a pas de pages, on en instantie une par défaut
if (!schema.value.pages || schema.value.pages.length === 0) {
  schema.value = {
    ...schema.value,
    pages: [{ id: "page_1", title: "Page 1", fields: [] }],
  }
}

// NOTE: cette fonction sert à éviter un bug d'affichage qui survient lors qu'un élément
// à l'intérieur d'un tab change de taille (comme le field card)
const forceTabsHeightRecalc = async () => {
  await nextTick()
  const tabsEl = tabsRef.value?.querySelector(".fr-tabs") as HTMLElement | null
  if (!tabsEl) return
  tabsEl.style.removeProperty("--tabs-height")
  await nextTick()
  const panel = tabsEl.querySelector(
    ".fr-tabs__panel--selected"
  ) as HTMLElement | null
  if (panel) {
    tabsEl.style.setProperty("--tabs-height", `${panel.scrollHeight + 56}px`)
  }
}

const tabTitles = computed(() =>
  (schema.value.pages ?? []).map((page, index) => ({
    title: page.title ?? `Page ${index + 1}`,
    tabId: `tab-${page.id}`,
    panelId: `panel-${page.id}`,
  }))
)

const activePageId = computed(
  () => schema.value.pages?.[activeTab.value]?.id ?? null
)

const activePageFields = computed(() => {
  const page = schema.value.pages?.[activeTab.value]
  if (!page) return []
  return page.fields
    .map((fid) => schema.value.fields.find((f) => f.id === fid))
    .filter((f): f is SurveyField => f !== undefined)
})

const previewSchema = computed<SurveySchema>(() => ({
  ...schema.value,
  fields: activePageFields.value,
  pages: undefined,
}))

const addPage = async () => {
  const newPage: SurveyPage = {
    id: `page_${Date.now()}`, // ID unique même pour éviter de réutiliser des pages supprimées
    title: `Page ${(schema.value.pages?.length ?? 0) + 1}`,
    fields: [],
  }
  schema.value = {
    ...schema.value,
    pages: [...(schema.value.pages ?? []), newPage],
  }

  await nextTick()

  activeTab.value = (schema.value.pages?.length ?? 1) - 1
}

const deletePage = async (pageId: string) => {
  const pages = schema.value.pages ?? []
  if (pages.length <= 1) return

  // On enlève les champs de cette page
  const pageToDelete = pages.find((p) => p.id === pageId)
  const fieldIdsToRemove = new Set(pageToDelete?.fields ?? [])

  schema.value = {
    ...schema.value,
    fields: schema.value.fields.filter((f) => !fieldIdsToRemove.has(f.id)),
    pages: pages.filter((p) => p.id !== pageId),
  }

  await nextTick()

  // Si on a supprimé la dernière page, on change l'active page à la précédente
  if (activeTab.value >= (schema.value.pages?.length ?? 1)) {
    activeTab.value = (schema.value.pages?.length ?? 1) - 1
  }
}

const addField = async (field: SurveyField) => {
  if (!activePageId.value) return
  schema.value = {
    ...schema.value,
    fields: [...schema.value.fields, field],
    pages: schema.value.pages?.map((p) =>
      p.id === activePageId.value
        ? { ...p, fields: [...p.fields, field.id] }
        : p
    ),
  }
  closeModal()
  await forceTabsHeightRecalc()
}

const removeField = async (fieldId: string) => {
  schema.value = {
    ...schema.value,
    fields: schema.value.fields.filter((f) => f.id !== fieldId),
    pages: schema.value.pages?.map((p) => ({
      ...p,
      fields: p.fields.filter((fid) => fid !== fieldId),
    })),
  }
  await forceTabsHeightRecalc()
}

const moveFieldUp = (fieldId: string) => {
  const page = schema.value.pages?.find((p) => p.id === activePageId.value)
  if (!page) return

  const fieldIds = [...page.fields]
  const index = fieldIds.indexOf(fieldId)
  if (index <= 0) return
  ;[fieldIds[index - 1], fieldIds[index]] = [
    fieldIds[index],
    fieldIds[index - 1],
  ] // <- Destructuring pour faire un swap. Pas très lisible, p-e à refactorer
  schema.value = {
    ...schema.value,
    pages: schema.value.pages?.map((p) =>
      p.id === activePageId.value ? { ...p, fields: fieldIds } : p
    ),
  }
}

const moveFieldDown = (fieldId: string) => {
  const page = schema.value.pages?.find((p) => p.id === activePageId.value)
  if (!page) return
  const fieldIds = [...page.fields]
  const index = fieldIds.indexOf(fieldId)
  if (index === -1 || index >= fieldIds.length - 1) return
  ;[fieldIds[index], fieldIds[index + 1]] = [
    fieldIds[index + 1],
    fieldIds[index],
  ] // <- Destructuring pour faire un swap. Pas très lisible, p-e à refactorer
  schema.value = {
    ...schema.value,
    pages: schema.value.pages?.map((p) =>
      p.id === activePageId.value ? { ...p, fields: fieldIds } : p
    ),
  }
}

const closeModal = () => (modalOpened.value = false)

// Ceci sert à re-render le composant DsfrTabs pour éviter des bugs liés à
// l'ajout et suppression programmatique des tabs
const tabsKey = computed(() =>
  (schema.value.pages ?? []).map((p) => p.id).join(",")
)
</script>

<template>
  <div class="grid grid-cols-12 gap-4" ref="tabsRef">
    <div class="col-span-12 sm:col-span-6 md:col-span-7 lg:col-span-8">
      <DsfrTabs
        v-model="activeTab"
        tab-list-name="Pages de l'enquête"
        :key="tabsKey"
      >
        <template #tab-items>
          <DsfrTabItem
            v-for="(tab, index) in tabTitles"
            :key="`dsfrtabitem-${tab.tabId}`"
            :tab-id="tab.tabId"
            :panel-id="tab.panelId"
            @click="activeTab = index"
          >
            <span class="flex items-center gap-2">
              {{ tab.title }}
              <button
                v-if="tabTitles.length > 1"
                class="text-xs text-gray-400 hover:text-red-500 leading-none"
                title="Supprimer cette page"
                @click.stop="deletePage(schema.pages?.[index]?.id ?? '')"
              >
                ✕
              </button>
            </span>
          </DsfrTabItem>
          <!-- Add page button as a pseudo-tab -->
          <button
            class="fr-tabs__tab text-sm text-blue-700 hover:underline px-3"
            @click="addPage"
          >
            + Ajouter une page
          </button>
        </template>

        <DsfrTabContent
          v-for="(tab, index) in tabTitles"
          :key="`dsfrtabcontent-${tab.tabId}`"
          :panel-id="tab.panelId"
          :tab-id="tab.tabId"
        >
          <div class="bg-slate-100 rounded p-4">
            <TransitionGroup tag="div" name="field-list" class="mb-4">
              <FieldCard
                v-for="field in index === activeTab ? activePageFields : []"
                :key="`card-${field.id}`"
                :field="field"
                @move-up="moveFieldUp(field.id)"
                @move-down="moveFieldDown(field.id)"
                @delete="removeField(field.id)"
                class="mb-1"
              />
            </TransitionGroup>
            <div class="flex items-center justify-center mt-2">
              <DsfrButton
                label="Ajouter un champ"
                icon="ri-add-circle-line"
                @click="modalOpened = true"
                secondary
              />
            </div>
          </div>
        </DsfrTabContent>
      </DsfrTabs>

      <NewFieldModal
        @add="(f) => addField(f)"
        :opened="modalOpened"
        @close="closeModal"
      />
    </div>

    <!-- Preview -->
    <div class="col-span-12 sm:col-span-6 md:col-span-5 lg:col-span-4">
      <div
        v-if="activePageFields.length"
        class="border rounded border-slate-300 p-4"
      >
        <p class="text-sm text-gray-500 mb-2">
          Aperçu « {{ schema.pages?.[activeTab]?.title }} »
        </p>
        <SurveyRenderer :schema="previewSchema" :allowSubmit="false" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.field-list-move {
  transition: transform 0.25s ease;
}
</style>
