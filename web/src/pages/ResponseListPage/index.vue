<route lang="json">
{
  "path": "/reponses",
  "meta": {
    "authenticationRequired": true,
    "title": "Réponses à mes enquêtes",
    "defaultQueryParams": {
      "page": 1,
      "limit": 2,
      "created_after": "",
      "created_before": ""
    }
  }
}
</route>

<script setup lang="ts">
import { computed, watch } from "vue"
import { useApiFetch } from "../../utils/data-fetching"
import type { ResponseDisplay } from "@shared-types/response"
import { useRouter, useRoute } from "vue-router"
import ProgressSpinner from "../../components/ProgressSpinner.vue"
import PaginationSizeSelect from "./PaginationSizeSelect.vue"
import DateRangeFilter from "./DateRangeFilter.vue"

const router = useRouter()
const route = useRoute()

const limit = computed(() => parseInt(route.query.limit as string))
const page = computed(() => parseInt(route.query.page as string))
const offset = computed(() => (page.value - 1) * limit.value)
const createdAfter = computed(() => (route.query.created_after as string) ?? "")
const createdBefore = computed(
  () => (route.query.created_before as string) ?? ""
)

const url = computed(() => {
  const params = new URLSearchParams({
    limit: String(limit.value),
    offset: String(offset.value),
  })
  if (createdAfter.value) params.set("created_after", createdAfter.value)
  if (createdBefore.value) params.set("created_before", createdBefore.value)
  return `/responses/?${params.toString()}`
})

type PaginatedResponse = { count: number; results: ResponseDisplay[] }

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
        to: { name: "/ResponsePage/", params: { id: response.id } },
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

watch([page, limit, createdAfter, createdBefore], fetchSearchResults)
</script>

<template>
  <div class="fr-container">
    <DsfrBreadcrumb
      :links="[{ to: '/dashboard', text: 'Dashboard' }, { text: 'Réponses' }]"
    />
    <div class="border mb-2 rounded border-gray-300 p-4 flex gap-4 items-end">
      <DateRangeFilter
        :created-after="createdAfter"
        :created-before="createdBefore"
        @update:created-after="updateCreatedAfter"
        @update:created-before="updateCreatedBefore"
      />
      <div class="grow"></div>
      <PaginationSizeSelect
        :modelValue="limit"
        @update:modelValue="updateLimit"
      />
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
      <DsfrPagination
        v-if="totalPages > 1"
        :pages="pages"
        :current-page="page - 1"
        @update:currentPage="updatePage"
      />
    </template>
  </div>
</template>

<style scoped>
.fr-table :deep(table) {
  @apply table!;
}
</style>
