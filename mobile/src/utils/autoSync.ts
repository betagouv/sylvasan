import { App } from "@capacitor/app"
import { useAuthStore } from "../stores/auth"
import { useSyncStore } from "../stores/sync"

export const setupAutoSync = async () => {
  const auth = useAuthStore()
  const syncStore = useSyncStore()

  if (auth.isLoggedIn) {
    await syncStore.bootstrap()
  }

  let syncInterval: ReturnType<typeof setInterval> | null = null

  const startSyncInterval = () => {
    syncInterval = setInterval(() => {
      if (auth.isLoggedIn) syncStore.syncAll().catch(() => {})
    }, 60000)
  }

  const stopSyncInterval = () => {
    if (syncInterval !== null) {
      clearInterval(syncInterval)
      syncInterval = null
    }
  }

  startSyncInterval()

  App.addListener("appStateChange", ({ isActive }: { isActive: boolean }) => {
    if (isActive) {
      if (auth.isLoggedIn) syncStore.syncAll().catch(() => {})
      startSyncInterval()
    } else {
      stopSyncInterval()
    }
  })
}
