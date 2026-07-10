import { computed, toValue } from "vue"
import type { MaybeRefOrGetter } from "vue"
import type { Survey, SurveyFollowUp } from "@shared-types/survey"
import type { Membership } from "@shared-types/api"
import { useAuthStore } from "../stores/auth"

export function canRespondToFollowUp(followUp: SurveyFollowUp, memberships: Membership[]): boolean {
  const responders = memberships.filter(
    (m) =>
      m.membershipType === "responder" &&
      m.organisation.id === followUp.organisation?.id,
  )
  // Org-level RESPONDER (pole === null) can respond to any follow-up of that org
  if (responders.some((m) => m.pole === null)) return true
  // Org-level follow-up: any pole-level RESPONDER of that org can respond
  if (followUp.pole === null) return responders.length > 0
  // Pole-specific follow-up: only that pole's RESPONDER can respond
  return responders.some((m) => m.pole?.id === followUp.pole?.id)
}

/**
 * Returns a computed boolean indicating whether the logged-in user can submit
 * at least one follow-up response for the given survey.
 */
export function useCanAddFollowUp(survey: MaybeRefOrGetter<Survey | undefined>) {
  const authStore = useAuthStore()
  return computed(() => {
    const s = toValue(survey)
    if (!s?.followUps.length) return false
    const memberships = authStore.loggedUser?.memberships ?? []
    return s.followUps.some((fu) => canRespondToFollowUp(fu, memberships))
  })
}
