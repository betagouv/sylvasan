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
import { useFetch } from "@vueuse/core"

const data = ref({
  username: "",
  password: "",
})

const validator = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
})

const loginUrl = `${import.meta.env.VITE_API_ROOT}/login/`
const { execute, isFetching, response } = useFetch(
  loginUrl,
  { headers: {} },
  { immediate: false }
)
  .post(data)
  .json()

const submit = async () => {
  try {
    const payload = validator.parse(data.value)
    await execute()
    console.log(response)
  } catch (error) {
    console.log(error)
  }
}
</script>

<template>
  <div class="fr-container">
    <h1>Se connecter</h1>

    <div>
      <DsfrInputGroup :error-message="''">
        <DsfrInput
          v-model="data.username"
          label="Identifiant ou adresse email"
          labelVisible
          @keyup.enter="submit"
        />
      </DsfrInputGroup>

      <DsfrInputGroup :error-message="''" type="password">
        <DsfrInput
          v-model="data.password"
          label="Mot de passe"
          labelVisible
          type="password"
          @keyup.enter="submit"
        />
      </DsfrInputGroup>

      <DsfrButton class="block! w-full!" label="Se connecter" @click="submit" />
    </div>
  </div>
</template>
