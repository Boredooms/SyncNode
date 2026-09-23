import { create } from 'zustand'
import type { HealthStatus } from '../lib/api/types'

interface HealthState {
  overall: HealthStatus | null
  model: HealthStatus | null
  database: HealthStatus | null
  rag: HealthStatus | null
  computer: HealthStatus | null
  browser: HealthStatus | null
  lastChecked: number | null
  setHealth: (key: keyof Omit<HealthState, 'lastChecked' | 'setHealth'>, value: HealthStatus) => void
  setLastChecked: (ts: number) => void
}

export const useHealthStore = create<HealthState>((set) => ({
  overall: null,
  model: null,
  database: null,
  rag: null,
  computer: null,
  browser: null,
  lastChecked: null,
  setHealth: (key, value) => set((s) => ({ ...s, [key]: value })),
  setLastChecked: (ts) => set({ lastChecked: ts }),
}))
