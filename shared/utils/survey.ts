import type { SurveyField, FieldWidget } from "../types/survey"

export const getEmptyValue = (field: SurveyField): any => {
  if (!field.ui?.widget) return ""
  const mapping: Record<FieldWidget, any> = {
    input: "",
    number: "",
    select: "",
    checkboxes: Array(),
    switch: false,
    radio: Array(),
    date: "",
    array: Array(),
  }
  return mapping[field.ui.widget]
}

export const resolveFieldValue = (
  field: SurveyField | undefined,
  raw: unknown
): string => {
  if (field?.ui?.widget === "switch") {
    if (raw === true) return field.ui.activeText ?? "Oui"
    if (raw === false) return field.ui.inactiveText ?? "Non"
    return ""
  }

  const choices = field?.ui?.choices
  if (!choices || !choices.length) return String(raw)

  if (field?.ui?.widget === "select") {
    const match = choices.find((c: any) => c.value === raw)
    return match ? (match as any).text ?? String(raw) : String(raw)
  }

  if (field?.ui?.widget === "radio") {
    const match = choices.find((c: any) => c.value === raw)
    return match ? (match as any).label ?? String(raw) : String(raw)
  }

  if (field?.ui?.widget === "checkboxes" && Array.isArray(raw)) {
    const labels = raw.map((v) => {
      const match = choices.find((c: any) => c.value === v)
      return match ? (match as any).label ?? String(v) : String(v)
    })
    return labels.join(", ") || ""
  }

  return String(raw)
}
