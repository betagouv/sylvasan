import { useScheme } from "@gouvminint/vue-dsfr"
import type { UseSchemeResult } from "@gouvminint/vue-dsfr"
const { setScheme } = useScheme() as UseSchemeResult

export const useLightTheme = () => setScheme("light")

export const useDarkTheme = () => setScheme("dark")
