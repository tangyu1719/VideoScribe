import { create } from 'zustand'
import type { ChatSession, ChatMessage, AIConfig, LLMAPIConfig, ChatSessionGroup } from '@/types'
import { chatApi } from '@/services/chat'

interface ChatState {
  sessions: ChatSession[]
  sessionGroups: ChatSessionGroup[]
  currentSession: ChatSession | null
  isLoading: boolean
  error: string | null
  aiConfig: AIConfig | null
  llmConfigs: LLMAPIConfig[]
  currentLLMConfigId: string
  streamingMessage: ChatMessage | null
  
  // Actions
  fetchSessions: () => Promise<void>
  fetchSessionGroups: () => Promise<void>
  createSession: () => Promise<void>
  deleteSession: (id: string) => Promise<void>
  renameSession: (id: string, title: string) => Promise<void>
  moveSessionToGroup: (sessionId: string, groupId: string | null) => Promise<void>
  createSessionGroup: (name: string) => Promise<void>
  setCurrentSession: (session: ChatSession | null) => void
  sendMessage: (content: string, options?: { images?: string[]; useDeepThinking?: boolean; useWebSearch?: boolean }) => Promise<void>
  sendMessageStream: (content: string, options?: { images?: string[]; useDeepThinking?: boolean; useWebSearch?: boolean }) => Promise<void>
  fetchAIConfig: () => Promise<void>
  fetchLLMConfigs: () => Promise<void>
  setCurrentLLMConfig: (id: string) => void
  updateAIConfig: (config: Partial<AIConfig>) => Promise<void>
  addMessageToSession: (sessionId: string, message: ChatMessage) => void
}

export const useChatStore = create<ChatState>()((set, get) => ({
      sessions: [],
      sessionGroups: [],
      currentSession: null,
      isLoading: false,
      error: null,
      aiConfig: null,
      llmConfigs: [],
      currentLLMConfigId: '',
      streamingMessage: null,

      fetchSessions: async () => {
        try {
          const sessions = await chatApi.getSessions()
          set({ sessions })
        } catch (err) {
          set({ error: err instanceof Error ? err.message : '获取会话列表失败' })
        }
      },

      fetchSessionGroups: async () => {
        try {
          const groups = await chatApi.getSessionGroups()
          set({ sessionGroups: groups })
        } catch (err) {
          console.error('获取会话分组失败:', err)
        }
      },

      createSession: async () => {
        try {
          const session = await chatApi.createSession()
          set((state) => ({
            sessions: [session, ...state.sessions],
            currentSession: session,
          }))
        } catch (err) {
          set({ error: err instanceof Error ? err.message : '创建会话失败' })
        }
      },

      deleteSession: async (id: string) => {
        try {
          await chatApi.deleteSession(id)
          set((state) => ({
            sessions: state.sessions.filter((s) => s.id !== id),
            currentSession: state.currentSession?.id === id ? null : state.currentSession,
          }))
        } catch (err) {
          set({ error: err instanceof Error ? err.message : '删除会话失败' })
        }
      },

      renameSession: async (id: string, title: string) => {
        try {
          const session = await chatApi.renameSession(id, title)
          set((state) => ({
            sessions: state.sessions.map((s) => (s.id === id ? session : s)),
            currentSession: state.currentSession?.id === id ? session : state.currentSession,
          }))
        } catch (err) {
          set({ error: err instanceof Error ? err.message : '重命名会话失败' })
        }
      },

      moveSessionToGroup: async (sessionId: string, groupId: string | null) => {
        try {
          await chatApi.moveSessionToGroup(sessionId, groupId)
          await get().fetchSessions()
        } catch (err) {
          console.error('移动会话失败:', err)
        }
      },

      createSessionGroup: async (name: string) => {
        try {
          await chatApi.createSessionGroup(name)
          await get().fetchSessionGroups()
        } catch (err) {
          console.error('创建分组失败:', err)
        }
      },

      setCurrentSession: (session) => set({ currentSession: session }),

      sendMessage: async (content: string, options = {}) => {
        const { currentSession } = get()
        if (!currentSession) return

        set({ isLoading: true, error: null })
        try {
          const message = await chatApi.sendMessage(currentSession.id, content, options)
          set((state) => ({
            currentSession: state.currentSession
              ? {
                  ...state.currentSession,
                  messages: [...state.currentSession.messages, message],
                }
              : null,
            isLoading: false,
          }))
        } catch (err) {
          set({ error: err instanceof Error ? err.message : '发送消息失败', isLoading: false })
        }
      },

      sendMessageStream: async (content: string, options = {}) => {
        const { currentSession } = get()
        if (!currentSession) return

        set({ isLoading: true, error: null, streamingMessage: null })
        
        try {
          const response = await fetch(`/api/chat/sessions/${currentSession.id}/messages/stream`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'text/event-stream'
            },
            body: JSON.stringify({
              content,
              useDeepThinking: options.useDeepThinking,
              useWebSearch: options.useWebSearch
            })
          })

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }

          const reader = response.body?.getReader()
          if (!reader) {
            throw new Error('ReadableStream not supported')
          }

          const decoder = new TextDecoder()
          let buffer = ''
          let fullContent = ''

          while (true) {
            const { done, value } = await reader.read()
            if (done) break

            const chunk = decoder.decode(value, { stream: true })
            buffer += chunk

            // 解析 SSE 格式 - 新版简化格式
            const lines = buffer.split('\n')
            buffer = lines.pop() || ''

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = line.slice(6)
                
                try {
                  const parsed = JSON.parse(data)
                  
                  // 处理内容片段
                  if (parsed.content) {
                    fullContent += parsed.content
                    set((state) => ({
                      streamingMessage: {
                        id: Date.now().toString(),
                        role: 'assistant',
                        content: fullContent,
                        timestamp: new Date().toISOString()
                      }
                    }))
                  }
                  
                  // 处理结束标记
                  if (parsed.done) {
                    set((state) => ({
                      currentSession: state.currentSession
                        ? {
                            ...state.currentSession,
                            messages: [
                              ...state.currentSession.messages,
                              state.streamingMessage!,
                            ],
                          }
                        : null,
                      streamingMessage: null,
                      isLoading: false,
                    }))
                    return
                  }
                  
                  // 处理错误
                  if (parsed.error) {
                    throw new Error(parsed.error)
                  }
                } catch (e) {
                  console.error('解析 SSE 数据失败:', e, '数据:', data)
                }
              }
            }
          }
        } catch (err) {
          console.error('流式请求失败:', err)
          set({ 
            error: err instanceof Error ? err.message : '流式响应出错', 
            isLoading: false, 
            streamingMessage: null 
          })
        }
      },

      fetchAIConfig: async () => {
        try {
          const config = await chatApi.getConfig()
          set({ aiConfig: config })
        } catch (err) {
          set({ error: err instanceof Error ? err.message : '获取AI配置失败' })
        }
      },

      fetchLLMConfigs: async () => {
        try {
          const configs = await chatApi.getLLMConfigs()
          set({ llmConfigs: configs })
          if (configs.length > 0 && !get().currentLLMConfigId) {
            set({ currentLLMConfigId: configs[0].id })
          }
        } catch (err) {
          console.error('获取LLM配置失败:', err)
        }
      },

      setCurrentLLMConfig: (id: string) => set({ currentLLMConfigId: id }),

      updateAIConfig: async (config) => {
        try {
          const updated = await chatApi.updateConfig(config)
          set({ aiConfig: updated })
        } catch (err) {
          set({ error: err instanceof Error ? err.message : '更新AI配置失败' })
        }
      },

      addMessageToSession: (sessionId: string, message: ChatMessage) => {
        set((state) => ({
          sessions: state.sessions.map((s) =>
            s.id === sessionId
              ? { ...s, messages: [...s.messages, message] }
              : s
          ),
          currentSession:
            state.currentSession?.id === sessionId
              ? {
                  ...state.currentSession,
                  messages: [...state.currentSession.messages, message],
                }
              : state.currentSession,
        }))
      },
    })
)
