import { get, post, del } from './api'
import type { LLMAPIConfig, AIPersona, DocumentParser, AppConfig, SystemLog, LinkAnalysisTask } from '@/types'

// 统一配置管理 API
export const configApi = {
  // 获取应用配置
  getAppConfig: () =>
    get<AppConfig>('/config'),

  // 更新应用配置
  updateAppConfig: (config: Partial<AppConfig>) =>
    post<AppConfig>('/config', config),
}

// LLM 的配置 API（统一管理）
export const llmConfigApi = {
  // 获取 LLM 配置列表
  getConfigs: () =>
    get<LLMAPIConfig[]>('/llm-configs'),

  // 保存 LLM 配置
  saveConfig: (config: LLMAPIConfig) =>
    post<LLMAPIConfig>('/llm-configs', config),

  // 删除 LLM 配置
  deleteConfig: (id: string) =>
    del<void>(`/llm-configs/${id}`),

  // 设为默认
  setDefault: (id: string) =>
    post<void>(`/llm-configs/${id}/default`),
}

// AI 形象 API（用于 AI 对话）
export const aiPersonaApi = {
  // 获取 AI 形象列表
  getPersonas: () =>
    get<AIPersona[]>('/ai-personas'),

  // 保存 AI 形象
  savePersona: (persona: AIPersona) =>
    post<AIPersona>('/ai-personas', persona),

  // 删除 AI 形象
  deletePersona: (id: string) =>
    del<void>(`/ai-personas/${id}`),

  // 设为默认
  setDefault: (id: string) =>
    post<void>(`/ai-personas/${id}/default`),
}

// 文档解析器 API（用于链接分析）
export const parserApi = {
  // 获取解析器列表
  getParsers: () =>
    get<DocumentParser[]>('/parsers'),

  // 保存解析器
  saveParser: (parser: DocumentParser) =>
    post<DocumentParser>('/parsers', parser),

  // 删除解析器
  deleteParser: (id: string) =>
    del<void>(`/parsers/${id}`),

  // 设为默认
  setDefault: (id: string) =>
    post<void>(`/parsers/${id}/default`),
}

// 链接分析任务 API
export const linkTaskApi = {
  // 获取任务列表
  getTasks: (page = 1, pageSize = 20) =>
    get<{ items: LinkAnalysisTask[]; total: number }>('/link/tasks', { page, pageSize }),

  // 创建任务
  createTask: (url: string) =>
    post<LinkAnalysisTask>('/link/tasks', { url }),

  // 获取任务详情
  getTask: (id: string) =>
    get<LinkAnalysisTask>(`/link/tasks/${id}`),

  // 删除任务
  deleteTask: (id: string) =>
    del<void>(`/link/tasks/${id}`),

  // 重新执行任务
  retryTask: (id: string) =>
    post<LinkAnalysisTask>(`/link/tasks/${id}/retry`),

  // 下载指定阶段的产物
  downloadStage: (taskId: string, stage: string) =>
    get<{ url: string; filename: string }>(`/link/tasks/${taskId}/download/${stage}`),

  // 清理缓存
  clearCache: (taskId: string) =>
    post<void>(`/link/tasks/${taskId}/clear-cache`),
}

export interface GetLogsParams {
  level?: string
  module?: string
  search?: string
  startTime?: string
  endTime?: string
  page?: number
  pageSize?: number
}

export interface GetLogsResponse {
  items: SystemLog[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 日志API
export const logApi = {
  // 获取日志列表 - 支持时间范围、搜索、筛选
  getLogs: (params: GetLogsParams = {}) =>
    get<GetLogsResponse>('/logs', {
      level: params.level,
      module: params.module,
      search: params.search,
      startTime: params.startTime,
      endTime: params.endTime,
      page: params.page || 1,
      pageSize: params.pageSize || 50
    }),

  // 获取日志统计
  getLogStats: () =>
    get<{ byLevel: Record<string, number>; byModule: Record<string, number> }>('/logs/stats'),

  // 清理日志
  clearLogs: (olderThan?: string) =>
    post<void>('/logs/clear', { olderThan }),
}
