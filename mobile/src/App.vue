<script setup lang="ts">
import { onMounted, onUnmounted } from "vue"
import { IonApp, IonRouterOutlet, loadingController } from "@ionic/vue"
import { App } from "@capacitor/app"
import type { PluginListenerHandle } from "@capacitor/core"
import { useRouter } from "vue-router"
import ToastContainer from "./components/ToastContainer.vue"
import { useAuthStore } from "./stores/auth"
import { useToastStore } from "./stores/toast"

const authStore = useAuthStore()
const toast = useToastStore()
const router = useRouter()
let urlOpenListener: PluginListenerHandle | null = null
let oauthHandled = false

const handleOAuthCallback = async (url: string) => {
  if (oauthHandled) return
  oauthHandled = true
  const loading = await loadingController.create({ message: "Connexion en cours…" })
  await loading.present()

  try {
    await authStore.handleDsfCallback(url)
    router.replace({ name: "PositionPage" })
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e)
    toast.show(`Échec de la connexion DSF : ${message}`, "error", 8000)
    router.replace({ name: "LoginPage" })
  } finally {
    await loading.dismiss()
  }
}

onMounted(async () => {
  urlOpenListener = await App.addListener("appUrlOpen", async ({ url }) => {
    if (!url.startsWith("sylvasan://oauth/callback")) return
    await handleOAuthCallback(url)
  })

  // Gère le cas où l'app a été lancée à froid par l'URL de callback OAuth
  const launchUrl = await App.getLaunchUrl()
  if (launchUrl?.url?.startsWith("sylvasan://oauth/callback")) {
    await handleOAuthCallback(launchUrl.url)
  }
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
