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
import { oauthErrorMessages, oauthErrorFallback } from "@shared-utils/auth"

const store = useRootStore()
const toast = useToastStore()
const router = useRouter()
const route = useRoute()

const dsfLoginUrl =
  import.meta.env.VITE_API_ROOT.replace(/\/api$/, "") + "/dsf/oauth/web/login/"

const oauthError = computed(() => {
  const code = route.query.error as string | undefined
  return code ? (oauthErrorMessages[code] ?? oauthErrorFallback) : null
})

const verificationFailed = computed(() => !!route.query.verification_failed)

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
    if (statusCode.value === 403) {
      router.push({ name: "/AccountNotActivatedPage", query: { identifier: payload.value.username } })
      return
    }
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

    <div class="grid grid-cols-1 md:grid-cols-2 md:gap-16 lg:gap-24">
      <div>
        <DsfrAlert
          v-if="verificationFailed"
          type="error"
          title="Lien invalide"
          description="Le lien de vérification est invalide ou expiré. Veuillez créer un nouveau compte."
          class="mb-6"
        />
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

        <div class="flex flex-col gap-2">
          <DsfrButton
            :disabled="isFetching"
            class="block! w-full!"
            label="Se connecter"
            @click="submit"
          />
          <a
            href="/creation-de-compte"
            class="fr-btn fr-btn--tertiary block! w-full! text-center!"
          >
            Créer un compte Sylva-San
          </a>

          <p class="mt-4!">
            <a href="/platform/reinitialisation-mot-de-passe">
              J'ai perdu mon mot de passe
            </a>
          </p>
        </div>
      </div>

      <div class="border border-gray-300 p-6">
        <h3>Vous avez déjà un compte DSF&nbsp;?</h3>
        <p>Connectez-vous avec vos identifiants du portail DSF.</p>
        <a
          :href="dsfLoginUrl"
          class="fr-btn fr-btn--secondary block! w-full! text-center!"
        >
          S'identifier avec un compte DSF
        </a>
      </div>
    </div>
  </div>
</template>
