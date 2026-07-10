import { computed, ref, watch } from "vue"
import { useRootStore } from "../stores/root.ts"

/**
 * Gestion de la sélection organisation / pôle pour les formulaires de création
 * et de modification d'enquêtes et de suivis.
 *
 * Retourne les refs mutables selectedOrganisationId et selectedPoleOption afin
 * que les callbacks onFetchResponse puissent pré-remplir les sélecteurs lors
 * d'une modification.
 */
export function useAdminScopeSelection() {
  const store = useRootStore()

  const adminMemberships = computed(() =>
    store.loggedUser?.memberships.filter((x) => x.membershipType === "admin")
  )

  // Organisations uniques parmi les rôles admin (un utilisateur peut avoir plusieurs
  // rôles dans la même organisation, ex. admin de deux pôles distincts)
  const uniqueAdminOrgs = computed(() => {
    const seen = new Set<number>()
    return (adminMemberships.value ?? [])
      .filter((m) => {
        if (seen.has(m.organisation.id)) return false
        seen.add(m.organisation.id)
        return true
      })
      .map((m) => m.organisation)
  })

  const orgOptions = computed(() =>
    uniqueAdminOrgs.value.map((org) => ({
      text: org.name,
      value: String(org.id),
    }))
  )

  const selectedOrganisationId = ref<string>("")

  const organisation = computed(() => {
    if (uniqueAdminOrgs.value.length === 1) return uniqueAdminOrgs.value[0].id
    return selectedOrganisationId.value
      ? Number(selectedOrganisationId.value)
      : undefined
  })

  // L'utilisateur a un rôle admin au niveau organisation (pole === null) pour l'org sélectionnée
  const hasOrgLevelAdmin = computed(
    () =>
      adminMemberships.value?.some(
        (m) => m.organisation.id === organisation.value && m.pole === null
      ) ?? false
  )

  // Pôles auxquels l'utilisateur a un rôle admin explicite dans l'org sélectionnée
  const adminPoles = computed(
    () =>
      adminMemberships.value
        ?.filter(
          (m) => m.organisation.id === organisation.value && m.pole !== null
        )
        .map((m) => m.pole!) ?? []
  )

  // Pôles de l'org sélectionnée issus du profil utilisateur (déjà chargés au login)
  const orgPoles = computed(
    () =>
      store.loggedUser?.organisations.find((o) => o.id === organisation.value)
        ?.poles ?? []
  )

  // Toutes les valeurs sont des strings pour éviter les problèmes de coercition du DsfrSelect :
  // "" = aucun pôle, "123" = pôle avec id 123
  const poleOptions = computed(() => {
    const opts: { text: string; value: string }[] = []
    if (hasOrgLevelAdmin.value) {
      // Les admins org voient "Aucun pôle" + tous les pôles de l'organisation
      opts.push({ text: "Tous les pôles (niveau organisation)", value: "" })
      for (const p of orgPoles.value) {
        opts.push({ text: p.name, value: String(p.id) })
      }
    } else {
      // Les admins pôle voient uniquement leurs pôles explicites
      for (const p of adminPoles.value) {
        opts.push({ text: p.name, value: String(p.id) })
      }
    }
    return opts
  })

  // Le sélecteur n'est affiché que s'il y a un vrai choix à faire
  const showPoleSelect = computed(() => poleOptions.value.length > 1)

  const selectedPoleOption = ref<string>(
    poleOptions.value.length === 1 ? poleOptions.value[0].value : ""
  )

  // Remise à zéro quand l'organisation change pour éviter une valeur obsolète
  watch(organisation, () => {
    selectedPoleOption.value = ""
  })

  // null → ressource au niveau organisation ; number → ressource rattachée à un pôle
  const pole = computed(() =>
    selectedPoleOption.value !== "" ? Number(selectedPoleOption.value) : null
  )

  return {
    selectedOrganisationId,
    selectedPoleOption,
    organisation,
    pole,
    orgOptions,
    poleOptions,
    showPoleSelect,
    hasOrgLevelAdmin,
    uniqueAdminOrgs,
  }
}
