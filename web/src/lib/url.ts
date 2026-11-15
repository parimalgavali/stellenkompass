/** The URL when it is an http(s) link, else undefined (blocks javascript:, data:, ...). */
export function safeUrl(url: unknown): string | undefined {
  if (typeof url !== 'string') return undefined
  try {
    const { protocol } = new URL(url)
    return protocol === 'https:' || protocol === 'http:' ? url : undefined
  } catch {
    return undefined
  }
}
