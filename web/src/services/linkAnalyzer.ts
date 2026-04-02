import { get, post } from './api'
import type { LinkAnalysisResult, LinkAnalyzerConfig, DocumentParser } from '@/types'

export interface ExportResultRequest {
  result: LinkAnalysisResult
  outputDir?: string
  parserId?: string
}

export interface ExportResultResponse {
  filePath: string
  filename: string
  content: string
}

export interface LinkTaskStage {
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  progress: number
  message: string
  result?: any
  updated_at: string
}

export interface LinkTask {
  id: string
  url: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  overall_progress: number
  created_at: string
  updated_at: string
  config: any
  stages: {
    detect_type: LinkTaskStage
    extract_content: LinkTaskStage
    transcribe: LinkTaskStage
    ai_analysis: LinkTaskStage
    generate_md: LinkTaskStage
    export: LinkTaskStage
  }
  result?: any
  error?: string
}

export interface CreateTaskRequest {
  url: string
  config?: {
    parserId?: string
    llmConfigId?: string
    outputDir?: string
    userPrompt?: string
  }
}

export interface CreateTaskResponse {
  taskId: string
  status: string
  message: string
}

export const linkAnalyzerApi = {
  // 分析链接 - 旧版同步接口
  analyzeLink: (url: string, config?: Partial<LinkAnalyzerConfig>) =>
    post<LinkAnalysisResult>('/link/analyze', { url, config }),

  // 创建链接分析任务 - 新版异步多阶段处理
  createTask: (data: CreateTaskRequest) =>
    post<CreateTaskResponse>('/link/tasks', data),

  // 获取任务状态
  getTask: (taskId: string) =>
    get<LinkTask>('/link/tasks/' + taskId),

  // 获取所有任务列表
  listTasks: () =>
    get<LinkTask[]>('/link/tasks'),

  // 删除任务
  deleteTask: (taskId: string) =>
    post<void>('/link/tasks/' + taskId + '/delete', {}),

  // 获取可用的解析器列表
  getParsers: () =>
    get<DocumentParser[]>('/link/parsers'),

  // 获取分析历史
  getHistory: (page = 1, pageSize = 20) =>
    get<{ items: LinkAnalysisResult[]; total: number }>('/link/history', { page, pageSize }),

  // 导出分析结果为MD文件到指定位置
  exportResult: (data: ExportResultRequest) =>
    post<ExportResultResponse>('/link/export', data),

  // 获取链接分析配置
  getConfig: () =>
    get<LinkAnalyzerConfig>('/link/config'),

  // 更新链接分析配置
  updateConfig: (config: Partial<LinkAnalyzerConfig>) =>
    post<LinkAnalyzerConfig>('/link/config', config),
}
