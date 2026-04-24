import { defineStore } from "pinia"

import type { ToastType, Toast } from "@shared-types/toast"

export const useToastStore = defineStore("toast", {
  state: () => ({
    toasts: [] as Toast[],
  }),

  actions: {
    show(message: string, type: ToastType = "info", timeout = 4000) {
      const id = crypto.randomUUID()

      this.toasts.push({ id, message, type, timeout })

      setTimeout(() => {
        this.dismiss(id)
      }, timeout)
    },

    dismiss(id: string) {
      this.toasts = this.toasts.filter((t) => t.id !== id)
    },
  },
})
