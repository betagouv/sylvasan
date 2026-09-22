import { Camera, CameraResultType, CameraSource } from "@capacitor/camera"
import type { LocalImageItem } from "@shared-types/survey"
import { compressBase64Image } from "@shared-utils/image"

export const captureImage = async (): Promise<LocalImageItem | null> => {
  try {
    const photo = await Camera.getPhoto({
      quality: 85,
      allowEditing: false,
      resultType: CameraResultType.Base64,
      source: CameraSource.Prompt,
      width: 2000,
      height: 2000,
    })
    if (!photo.base64String) return null
    const file = await compressBase64Image(photo.base64String)
    return { file }
  } catch {
    return null
  }
}
