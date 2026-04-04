import type { FieldType, FieldWidget } from "@shared-types/survey"

export type WidgetData = {
  type: FieldType
  widget: FieldWidget
  label: string
  icon: string
  color: string
}

export const typeWidgetMapping: Record<FieldWidget, WidgetData> = {
  input: {
    type: "string",
    widget: "input",
    label: "Texte",
    icon: "ri-input-method-line",
    color: "#50d71e",
  },
  number: {
    type: "number",
    widget: "number",
    label: "Numérique",
    icon: "ri-numbers-line",
    color: "",
  },
  select: {
    type: "string",
    widget: "select",
    label: "Liste déroulante",
    icon: "ri-dropdown-list",
    color: "",
  },
  checkbox: {
    type: "string",
    widget: "checkbox",
    label: "Cases à cocher",
    icon: "ri-list-check-3",
    color: "",
  },
  textarea: {
    type: "string",
    widget: "textarea",
    label: "Texte multi-ligne",
    icon: "ri-align-left",
    color: "",
  },
  radio: {
    type: "string",
    widget: "radio",
    label: "Boutons radio",
    icon: "ri-list-radio",
    color: "",
  },
  date: {
    type: "string",
    widget: "date",
    label: "Date",
    icon: "ri-calendar-line",
    color: "",
  },
}
