type Organisation = {
  id: number
  name: string
}

type Pole = {
  id: number
  name: string
}

type Membership = {
  organisation: Organisation
  pole: Pole | null
  membershipType: string
}

type LoggedUser = {
  firstName: string
  lastName?: string
  username: string
  id: number
  memberships: Membership[]
}

type SurveyDisplay = {
  id: number
  title: string
  organisationName: string | null
  poleName: string | null
  campaignTitle: string | null
}

type UserDisplay = {
  id: number
  firstName: string
  lastName: string
}

type ResponseStatus = "draft" | "submitted" | "exported"

type Response = {
  id: number
  survey: SurveyDisplay
  respondant: UserDisplay | null
  status: ResponseStatus
  creationDate: string
}

export {
  LoggedUser,
  Membership,
  Organisation,
  Pole,
  Response,
  ResponseStatus,
  SurveyDisplay,
  UserDisplay,
}
