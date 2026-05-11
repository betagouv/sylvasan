import maplibregl, { type StyleSpecification } from "maplibre-gl"
import { Capacitor } from "@capacitor/core"
import { Filesystem, Directory, Encoding } from "@capacitor/filesystem"
import { openDB } from "idb"
import ignStyle from "../assets/ign-style.json"

export const OFFLINE_PROTOCOL = "offline"

const IGN_TILE_URL = "https://data.geopf.fr/tms/1.0.0/PLAN.IGN/{z}/{x}/{y}.pbf"

let protocolActive = false

const base64ToArrayBuffer = (b64: string): ArrayBuffer => {
  const binary = atob(b64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  return bytes.buffer
}

export const registerOfflineProtocol = () => {
  if (protocolActive) return
  maplibregl.addProtocol(OFFLINE_PROTOCOL, async (params) => {
    const key = params.url.replace(`${OFFLINE_PROTOCOL}://`, "")
    try {
      if (Capacitor.isNativePlatform()) {
        const result = await Filesystem.readFile({
          path: `tiles/${key}.pbf`,
          directory: Directory.Data,
          encoding: Encoding.UTF8,
        })
        return { data: base64ToArrayBuffer(result.data as string) }
      } else {
        const db = await openDB("ign-tile-store", 1)
        const b64 = await db.get("tiles", key)
        if (!b64) return { data: new ArrayBuffer(0) }
        return { data: base64ToArrayBuffer(b64) }
      }
    } catch {
      return { data: new ArrayBuffer(0) }
    }
  })
  protocolActive = true
}

export const deregisterOfflineProtocol = () => {
  if (!protocolActive) return
  maplibregl.removeProtocol(OFFLINE_PROTOCOL)
  protocolActive = false
}

/** Loads the bundled IGN style and rewrites tile URLs for offline use. */
export const loadOfflineStyle = () => {
  return patchStyleForOffline(ignStyle as StyleSpecification)
}

/** Returns a new style object with tile URLs rewritten to use the offline protocol. */
export const patchStyleForOffline = (
  style: StyleSpecification
): StyleSpecification => {
  const patched = JSON.parse(JSON.stringify(style))
  for (const source of Object.values((patched as any).sources) as any[]) {
    if (Array.isArray(source.tiles)) {
      source.tiles = source.tiles.map((url: string) =>
        url.replace(IGN_TILE_URL, `${OFFLINE_PROTOCOL}://PLAN.IGN/{z}/{x}/{y}`)
      )
    }
  }
  return patched
}
