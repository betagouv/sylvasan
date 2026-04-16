import type { SurveyDisplay, SurveySchema } from "./survey"
import type { UserDisplay } from "./user"

export type LocalResponseStatus = "draft" | "pending" | "synced"
export type BackendResponseStatus = "draft" | "submitted" | "exported"

export interface LocalResponse {
  localId: string
  surveyId: number
  surveyTitle: string
  backendId?: number // mis une fois que le backend confirme la sauvegarde
  status: LocalResponseStatus
  data: Record<string, unknown>
  context: Record<string, unknown>
  creationDate: string
  modificationDate: string
}

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
  status: BackendResponseStatus
  creationDate: string
}

// Correspond à FullResponseSerializer
export interface ResponseFull {
  id: number
  survey: SurveyFull
  respondant: UserDisplay | null
  data: Record<string, unknown>
  context: Record<string, unknown> | null
  status: BackendResponseStatus
  creationDate: string
}
