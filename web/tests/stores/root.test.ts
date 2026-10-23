import { describe, it, expect, beforeEach } from "vitest"
import { setActivePinia, createPinia } from "pinia"
import { useRootStore } from "../../src/stores/root"

import { vi } from "vitest"

vi.mock("../../src/utils/data-fetching", () => {
  return {
    useApiFetch: (url: string) => {
      if (url === "/auth/me/") {
        const data = { value: null as any }
        return {
          json: () => ({
            data,
            execute: async () => {
              data.value = { firstName: "Lena", lastName: "Cordier" }
            },
          }),
        }
      }

      return {
        json: () => ({ data: { value: null }, execute: async () => {} }),
      }
    },
  }
})

describe("root store", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it("sets logged user", () => {
    const store = useRootStore()

    store.setLoggedUser({
      firstName: "Anne",
      lastName: "Yversaire",
    } as any)

    expect(store.loggedUser?.firstName).toBe("Anne")
  })

  it("fetches initial data", async () => {
    const store = useRootStore()

    await store.fetchInitialData()

    expect(store.loggedUser?.firstName).toBe("Lena")
    expect(store.initialDataLoaded).toBe(true)
  })
})
