<route lang="json">
{
  "path": "/enquetes",
  "meta": {
    "authenticationRequired": true,
    "title": "Mes enquêtes",
    "defaultQueryParams": {
      "page": 1,
      "limit": 10,
      "created_after": "",
      "created_before": "",
      "triage": "-creation_date",
      "organisation": ""
    }
  }
}
</route>

<script setup lang="ts">
import { useApiFetch } from "../utils/data-fetching"
import { computed, watch } from "vue"
import type { Organisation, SurveyDisplay } from "@shared-types/api"
import { useRouter, useRoute } from "vue-router"
import ProgressSpinner from "../components/ProgressSpinner.vue"
import PaginationSizeSelect from "../components/PaginationSizeSelect.vue"
import DateRangeFilter from "../components/DateRangeFilter.vue"
import OrderingFilter from "../components/OrderingFilter.vue"

const router = useRouter()
const route = useRoute()

const limit = computed(() => parseInt(route.query.limit as string))
const page = computed(() => parseInt(route.query.page as string))
const offset = computed(() => (page.value - 1) * limit.value)
const createdAfter = computed(() => (route.query.created_after as string) ?? "")
const createdBefore = computed(
  () => (route.query.created_before as string) ?? ""
)
const ordering = computed(() => route.query.triage as string)
const organisationFilter = computed(
  () => (route.query.organisation as string) ?? ""
)

const filterParams = computed(() => {
  const params = new URLSearchParams()
  if (createdAfter.value) params.set("created_after", createdAfter.value)
  if (createdBefore.value) params.set("created_before", createdBefore.value)
  if (ordering.value) params.set("ordering", String(ordering.value))
  if (organisationFilter.value)
    params.set("organisation", organisationFilter.value)
  return params
})

const url = computed(() => {
  const params = new URLSearchParams(filterParams.value)
  params.set("limit", String(limit.value))
  params.set("offset", String(offset.value))
  return `/surveys/?${params.toString()}`
})

type PaginatedSurvey = {
  count: number
  results: SurveyDisplay[]
  organisations: Organisation[] | undefined
}

const { data, execute, isFetching } = useApiFetch(url)
  .get()
  .json<PaginatedSurvey>()

const fetchSearchResults = async () => {
  await execute()
  // TODO  <- Gestion d'erreur
}

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

const rows = computed(() =>
  (data.value?.results ?? []).map((survey: SurveyDisplay) => ({
    rowData: [
      survey.id,
      {
        component: "router-link",
        text: survey.title,
        class: "font-bold",
        to: { name: "/SurveyPage", params: { id: survey.id } },
      },
      survey.organisationName,
      survey.poleName,
      new Date(survey.creationDate).toLocaleDateString("fr-FR", {
        day: "numeric",
        month: "long",
      }),
    ],
  }))
)

const headers = [
  { text: "ID", headerAttrs: { id: "th-id" } },
  { text: "Titre", headerAttrs: { id: "th-title" } },
  { text: "Organisation", headerAttrs: { id: "th-organisation" } },
  { text: "Pole", headerAttrs: { id: "th-pole" } },
  { text: "Date de création", headerAttrs: { id: "th-creation-date" } },
]

const updateQuery = (newQuery: Record<string, string | number>) =>
  router.push({ query: { ...route.query, ...newQuery } })

const updateLimit = (newValue: number) =>
  updateQuery({ limit: newValue, page: 1 })
const updatePage = (newPage: number) => updateQuery({ page: newPage + 1 })
const updateCreatedAfter = (value: string) =>
  updateQuery({ created_after: value, page: 1 })
const updateCreatedBefore = (value: string) =>
  updateQuery({ created_before: value, page: 1 })
const updateOrdering = (value: string) => updateQuery({ triage: value })
const updateOrganisation = (value: string) =>
  updateQuery({ organisation: value, page: 1 })

const hasActiveFilters = computed(
  () => !!createdAfter.value || !!createdBefore.value || !!organisationFilter.value
)

watch(
  [page, limit, createdAfter, createdBefore, ordering, organisationFilter],
  fetchSearchResults
)
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[
        { to: '/dashboard', text: 'Dashboard' },
        { text: 'Mes enquêtes' },
      ]"
    />
    <div class="filters border mb-2 rounded border-gray-300 p-4 flex gap-8">
      <div>
        <DateRangeFilter
          class="mb-3"
          :created-after="createdAfter"
          :created-before="createdBefore"
          @update:created-after="updateCreatedAfter"
          @update:created-before="updateCreatedBefore"
        />
        <DsfrInputGroup>
          <DsfrSelect
            label="Organisation"
            :model-value="organisationFilter"
            :options="[
              { value: '', text: 'Toutes les enquêtes' },
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
      <div class="flex flex-col gap-4">
        <PaginationSizeSelect
          :modelValue="limit"
          @update:modelValue="updateLimit"
        />
        <OrderingFilter
          :model-value="ordering"
          @update:modelValue="updateOrdering"
        />
      </div>
      <div class="grow"></div>
      <p v-if="data?.count" class="fr-text--sm text-stone-500 mb-0!">
        {{ data.count }} enquêtes au total
      </p>
    </div>

    <div v-if="isFetching" class="flex justify-center my-20">
      <ProgressSpinner />
    </div>

    <div
      v-else-if="data && !data.results.length"
      class="border rounded border-slate-200 p-10 mb-10"
    >
      <p class="text-stone-500 italic mb-0!">
        <template v-if="hasActiveFilters"
          >Aucune enquête ne correspond aux filtres sélectionnés</template
        >
        <template v-else>Aucune enquête n'a été créée</template>
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
