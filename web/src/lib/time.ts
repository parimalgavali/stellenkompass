export const DAY = 24 * 60 * 60 * 1000

export function daysBetween(from: string | Date, to: string | Date): number {
  return (new Date(to).getTime() - new Date(from).getTime()) / DAY
}

export function relativeTime(iso: string, now: Date = new Date()): string {
  if (!iso) return ''
  const minutes = Math.round((now.getTime() - new Date(iso).getTime()) / 60000)
  if (minutes < 60) return minutes <= 1 ? 'just now' : `${minutes} min ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} h ago`
  const days = Math.round(hours / 24)
  if (days < 30) return days === 1 ? 'yesterday' : `${days} days ago`
  const months = Math.round(days / 30)
  return months < 12 ? `${months} mo ago` : `${Math.round(months / 12)} y ago`
}

export function formatDate(iso?: string): string {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

export function toDateInput(iso?: string): string {
  return iso ? iso.slice(0, 10) : ''
}

export function fromDateInput(value: string): string | undefined {
  return value ? new Date(`${value}T12:00:00`).toISOString() : undefined
}

/** Whole days left until the end of `day` (YYYY-MM-DD): 0 on the day itself, negative after it. */
export function daysLeft(day: string, now: Date = new Date()): number {
  return Math.floor((new Date(`${day}T23:59:59`).getTime() - now.getTime()) / DAY)
}

export function closesText(left: number): string {
  return left === 0 ? 'Closes today' : `Closes in ${left} day${left === 1 ? '' : 's'}`
}
