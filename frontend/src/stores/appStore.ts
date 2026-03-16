import { create } from 'zustand'

interface AppState {
  sidebarCollapsed: boolean
  theme: 'dark' | 'light'
  
  toggleSidebar: () => void
  setTheme: (theme: 'dark' | 'light') => void
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  theme: 'dark',
  
  toggleSidebar: () => set((state) => ({ 
    sidebarCollapsed: !state.sidebarCollapsed 
  })),
  
  setTheme: (theme) => set({ theme }),
}))