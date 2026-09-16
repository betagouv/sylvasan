import { describe, it, expect } from "vitest"
import { validateResponse } from "../../../shared/utils/validateField"
import { getEmptyValue } from "../../../shared/utils/survey"
import type { SurveyField } from "../../../shared/types/survey"

function makeField(overrides: Partial<SurveyField>): SurveyField {
  return { id: "f", type: "string", label: "Champ", ...overrides }
}

const outerArray: SurveyField = makeField({
  id: "observations",
  type: "array",
  ui: { widget: "array" },
  fields: [
    makeField({ id: "espece", type: "string", ui: { widget: "input" }, required: true }),
    makeField({
      id: "prelevements",
      type: "array",
      ui: { widget: "array" },
      fields: [
        makeField({ id: "volume", type: "number", ui: { widget: "number" }, validation: { min: 0 } }),
        makeField({ id: "note", type: "string", ui: { widget: "input" }, required: true }),
      ],
    }),
  ],
})

const schema = [outerArray]

describe("two-level ArrayField — rendering data", () => {
  it("getEmptyValue returns [] for an array field", () => {
    expect(getEmptyValue(outerArray)).toEqual([])
  })

  it("getEmptyValue returns [] for a nested array sub-field", () => {
    const innerArray = outerArray.fields!.find((f) => f.id === "prelevements")!
    expect(getEmptyValue(innerArray)).toEqual([])
  })
})

describe("two-level ArrayField — validateResponse", () => {
  it("returns no errors when all nested fields are valid", () => {
    const errors = validateResponse(schema, {
      observations: [
        {
          espece: "Aigle",
          prelevements: [{ volume: 1.5, note: "OK" }],
        },
      ],
    })
    expect(errors).toEqual({})
  })

  it("returns no errors when inner array is empty", () => {
    const errors = validateResponse(schema, {
      observations: [{ espece: "Aigle", prelevements: [] }],
    })
    expect(errors).toEqual({})
  })

  it("catches a required error on a depth-1 sub-field", () => {
    const errors = validateResponse(schema, {
      observations: [{ espece: "", prelevements: [] }],
    })
    expect(errors).toHaveProperty("observations.espece")
  })

  it("catches a required error on a depth-2 sub-sub-field", () => {
    const errors = validateResponse(schema, {
      observations: [
        { espece: "Aigle", prelevements: [{ volume: 1, note: "" }] },
      ],
    })
    expect(errors).toHaveProperty("observations.prelevements.note")
  })

  it("catches a constraint violation on a depth-2 sub-sub-field", () => {
    const errors = validateResponse(schema, {
      observations: [
        { espece: "Aigle", prelevements: [{ volume: -1, note: "OK" }] },
      ],
    })
    expect(errors).toHaveProperty("observations.prelevements.volume")
  })

  it("records only the first occurrence across multiple outer items", () => {
    const errors = validateResponse(schema, {
      observations: [
        { espece: "", prelevements: [{ volume: -1, note: "" }] },
        { espece: "", prelevements: [{ volume: -2, note: "" }] },
      ],
    })
    const depth1Keys = Object.keys(errors).filter((k) => k === "observations.espece")
    const depth2Keys = Object.keys(errors).filter((k) => k === "observations.prelevements.note")
    expect(depth1Keys).toHaveLength(1)
    expect(depth2Keys).toHaveLength(1)
  })

  it("returns no errors when outer array is empty", () => {
    const errors = validateResponse(schema, { observations: [] })
    expect(errors).toEqual({})
  })

  it("handles multiple valid inner items without errors", () => {
    const errors = validateResponse(schema, {
      observations: [
        {
          espece: "Aigle",
          prelevements: [
            { volume: 0, note: "premier" },
            { volume: 5, note: "deuxième" },
          ],
        },
      ],
    })
    expect(errors).toEqual({})
  })
})
