<route lang="json">
{
  "path": "/reponses",
  "meta": {
    "authenticationRequired": true,
    "title": "Réponses à mes enquêtes",
    "defaultQueryParams": {
      "page": 1,
      "limit": 10,
      "created_after": "",
      "created_before": "",
      "triage": "",
      "survey": ""
    }
  }
}
</route>

<script setup lang="ts">
import { computed, watch } from "vue"
import { useApiFetch } from "../utils/data-fetching.ts"
import type { ResponseDisplay } from "@shared-types/response"
import type { SurveyDisplay } from "@shared-types/api"
import { useRouter, useRoute } from "vue-router"
import ProgressSpinner from "../components/ProgressSpinner.vue"
import PaginationSizeSelect from "../components/ResponseListPage/PaginationSizeSelect.vue"
import DateRangeFilter from "../components/ResponseListPage/DateRangeFilter.vue"
import OrderingFilter from "../components/ResponseListPage/OrderingFilter.vue"

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
const surveyFilter = computed(() => (route.query.survey as string) ?? "")

const filterParams = computed(() => {
  const params = new URLSearchParams()
  if (createdAfter.value) params.set("created_after", createdAfter.value)
  if (createdBefore.value) params.set("created_before", createdBefore.value)
  if (ordering.value) params.set("ordering", String(ordering.value))
  if (surveyFilter.value) params.set("survey", surveyFilter.value)
  return params
})

const url = computed(() => {
  const params = new URLSearchParams(filterParams.value)
  params.set("limit", String(limit.value))
  params.set("offset", String(offset.value))
  return `/responses/?${params.toString()}`
})

const base = import.meta.env.VITE_API_ROOT
const exportJsonUrl = computed(() => {
  const q = filterParams.value.toString()
  return `${base}/responses/export/json/${q ? `?${q}` : ""}`
})
const exportCsvUrl = computed(() => {
  const q = filterParams.value.toString()
  return `${base}/responses/export/csv/${q ? `?${q}` : ""}`
})

type PaginatedResponse = {
  count: number
  results: ResponseDisplay[]
  surveys: SurveyDisplay[]
}

const { data, execute, isFetching } = useApiFetch(url)
  .get()
  .json<PaginatedResponse>()

const fetchSearchResults = async () => {
  await execute()
  // <- Gestion d'erreur
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
  (data.value?.results ?? []).map((response: ResponseDisplay) => ({
    rowData: [
      response.id,
      {
        component: "router-link",
        text: response.survey.title,
        class: "font-bold",
        to: { name: "/ResponsePage", params: { id: response.id } },
      },
      `${response.respondant?.firstName} ${response.respondant?.lastName}`,
      new Date(response.creationDate).toLocaleDateString("fr-FR", {
        day: "numeric",
        month: "long",
      }),
    ],
  }))
)

const headers = [
  { text: "ID", headerAttrs: { id: "th-id" } },
  { text: "Enquête", headerAttrs: { id: "th-survey" } },
  { text: "Répondant", headerAttrs: { id: "th-respondent" } },
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
const updateSurvey = (value: string) => updateQuery({ survey: value, page: 1 })

const exportJson = () => {
  window.location.href = exportJsonUrl.value
}
const exportCsv = () => {
  window.location.href = exportCsvUrl.value
}

watch(
  [page, limit, createdAfter, createdBefore, ordering, surveyFilter],
  fetchSearchResults
)
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[{ to: '/dashboard', text: 'Dashboard' }, { text: 'Réponses' }]"
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
            label="Enquête"
            :model-value="surveyFilter"
            :options="[
              { value: '', text: 'Toutes les enquêtes' },
              ...(data?.surveys ?? []).map((s) => ({
                value: String(s.id),
                text: s.title,
              })),
            ]"
            class="text-sm!"
            @update:modelValue="updateSurvey"
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
      <div class="flex flex-col gap-4">
        <DsfrButton
          label="Exporter JSON"
          secondary
          size="sm"
          icon="ri-file-code-line"
          @click="exportJson"
        />
        <DsfrButton
          label="Exporter CSV"
          secondary
          size="sm"
          icon="ri-table-3"
          @click="exportCsv"
        />
        <p v-if="data?.count" class="fr-text--sm text-stone-500 mb-0!">
          {{ data.count }} réponses au total
        </p>
      </div>
    </div>
    <div v-if="isFetching" class="flex justify-center my-20">
      <ProgressSpinner />
    </div>
    <div
      v-else-if="data && !data.results.length"
      class="border rounded border-slate-200 p-10 mb-10"
    >
      <p class="text-stone-500 italic mb-0!">
        Pas de réponse avec ces paramètres
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
            {{ data.count }} réponses au total
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
