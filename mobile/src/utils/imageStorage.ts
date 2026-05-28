import { Filesystem, Directory } from "@capacitor/filesystem"
import type { SurveySchema } from "@shared-types/survey"

const IMAGE_DIR = Directory.Data
const IMAGE_PREFIX = "response_images"

/**
 * Writes base64 image items to the filesystem and replaces them with
 * { type: "local", path } references. Only processes fields with widget "image".
 * Idempotent: filesystem items are left untouched.
 */
export async function saveImagesToFilesystem(
  data: Record<string, unknown>,
  schema: SurveySchema
): Promise<Record<string, unknown>> {
  const result = { ...data }

  for (const field of schema.fields) {
    if (field.ui?.widget !== "image") continue
    const images = result[field.id]
    if (!Array.isArray(images)) continue

    result[field.id] = await Promise.all(
      images.map(async (item: unknown) => {
        if (
          typeof item !== "object" ||
          item === null ||
          !("file" in item) ||
          typeof (item as any).file !== "string"
        ) {
          return item
        }
        const path = `${IMAGE_PREFIX}/${crypto.randomUUID()}.jpg`
        await Filesystem.writeFile({
          path,
          data: (item as any).file,
          directory: IMAGE_DIR,
          recursive: true,
        })
        return { type: "local", path }
      })
    )
  }

  return result
}

/**
 * Reads filesystem image items back to base64 { file } objects for API submission.
 * Uses duck-typing so no schema is needed.
 */
export async function loadImagesFromFilesystem(
  data: Record<string, unknown>
): Promise<Record<string, unknown>> {
  const result = { ...data }

  for (const key of Object.keys(result)) {
    const value = result[key]
    if (!Array.isArray(value)) continue

    result[key] = await Promise.all(
      value.map(async (item: unknown) => {
        if (
          typeof item !== "object" ||
          item === null ||
          (item as any).type !== "local" ||
          typeof (item as any).path !== "string"
        ) {
          return item
        }
        const { data: b64 } = await Filesystem.readFile({
          path: (item as any).path,
          directory: IMAGE_DIR,
        })
        return { file: b64 as string }
      })
    )
  }

  return result
}

/**
 * Deletes all local image files referenced in data. Call after a draft is deleted
 * or a response is successfully submitted.
 */
export async function deleteLocalImages(
  data: Record<string, unknown>
): Promise<void> {
  for (const value of Object.values(data)) {
    if (!Array.isArray(value)) continue
    for (const item of value) {
      if (
        typeof item === "object" &&
        item !== null &&
        (item as any).type === "local" &&
        typeof (item as any).path === "string"
      ) {
        await Filesystem.deleteFile({
          path: (item as any).path,
          directory: IMAGE_DIR,
        }).catch(() => {
          // File may already be gone — ignore
        })
      }
    }
  }
}
