<script setup lang="ts">
import * as z from "zod"
import { ref, computed } from "vue"
import { ZodError } from "zod"
import { useApiFetch } from "../../utils/data-fetching"
import { useToastStore } from "../../stores/toast"
import type { VocabularyEntry } from "@shared-types/survey"
import ProgressSpinner from "../ProgressSpinner.vue"
import { DsfrTable } from "@gouvminint/vue-dsfr"

const props = defineProps<{
  opened: boolean
  vocabularysetId: string | number
}>()

const emit = defineEmits<{ close: []; saved: [] }>()
const csvFile = ref<File | null>(null)
const apiError = ref<string | null>(null)
const dryRunEntries = ref<VocabularyEntry[]>([])
const toast = useToastStore()
const fileInput = ref<HTMLInputElement | null>(null)

const openFilePicker = () => fileInput.value?.click()

const dryRunBody = ref(new FormData())

const {
  execute: executeDryRun,
  response: dryRunResponse,
  isFetching: isDryRunFetching,
  statusCode: dryRunStatusCode,
  data: dryRunData,
} = useApiFetch(
  () => `/admin/vocabularies/${props.vocabularysetId}/bulk-import/`,
  { immediate: false },
)
  .post(dryRunBody)
  .json()

const onFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  csvFile.value = file
  apiError.value = null
  dryRunEntries.value = []

  const formData = new FormData()
  formData.append("file", file)
  formData.append("dryRun", "true")
  dryRunBody.value = formData

  await executeDryRun()

  if (dryRunStatusCode.value === 200) {
    dryRunEntries.value = dryRunData.value as VocabularyEntry[]
  } else {
    const body = await dryRunResponse.value?.json().catch(() => null)
    apiError.value =
      (body as { detail?: string })?.detail ?? "Une erreur s'est produite."
  }
}

const onSave = async () => {
  if (!csvFile.value) return

  const formData = new FormData()
  formData.append("file", csvFile.value)
  formData.append("dryRun", "false")
  dryRunBody.value = formData

  await executeDryRun()

  if (dryRunStatusCode.value === 201) {
    const saved = dryRunData.value as VocabularyEntry[]
    const n = saved.length
    toast.show(
      `L'import du fichier « ${csvFile.value.name} » a bien été effectué. ${n} entrée${n > 1 ? "s ont été ajoutées" : " a été ajoutée"}.`,
      "success",
    )
    emit("saved")
    emit("close")
  } else {
    const body = await dryRunResponse.value?.json().catch(() => null)
    apiError.value =
      (body as { detail?: string })?.detail ?? "Une erreur s'est produite."
  }
}
</script>

<template>
  <DsfrModal
    :opened="opened"
    title="Importer via un fichier CSV"
    @close="emit('close')"
    size="lg"
  >
    <div class="fr-text--sm mb-4!">
      <p class="fr-text--sm mb-0!">
        Le fichier doit être encodé en UTF-8 et ne doit pas inclure des entêtes.
      </p>
      <ul>
        <li class="pb-0!">
          <span class="font-bold">Colonne A</span> : Le code de l'entrée (par
          ex. « CHALFRA »)
        </li>
        <li class="pb-0!">
          <span class="font-bold">Colonne B</span> : Le libellé de l'entrée (par
          ex. « Chalara fraxinea »)
        </li>
        <li class="pb-0!">
          <span class="font-bold">Colonne C</span> : (Facultatif) la position
          dans la liste (par ex. « 4 »)
        </li>
      </ul>
    </div>
    <div
      v-if="apiError"
      class="fr-text--sm mb-2! border border-red-200 p-2 bg-red-50"
    >
      <v-icon icon="ri-error-warning-fill" />
      {{ apiError }}
    </div>
    <div class="bg-slate-50 border p-2 border-slate-200 pb-0">
      <div class="flex items-center">
        <p class="fr-text--sm mb-0! grow" v-if="!csvFile">
          Aucun fichier sélectionné
        </p>
        <p class="fr-text--sm mb-0! grow" v-else>
          <v-icon icon="ri-attachment-fill" />
          {{ csvFile.name }}
        </p>
        <input
          type="file"
          class="sr-only"
          accept=".csv"
          id="input-id"
          ref="fileInput"
          @change="onFileChange"
        />
        <DsfrButton
          type="button"
          secondary
          icon="ri-file-line"
          label="Sélectionner un fichier"
          size="sm"
          @click="openFilePicker"
        />
      </div>
      <hr class="mt-2! pb-1!" />

      <div class="flex align-center justify-center md:h-64 overflow-y-scroll">
        <v-icon
          v-if="!csvFile"
          icon="ri-table-2"
          scale="4"
          color="#EEE"
          class="mt-10"
        />

        <div class="mt-10" v-else-if="isDryRunFetching">
          <ProgressSpinner />
        </div>

        <table
          v-else-if="dryRunEntries.length"
          class="w-full fr-text--sm border-collapse"
        >
          <thead>
            <tr class="text-left border-b border-slate-200">
              <th class="py-1 pr-4 font-semibold">Code</th>
              <th class="py-1 pr-4 font-semibold">Libellé</th>
              <th class="py-1 font-semibold">Position</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="entry in dryRunEntries"
              :key="entry.code"
              class="border-b border-slate-100"
            >
              <td class="py-1 pr-4 font-mono">
                <div
                  class="bg-white border border-gray-200 rounded px-1 inline"
                >
                  {{ entry.code }}
                </div>
              </td>
              <td class="py-1 pr-4">{{ entry.label }}</td>
              <td class="py-1 text-slate-500">{{ entry.position ?? "—" }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <template #footer>
      <div class="flex justify-end gap-2 w-full">
        <DsfrButton
          :label="`Ajouter les ${dryRunEntries?.length || ''} entrées`"
          icon="ri-save-line"
          :disabled="
            !csvFile || !!apiError || !dryRunEntries?.length || isDryRunFetching
          "
          @click="onSave"
        />
      </div>
    </template>
  </DsfrModal>
</template>
