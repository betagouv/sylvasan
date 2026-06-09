import type { SurveyField } from "../types/survey"

/**
 * Validation d'un champ considérant les règles dans "validation"
 * null si tout est OK, sinon message d'erreur
 */
export function validateField(
  field: SurveyField,
  value: unknown
): string | null {
  const v = field.validation

  if (field.required) {
    if (isEmpty(value)) return "Ce champ est obligatoire"
  }

  // Rien d'autre à valider si le champ est vide
  if (isEmpty(value)) return null

  const widget = field.ui?.widget

  // Number
  if (widget === "number") {
    const num = Number(value)

    if (isNaN(num)) return "La valeur doit être un nombre"

    if (v?.numberType === "integer" && !Number.isInteger(num))
      return "La valeur doit être un nombre entier"

    if (v?.min !== undefined && num < Number(v.min))
      return `La valeur doit être supérieure ou égale à ${v.min}`

    if (v?.max !== undefined && num > Number(v.max))
      return `La valeur doit être inférieure ou égale à ${v.max}`
  }

  // Date
  if (widget === "date" && typeof value === "string") {
    if (v?.min !== undefined && value < String(v.min))
      return `La date doit être après le ${formatDate(String(v.min))}`

    if (v?.max !== undefined && value > String(v.max))
      return `La date doit être avant le ${formatDate(String(v.max))}`
  }

  // String
  if (
    (widget === "input" || widget === "autocomplete") &&
    typeof value === "string"
  ) {
    if (v?.minLength !== undefined && value.length < v.minLength)
      return `La valeur doit contenir au moins ${v.minLength} caractère(s)`

    if (v?.maxLength !== undefined && value.length > v.maxLength)
      return `La valeur doit contenir au plus ${v.maxLength} caractère(s)`
  }

  // Array
  if (widget === "array" || widget === "checkboxes" || widget === "image") {
    const arr = Array.isArray(value) ? value : []

    if (v?.minItems !== undefined && arr.length < v.minItems)
      return `Au moins ${v.minItems} élément(s) requis`

    if (v?.maxItems !== undefined && arr.length > v.maxItems)
      return `Au plus ${v.maxItems} élément(s) autorisés`
  }

  return null
}

/**
 * Execute la validation sur chaque champ. Prend en compte seulement
 * les champs visibles.
 */
export function validateResponse(
  fields: SurveyField[],
  data: Record<string, unknown>,
  visibleFieldIds?: Set<string>
): Record<string, string> {
  const errors: Record<string, string> = {}

  for (const field of fields) {
    if (visibleFieldIds && !visibleFieldIds.has(field.id)) continue

    const error = validateField(field, data[field.id] ?? null)
    if (error) errors[field.id] = error

    if (field.fields && Array.isArray(data[field.id])) {
      const items = data[field.id] as Record<string, unknown>[]
      for (const item of items) {
        const subFields: SurveyField[] = field.fields!
        for (const subField of subFields) {
          const subError = validateField(subField, item[subField.id] ?? null)
          if (subError) {
            const key = `${field.id}.${subField.id}`
            if (!errors[key]) errors[key] = subError
          }
        }
      }
    }
  }

  return errors
}

function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined || value === "") return true
  if (Array.isArray(value) && value.length === 0) return true
  return false
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString("fr-FR", {
      day: "numeric",
      month: "long",
      year: "numeric",
    })
  } catch {
    return iso
  }
}
