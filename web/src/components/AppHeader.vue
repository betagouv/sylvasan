<script setup lang="ts">
import { computed } from "vue"
import { useRootStore } from "../stores/root"
import { useToastStore } from "../stores/toast"
// import imgUrl from "../assets/logo.png"
import { useApiFetch } from "../utils/data-fetching"
import { useRouter } from "vue-router"

const router = useRouter()
const store = useRootStore()

const toast = useToastStore()

// const environment = window.ENVIRONMENT
defineProps({ logoText: Array })
const navItems = computed(() => {
  const links = [
    {
      to: "/accueil",
      text: "Accueil",
    },
  ]
  if (store.loggedUser)
    links.push({
      to: "/dashboard",
      text: "Tableau de bord",
    })
  return links
})

const quickLinks = computed(() => {
  if (store.loggedUser)
    return [
      {
        label: "Se déconnecter",
        icon: "ri-logout-circle-line",
        button: true,
        onClick: logout,
      },
    ]
  else
    return [
      {
        label: "Se connecter",
        icon: "ri-login-circle-line",
        to: "/s-identifier",
      },
    ]
})

const logout = async () => {
  await useApiFetch("/auth/logout/").post()
  store.setLoggedUser(null)
  toast.show("Déconnexion réussite", "success")
  router.push({ name: "/HomePage" })
}
</script>

<template>
  <DsfrHeader
    :logo-text="logoText"
    :homeTo="{ name: '/HomePage' }"
    :quickLinks="quickLinks"
    homeLabel="Accueil - SylvaSan - Ministère de l'Agriculture, de l'Agro-alimentaire et de la Souveraineté Alimentaire"
  >
    <template #operator>
      <div class="flex items-center">
        <!-- <img :src="imgUrl" alt="SylvaSan" class="h-10 object-contain" /> -->
        <p class="font-bold">SylvaSan</p>
      </div>
    </template>
    <template #mainnav>
      <DsfrNavigation
        :nav-items="navItems"
        :class="{ 'last-link-right': store.loggedUser }"
      />
    </template>
  </DsfrHeader>
</template>

<style>
.fr-header__menu:not(.fr-modal--opened)
  nav.last-link-right
  > ul
  > li:last-child {
  margin-left: auto;
}
</style>
