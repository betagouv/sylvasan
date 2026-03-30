// Persistence pour les metadonnées d'une carte téléchargée
// Les tuiles sont dans Filesystem/IndexedDB. Les metadonnées
// sont dans @capacitor/preferences

import { Preferences } from "@capacitor/preferences"
import type { OfflineMapRecord } from "@shared-types/maps"

const MAPS_INDEX_KEY = "offline_maps_index"

async function readIndex(): Promise<OfflineMapRecord[]> {
  const { value } = await Preferences.get({ key: MAPS_INDEX_KEY })
  if (!value) return []
  try {
    return JSON.parse(value) as OfflineMapRecord[]
  } catch {
    return []
  }
}

async function writeIndex(records: OfflineMapRecord[]): Promise<void> {
  await Preferences.set({ key: MAPS_INDEX_KEY, value: JSON.stringify(records) })
}

export async function saveMapRecord(record: OfflineMapRecord): Promise<void> {
  const records = await readIndex()
  const existingIndex = records.findIndex((r) => r.id === record.id)
  if (existingIndex >= 0) {
    records[existingIndex] = record
  } else {
    records.unshift(record)
  }
  await writeIndex(records)
}

export async function loadAllMapRecords(): Promise<OfflineMapRecord[]> {
  return readIndex()
}

export async function deleteMapRecord(id: string): Promise<void> {
  const records = await readIndex()
  await writeIndex(records.filter((r) => r.id !== id))
}

export async function renameMapRecord(id: string, name: string): Promise<void> {
  const records = await readIndex()
  const record = records.find((r) => r.id === id)
  if (record) {
    record.name = name
    await writeIndex(records)
  }
}

export function generateMapId(): string {
  return `map_${Date.now()}`
}

export function formatBytes(bytes: number): string {
  if (bytes < 1_000) return `${bytes} o`
  if (bytes < 1_000_000) return `${(bytes / 1_000).toFixed(0)} Ko`
  return `${(bytes / 1_000_000).toFixed(1)} Mo`
}

export function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString("fr-FR", {
    day: "numeric",
    month: "long",
    year: "numeric",
  })
}
