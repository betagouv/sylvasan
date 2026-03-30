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

export { LoggedUser, Membership, Organisation, Pole }
