<route lang="json">
{
  "path": "/s-identifier",
  "meta": {
    "title": "S'identifier",
    "omitIfLoggedIn": true,
    "sitemap": true
  }
}
</route>

<script setup lang="ts">
import * as z from "zod"
import { ref, computed } from "vue"
import { DsfrInput } from "@gouvminint/vue-dsfr"
import { useApiFetch } from "../utils/data-fetching"
import { ZodError } from "zod"
import { useRootStore } from "../stores/root"
import { useToastStore } from "../stores/toast"
import { useRouter, useRoute } from "vue-router"

const store = useRootStore()
const toast = useToastStore()
const router = useRouter()
const route = useRoute()

const dsfLoginUrl =
  import.meta.env.VITE_API_ROOT.replace(/\/api$/, "") + "/dsf/oauth/web/login/"

const oauthErrorMessages: Record<string, string> = {
  invalid_state:
    "La session a expiré ou la connexion n'est pas valide. Veuillez réessayer.",
  missing_params: "Des paramètres sont manquants. Veuillez réessayer.",
  oauth_failed:
    "La connexion avec le portail DSF a échoué. Veuillez réessayer.",
  missing_sub:
    "Votre identifiant DSF n'a pas pu être récupéré. Veuillez réessayer.",
}

const oauthError = computed(() => {
  const code = route.query.error as string | undefined
  return code
    ? oauthErrorMessages[code] ?? "Une erreur est survenue. Veuillez réessayer."
    : null
})

const payload = ref({
  username: "",
  password: "",
})

const validator = z.object({
  username: z.string().min(1, "Ce champ ne peut pas être vide"),
  password: z.string().min(1, "Ce champ ne peut pas être vide"),
})

const formErrors = ref<any>()

const { execute, isFetching, data, statusCode } = useApiFetch("/auth/login/", {
  immediate: false,
})
  .post(payload)
  .json()

const submit = async () => {
  try {
    validator.parse(payload.value)
    await execute()
    if (statusCode.value === 401) {
      toast.show("Identifiant ou mot de passe incorrect.", "error")
      return
    }
    store.setLoggedUser(data.value.user)
    toast.show(`Bienvenue ${data.value.user.firstName}`, "success")
    router.push({ name: "/DashboardPage" })
  } catch (error) {
    if (error instanceof ZodError) formErrors.value = z.flattenError(error)
  }
}
</script>

<template>
  <div class="fr-container my-10">
    <h1>Se connecter</h1>

    <div class="max-w-md">
      <DsfrAlert
        v-if="oauthError"
        type="error"
        title="Erreur"
        :description="oauthError"
        class="mb-6"
      />

      <DsfrInputGroup :error-message="formErrors?.fieldErrors?.username">
        <DsfrInput
          v-model="payload.username"
          label="Identifiant ou adresse email"
          labelVisible
          @keyup.enter="submit"
        />
      </DsfrInputGroup>

      <DsfrInputGroup
        :error-message="formErrors?.fieldErrors?.password"
        type="password"
      >
        <DsfrInput
          v-model="payload.password"
          label="Mot de passe"
          labelVisible
          type="password"
          @keyup.enter="submit"
        />
      </DsfrInputGroup>

      <DsfrButton
        :disabled="isFetching"
        class="block! w-full!"
        label="Se connecter"
        @click="submit"
      />

      <hr class="mt-10! mb-4!" />

      <a
        :href="dsfLoginUrl"
        class="fr-btn fr-btn--secondary block! w-full! text-center!"
      >
        S'identifier avec un compte DSF
      </a>
    </div>
  </div>
</template>
