import type { SurveyDisplay, SurveySchema } from "./survey"
import type { UserDisplay } from "./user"

export type ResponseStatus = "draft" | "submitted" | "exported"

// Correspond à ResponseSerializer
export interface ResponseWrite {
  survey: number
  respondant: number | null
  data: Record<string, unknown>
  context?: Record<string, unknown>
}

// Correspond à ResponseDisplaySerializer
export interface ResponseDisplay {
  id: number
  survey: SurveyDisplay
  respondant: UserDisplay | null
  status: ResponseStatus
  creationDate: string
}

// Correspond à FullResponseSerializer
export interface ResponseFull {
  id: number
  survey: SurveyFull
  respondant: UserDisplay | null
  data: Record<string, unknown>
  context: Record<string, unknown> | null
  status: ResponseStatus
  creationDate: string
}
