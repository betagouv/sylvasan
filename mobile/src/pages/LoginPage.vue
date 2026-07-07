<script setup lang="ts">
import { IonContent, IonPage } from "@ionic/vue"
import * as z from "zod"
import { ref } from "vue"
import { ZodError } from "zod"
import { useRouter } from "vue-router"
import { useAuthStore, LoginError } from "../stores/auth"
import { useToastStore } from "../stores/toast"
import { oauthErrorFallback } from "@shared-utils/auth"

const authStore = useAuthStore()
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
const loading = ref(false)

const resetFields = () => {
  payload.value.username = ""
  payload.value.password = ""
  formErrors.value = null
}

const submit = async () => {
  try {
    const validatedData = validator.parse(payload.value)
    loading.value = true
    await authStore.login(validatedData.username, validatedData.password)
    router.push({ name: "PositionPage" })
    resetFields()
  } catch (error) {
    if (error instanceof ZodError) {
      formErrors.value = z.flattenError(error)
    } else if (error instanceof LoginError) {
      if (error.statusCode === 401) {
        toast.show("Identifiant ou mot de passe incorrect.", "error")
      } else if (error.statusCode === 403) {
        toast.show("Ce compte n'est pas encore activé.", "error")
      } else {
        toast.show(oauthErrorFallback, "error")
      }
    } else {
      toast.show(oauthErrorFallback, "error")
    }
  } finally {
    loading.value = false
  }
}

const loginWithDsf = async () => {
  try {
    await authStore.loginWithDsf()
  } catch {
    toast.show("Impossible d'ouvrir la page de connexion DSF. Veuillez réessayer.", "error")
  }
}
</script>

<template>
  <ion-page>
    <ion-content :scrollY="false">
      <div class="flex items-center justify-center min-h-full p-4 box-border!">
        <div class="w-full">
          <h1 class="fr-h2 text-center">Se connecter</h1>

          <DsfrInputGroup
            :error-message="formErrors?.fieldErrors?.username?.[0]"
          >
            <DsfrInput
              v-model="payload.username"
              label="Identifiant ou adresse email"
              labelVisible
              @keyup.enter="submit"
            />
          </DsfrInputGroup>

          <DsfrInputGroup
            :error-message="formErrors?.fieldErrors?.password?.[0]"
          >
            <DsfrInput
              v-model="payload.password"
              label="Mot de passe"
              labelVisible
              type="password"
              @keyup.enter="submit"
            />
          </DsfrInputGroup>

          <div class="fr-mt-4w text-center">
            <DsfrButton
              label="Se connecter"
              :icon="loading ? { name: 'ri-refresh-line', animation: 'spin' } : undefined"
              :disabled="loading"
              @click="submit"
            />
          </div>

          <div class="flex items-center gap-3 fr-mt-4w">
            <hr class="flex-1 border-gray-300" />
            <span class="fr-text--sm text-gray-500">ou</span>
            <hr class="flex-1 border-gray-300" />
          </div>

          <div class="fr-mt-4w text-center">
            <DsfrButton
              label="S'identifier avec un compte DSF"
              secondary
              @click="loginWithDsf"
            />
          </div>
        </div>
      </div>
    </ion-content>
  </ion-page>
</template>

<style scoped>
ion-content::part(background) {
  background: #f5f5fe;
}
</style>
