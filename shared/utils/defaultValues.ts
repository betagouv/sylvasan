import type { SurveyField } from "@shared-types/survey"

export const getDefaultValue = (field: SurveyField) => {
  if (field.ui?.widget === "date" && field.default === "today") {
    const d = new Date()
    const mm = String(d.getMonth() + 1).padStart(2, "0")
    const dd = String(d.getDate()).padStart(2, "0")
    return `${d.getFullYear()}-${mm}-${dd}`
  }
  return field.default || null
}
