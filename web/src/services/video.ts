import { get, post, del } from './api'
import type { VideoTask, Platform, PaginatedResult } from '@/types'

export const videoApi = {
  // 获取任务列表
  getTasks: (page = 1, pageSize = 20) =>
    get<PaginatedResult<VideoTask>>('/video/tasks', { page, pageSize }),

  // 创建新任务
  createTask: (url: string, platform: Platform) =>
    post<VideoTask>('/video/tasks', { url, platform }),

  // 获取任务详情
  getTask: (id: string) =>
    get<VideoTask>(`/video/tasks/${id}`),

  // 删除任务
  deleteTask: (id: string) =>
    del<void>(`/video/tasks/${id}`),

  // 重新处理任务
  retryTask: (id: string) =>
    post<VideoTask>(`/video/tasks/${id}/retry`),

  // 获取任务日志
  getTaskLogs: (id: string) =>
    get<string[]>(`/video/tasks/${id}/logs`),

  // 下载结果文件
  downloadResult: (id: string) =>
    get<{ url: string; filename: string }>(`/video/tasks/${id}/download`),
}
