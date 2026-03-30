// Cet composable aide à la liste des cartes téléchargées et
// offre la possibilité de les supprimer ou modifier

import { ref } from "vue"
import { Capacitor } from "@capacitor/core"
import { Filesystem, Directory } from "@capacitor/filesystem"
import { openDB } from "idb"
import {
  loadAllMapRecords,
  deleteMapRecord,
  renameMapRecord,
} from "./offlineMapMetadata"

import type { OfflineMapRecord } from "@shared-types/maps"

function enumerateTileKeys(record: OfflineMapRecord): string[] {
  const { boundaryBox, zoomLevels } = record
  const keys: string[] = []
  for (const z of zoomLevels) {
    const n = 2 ** z
    const toTile = (lng: number, lat: number) => {
      const x = Math.floor(((lng + 180) / 360) * n)
      const latRad = (lat * Math.PI) / 180
      const y = Math.floor(
        ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) /
          2) *
          n
      )
      return { x, y }
    }
    const { x: x0, y: y0 } = toTile(boundaryBox.minLng, boundaryBox.maxLat)
    const { x: x1, y: y1 } = toTile(boundaryBox.maxLng, boundaryBox.minLat)
    for (let x = x0; x <= x1; x++)
      for (let y = y0; y <= y1; y++) keys.push(`PLAN.IGN/${z}/${x}/${y}`)
  }
  return keys
}

async function deleteTilesForMap(record: OfflineMapRecord): Promise<void> {
  const keysToDelete = new Set(enumerateTileKeys(record))

  // Pour éviter de supprimer des tuiles utilisées par d'autres cartes
  // téléchargées, on vérifie les autres cartes
  const allRecords = await loadAllMapRecords()
  for (const other of allRecords) {
    if (other.id === record.id) continue
    for (const key of enumerateTileKeys(other)) {
      keysToDelete.delete(key)
    }
  }

  // On ne supprime que les tuiles qui ne sont pas référencées par d'autres
  // cartes
  if (Capacitor.isNativePlatform()) {
    await Promise.allSettled(
      [...keysToDelete].map((key) =>
        Filesystem.deleteFile({
          path: `tiles/${key}.pbf`,
          directory: Directory.Data,
        })
      )
    )
  } else {
    const db = await openDB("ign-tile-store", 1)
    const tx = db.transaction("tiles", "readwrite")
    await Promise.allSettled(
      [...keysToDelete].map((key) => tx.store.delete(key))
    )
    await tx.done
  }
}

export function useOfflineMaps() {
  const maps = ref<OfflineMapRecord[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function loadMaps() {
    loading.value = true
    error.value = null
    try {
      maps.value = await loadAllMapRecords()
    } catch (e) {
      error.value = "Impossible de charger les cartes."
      console.error("[useOfflineMaps] loadMaps failed", e)
    } finally {
      loading.value = false
    }
  }

  async function deleteMap(id: string) {
    const record = maps.value.find((m) => m.id === id)
    if (!record) return
    try {
      await deleteTilesForMap(record)
      await deleteMapRecord(id)
      maps.value = maps.value.filter((m) => m.id !== id)
    } catch (e) {
      error.value = "Impossible de supprimer la carte."
      console.error("[useOfflineMaps] deleteMap failed", e)
    }
  }

  async function renameMap(id: string, newName: string) {
    try {
      await renameMapRecord(id, newName)
      const record = maps.value.find((m) => m.id === id)
      if (record) record.name = newName
    } catch (e) {
      error.value = "Impossible de renommer la carte."
      console.error("[useOfflineMaps] renameMap failed", e)
    }
  }

  return { maps, loading, error, loadMaps, deleteMap, renameMap }
}
