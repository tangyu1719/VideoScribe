import { get, post, del } from './api'
import type { ChatSession, ChatMessage, AIConfig, LLMAPIConfig } from '@/types'

export const chatApi = {
  // 获取会话列表
  getSessions: () =>
    get<ChatSession[]>('/chat/sessions'),

  // 创建新会话
  createSession: () =>
    post<ChatSession>('/chat/sessions'),

  // 获取会话详情
  getSession: (id: string) =>
    get<ChatSession>(`/chat/sessions/${id}`),

  // 删除会话
  deleteSession: (id: string) =>
    del<void>(`/chat/sessions/${id}`),

  // 重命名会话
  renameSession: (id: string, title: string) =>
    post<ChatSession>(`/chat/sessions/${id}/rename`, { title }),

  // 发送消息（非流式）
  sendMessage: (sessionId: string, content: string, options?: {
    images?: string[]
    useDeepThinking?: boolean
    useWebSearch?: boolean
  }) =>
    post<ChatMessage>(`/chat/sessions/${sessionId}/messages`, { 
      content, 
      ...options 
    }),

  // 发送消息（流式）- 使用 fetch + ReadableStream 解析 SSE
  sendMessageStream: (sessionId: string, content: string, options?: {
    images?: string[]
    useDeepThinking?: boolean
    useWebSearch?: boolean
  }) => {
    return post<ReadableStream>(`/chat/sessions/${sessionId}/messages/stream`, { 
      content, 
      ...options 
    }, {
      headers: {
        'Accept': 'text/event-stream'
      }
    })
  },

  // 获取AI配置
  getConfig: () =>
    get<AIConfig>('/chat/config'),

  // 更新AI配置
  updateConfig: (config: Partial<AIConfig>) =>
    post<AIConfig>('/chat/config', config),

  // 获取LLM配置列表
  getLLMConfigs: () =>
    get<LLMAPIConfig[]>('/chat/llm-configs'),

  // 保存LLM配置
  saveLLMConfig: (config: LLMAPIConfig) =>
    post<LLMAPIConfig>('/chat/llm-configs', config),

  // 删除LLM配置
  deleteLLMConfig: (id: string) =>
    del<void>(`/chat/llm-configs/${id}`),

  // 获取会话分组列表
  getSessionGroups: () =>
    get<{ id: string; name: string; sessions: string[] }[]>('/chat/session-groups'),

  // 创建会话分组
  createSessionGroup: (name: string) =>
    post<{ id: string; name: string }>('/chat/session-groups', { name }),

  // 移动会话到分组
  moveSessionToGroup: (sessionId: string, groupId: string | null) =>
    post<void>(`/chat/sessions/${sessionId}/move`, { groupId }),
}
