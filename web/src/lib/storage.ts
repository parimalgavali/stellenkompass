import { useCallback, useEffect, useState } from 'react'

export const KEYS = {
  profile: 'stellenkompass.profile',
  tracker: 'stellenkompass.tracker',
  lastVisit: 'stellenkompass.lastVisit',
  theme: 'stellenkompass.theme',
}

export function readStored<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    return raw === null ? fallback : (JSON.parse(raw) as T)
  } catch {
    return fallback
  }
}

export function useStored<T>(key: string, fallback: T): [T, (value: T | ((prev: T) => T)) => void] {
  const [value, setValue] = useState<T>(() => readStored(key, fallback))
  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value))
  }, [key, value])
  const set = useCallback((v: T | ((prev: T) => T)) => setValue(v), [])
  return [value, set]
}
