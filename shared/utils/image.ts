const MAX_DIM = 2000
const MAX_BYTES = 2 * 1024 * 1024

export const compressBase64Image = (base64: string): Promise<string> =>
  compressImageUrl(`data:image/jpeg;base64,${base64}`)

export const compressFileImage = (file: File): Promise<string> => {
  const url = URL.createObjectURL(file)
  return compressImageUrl(url).finally(() => URL.revokeObjectURL(url))
}

// Implémentation commune : redimensionne puis réduit graduellement la qualité
// jusqu'à passer sous MAX_BYTES. Retourne la chaîne base64 sans le préfixe data:.
const compressImageUrl = (url: string): Promise<string> =>
  new Promise((resolve, reject) => {
    const img = new Image()
    img.onerror = () => reject(new Error("Lecture image échouée"))
    img.onload = async () => {
      // Redimensionnement : le côté le plus long est ramené à MAX_DIM si nécessaire
      let { width, height } = img
      if (Math.max(width, height) > MAX_DIM) {
        if (width >= height) {
          height = Math.round((height / width) * MAX_DIM)
          width = MAX_DIM
        } else {
          width = Math.round((width / height) * MAX_DIM)
          height = MAX_DIM
        }
      }

      const canvas = document.createElement("canvas")
      canvas.width = width
      canvas.height = height
      canvas.getContext("2d")!.drawImage(img, 0, 0, width, height)

      // Réduction itérative de la qualité jusqu'à passer sous MAX_BYTES
      let quality = 0.85
      let blob: Blob
      while (true) {
        blob = await new Promise<Blob>((res, rej) =>
          canvas.toBlob(
            (b) => (b ? res(b) : rej(new Error("Compression échouée"))),
            "image/jpeg",
            quality
          )
        )
        if (blob.size <= MAX_BYTES || quality <= 0.1) break
        quality = Math.max(0.1, quality - 0.1)
      }

      const reader = new FileReader()
      reader.onerror = reject
      reader.onload = () => resolve((reader.result as string).split(",")[1])
      reader.readAsDataURL(blob)
    }
    img.src = url
  })
