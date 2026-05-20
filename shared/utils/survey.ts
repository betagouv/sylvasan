import type {
  SurveyField,
  FieldWidget,
  Condition,
  SimpleCondition,
  ConditionOperator,
} from "../types/survey"

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
    autocomplete: "",
    map: null,
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

  if (
    field?.ui?.widget === "map" &&
    typeof raw === "object" &&
    raw !== null &&
    "lat" in raw &&
    "lon" in raw
  ) {
    const { lat, lon } = raw as { lat: number; lon: number }
    return `Latitude : ${lat}, longitude : ${lon}`
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

export function evaluateCondition(
  condition: Condition,
  formData: Record<string, unknown>
): boolean {
  // Condition composée
  if ("conditions" in condition) {
    if (condition.operator === "and") {
      return condition.conditions.every((c) => evaluateCondition(c, formData))
    } else {
      return condition.conditions.some((c) => evaluateCondition(c, formData))
    }
  }

  // Condition simple
  const fieldValue = formData[condition.field]
  switch (condition.operator) {
    case "eq":
      return fieldValue === condition.value
    case "neq":
      return fieldValue !== condition.value
    case "in":
      return Array.isArray(condition.value)
        ? condition.value.includes(fieldValue)
        : false
    case "not_in":
      return Array.isArray(condition.value)
        ? !condition.value.includes(fieldValue)
        : true
    default:
      return true
  }
}

const operatorLabel: Record<ConditionOperator, string> = {
  eq: "=",
  neq: "≠",
  in: "dans",
  not_in: "pas dans",
}

const formatSimpleCondition = (c: SimpleCondition): string => {
  const val = Array.isArray(c.value) ? c.value.join(", ") : String(c.value)
  return `« ${c.field} » ${operatorLabel[c.operator]} « ${val} »`
}

const formatCondition = (condition: Condition): string => {
  if ("conditions" in condition) {
    const sep = condition.operator === "and" ? " ET " : " OU "
    return condition.conditions.map(formatCondition).join(sep)
  }
  return formatSimpleCondition(condition)
}

export const conditionsText = (condition: Condition): string => {
  return "Affiché si : " + formatCondition(condition)
}
