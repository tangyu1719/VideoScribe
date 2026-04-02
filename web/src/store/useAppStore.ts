import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AppState {
  // 侧边栏折叠状态
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  
  // 当前主题
  theme: 'light' | 'dark'
  toggleTheme: () => void
  setTheme: (theme: 'light' | 'dark') => void
  
  // 全局加载状态
  isLoading: boolean
  setLoading: (loading: boolean) => void
  
  // 全局错误提示
  error: string | null
  setError: (error: string | null) => void
  
  // 全局成功提示
  success: string | null
  setSuccess: (success: string | null) => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      
      theme: 'light',
      toggleTheme: () => set((state) => ({ theme: state.theme === 'light' ? 'dark' : 'light' })),
      setTheme: (theme) => set({ theme }),
      
      isLoading: false,
      setLoading: (loading) => set({ isLoading: loading }),
      
      error: null,
      setError: (error) => set({ error }),
      
      success: null,
      setSuccess: (success) => set({ success }),
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({ sidebarCollapsed: state.sidebarCollapsed, theme: state.theme }),
    }
  )
)
