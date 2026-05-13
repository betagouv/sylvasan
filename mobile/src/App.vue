<script setup lang="ts">
import { onMounted, onUnmounted } from "vue"
import { IonApp, IonRouterOutlet } from "@ionic/vue"
import { App } from "@capacitor/app"
import type { PluginListenerHandle } from "@capacitor/core"
import { useRouter } from "vue-router"
import ToastContainer from "./components/ToastContainer.vue"
import { useAuthStore } from "./stores/auth"

const authStore = useAuthStore()
const router = useRouter()
let urlOpenListener: PluginListenerHandle | null = null

onMounted(async () => {
  urlOpenListener = await App.addListener("appUrlOpen", async ({ url }) => {
    if (!url.startsWith("sylvasan://oauth/callback")) return
    try {
      await authStore.handleDsfCallback(url)
      router.replace({ name: "PositionPage" })
    } catch {
      router.replace({ name: "LoginPage" })
    }
  })
})

onUnmounted(() => {
  urlOpenListener?.remove()
})
</script>

<template>
  <ion-app>
    <ToastContainer />
    <ion-router-outlet></ion-router-outlet>
  </ion-app>
</template>
