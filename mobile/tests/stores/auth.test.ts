import { describe, it, expect, beforeEach, vi } from "vitest"
import { setActivePinia, createPinia } from "pinia"
import { useAuthStore } from "../../src/stores/auth"
import { Preferences } from "@capacitor/preferences"
import { useApiFetch } from "../../src/utils/data-fetching"
import { setupApiMocks } from "./mocks/api"

vi.mock("@capacitor/preferences", () => ({
  Preferences: {
    get: vi.fn(),
    set: vi.fn(),
    remove: vi.fn(),
  },
}))

vi.mock("../../src/utils/data-fetching", () => ({
  useApiFetch: vi.fn(),
}))

describe("auth store", () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    setupApiMocks()
  })

  it("logs in successfully and fetches user", async () => {
    const store = useAuthStore()
    await store.login("jean", "secret")

    expect(store.access).toBe("a1")
    expect(store.refresh).toBe("r1")
    expect(store.loggedUser.username).toEqual("jean")
    expect(store.loggedUser.id).toEqual(1)
  })

  it("throws on failed login", async () => {
    setupApiMocks({ tokenOk: false }) // override just the token endpoint

    const store = useAuthStore()
    await expect(store.login("jean", "wrong")).rejects.toThrow("login failed")
  })

  it("fetchUser does nothing if response is not ok", async () => {
    setupApiMocks({ meOk: false }) // override just /api/me/

    const store = useAuthStore()
    await store.fetchUser()

    expect(store.loggedUser).toBeNull()
  })

  it("logs out if refresh fails", async () => {
    setupApiMocks({ refreshOk: false })

    const store = useAuthStore()
    store.refresh = "refresh123"

    const result = await store.refreshToken()

    expect(result).toBe(false)
    expect(store.access).toBeNull()
  })
})
