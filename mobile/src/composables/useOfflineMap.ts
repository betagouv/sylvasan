import { ref, computed } from "vue"
import { Capacitor } from "@capacitor/core"
import { Filesystem, Directory, Encoding } from "@capacitor/filesystem"
import { openDB, type IDBPDatabase } from "idb"
import type {
  BoundaryBox,
  DownloadProgress,
  DownloadStatus,
  TileCoord,
} from "@shared-types/maps"

const CONCURRENCY = 10
const MAX_RETRIES = 3
const RETRY_BASE_MS = 500

// Taille moyenne de chaque tuile par niveau de zoom. Valeurs prises du code IGN
// https://github.com/IGNF/cartes-ign-app/blob/92fd947e6721ce5e2c4bfdac3d1ea99f993b00c1/src/js/offline-maps.js#L40
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

// Cette fonction fait la conversion entre une coordonnée lat/lng et un niveau de zoom
// et la position x, y de la tuile.
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
    binary += String.fromCharCode(bytes[i] || 0) // TODO : Petit hack pour enlever une warning TS
  return btoa(binary)
}

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

const fetchTileWithRetry = async (
  url: string,
  signal: AbortSignal
): Promise<ArrayBuffer> => {
  let lastError: unknown
  for (let attempt = 0; attempt < MAX_RETRIES; attempt++) {
    if (signal.aborted) throw new DOMException("Aborted", "AbortError")
    try {
      const response = await fetch(url, { signal })
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
    (sum, { z }) => sum + (AVG_TILE_BYTES[z] ?? 50000),
    0
  )
  // On ajoute 25% pour l'overhead de l'encodage en base 64
  return { tiles: tiles.length, bytes: Math.round(bytes * 1.25) }
}

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

  let abortController = new AbortController()
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
        // >5% d'échec -> erreur
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
