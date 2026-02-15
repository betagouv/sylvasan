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
import { ref } from "vue"
import { DsfrInput } from "@gouvminint/vue-dsfr"
import { useApiFetch } from "../utils/data-fetching"
import { ZodError } from "zod"
import { useRootStore } from "../stores/root"
import { useToastStore } from "../stores/toast"
import { useRouter } from "vue-router"

const store = useRootStore()
const toast = useToastStore()
const router = useRouter()

const payload = ref({
  username: "",
  password: "",
})

const validator = z.object({
  username: z.string().min(1, "Ce champ ne peut pas être vide"),
  password: z.string().min(1, "Ce champ ne peut pas être vide"),
})

const formErrors = ref<any>()

const { execute, isFetching, data } = useApiFetch("/auth/login/", {
  immediate: false,
})
  .post(payload)
  .json()

const submit = async () => {
  try {
    validator.parse(payload.value)
    await execute()
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
    </div>
  </div>
</template>
