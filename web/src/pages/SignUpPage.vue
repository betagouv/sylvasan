<route lang="json">
{
  "path": "/creation-de-compte",
  "meta": {
    "title": "Créez votre compte Sylva-San",
    "omitIfLoggedIn": true,
    "sitemap": true
  }
}
</route>

<script setup lang="ts">
import * as z from "zod"
import { ref } from "vue"
import { DsfrInput } from "@gouvminint/vue-dsfr"
import { ZodError } from "zod"
import { useApiFetch } from "../utils/data-fetching"
import { useToastStore } from "../stores/toast"
import { useRouter } from "vue-router"

const toast = useToastStore()
const router = useRouter()

const payload = ref({
  firstName: "",
  lastName: "",
  username: "",
  email: "",
  password: "",
  passwordConfirm: "",
})

const validator = z
  .object({
    firstName: z.string().min(1, "Le prénom est obligatoire"),
    lastName: z.string().optional(),
    username: z.string().min(1, "L'identifiant est obligatoire"),
    email: z.string().email("Adresse email invalide"),
    password: z
      .string()
      .min(8, "Le mot de passe doit contenir au moins 8 caractères"),
    passwordConfirm: z.string().min(1, "Ce champ est obligatoire"),
  })
  .superRefine(({ password, passwordConfirm }, ctx) => {
    if (password !== passwordConfirm) {
      ctx.addIssue({
        code: "custom",
        message: "Les mots de passe ne correspondent pas",
        path: ["passwordConfirm"],
      })
    }
  })

const formErrors = ref<{
  formErrors: string[]
  fieldErrors: Record<string, string[]>
}>({
  formErrors: [],
  fieldErrors: {},
})

function clearFieldError(field: string) {
  if (formErrors.value.fieldErrors[field])
    delete formErrors.value.fieldErrors[field]
}

const apiErrorBody = ref<Record<string, string[]> | null>(null)

const { execute, isFetching, statusCode } = useApiFetch("/auth/register/", {
  immediate: false,
  onFetchError(ctx) {
    apiErrorBody.value = ctx.data ?? null
    return ctx
  },
})
  .post(payload)
  .json()

const submit = async () => {
  formErrors.value = { formErrors: [], fieldErrors: {} }
  apiErrorBody.value = null
  try {
    validator.parse(payload.value)
  } catch (error) {
    if (error instanceof ZodError) formErrors.value = z.flattenError(error)
    return
  }
  await execute()
  if (statusCode.value === 201) {
    toast.show("Compte créé. Vous pouvez maintenant vous connecter.", "success")
    router.push({ name: "/LoginPage" })
    return
  }
  if (statusCode.value === 400 && apiErrorBody.value) {
    formErrors.value = { formErrors: [], fieldErrors: apiErrorBody.value }
    return
  }
  toast.show("Une erreur s'est produite, veuillez réessayer.", "error")
}
</script>

<template>
  <div class="fr-container my-10">
    <h1>Créez votre compte</h1>

    <div class="max-w-lg">
      <div class="flex gap-4">
        <DsfrInputGroup
          class="flex-1"
          :error-message="formErrors.fieldErrors.firstName?.[0]"
        >
          <DsfrInput
            v-model="payload.firstName"
            label="Prénom"
            label-visible
            :required="true"
            @update:model-value="clearFieldError('firstName')"
            @keyup.enter="submit"
          />
        </DsfrInputGroup>
        <DsfrInputGroup
          class="flex-1"
          :error-message="formErrors.fieldErrors.lastName?.[0]"
        >
          <DsfrInput
            v-model="payload.lastName"
            label="Nom"
            label-visible
            @update:model-value="clearFieldError('lastName')"
            @keyup.enter="submit"
          />
        </DsfrInputGroup>
      </div>

      <DsfrInputGroup :error-message="formErrors.fieldErrors.username?.[0]">
        <DsfrInput
          v-model="payload.username"
          label="Identifiant"
          label-visible
          :required="true"
          @update:model-value="clearFieldError('username')"
          @keyup.enter="submit"
        />
      </DsfrInputGroup>

      <DsfrInputGroup :error-message="formErrors.fieldErrors.email?.[0]">
        <DsfrInput
          v-model="payload.email"
          label="Adresse email"
          label-visible
          :required="true"
          type="email"
          @update:model-value="clearFieldError('email')"
          @keyup.enter="submit"
        />
      </DsfrInputGroup>

      <hr />

      <DsfrInputGroup :error-message="formErrors.fieldErrors.password?.[0]">
        <DsfrInput
          v-model="payload.password"
          label="Mot de passe"
          label-visible
          :required="true"
          type="password"
          @update:model-value="clearFieldError('password')"
          @keyup.enter="submit"
        />
      </DsfrInputGroup>

      <DsfrInputGroup
        :error-message="formErrors.fieldErrors.passwordConfirm?.[0]"
      >
        <DsfrInput
          v-model="payload.passwordConfirm"
          label="Confirmer le mot de passe"
          label-visible
          :required="true"
          type="password"
          @update:model-value="clearFieldError('passwordConfirm')"
          @keyup.enter="submit"
        />
      </DsfrInputGroup>

      <hr />
      <DsfrButton
        :disabled="isFetching"
        class="block! w-full!"
        label="Créer mon compte"
        @click="submit"
      />

      <hr class="mt-10! mb-4!" />

      <p class="fr-text--sm text-center">
        Vous avez déjà un compte ?
        <a href="/s-identifier">Se connecter</a>
      </p>
    </div>
  </div>
</template>
