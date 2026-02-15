<script setup lang="ts">
import { IonContent } from "@ionic/vue"

import * as z from "zod"
import { ref } from "vue"
import { DsfrInput } from "@gouvminint/vue-dsfr"
import { ZodError } from "zod"
import { useRouter } from "vue-router"
import { useApiFetch } from "../utils/data-fetching"
import { useDarkTheme } from "../utils/ui"
import { useAuthStore } from "../stores/auth"

const authStore = useAuthStore()
useDarkTheme()

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

useApiFetch("/auth/test/").post().json()
useApiFetch("/auth/test/").get().json()

const submit = async () => {
  try {
    const validatedData = validator.parse(payload.value)
    await authStore.login(validatedData.username, validatedData.password)
    router.push({ name: "HomePage" })
  } catch (error) {
    if (error instanceof ZodError) formErrors.value = z.flattenError(error)
  }
}
</script>

<template>
  <ion-content>
    <div
      class="text-center w-[90%] p-[5%] absolute top-[50%] translate-y-[-50%]"
    >
      <h1>Se connecter</h1>

      <div class="overflow-auto mb-10">
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
      </div>
      <DsfrButton label="Se connecter" @click="submit" />
    </div>
  </ion-content>
</template>

<style scoped>
ion-content::part(background) {
  background: #1b1b35;
}
</style>
