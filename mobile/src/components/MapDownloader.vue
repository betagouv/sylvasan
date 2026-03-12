<script setup lang="ts">
/**
 * UI pour télécharger une zone de la carte
 */
import { computed } from "vue"
import { IonProgressBar } from "@ionic/vue"
import { DsfrButton, DsfrAlert } from "@gouvminint/vue-dsfr"
import {
  useOfflineMap,
  estimateDownload,
  type BoundaryBox,
} from "../composables/useOfflineMap"

const props = defineProps<{
  boundaryBox: BoundaryBox
  zoomLevels: number[]
}>()
const { status, progress, errorMessage, download, cancel, reset } =
  useOfflineMap()

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

// Gestion du niveau de zoom minimale autorisé
const MIN_DOWNLOAD_ZOOM = 9
const tooZoomedOut = computed(() =>
  props.zoomLevels.some((x) => x < MIN_DOWNLOAD_ZOOM)
)

async function startDownload() {
  await download(props.boundaryBox, props.zoomLevels)
}
</script>

<template>
  <div class="offline-dl">
    <template v-if="status === 'idle'">
      <div class="offline-dl__summary">
        <div class="offline-dl__stat">
          <span class="offline-dl__stat-value">{{
            tooZoomedOut ? "-" : estimate.tiles.toLocaleString("fr-FR")
          }}</span>
          <span class="offline-dl__stat-label">tuiles</span>
        </div>
        <div class="offline-dl__divider" aria-hidden="true" />
        <div class="offline-dl__stat">
          <span class="offline-dl__stat-value" v-if="tooZoomedOut">-</span>
          <span class="offline-dl__stat-value" v-else
            >~{{ estimateMb }} Mo</span
          >
          <span class="offline-dl__stat-label">estimé</span>
        </div>
      </div>

      <p class="fr-text--sm fr-mb-2w offline-dl__info" v-if="tooZoomedOut">
        <strong>Zone trop large.</strong> <br />
        Merci d'augmenter le zoom.
      </p>

      <p class="fr-text--sm fr-mb-2w offline-dl__info" v-else>
        La zone visible sera téléchargée aux niveaux de zoom
        <strong>{{ zoomLevels[0] }}</strong> à
        <strong>{{ zoomLevels[zoomLevels.length - 1] }}</strong>
      </p>

      <DsfrButton
        label="Télécharger la zone"
        icon="ri-download-2-line"
        :disabled="tooZoomedOut"
        @click="startDownload"
      />
    </template>

    <template v-else-if="status === 'downloading'">
      <div class="offline-dl__progress-header">
        <span class="offline-dl__progress-pct"
          >{{ progress.percent }}&thinsp;%</span
        >
        <span class="offline-dl__progress-eta">ETA&nbsp;: {{ etaLabel }}</span>
      </div>

      <ion-progress-bar
        :value="progress.percent / 100"
        color="primary"
        class="offline-dl__bar"
      />

      <div class="offline-dl__stats-row">
        <span>{{ progress.downloaded }} / {{ progress.total }} tuiles</span>
        <span>{{ mbDownloaded }} Mo téléchargés</span>
        <span v-if="progress.failed > 0" class="offline-dl__failed">
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
      <DsfrAlert
        type="success"
        title="Carte téléchargée"
        :description="`${progress.downloaded} tuiles enregistrées (${mbDownloaded} Mo). La zone est maintenant disponible hors ligne.`"
        class="fr-mb-2w"
      />
      <DsfrButton label="Fermer" secondary @click="reset" />
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
.offline-dl {
  padding: 1rem 0;
}

/* Summary stats row */
.offline-dl__summary {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}
.offline-dl__stat {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;
}
.offline-dl__stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--blue-france-sun-113-625, #000091);
  line-height: 1;
}
.offline-dl__stat-label {
  font-size: 0.75rem;
  color: var(--grey-625-425, #666);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.offline-dl__divider {
  width: 1px;
  height: 2rem;
  background: var(--grey-925-125, #ddd);
}

.offline-dl__info {
  color: var(--grey-425-625, #555);
}

/* Progress section */
.offline-dl__progress-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.5rem;
}
.offline-dl__progress-pct {
  font-size: 2rem;
  font-weight: 700;
  color: var(--blue-france-sun-113-625, #000091);
  line-height: 1;
}
.offline-dl__progress-eta {
  font-size: 0.875rem;
  color: var(--grey-425-625, #555);
}

.offline-dl__bar {
  --progress-background: var(--blue-france-sun-113-625, #000091);
  height: 6px;
  border-radius: 3px;
  margin-bottom: 0.75rem;
}

.offline-dl__stats-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8125rem;
  color: var(--grey-425-625, #555);
}
.offline-dl__failed {
  color: var(--warning-425-625, #b34000);
}
</style>
