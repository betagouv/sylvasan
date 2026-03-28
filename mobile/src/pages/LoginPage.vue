<script setup lang="ts">
import { IonContent, IonPage } from "@ionic/vue"
import * as z from "zod"
import { ref } from "vue"
import { ZodError } from "zod"
import { useRouter } from "vue-router"
import { useAuthStore } from "../stores/auth"

const authStore = useAuthStore()
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

const resetFields = () => {
  payload.value.username = ""
  payload.value.password = ""
  formErrors.value = null
}

const submit = async () => {
  try {
    const validatedData = validator.parse(payload.value)
    await authStore.login(validatedData.username, validatedData.password)
    router.push({ name: "SurveyListPage" })
    resetFields()
  } catch (error) {
    if (error instanceof ZodError) formErrors.value = z.flattenError(error)
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
            <DsfrButton label="Se connecter" @click="submit" />
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
