export const oauthErrorMessages: Record<string, string> = {
  invalid_state:
    "La session a expiré ou la connexion n'est pas valide. Veuillez réessayer.",
  missing_params: "Des paramètres sont manquants. Veuillez réessayer.",
  oauth_failed:
    "La connexion avec le portail DSF a échoué. Veuillez réessayer.",
  missing_sub:
    "Votre identifiant DSF n'a pas pu être récupéré. Veuillez réessayer.",
}

export const oauthErrorFallback = "Une erreur est survenue. Veuillez réessayer."
