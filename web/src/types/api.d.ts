type Membership = {
  organisation: number
  pole: number | null
  membershipType: string
}

type LoggedUser = {
  firstName: string
  lastName?: string
  username: string
  id: number
  memberships: Membership[]
}

export { LoggedUser, Membership }
