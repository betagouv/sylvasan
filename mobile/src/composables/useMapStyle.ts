import { ref } from "vue"
import type { StyleSpecification } from "maplibre-gl"

export type MapStyleKey = "vector" | "satellite"

export interface MapStyleOption {
  label: string
  icon: string
}

export const IGN_SATELLITE_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    orthophotos: {
      type: "raster",
      tiles: [
        "https://data.geopf.fr/wmts?layer=HR.ORTHOIMAGERY.ORTHOPHOTOS&style=normal&tilematrixset=PM&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image%2Fjpeg&TileMatrix={z}&TileCol={x}&TileRow={y}",
      ],
      tileSize: 256,
      maxzoom: 19,
    },
  },
  layers: [{ id: "orthophotos", type: "raster", source: "orthophotos" }],
}

export const MAP_STYLE_OPTIONS: Record<MapStyleKey, MapStyleOption> = {
  vector: { label: "Carte IGN", icon: "ri-map-2-line" },
  satellite: { label: "Photos aériennes", icon: "ri-radar-line" },
}

export function useMapStyle(initial: MapStyleKey = "vector") {
  const activeStyle = ref<MapStyleKey>(initial)
  return { activeStyle }
}
