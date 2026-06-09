type Organisation = {
  id: number
  name: string
}

type Pole = {
  id: number
  name: string
}

type OrganisationWithPoles = {
  id: number
  name: string
  poles: Pole[]
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
  organizations: OrganisationWithPoles[]
  source: string
}

type SurveyDisplay = {
  id: number
  title: string
  organisationName: string | null
  poleName: string | null
  campaignTitle: string | null
  creationDate: string
}

type UserDisplay = {
  id: number
  firstName: string
  lastName: string
}

export {
  LoggedUser,
  Membership,
  Organisation,
  OrganisationWithPoles,
  Pole,
  Response,
  ResponseStatus,
  SurveyDisplay,
  UserDisplay,
}
