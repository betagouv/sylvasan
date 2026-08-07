import { describe, it, expect, beforeEach, vi } from "vitest"
import { setActivePinia, createPinia } from "pinia"
import { useResponsesStore } from "../../src/stores/responses"
import { useApiFetch } from "../../src/utils/data-fetching"
import type { LocalResponse } from "@shared-types/response"

vi.mock("@capacitor/preferences", () => ({
  Preferences: {
    get: vi.fn().mockResolvedValue({ value: null }),
    set: vi.fn().mockResolvedValue(undefined),
    remove: vi.fn().mockResolvedValue(undefined),
  },
}))

vi.mock("../../src/utils/data-fetching", () => ({
  useApiFetch: vi.fn(),
}))

vi.mock("../../src/utils/imageStorage", () => ({
  loadImagesFromFilesystem: vi.fn((data) => Promise.resolve(data)),
  deleteLocalImages: vi.fn(() => Promise.resolve()),
}))

// Réponse API simulant un POST réussi
const OK_POST = { response: { value: { ok: true } }, data: { value: null } }
// Réponse API simulant un POST échoué
const FAIL_POST = { response: { value: { ok: false, status: 500 } }, data: { value: null } }
// Réponse GET /mobile/responses/ vide
const EMPTY_GET = { response: { value: { ok: true } }, data: { value: [] } }

function makePostMock(result: typeof OK_POST | typeof FAIL_POST) {
  return {
    post: () => ({ json: () => Promise.resolve(result) }),
  }
}

function makeGetMock(result: typeof EMPTY_GET) {
  return {
    get: () => ({ json: () => Promise.resolve(result) }),
  }
}

function makePending(localId: string, surveyId = 1): LocalResponse {
  return {
    localId,
    surveyId,
    surveyTitle: "Enquête test",
    status: "pending",
    data: {},
    context: {},
    creationDate: new Date().toISOString(),
    modificationDate: new Date().toISOString(),
    surveyFollowUp: null,
    parentResponse: null,
  }
}

describe("responses store", () => {
  let store: ReturnType<typeof useResponsesStore>

  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    store = useResponsesStore()
  })

  describe("sync()", () => {
    it("bails immediately when already syncing", async () => {
      store.localResponses = [makePending("a")]
      store.syncing = true

      await store.sync()

      expect(useApiFetch).not.toHaveBeenCalled()
    })

    it("retries a pending response and removes it on success", async () => {
      store.localResponses = [makePending("a")]

      ;(useApiFetch as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
        if (url === "/responses/") return makePostMock(OK_POST)
        if (url === "/mobile/responses/") return makeGetMock(EMPTY_GET)
        throw new Error(`URL inattendue : ${url}`)
      })

      await store.sync()

      expect(store.localResponses).toHaveLength(0)
    })

    it("keeps a pending response when the POST fails", async () => {
      store.localResponses = [makePending("a")]

      ;(useApiFetch as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
        if (url === "/responses/") return makePostMock(FAIL_POST)
        if (url === "/mobile/responses/") return makeGetMock(EMPTY_GET)
        throw new Error(`URL inattendue : ${url}`)
      })

      await store.sync()

      expect(store.localResponses).toHaveLength(1)
      expect(store.localResponses[0].status).toBe("pending")
    })

    it("ne soumet pas deux fois une réponse en attente quand un sync concurrent se déclenche pendant l'envoi", async () => {
      store.localResponses = [makePending("a"), makePending("b")]

      // Promesses à résolution manuelle : permet de contrôler l'ordre des réponses réseau
      const resolvers: Array<(v: typeof OK_POST) => void> = []

      ;(useApiFetch as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
        if (url === "/responses/") {
          return {
            post: () => ({
              json: () => new Promise<typeof OK_POST>((resolve) => resolvers.push(resolve)),
            }),
          }
        }
        if (url === "/mobile/responses/") return makeGetMock(EMPTY_GET)
        throw new Error(`URL inattendue : ${url}`)
      })

      const syncPromise = store.sync()

      // On attend que les deux _postDraft atteignent leur await POST
      await new Promise((resolve) => setTimeout(resolve, 0))
      expect(resolvers).toHaveLength(2)

      // A se termine en premier : son _postDraft appelle sync() qui doit être bloqué (syncing=true)
      resolvers[0](OK_POST)
      await new Promise((resolve) => setTimeout(resolve, 0))

      // B se termine : son _postDraft appelle aussi sync() qui doit être bloqué
      resolvers[1](OK_POST)
      await syncPromise

      // Chaque réponse a été soumise exactement une fois — pas de double envoi
      expect(resolvers).toHaveLength(2)
      expect(store.localResponses).toHaveLength(0)
    })
  })
})
