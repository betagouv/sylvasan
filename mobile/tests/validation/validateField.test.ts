import { describe, it, expect } from "vitest"
import {
  validateField,
  validateResponse,
} from "../../../shared/utils/validateField"
import type { SurveyField } from "../../../shared/types/survey"

function field(overrides: Partial<SurveyField> = {}): SurveyField {
  return { id: "f1", type: "string", label: "Champ", ...overrides }
}

describe("required", () => {
  it("returns error when required field is empty string", () => {
    expect(validateField(field({ required: true }), "")).not.toBeNull()
  })

  it("returns error when required field is null", () => {
    expect(validateField(field({ required: true }), null)).not.toBeNull()
  })

  it("returns error when required field is empty array", () => {
    expect(validateField(field({ required: true }), [])).not.toBeNull()
  })

  it("returns null when required field has a value", () => {
    expect(validateField(field({ required: true }), "hello")).toBeNull()
  })

  it("returns null when non-required field is empty", () => {
    expect(validateField(field({ required: false }), "")).toBeNull()
  })
})

describe("number widget", () => {
  const num = (validation: SurveyField["validation"] = {}) =>
    field({ ui: { widget: "number" }, validation })

  it("accepts a valid integer when numberType is integer", () => {
    expect(validateField(num({ numberType: "integer" }), 3)).toBeNull()
  })

  it("rejects a float when numberType is integer", () => {
    expect(validateField(num({ numberType: "integer" }), 3.5)).not.toBeNull()
  })

  it("accepts a float when numberType is float", () => {
    expect(validateField(num({ numberType: "float" }), 3.14)).toBeNull()
  })

  it("rejects a non-numeric string", () => {
    expect(validateField(num(), "abc")).not.toBeNull()
  })

  it("rejects a value below min", () => {
    expect(validateField(num({ min: 5 }), 3)).not.toBeNull()
  })

  it("accepts a value equal to min", () => {
    expect(validateField(num({ min: 5 }), 5)).toBeNull()
  })

  it("rejects a value above max", () => {
    expect(validateField(num({ max: 10 }), 12)).not.toBeNull()
  })

  it("accepts a value equal to max", () => {
    expect(validateField(num({ max: 10 }), 10)).toBeNull()
  })

  it("accepts a value within [min, max]", () => {
    expect(validateField(num({ min: 1, max: 100 }), 50)).toBeNull()
  })

  it("returns null for empty value even with constraints (not required)", () => {
    expect(
      validateField(num({ min: 1, numberType: "integer" }), null)
    ).toBeNull()
  })
})

describe("date widget", () => {
  const dateField = (validation: SurveyField["validation"] = {}) =>
    field({ ui: { widget: "date" }, validation })

  it("rejects a date before min", () => {
    expect(
      validateField(dateField({ min: "2024-01-01" }), "2023-06-15")
    ).not.toBeNull()
  })

  it("accepts a date equal to min", () => {
    expect(
      validateField(dateField({ min: "2024-01-01" }), "2024-01-01")
    ).toBeNull()
  })

  it("rejects a date after max", () => {
    expect(
      validateField(dateField({ max: "2024-12-31" }), "2025-03-01")
    ).not.toBeNull()
  })

  it("accepts a date equal to max", () => {
    expect(
      validateField(dateField({ max: "2024-12-31" }), "2024-12-31")
    ).toBeNull()
  })

  it("accepts a date within [min, max]", () => {
    expect(
      validateField(
        dateField({ min: "2024-01-01", max: "2024-12-31" }),
        "2024-06-15"
      )
    ).toBeNull()
  })
})

describe("string widget", () => {
  const str = (
    widget: "input" | "autocomplete",
    validation: SurveyField["validation"] = {}
  ) => field({ ui: { widget }, validation })

  it.each(["input", "autocomplete"] as const)(
    "%s: rejects value shorter than minLength",
    (widget) => {
      expect(validateField(str(widget, { minLength: 5 }), "hi")).not.toBeNull()
    }
  )

  it.each(["input", "autocomplete"] as const)(
    "%s: accepts value equal to minLength",
    (widget) => {
      expect(validateField(str(widget, { minLength: 3 }), "abc")).toBeNull()
    }
  )

  it.each(["input", "autocomplete"] as const)(
    "%s: rejects value longer than maxLength",
    (widget) => {
      expect(
        validateField(str(widget, { maxLength: 3 }), "toolong")
      ).not.toBeNull()
    }
  )

  it.each(["input", "autocomplete"] as const)(
    "%s: accepts value equal to maxLength",
    (widget) => {
      expect(validateField(str(widget, { maxLength: 5 }), "hello")).toBeNull()
    }
  )
})

describe("array-like widgets", () => {
  const arr = (
    widget: "array" | "checkboxes" | "image",
    validation: SurveyField["validation"] = {}
  ) => field({ ui: { widget }, validation })

  it.each(["array", "checkboxes", "image"] as const)(
    "%s: rejects fewer items than minItems",
    (widget) => {
      expect(validateField(arr(widget, { minItems: 2 }), ["a"])).not.toBeNull()
    }
  )

  it.each(["array", "checkboxes", "image"] as const)(
    "%s: accepts count equal to minItems",
    (widget) => {
      expect(validateField(arr(widget, { minItems: 2 }), ["a", "b"])).toBeNull()
    }
  )

  it.each(["array", "checkboxes", "image"] as const)(
    "%s: rejects more items than maxItems",
    (widget) => {
      expect(
        validateField(arr(widget, { maxItems: 2 }), ["a", "b", "c"])
      ).not.toBeNull()
    }
  )

  it.each(["array", "checkboxes", "image"] as const)(
    "%s: accepts count equal to maxItems",
    (widget) => {
      expect(
        validateField(arr(widget, { maxItems: 3 }), ["a", "b", "c"])
      ).toBeNull()
    }
  )
})

describe("validateResponse", () => {
  const schema: SurveyField[] = [
    field({
      id: "age",
      ui: { widget: "number" },
      validation: { numberType: "integer" },
    }),
    field({ id: "name", ui: { widget: "input" }, required: true }),
    field({
      id: "note",
      ui: { widget: "input" },
      validation: { maxLength: 5 },
    }),
  ]

  it("returns empty object when all fields are valid", () => {
    const errors = validateResponse(schema, {
      age: 25,
      name: "Alice",
      note: "ok",
    })
    expect(errors).toEqual({})
  })

  it("returns errors for each invalid field", () => {
    const errors = validateResponse(schema, {
      age: 1.5,
      name: "",
      note: "toolongvalue",
    })
    expect(errors).toHaveProperty("age")
    expect(errors).toHaveProperty("name")
    expect(errors).toHaveProperty("note")
  })

  it("omits fields not in visibleFieldIds", () => {
    const errors = validateResponse(
      schema,
      { age: 1.5, name: "", note: "" },
      new Set(["name"])
    )
    expect(errors).not.toHaveProperty("age")
    expect(errors).toHaveProperty("name")
  })

  it("returns only failing fields, not passing ones", () => {
    const errors = validateResponse(schema, { age: 5, name: "", note: "hi" })
    expect(errors).not.toHaveProperty("age")
    expect(errors).toHaveProperty("name")
    expect(errors).not.toHaveProperty("note")
  })
})

describe("validateResponse — sub-fields (array widget)", () => {
  const arraySchema: SurveyField[] = [
    field({
      id: "observations",
      type: "array",
      ui: { widget: "array" },
      fields: [
        field({ id: "espece", type: "string", required: true }),
        field({ id: "count", type: "number", ui: { widget: "number" }, validation: { min: 1 } }),
      ],
    }),
  ]

  it("returns no errors when all sub-fields are valid", () => {
    const errors = validateResponse(arraySchema, {
      observations: [{ espece: "Aigle", count: 3 }],
    })
    expect(errors).toEqual({})
  })

  it("reports a required sub-field error with composite key parentId.subFieldId", () => {
    const errors = validateResponse(arraySchema, {
      observations: [{ espece: "", count: 3 }],
    })
    expect(errors).toHaveProperty("observations.espece")
  })

  it("reports a constraint violation on a sub-field", () => {
    const errors = validateResponse(arraySchema, {
      observations: [{ espece: "Aigle", count: 0 }],
    })
    expect(errors).toHaveProperty("observations.count")
  })

  it("records only the first occurrence when multiple items fail the same sub-field", () => {
    const errors = validateResponse(arraySchema, {
      observations: [
        { espece: "", count: 1 },
        { espece: "", count: 1 },
      ],
    })
    expect(Object.keys(errors).filter((k) => k === "observations.espece")).toHaveLength(1)
  })

  it("returns no sub-field errors when the array is empty", () => {
    const errors = validateResponse(arraySchema, { observations: [] })
    expect(errors).toEqual({})
  })
})
