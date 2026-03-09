/**
 * useOfflineMap.ts
 * Composable for downloading and managing offline IGN map tiles.
 *
 * Key improvements over IGN reference implementation:
 * - Per-tile retry with exponential backoff (avoids full restart on transient errors)
 * - Resume support: already-stored tiles are skipped on retry
 * - Reactive progress state suitable for Vue UI binding
 * - Clean abort/cancel without corrupting stored data
 */

import { ref, computed } from "vue"
import { Capacitor } from "@capacitor/core"
import { Filesystem, Directory, Encoding } from "@capacitor/filesystem"
import { openDB, type IDBPDatabase } from "idb"

const CONCURRENCY = 10
const MAX_RETRIES = 3
const RETRY_BASE_MS = 500

// Taille moyenne de chaque tuile par niveau de zoom. Valeurs prises du code IGN
// TODO : ajouter lien vers le fichier IGN
const AVG_TILE_BYTES: Record<number, number> = {
  0: 484467,
  1: 272629,
  2: 209715,
  3: 209715,
  4: 104857,
  5: 83886,
  6: 20971,
  7: 104857,
  8: 41943,
  9: 10485,
  10: 78643,
  11: 24117,
  12: 17825,
  13: 68157,
  14: 52428,
  15: 68157,
  16: 16777,
  17: 7340,
  18: 6291,
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface BoundaryBox {
  minLng: number
  minLat: number
  maxLng: number
  maxLat: number
}

export interface DownloadProgress {
  downloaded: number
  total: number
  failed: number
  bytesStored: number
  etaSeconds: number
  percent: number
}

export type DownloadStatus =
  | "idle"
  | "downloading"
  | "paused"
  | "done"
  | "error"
  | "cancelled"

interface TileCoord {
  z: number
  x: number
  y: number
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

// TODO : understand
const lngLatToTile = (
  lng: number,
  lat: number,
  zoom: number
): { x: number; y: number } => {
  const n = 2 ** zoom
  const x = Math.floor(((lng + 180) / 360) * n)
  const latRad = (lat * Math.PI) / 180
  const y = Math.floor(
    ((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2) * n
  )
  return { x, y }
}

const sleep = (ms: number): Promise<void> =>
  new Promise((r) => setTimeout(r, ms))

const tileKey = (z: number, x: number, y: number): string =>
  `PLAN.IGN/${z}/${x}/${y}`

const tileUrl = (tileKey: string): string =>
  `https://data.geopf.fr/tms/1.0.0/${tileKey}.pbf`

const arrayBufferToBase64 = (buffer: ArrayBuffer): string => {
  const bytes = new Uint8Array(buffer)
  let binary = ""
  for (let i = 0; i < bytes.byteLength; i++)
    binary += String.fromCharCode(bytes[i] || 0) // TODO : Klunk to apease TS
  return btoa(binary)
}

// ---------------------------------------------------------------------------
// Storage abstraction (Capacitor on device, IndexedDB on web)
// ---------------------------------------------------------------------------

const getWebDb = async (): Promise<IDBPDatabase> => {
  return openDB("ign-tile-store", 1, {
    upgrade(db: any) {
      if (!db.objectStoreNames.contains("tiles")) db.createObjectStore("tiles")
    },
  })
}

const tileExists = async (key: string, db?: IDBPDatabase): Promise<boolean> => {
  if (Capacitor.isNativePlatform()) {
    try {
      await Filesystem.stat({
        path: `tiles/${key}.pbf`,
        directory: Directory.Data,
      })
      return true
    } catch {
      return false
    }
  } else {
    const val = await db!.get("tiles", key)
    return val !== undefined
  }
}

const storeTile = async (
  key: string,
  data: string,
  db?: IDBPDatabase
): Promise<void> => {
  if (Capacitor.isNativePlatform()) {
    await Filesystem.writeFile({
      path: `tiles/${key}.pbf`,
      data,
      directory: Directory.Data,
      encoding: Encoding.UTF8,
      recursive: true,
    })
  } else {
    await db!.put("tiles", data, key)
  }
}

// ---------------------------------------------------------------------------
// Core fetch with retry + exponential backoff
// ---------------------------------------------------------------------------

const fetchTileWithRetry = async (
  url: string,
  signal: AbortSignal
): Promise<ArrayBuffer> => {
  let lastError: unknown
  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    if (signal.aborted) throw new DOMException("Aborted", "AbortError")
    try {
      const response = await fetch(url, { signal }) // TODO: understand this signal
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      return await response.arrayBuffer()
    } catch (err) {
      lastError = err
      if (signal.aborted) throw err
      let retry = attempt < MAX_RETRIES - 1
      if (retry) await sleep(RETRY_BASE_MS * 2 ** attempt)
    }
  }
  throw lastError
}

// ---------------------------------------------------------------------------
// Tile enumeration
// ---------------------------------------------------------------------------

const enumerateTiles = (
  boundaryBox: BoundaryBox,
  zoomLevels: number[]
): TileCoord[] => {
  const tiles: TileCoord[] = []
  for (const z of zoomLevels) {
    // La tuile en haut à gauche (première)
    const { x: x0, y: y0 } = lngLatToTile(
      boundaryBox.minLng,
      boundaryBox.maxLat,
      z
    )

    // La tuile en bas à droite (dernière)
    const { x: x1, y: y1 } = lngLatToTile(
      boundaryBox.maxLng,
      boundaryBox.minLat,
      z
    )

    // On parcourt toutes le tuiles entre les deux
    for (let x = x0; x <= x1; x++) {
      for (let y = y0; y <= y1; y++) {
        tiles.push({ z, x, y })
      }
    }
  }
  return tiles
}

export const estimateDownload = (
  boundaryBox: BoundaryBox,
  zoomLevels: number[]
): { tiles: number; bytes: number } => {
  const tiles = enumerateTiles(boundaryBox, zoomLevels)
  const bytes = tiles.reduce(
    (sum, { z }) => sum + (AVG_TILE_BYTES[z] ?? 50000), // TODO : understand
    0
  )
  // On ajoute 33% pour l'overhead de l'encoding en base 64 // TODO : nécessaire ?
  return { tiles: tiles.length, bytes: Math.round(bytes * 1.33) }
}

// ---------------------------------------------------------------------------
// Composable
// ---------------------------------------------------------------------------

export const useOfflineMap = () => {
  const status = ref<DownloadStatus>("idle")
  const progress = ref<DownloadProgress>({
    downloaded: 0,
    total: 0,
    failed: 0,
    bytesStored: 0,
    etaSeconds: 0,
    percent: 0,
  })
  const errorMessage = ref<string | null>(null)

  let abortController = new AbortController() // TODO: understand abort controller
  let db: IDBPDatabase | undefined

  const isDownloading = computed(() => status.value === "downloading")

  async function download(
    boundaryBox: BoundaryBox,
    zoomLevels: number[]
  ): Promise<boolean> {
    if (status.value === "downloading") return false

    abortController = new AbortController()
    const signal = abortController.signal
    status.value = "downloading"
    errorMessage.value = null

    if (!Capacitor.isNativePlatform()) {
      db = await getWebDb()
    }

    const allTiles = enumerateTiles(boundaryBox, zoomLevels)

    // On enlève les tuiles qu'on a déjà téléchargé
    const pendingTiles: TileCoord[] = []
    for (const tile of allTiles) {
      const key = tileKey(tile.z, tile.x, tile.y)
      if (!(await tileExists(key, db))) pendingTiles.push(tile)
    }

    progress.value = {
      downloaded: allTiles.length - pendingTiles.length,
      total: allTiles.length,
      failed: 0,
      bytesStored: 0,
      etaSeconds: 0,
      percent: Math.round(
        ((allTiles.length - pendingTiles.length) / allTiles.length) * 100
      ),
    }

    const startTime = Date.now()
    let completedSinceStart = 0

    // On ne traite qu'un numéro limité de tuiles
    const semaphore = Array(CONCURRENCY).fill(null)
    let tileIndex = 0

    async function worker(): Promise<void> {
      while (tileIndex < pendingTiles.length && !signal.aborted) {
        const tile = pendingTiles[tileIndex++]
        if (!tile) continue
        const key = tileKey(tile.z, tile.x, tile.y)
        const url = tileUrl(key)
        try {
          const buffer = await fetchTileWithRetry(url, signal)
          const b64 = arrayBufferToBase64(buffer)
          await storeTile(key, b64, db)

          completedSinceStart++
          progress.value.downloaded++
          progress.value.bytesStored += buffer.byteLength

          const elapsed = (Date.now() - startTime) / 1000
          const rate = completedSinceStart / elapsed
          const remaining = pendingTiles.length - completedSinceStart
          progress.value.etaSeconds =
            rate > 0 ? Math.round(remaining / rate) : 0
          progress.value.percent = Math.round(
            (progress.value.downloaded / progress.value.total) * 100
          )
        } catch (err) {
          if (signal.aborted) return
          progress.value.failed++
          console.warn(
            `[offline-map] Failed tile ${key} after ${MAX_RETRIES} retries`,
            err
          )
        }
      }
    }

    // On lance les workers de façon concurrente
    await Promise.all(semaphore.map(() => worker()))

    if (signal.aborted) {
      status.value = "cancelled"
      return false
    }

    if (progress.value.failed > 0) {
      const failRate = progress.value.failed / progress.value.total
      if (failRate > 0.05) {
        // >5% failure rate → treat as error // TODO : penser à une valeur acceptable
        status.value = "error"
        errorMessage.value = `${progress.value.failed} tuiles n'ont pas pu être téléchargées.`
        return false
      }
    }

    status.value = "done"
    return true
  }

  function cancel() {
    abortController.abort()
    status.value = "cancelled"
  }

  function reset() {
    status.value = "idle"
    errorMessage.value = null
    progress.value = {
      downloaded: 0,
      total: 0,
      failed: 0,
      bytesStored: 0,
      etaSeconds: 0,
      percent: 0,
    }
  }

  return {
    status,
    progress,
    errorMessage,
    isDownloading,
    download,
    cancel,
    reset,
    estimateDownload,
  }
}
