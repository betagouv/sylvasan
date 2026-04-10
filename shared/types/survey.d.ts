export type FieldType = "string" | "number" | "boolean" | "array"

export type ConditionOperator = "eq" | "neq" | "in" | "not_in"
export type LogicalOperator = "and" | "or"

export interface SimpleCondition {
  field: string
  operator: ConditionOperator
  value: unknown
}

export interface CompoundCondition {
  operator: LogicalOperator
  conditions: Condition[]
}

export type Condition = SimpleCondition | CompoundCondition

export interface FieldValidation {
  maxLength?: number
  minLength?: number
  min?: number | string
  max?: number | string
  required_if?: Condition
}

export interface FieldUI {
  widget?: FieldWidget
  choices?: DsfrSelectOption[] | DsfrCheckboxProps[]
  hint?: string
  placeholder?: string
  textarea?: boolean
  activeText?: string
  inactiveText?: string
}

export interface SurveyField {
  id: string
  type: FieldType
  label: string
  required?: boolean
  vocabulary?: string
  condition?: Condition
  validation?: FieldValidation
  ui?: FieldUI
}

export type FieldWidget =
  | "input"
  | "number"
  | "select"
  | "radio"
  | "checkboxes"
  | "switch"
  | "date"

export interface SurveyPage {
  id: string
  title?: string
  fields: string[]
}

export interface SurveySchema {
  version: string
  fields: SurveyField[]
  pages?: SurveyPage[]
}

export interface Survey {
  id: number
  title: string
  jsonSchema: SurveySchema
  surveyType: string
}
