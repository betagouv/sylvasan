import type { FieldType, FieldWidget } from "@shared-types/survey"

export type WidgetData = {
  type: FieldType
  widget: FieldWidget
  label: string
  icon: string
}

export const typeWidgetMapping: Record<FieldWidget, WidgetData> = {
  input: {
    type: "string",
    widget: "input",
    label: "Texte",
    icon: "ri-input-method-line",
  },
  number: {
    type: "number",
    widget: "number",
    label: "Numérique",
    icon: "ri-numbers-line",
  },
  select: {
    type: "string",
    widget: "select",
    label: "Liste déroulante",
    icon: "ri-dropdown-list",
  },
  checkboxes: {
    type: "array",
    widget: "checkboxes",
    label: "Cases à cocher",
    icon: "ri-list-check-3",
  },
  switch: {
    type: "boolean",
    widget: "switch",
    label: "Interrupteur",
    icon: "ri-toggle-line",
  },
  radio: {
    type: "string",
    widget: "radio",
    label: "Boutons radio",
    icon: "ri-list-radio",
  },
  date: {
    type: "string",
    widget: "date",
    label: "Date",
    icon: "ri-calendar-line",
  },
  array: {
    type: "array",
    widget: "array",
    label: "Liste d'objets",
    icon: "ri-layout-horizontal-line",
  },
}
