// TODO : ceci est un dupliqué de ce qu'il y a dans web. Factor out.

export type FieldType =
  | "text"
  | "textarea"
  | "number"
  | "date"
  | "vocabulary_select"

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
  min?: number
  max?: number
  required_if?: Condition
}

export interface SurveyField {
  id: string
  type: FieldType
  label: string
  required?: boolean
  vocabulary?: string
  condition?: Condition
  validation?: FieldValidation
}

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
