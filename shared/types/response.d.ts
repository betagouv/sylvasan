import type {
  Survey,
  SurveyDisplay,
  SurveyFollowUp,
  SurveySchema,
} from "./survey"
import type { UserDisplay } from "./api"

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
  surveyFollowUp: SurveyFollowUp | null
  parentResponse: number | null
}

// Correspond à ResponseSerializer
export interface ResponseWrite {
  survey: number
  respondant: number | null
  data: Record<string, unknown>
  context?: Record<string, unknown>
}

// Correspond à FollowUpResponseSerializer
export interface FollowUpResponseWrite {
  surveyFollowUp: number
  parentResponse: number
  data: Record<string, unknown>
  context?: Record<string, unknown>
}

// Correspond à GeoResponseSerializer
export interface ResponseGeo {
  id: number
  surveyId: number | null
  surveyTitle: string | null
  status: BackendResponseStatus
  creationDate: string
  lat: number
  lon: number
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
  survey: Survey | null
  surveyFollowUp: SurveyFollowUp | null
  parentResponse: number | null
  respondant: UserDisplay | null
  data: Record<string, unknown>
  context: Record<string, unknown> | null
  status: BackendResponseStatus
  creationDate: string
}
