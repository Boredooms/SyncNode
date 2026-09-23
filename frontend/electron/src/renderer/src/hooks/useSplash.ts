import { useState, useCallback } from 'react'

export function useSplash() {
  // In development, skip splash; in production show it
  const [splashDone, setSplashDone] = useState(false)
  const onSplashComplete = useCallback(() => setSplashDone(true), [])
  return { splashDone, onSplashComplete }
}
