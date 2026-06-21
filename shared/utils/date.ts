export const timeAgo = (date: Date | string): string => {
  const d = typeof date === "string" ? new Date(date) : date
  const prefix = "il y a"

  const seconds = (Date.now() - d.getTime()) / 1000
  if (seconds < 60) return "à l'instant"

  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `${prefix} ${minutes} m`

  const hours = Math.round(seconds / 3600)
  if (hours < 24) return `${prefix} ${hours} h`

  const days = Math.round(seconds / 3600 / 24)
  if (days < 120)
    return d.toLocaleString("fr-FR", { month: "long", day: "numeric" })
  return d.toLocaleString("fr-FR", {
    month: "long",
    day: "numeric",
    year: "numeric",
  })
}
