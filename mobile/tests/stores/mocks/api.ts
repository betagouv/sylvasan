import { vi } from "vitest"
import { useApiFetch } from "../../../src/utils/data-fetching"

const mockUser = { id: 1, username: "jean", email: "jean@example.com" }

function makePostMock(ok: boolean, data: unknown) {
  return {
    post: () => ({
      json: () =>
        Promise.resolve({
          response: { value: { ok } },
          data: { value: data },
        }),
    }),
  }
}

function makeGetMock(ok: boolean, data: unknown) {
  return {
    get: () => ({
      json: () =>
        Promise.resolve({
          response: { value: { ok } },
          data: { value: data },
        }),
    }),
  }
}

export const setupApiMocks = ({
  tokenOk = true,
  tokenData = { access: "a1", refresh: "r1" },
  meOk = true,
  meData = mockUser,
  refreshOk = true,
  refreshData = { access: "newAccess" },
  surveyOk = true,
  surveysData = [],
} = {}) => {
  ;(useApiFetch as ReturnType<typeof vi.fn>).mockImplementation(
    (url: string) => {
      if (url === "/mobile/token/") return makePostMock(tokenOk, tokenData)
      if (url === "/mobile/token/refresh/")
        return makePostMock(refreshOk, refreshData)
      if (url === "/auth/me/") return makeGetMock(meOk, meData)
      if (url === "/surveys/") return makeGetMock(surveyOk, surveysData)
      throw new Error(`Unexpected useApiFetch call with URL: ${url}`)
    }
  )
}
