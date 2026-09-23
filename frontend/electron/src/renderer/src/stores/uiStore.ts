import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UISettings {
  sidebarCollapsed: boolean
  rightPanelCollapsed: boolean
  theme: 'dark'
  density: 'compact' | 'comfort'
  activeRunTab: string
}

interface UIStore extends UISettings {
  setSidebarCollapsed: (v: boolean) => void
  setRightPanelCollapsed: (v: boolean) => void
  setDensity: (v: 'compact' | 'comfort') => void
  setActiveRunTab: (tab: string) => void
  commandPaletteOpen: boolean
  setCommandPaletteOpen: (v: boolean) => void
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      rightPanelCollapsed: false,
      theme: 'dark',
      density: 'compact',
      activeRunTab: 'overview',
      commandPaletteOpen: false,
      setSidebarCollapsed: (v) => set({ sidebarCollapsed: v }),
      setRightPanelCollapsed: (v) => set({ rightPanelCollapsed: v }),
      setDensity: (v) => set({ density: v }),
      setActiveRunTab: (tab) => set({ activeRunTab: tab }),
      setCommandPaletteOpen: (v) => set({ commandPaletteOpen: v }),
    }),
    { name: 'syncnode-ui' }
  )
)
