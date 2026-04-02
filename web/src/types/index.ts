// 视频任务相关类型
export interface VideoTask {
  id: string
  url: string
  platform: Platform
  status: TaskStatus
  progress: number
  title?: string
  createdAt: string
  completedAt?: string
  error?: string
  outputPath?: string
  transcript?: string
  summary?: string
}

export type Platform = 'douyin' | 'bilibili' | 'xiaohongshu' | 'youtube' | 'other'

export type TaskStatus = 'pending' | 'downloading' | 'transcribing' | 'analyzing' | 'completed' | 'failed'

// AI 对话相关类型
export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: string
  updatedAt: string
  groupId?: string
  contextLength: number
  maxContextLength: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  thinking?: string
  images?: string[]
  timestamp: string
  useDeepThinking?: boolean
  useWebSearch?: boolean
  knowledgeReferences?: KnowledgeReference[]
}

export interface KnowledgeReference {
  content: string
  source: string
  similarity: number
}

// 统一 LLM 配置（所有功能共用）
export interface LLMAPIConfig {
  id: string
  name: string
  apiKey: string
  baseUrl: string
  model: string
  // 火山引擎接入点 ID（可选）
  endpointId?: string
  requestFormat?: 'openai' | 'custom'
  headers?: Record<string, string>
  enabled: boolean
  createdAt: string
  updatedAt: string
  // 备用配置列表
  backupConfigs?: BackupConfig[]
}

// 备用 API 配置
export interface BackupConfig {
  id: string
  name: string
  apiKey: string
  baseUrl: string
  model: string
  endpointId?: string
  enabled: boolean
  priority: number // 1-5，数字越小优先级越高
}

// AI 形象配置（用于 AI 对话）
export interface AIPersona {
  id: string
  name: string
  description: string
  systemPrompt: string
  thinkingSystemPrompt?: string
  temperature: number
  maxTokens: number
  topP: number
  avatar?: string
  enabled: boolean
  createdAt: string
  updatedAt: string
}

// 文档解析器配置（用于链接分析）
export interface DocumentParser {
  id: string
  name: string
  description: string
  systemPrompt: string
  rules: string
  fileNamingRule: string
  outputTemplate: string
  userPrompt: string
  summaryPrompt: string
  enabled: boolean
  createdAt: string
  updatedAt: string
}

// 链接分析配置
export interface LinkAnalyzerConfig {
  parserId: string
  enableImageAnalysis: boolean
  enableCommentExtraction: boolean
  enableAIAnalysis: boolean
  llmConfigId: string
}

// 链接分析任务
export interface LinkAnalysisTask {
  id: string
  url: string
  platform: string
  status: TaskStatus
  stages: TaskStageStatus[]
  createdAt: string
  completedAt?: string
  result?: LinkAnalysisResult
  videoPath?: string
  transcriptPath?: string
  outputPath?: string
  deleteVideoAfterComplete: boolean
}

export type TaskStage = 'download' | 'transcribe' | 'analyze' | 'export'

export interface TaskStageStatus {
  stage: TaskStage
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  startTime?: string
  endTime?: string
  message?: string
}

export interface LinkAnalysisResult {
  url: string
  platform: string
  title?: string
  content?: string
  images?: string[]
  author?: string
  publishTime?: string
  type: 'video' | 'image' | 'article'
  aiAnalysis?: LinkAIAnalysis
}

export interface LinkAIAnalysis {
  summary: string
  keyPoints: string[]
  sentiment: 'positive' | 'neutral' | 'negative'
  tags: string[]
}

// RAG 知识库相关类型
export interface KnowledgeBaseFile {
  id: string
  name: string
  path: string
  size: number
  type: string
  createdAt: string
  indexedAt?: string
  status: 'pending' | 'indexed' | 'failed'
}

export interface KnowledgeBaseStats {
  totalFiles: number
  indexedFiles: number
  totalSize: number
  lastUpdated?: string
}

export interface SearchResult {
  content: string
  source: string
  similarity: number
}

// 应用配置类型
export interface AppConfig {
  currentLLMConfigId: string
  currentAIPersonaId: string
  currentParserId: string
  knowledgeBaseThreshold: number
  defaultDeepThinking: boolean
  defaultWebSearch: boolean
  // 统一配置还是分开配置
  useUnifiedAPIConfig: boolean
}

// API 响应类型
export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

// 分页类型
export interface PaginationParams {
  page: number
  pageSize: number
}

export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

// 会话分组
export interface ChatSessionGroup {
  id: string
  name: string
  createdAt: string
  sessions: string[]
}

// 日志类型
export interface SystemLog {
  id: string
  level: 'info' | 'warning' | 'error' | 'debug'
  module: string
  message: string
  timestamp: string
  details?: string | Record<string, unknown>
}
