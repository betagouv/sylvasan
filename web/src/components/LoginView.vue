<script setup lang="ts">
import * as z from "zod"
import { ref } from "vue"
import { DsfrInput } from "@gouvminint/vue-dsfr"

const data = ref({
  username: "",
  password: "",
})

const validator = z.object({
  username: z.string().min(1),
  password: z.string().min(1),
})

const submit = () => {
  try {
    const payload = validator.parse(data.value)
    console.log(payload)
  } catch (error) {
    console.log(error)
  }
}
</script>

<template>
  <div class="fr-container">
    <h1>Se connecter</h1>

    <form @submit="submit">
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
          @keyup.enter="submit"
        />
      </DsfrInputGroup>

      <DsfrButton class="block! w-full!" label="Se connecter" @click="submit" />
    </form>
  </div>
</template>
