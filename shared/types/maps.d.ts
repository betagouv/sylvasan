export interface OfflineMapRecord {
  id: string // type uuid, par ex "map_1718000000000"
  name: string
  createdAt: string // date en format ISO
  tiles: number
  bytes: number
  boundaryBox: BoundaryBox
  zoomLevels: number[]
}

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

export interface TileCoord {
  z: number
  x: number
  y: number
}
