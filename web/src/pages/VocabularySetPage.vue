<route lang="json">
{
  "path": "/referentiels",
  "meta": {
    "authenticationRequired": true,
    "title": "Mes référentiels",
    "defaultQueryParams": {
      "page": 1,
      "limit": 30,
      "organisation": "",
      "triage": "code",
      "recherche": ""
    }
  }
}
</route>

<script setup lang="ts">
import { useApiFetch } from "../utils/data-fetching"
import { computed, watch, ref } from "vue"
import ProgressSpinner from "../components/ProgressSpinner.vue"
import { useRouter, useRoute } from "vue-router"
import type { Organisation } from "@shared-types/api"
import type { VocabularySet } from "@shared-types/survey"
import PaginationSizeSelect from "../components/PaginationSizeSelect.vue"
import VocabularySetOrderingFilter from "../components/VocabularySetOrderingFilter.vue"
import VocabularyModal from "../components/SurveyBuilder/VocabularyModal.vue"
import VocabularySetCreationModal from "../components/VocabularySetPage/VocabularySetCreationModal.vue"

const router = useRouter()
const route = useRoute()

const limit = computed(() => parseInt(route.query.limit as string))
const page = computed(() => parseInt(route.query.page as string))
const offset = computed(() => (page.value - 1) * limit.value)
const ordering = computed(() => route.query.triage as string)
const organisationFilter = computed(
  () => (route.query.organisation as string) ?? ""
)
const searchTerm = ref(route.query.recherche || "")

const filterParams = computed(() => {
  const params = new URLSearchParams()
  if (ordering.value) params.set("ordering", String(ordering.value))
  if (organisationFilter.value)
    params.set("organisation", organisationFilter.value)
  return params
})

const url = computed(() => {
  const params = new URLSearchParams(filterParams.value)
  params.set("limit", String(limit.value))
  params.set("offset", String(offset.value))
  params.set("search", String(searchTerm.value))
  return `/admin/vocabularies/?${params.toString()}`
})

type PaginatedVocabularySet = {
  count: number
  results: VocabularySet[]
  organisations: Organisation[] | undefined
}

const { data, execute, isFetching } = useApiFetch(url)
  .get()
  .json<PaginatedVocabularySet>()

const totalPages = computed(() =>
  data.value ? Math.ceil(data.value.count / limit.value) : 0
)
const pages = computed(() =>
  Array.from({ length: totalPages.value }, (_, i) => ({
    label: String(i + 1),
    title: `Page ${i + 1}`,
    href: `${route.path}?page=${i + 1}`,
  }))
)

const updateQuery = (newQuery: Record<string, string | number>) =>
  router.push({ query: { ...route.query, ...newQuery } })

const updateLimit = (newValue: number) =>
  updateQuery({ limit: newValue, page: 1 })
const updatePage = (newPage: number) => updateQuery({ page: newPage + 1 })
const updateOrdering = (value: string) => updateQuery({ triage: value })
const updateOrganisation = (value: string) =>
  updateQuery({ organisation: value, page: 1 })
const updateSearch = () => updateQuery({ recherche: String(searchTerm.value) })

const hasActiveFilters = computed(() => !!organisationFilter.value)

const fetchResults = async () => {
  await execute()
  // TODO  <- Gestion d'erreur
}

const rows = computed(() =>
  (data.value?.results ?? []).map((vocabularySet: VocabularySet) => ({
    rowData: [
      {
        component: "router-link",
        text: vocabularySet.code,
        class: "font-bold",
        to: {
          name: "/VocabularySetDetailPage",
          params: { id: vocabularySet.id },
        },
      },
      vocabularySet.name,
      {
        component: VocabularyModal,
        vocabulary: vocabularySet,
        icon: "ri-list-check",
        showCount: true,
      },
      vocabularySet.organisationName,
    ],
  }))
)

const headers = [
  { text: "ID", headerAttrs: { id: "th-id" } },
  { text: "Titre", headerAttrs: { id: "th-title" } },
  { text: "Entrées", headerAttrs: { id: "th-entries" } },
  { text: "Organisation", headerAttrs: { id: "th-organisation" } },
]

const clearSearchIfEmpty = () => {
  if (!searchTerm.value) updateSearch()
}

watch(() => route.query, fetchResults)

const addModalOpen = ref(false)
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/dashboard', text: 'Dashboard' },
        { text: 'Mes référentiels' },
      ]"
    />
    <div>
      <div class="flex mb-4">
        <h1 class="fr-h4 grow mb-0!">Mes référentiels</h1>
        <DsfrButton
          label="Ajouter un référentiel"
          size="md"
          icon="ri-add-line"
          @click="addModalOpen = true"
        />
      </div>
      <div class="filters border mb-2 rounded border-gray-300 p-4">
        <div class="mb-6 max-w-lg">
          <DsfrSearchBar
            @search="updateSearch"
            v-model="searchTerm"
            @update:modelValue="clearSearchIfEmpty"
          />
        </div>
        <div class="flex gap-8">
          <div>
            <DsfrInputGroup>
              <DsfrSelect
                label="Organisation"
                :model-value="organisationFilter"
                :options="[
                  { value: '', text: 'Tous les référentiels' },
                  ...(data?.organisations ?? []).map((s) => ({
                    value: String(s.id),
                    text: s.name,
                  })),
                ]"
                class="text-sm!"
                @update:modelValue="updateOrganisation"
              />
            </DsfrInputGroup>
          </div>

          <PaginationSizeSelect
            :modelValue="limit"
            @update:modelValue="updateLimit"
          />
          <VocabularySetOrderingFilter
            :model-value="ordering"
            @update:modelValue="updateOrdering"
          />

          <div class="grow"></div>
          <p v-if="data?.count" class="fr-text--sm text-stone-500 mb-0!">
            {{ data.count }} référentiels au total
          </p>
        </div>
      </div>
      <div v-if="isFetching" class="flex justify-center my-20">
        <ProgressSpinner />
      </div>
      <div v-else>
        <div
          v-if="data && !data.results.length"
          class="border rounded border-slate-200 p-10 mb-10"
        >
          <p class="text-stone-500 italic mb-0!">
            <template v-if="hasActiveFilters"
              >Aucun référentiel ne correspond aux filtres
              sélectionnés</template
            >
            <template v-else>Aucun référentiel n'a été créée</template>
          </p>
        </div>
        <template v-else-if="data?.results.length">
          <DsfrTable :rows="rows" :headers="headers" />
          <div class="flex" v-if="totalPages > 1">
            <DsfrPagination
              :pages="pages"
              :current-page="page - 1"
              @update:currentPage="updatePage"
            />
            <div class="grow"></div>
            <div>
              <p v-if="data.count" class="fr-text--sm text-stone-500">
                {{ data.count }} enquêtes au total
              </p>
            </div>
          </div>
        </template>
      </div>
    </div>

    <VocabularySetCreationModal
      :opened="addModalOpen"
      @close="addModalOpen = false"
    />
  </div>
</template>

<style scoped>
.fr-table :deep(table) {
  @apply table!;
}

.filters :deep(.fr-input-group) {
  margin-bottom: 0;
}
.filters :deep(.fr-select-group) {
  margin-bottom: 0;
}
</style>
