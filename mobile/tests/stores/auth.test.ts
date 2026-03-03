import { vi } from "vitest"
import { describe, it, expect, beforeEach, vi } from "vitest"
import { setActivePinia, createPinia } from "pinia"
import { useAuthStore } from "../../src/stores/auth"
import { Preferences } from "@capacitor/preferences"
import { useApiFetch } from "../../src/utils/data-fetching"

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
  })

  it("loads tokens from storage", async () => {
    ;(Preferences.get as any)
      .mockResolvedValueOnce({ value: "access123" })
      .mockResolvedValueOnce({ value: "refresh123" })

    const store = useAuthStore()
    await store.loadFromStorage()

    expect(store.access).toBe("access123")
    expect(store.refresh).toBe("refresh123")
  })

  it("logs in successfully", async () => {
    const mockJson = vi.fn().mockResolvedValue({
      response: { value: { ok: true } },
      data: { value: { access: "a1", refresh: "r1" } },
    })

    ;(useApiFetch as any).mockReturnValue({
      post: () => ({ json: mockJson }),
    })

    const store = useAuthStore()
    await store.login("john", "secret")

    expect(store.access).toBe("a1")
    expect(store.refresh).toBe("r1")
    expect(Preferences.set).toHaveBeenCalled()
  })

  it("refreshes token successfully", async () => {
    const mockJson = vi.fn().mockResolvedValue({
      response: { value: { ok: true } },
      data: { value: { access: "newAccess" } },
    })

    ;(useApiFetch as any).mockReturnValue({
      post: () => ({ json: mockJson }),
    })

    const store = useAuthStore()
    store.refresh = "refresh123"

    const result = await store.refreshToken()

    expect(result).toBe(true)
    expect(store.access).toBe("newAccess")
  })

  it("logs out if refresh fails", async () => {
    const mockJson = vi.fn().mockResolvedValue({
      response: { value: { ok: false } },
      data: { value: {} },
    })

    ;(useApiFetch as any).mockReturnValue({
      post: () => ({ json: mockJson }),
    })

    const store = useAuthStore()
    store.refresh = "refresh123"

    const result = await store.refreshToken()

    expect(result).toBe(false)
    expect(store.access).toBe(null)
    expect(store.refresh).toBe(null)
  })

  it("bootstrap sets ready to true", async () => {
    ;(Preferences.get as any)
      .mockResolvedValueOnce({ value: null })
      .mockResolvedValueOnce({ value: null })

    const store = useAuthStore()
    await store.bootstrap()

    expect(store.ready).toBe(true)
  })
})
