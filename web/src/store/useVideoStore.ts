import { create } from 'zustand'
import type { VideoTask, Platform } from '@/types'
import { videoApi } from '@/services/video'

interface VideoState {
  tasks: VideoTask[]
  currentTask: VideoTask | null
  isLoading: boolean
  error: string | null
  
  // Actions
  fetchTasks: () => Promise<void>
  createTask: (url: string, platform: Platform) => Promise<VideoTask | null>
  deleteTask: (id: string) => Promise<void>
  retryTask: (id: string) => Promise<void>
  setCurrentTask: (task: VideoTask | null) => void
  updateTaskStatus: (id: string, status: VideoTask['status'], progress: number) => void
}

export const useVideoStore = create<VideoState>((set, get) => ({
  tasks: [],
  currentTask: null,
  isLoading: false,
  error: null,

  fetchTasks: async () => {
    set({ isLoading: true, error: null })
    try {
      const result = await videoApi.getTasks(1, 100)
      set({ tasks: result.items, isLoading: false })
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '获取任务列表失败', isLoading: false })
    }
  },

  createTask: async (url: string, platform: Platform) => {
    set({ isLoading: true, error: null })
    try {
      const task = await videoApi.createTask(url, platform)
      set((state) => ({ 
        tasks: [task, ...state.tasks],
        isLoading: false 
      }))
      return task
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '创建任务失败', isLoading: false })
      return null
    }
  },

  deleteTask: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      await videoApi.deleteTask(id)
      set((state) => ({
        tasks: state.tasks.filter((t) => t.id !== id),
        isLoading: false,
      }))
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '删除任务失败', isLoading: false })
    }
  },

  retryTask: async (id: string) => {
    set({ isLoading: true, error: null })
    try {
      const task = await videoApi.retryTask(id)
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === id ? task : t)),
        isLoading: false,
      }))
    } catch (err) {
      set({ error: err instanceof Error ? err.message : '重试任务失败', isLoading: false })
    }
  },

  setCurrentTask: (task) => set({ currentTask: task }),

  updateTaskStatus: (id, status, progress) => {
    set((state) => ({
      tasks: state.tasks.map((t) =>
        t.id === id ? { ...t, status, progress } : t
      ),
    }))
  },
}))
