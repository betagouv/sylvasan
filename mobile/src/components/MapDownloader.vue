<script setup lang="ts">
// UI pour télécharger une zone de la carte.
// Sauvegarde les métadonnées à la fin du téléchargement.

import { computed, ref } from "vue"
import { IonProgressBar } from "@ionic/vue"
import type { BoundaryBox, OfflineMapRecord } from "../types/maps"
import { useOfflineMap, estimateDownload } from "../composables/useOfflineMap"
import { saveMapRecord, generateMapId } from "../composables/offlineMapMetadata"

const props = defineProps<{
  boundaryBox: BoundaryBox
  zoomLevels: number[]
}>()

const emit = defineEmits<{
  saved: [record: OfflineMapRecord]
}>()

const { status, progress, errorMessage, download, cancel, reset } =
  useOfflineMap()

const mapName = ref("")
const nameError = ref<string | null>(null)

let currentMapId = generateMapId()

const estimate = computed(() =>
  estimateDownload(props.boundaryBox, props.zoomLevels)
)
const estimateMb = computed(() => (estimate.value.bytes / 1_000_000).toFixed(1))

const etaLabel = computed(() => {
  const s = progress.value.etaSeconds
  if (s <= 0) return "…"
  const m = Math.floor(s / 60)
  const sec = s % 60
  return m > 0 ? `${m}min ${sec}s` : `${sec}s`
})

const mbDownloaded = computed(() =>
  (progress.value.bytesStored / 1_000_000).toFixed(1)
)

const MIN_DOWNLOAD_ZOOM = 9
const tooZoomedOut = computed(() =>
  props.zoomLevels.some((x) => x < MIN_DOWNLOAD_ZOOM)
)

async function startDownload() {
  currentMapId = generateMapId()
  mapName.value = `Carte du ${new Date().toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
  })}`
  await download(props.boundaryBox, props.zoomLevels)
}

async function confirmSave() {
  const name = mapName.value.trim()
  if (!name) {
    nameError.value = "Veuillez donner un nom à cette carte."
    return
  }
  nameError.value = null

  const record: OfflineMapRecord = {
    id: currentMapId,
    name,
    createdAt: new Date().toISOString(),
    tiles: progress.value.downloaded,
    bytes: progress.value.bytesStored,
    boundaryBox: props.boundaryBox,
    zoomLevels: props.zoomLevels,
  }

  await saveMapRecord(record)
  emit("saved", record)
  reset()
}
</script>

<template>
  <div class="p-2">
    <template v-if="status === 'idle'">
      <div class="flex items-center justify-center gap-4 mb-2">
        <div class="flex flex-col">
          <span class="stat-value">{{
            tooZoomedOut ? "—" : estimate.tiles.toLocaleString("fr-FR")
          }}</span>
          <span class="stat-label">tuiles</span>
        </div>
        <div class="w-px h-[2rem] bg-stone-300" aria-hidden="true" />
        <div class="flex flex-col">
          <span class="stat-value">{{
            tooZoomedOut ? "—" : `~${estimateMb} Mo`
          }}</span>
          <span class="stat-label">estimé</span>
        </div>
      </div>

      <p class="fr-text--sm fr-mb-2w" v-if="tooZoomedOut">
        <strong>Zone trop large.</strong><br />Merci d'augmenter le zoom.
      </p>
      <p class="fr-text--sm fr-mb-2w" v-else>
        La zone visible sera téléchargée aux niveaux de zoom
        <strong>{{ zoomLevels[0] }}</strong> à
        <strong>{{ zoomLevels[zoomLevels.length - 1] }}</strong
        >.
      </p>

      <DsfrButton
        label="Télécharger la zone"
        icon="ri-download-2-line"
        :disabled="tooZoomedOut"
        @click="startDownload"
      />
    </template>

    <template v-else-if="status === 'downloading'">
      <div class="flex justify-between items-baseline mb-1">
        <span class="text-3xl font-bold leading-none" style="color: #000091">
          {{ progress.percent }}&thinsp;%
        </span>
        <span class="text-sm text-stone-500">ETA&nbsp;: {{ etaLabel }}</span>
      </div>

      <ion-progress-bar
        :value="progress.percent / 100"
        color="primary"
        class="progress-bar"
      />

      <div class="flex flex-col gap-1 text-sm">
        <span>{{ progress.downloaded }} / {{ progress.total }} tuiles</span>
        <span>{{ mbDownloaded }} Mo téléchargés</span>
        <span v-if="progress.failed > 0" class="failed">
          ⚠ {{ progress.failed }} erreurs (nouvelle tentative automatique)
        </span>
      </div>

      <DsfrButton
        label="Annuler"
        secondary
        icon="ri-close-line"
        class="fr-mt-2w"
        @click="cancel"
      />
    </template>

    <template v-else-if="status === 'done'">
      <p class="fr-text--sm fr-mb-1w text-stone-600">
        {{ progress.downloaded }} tuiles téléchargées ({{ mbDownloaded }} Mo).
        Donnez un nom à cette carte pour la retrouver facilement.
      </p>

      <DsfrInputGroup :error-message="nameError ?? undefined">
        <DsfrInput
          v-model="mapName"
          label="Nom de la carte"
          label-visible
          @keyup.enter="confirmSave"
          class="box-border!"
        />
      </DsfrInputGroup>

      <div class="flex gap-2 fr-mt-2w">
        <DsfrButton
          label="Enregistrer"
          icon="ri-save-line"
          @click="confirmSave"
        />
        <DsfrButton label="Ignorer" secondary @click="reset" />
      </div>
    </template>

    <template v-else-if="status === 'cancelled'">
      <DsfrAlert
        type="warning"
        title="Téléchargement annulé"
        description="Les tuiles déjà téléchargées ont été conservées. Vous pouvez reprendre le téléchargement à tout moment."
        class="fr-mb-2w"
      />
      <DsfrButton
        label="Reprendre"
        icon="ri-download-2-line"
        @click="startDownload"
      />
      <DsfrButton
        label="Recommencer"
        secondary
        class="fr-ml-1w"
        @click="reset"
      />
    </template>

    <template v-else-if="status === 'error'">
      <DsfrAlert
        type="error"
        title="Échec du téléchargement"
        :description="errorMessage ?? 'Une erreur est survenue.'"
        class="fr-mb-2w"
      />
      <DsfrButton
        label="Réessayer"
        icon="ri-refresh-line"
        @click="startDownload"
      />
      <DsfrButton label="Annuler" secondary class="fr-ml-1w" @click="reset" />
    </template>
  </div>
</template>

<style scoped>
.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--blue-france-sun-113-625, #000091);
  line-height: 1;
}
.stat-label {
  font-size: 0.75rem;
  color: var(--grey-625-425, #666);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.progress-bar {
  --progress-background: var(--blue-france-sun-113-625, #000091);
  height: 6px;
  border-radius: 3px;
  margin-bottom: 0.75rem;
}

.failed {
  color: var(--warning-425-625, #b34000);
}
</style>
