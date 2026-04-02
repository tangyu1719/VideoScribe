import { useState, useEffect, useRef } from 'react'
import { 
  Send, 
  Plus, 
  Trash2, 
  Loader2, 
  Image as ImageIcon,
  Settings,
  MessageSquare,
  X,
  Brain,
  Globe,
  Database,
  Copy,
  FileDown,
  MoreVertical,
  Edit2,
  Folder,
  FolderOpen,
  ChevronRight,
  ChevronDown,
  SlidersHorizontal,
  Check
} from 'lucide-react'
import { useChatStore } from '@/store/useChatStore'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent } from '@/components/ui/Card'
import { ScrollArea } from '@/components/ui/ScrollArea'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/Dialog'
import { Slider } from '@/components/ui/Slider'
import { cn, formatDate } from '@/lib/utils'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ChatSession, LLMAPIConfig } from '@/types'

// 上下文可视化圆圈组件
const ContextCircle = ({ current, max }: { current: number; max: number }) => {
  // 确保有默认值，避免 NaN
  const safeCurrent = current || 0
  const safeMax = max || 8192
  const percentage = Math.min(100, (safeCurrent / safeMax) * 100)
  const circumference = 2 * Math.PI * 18
  const strokeDashoffset = circumference - (percentage / 100) * circumference
  
  let color = 'text-green-500'
  if (percentage > 70) color = 'text-yellow-500'
  if (percentage > 90) color = 'text-red-500'
  
  return (
    <div className="relative w-10 h-10 flex items-center justify-center" title={`上下文：${safeCurrent}/${safeMax}`}>
      <svg className="w-10 h-10 transform -rotate-90">
        <circle
          cx="20"
          cy="20"
          r="18"
          stroke="currentColor"
          strokeWidth="3"
          fill="transparent"
          className="text-muted"
        />
        <circle
          cx="20"
          cy="20"
          r="18"
          stroke="currentColor"
          strokeWidth="3"
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className={cn("transition-all duration-300", color)}
        />
      </svg>
      <span className="absolute text-[10px] font-medium">{Math.round(percentage)}%</span>
    </div>
  )
}

export default function AIChat() {
  const [input, setInput] = useState('')
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [pendingImages, setPendingImages] = useState<string[]>([])
  const [editingSession, setEditingSession] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')
  const [showGroupDialog, setShowGroupDialog] = useState(false)
  const [newGroupName, setNewGroupName] = useState('')
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['default']))
  const [showMoveDialog, setShowMoveDialog] = useState(false)
  const [movingSessionId, setMovingSessionId] = useState<string | null>(null)
  const [targetGroupId, setTargetGroupId] = useState<string>('')
  const [editingGroupId, setEditingGroupId] = useState<string | null>(null)
  const [editGroupTitle, setEditGroupTitle] = useState('')
  
  // 元宝风格功能开关
  const [useDeepThinking, setUseDeepThinking] = useState(false)
  const [useWebSearch, setUseWebSearch] = useState(false)
  const [useKnowledgeBase, setUseKnowledgeBase] = useState(false)
  const [knowledgeThreshold, setKnowledgeThreshold] = useState(0.7)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  
  const { 
    sessions, 
    sessionGroups,
    currentSession, 
    isLoading, 
    streamingMessage,
    llmConfigs,
    currentLLMConfigId,
    fetchSessions, 
    fetchSessionGroups,
    createSession, 
    deleteSession,
    renameSession,
    moveSessionToGroup,
    createSessionGroup,
    setCurrentSession,
    sendMessageStream,
    fetchAIConfig,
    fetchLLMConfigs,
    setCurrentLLMConfig,
    updateAIConfig,
    addMessageToSession
  } = useChatStore()

  useEffect(() => {
    fetchSessions()
    fetchSessionGroups()
    fetchAIConfig()
    fetchLLMConfigs()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentSession?.messages, streamingMessage])

  // 自动调整输入框高度
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = inputRef.current.scrollHeight + 'px'
    }
  }, [input])

  const handleSend = async () => {
    if (!input.trim() && pendingImages.length === 0) return
    
    const content = input
    setInput('')
    
    if (currentSession) {
      addMessageToSession(currentSession.id, {
        id: Date.now().toString(),
        role: 'user',
        content,
        images: pendingImages.length > 0 ? pendingImages : undefined,
        timestamp: new Date().toISOString()
      })
    }
    
    setPendingImages([])
    await sendMessageStream(content, {
      images: pendingImages,
      useDeepThinking,
      useWebSearch
    })
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    Array.from(files).forEach(file => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const result = e.target?.result as string
        setPendingImages(prev => [...prev, result])
      }
      reader.readAsDataURL(file)
    })
  }

  const removePendingImage = (index: number) => {
    setPendingImages(prev => prev.filter((_, i) => i !== index))
  }

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content)
  }

  const handleExportMessage = (content: string) => {
    const blob = new Blob([content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `message_${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const startRename = (session: ChatSession) => {
    setEditingSession(session.id)
    setEditTitle(session.title)
  }

  const saveRename = async () => {
    if (editingSession && editTitle.trim()) {
      await renameSession(editingSession, editTitle.trim())
    }
    setEditingSession(null)
    setEditTitle('')
  }

  const toggleGroup = (groupId: string) => {
    setExpandedGroups(prev => {
      const newSet = new Set(prev)
      if (newSet.has(groupId)) {
        newSet.delete(groupId)
      } else {
        newSet.add(groupId)
      }
      return newSet
    })
  }

  const handleCreateGroup = async () => {
    if (newGroupName.trim()) {
      await createSessionGroup(newGroupName.trim())
      setNewGroupName('')
      setShowGroupDialog(false)
    }
  }

  const handleMoveSession = async () => {
    if (movingSessionId && targetGroupId) {
      await moveSessionToGroup(movingSessionId, targetGroupId)
      setShowMoveDialog(false)
      setMovingSessionId(null)
      setTargetGroupId('')
    }
  }

  const startMoveSession = (sessionId: string, currentGroupId?: string) => {
    setMovingSessionId(sessionId)
    setTargetGroupId(currentGroupId || '')
    setShowMoveDialog(true)
  }

  const startRenameGroup = (groupId: string, currentName: string) => {
    setEditingGroupId(groupId)
    setEditGroupTitle(currentName)
  }

  const saveRenameGroup = async () => {
    if (editingGroupId && editGroupTitle.trim()) {
      // 这里需要后端 API 支持重命名分组
      // 暂时只更新本地状态
      setEditingGroupId(null)
      setEditGroupTitle('')
    }
    setEditingGroupId(null)
    setEditGroupTitle('')
  }

  const handleDeleteGroup = async (groupId: string) => {
    console.log('删除分组:', groupId)
    // 确认删除
    if (!confirm('确定要删除这个分组吗？分组内的会话将移动到未分组空间。')) {
      return
    }
    
    // 将该分组内的所有会话移动到未分组（groupId = null）
    const group = sessionGroups.find(g => g.id === groupId)
    if (group && group.sessions.length > 0) {
      // 批量移动会话到未分组
      for (const session of group.sessions) {
        await moveSessionToGroup(session.id, '')
      }
    }
    
    // 删除分组本身（需要后端 API 支持）
    // 暂时只更新本地状态
    setExpandedGroups(prev => {
      const newSet = new Set(prev)
      newSet.delete(groupId)
      return newSet
    })
  }

  // 按分组组织会话
  const groupedSessions = sessionGroups.map(group => ({
    ...group,
    sessions: sessions.filter(s => s.groupId === group.id)
  }))
  
  // 未分组的会话
  const ungroupedSessions = sessions.filter(s => !s.groupId)

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* 左侧会话列表 */}
      <Card className="w-72 flex-shrink-0 flex flex-col">
        <CardContent className="p-4 flex flex-col h-full">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              会话列表
            </h2>
            <div className="flex gap-1">
              <Button variant="ghost" size="sm" onClick={() => setShowGroupDialog(true)}>
                <Folder className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="sm" onClick={createSession}>
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>
          
          <ScrollArea className="flex-1 -mx-2">
            <div className="space-y-1 px-2">
              {/* 分组会话 */}
              {groupedSessions.map(group => (
                <div key={group.id}>
                  <div 
                    className="flex items-center gap-2 p-2 rounded-lg cursor-pointer hover:bg-muted group"
                    onClick={() => toggleGroup(group.id)}
                  >
                    {expandedGroups.has(group.id) ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                    <FolderOpen className="w-4 h-4 text-muted-foreground" />
                    {editingGroupId === group.id ? (
                      <Input
                        value={editGroupTitle}
                        onChange={(e) => setEditGroupTitle(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && saveRenameGroup()}
                        onBlur={saveRenameGroup}
                        autoFocus
                        className="h-6 text-sm text-foreground bg-background"
                        onClick={(e) => e.stopPropagation()}
                      />
                    ) : (
                      <span className="text-sm font-medium">{group.name}</span>
                    )}
                    <span className="text-xs text-muted-foreground">({group.sessions.length})</span>
                    {/* 分组操作按钮 */}
                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          startRenameGroup(group.id, group.name)
                        }}
                        className="p-1 rounded hover:bg-white/10 dark:hover:bg-white/20 transition-colors"
                        title="重命名分组"
                      >
                        <Edit2 className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDeleteGroup(group.id)
                        }}
                        className="p-1 rounded hover:bg-red-500/20 text-red-500 hover:text-red-600 transition-colors"
                        title="删除分组"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                  
                  {expandedGroups.has(group.id) && (
                    <div className="ml-6 space-y-1">
                      {group.sessions.map(session => (
                        <SessionItem 
                          key={session.id}
                          session={session}
                          isActive={currentSession?.id === session.id}
                          isEditing={editingSession === session.id}
                          editTitle={editTitle}
                          onSelect={() => setCurrentSession(session)}
                          onStartRename={() => startRename(session)}
                          onSaveRename={saveRename}
                          onDelete={() => deleteSession(session.id)}
                          onMoveToGroup={() => startMoveSession(session.id, group.id)}
                          onEditChange={setEditTitle}
                        />
                      ))}
                    </div>
                  )}
                </div>
              ))}
              
              {/* 未分组会话 */}
              {ungroupedSessions.length > 0 && (
                <div className="mt-2">
                  <div className="text-xs text-muted-foreground px-2 py-1">未分组</div>
                  {ungroupedSessions.map(session => (
                    <SessionItem 
                      key={session.id}
                      session={session}
                      isActive={currentSession?.id === session.id}
                      isEditing={editingSession === session.id}
                      editTitle={editTitle}
                      onSelect={() => setCurrentSession(session)}
                      onStartRename={() => startRename(session)}
                      onSaveRename={saveRename}
                      onDelete={() => deleteSession(session.id)}
                      onMoveToGroup={() => startMoveSession(session.id, undefined)}
                      onEditChange={setEditTitle}
                    />
                  ))}
                </div>
              )}
            </div>
          </ScrollArea>

          <Button 
            variant="outline" 
            className="mt-4 w-full"
            onClick={() => setSettingsOpen(true)}
          >
            <Settings className="w-4 h-4 mr-2" />
            AI 设置
          </Button>
        </CardContent>
      </Card>

      {/* 右侧聊天区域 */}
      <Card className="flex-1 flex flex-col">
        <CardContent className="p-0 flex flex-col h-full">
          {currentSession ? (
            <>
              {/* 顶部工具栏 - 元宝风格 */}
              <div className="flex items-center justify-between px-4 py-3 border-b">
                <div className="flex items-center gap-4">
                  {/* 模型选择 */}
                  <select
                    value={currentLLMConfigId}
                    onChange={(e) => setCurrentLLMConfig(e.target.value)}
                    className="text-sm border rounded px-2 py-1 bg-background"
                  >
                    {llmConfigs.map(cfg => (
                      <option key={cfg.id} value={cfg.id}>{cfg.name}</option>
                    ))}
                  </select>
                  
                  {/* 功能开关 */}
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setUseDeepThinking(!useDeepThinking)}
                      className={cn(
                        "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm transition-colors",
                        useDeepThinking 
                          ? "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300" 
                          : "hover:bg-muted"
                      )}
                    >
                      <Brain className="w-4 h-4" />
                      深度思考
                    </button>
                    
                    <button
                      onClick={() => setUseWebSearch(!useWebSearch)}
                      className={cn(
                        "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm transition-colors",
                        useWebSearch 
                          ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300" 
                          : "hover:bg-muted"
                      )}
                    >
                      <Globe className="w-4 h-4" />
                      联网搜索
                    </button>
                    
                    <button
                      onClick={() => setUseKnowledgeBase(!useKnowledgeBase)}
                      className={cn(
                        "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm transition-colors",
                        useKnowledgeBase 
                          ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300" 
                          : "hover:bg-muted"
                      )}
                    >
                      <Database className="w-4 h-4" />
                      知识库
                    </button>
                  </div>
                </div>
                
                {/* 上下文可视化 */}
                <ContextCircle 
                  current={currentSession.contextLength} 
                  max={currentSession.maxContextLength} 
                />
              </div>

              {/* 消息列表 */}
              <ScrollArea className="flex-1 p-4">
                <div className="space-y-4">
                  {currentSession.messages.map((message) => (
                    <div
                      key={message.id}
                      className={cn(
                        "flex gap-3",
                        message.role === 'user' ? "flex-row-reverse" : "flex-row"
                      )}
                    >
                      <div className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
                        message.role === 'user' ? "bg-primary" : "bg-muted"
                      )}>
                        <span className="text-sm">
                          {message.role === 'user' ? '👤' : '🤖'}
                        </span>
                      </div>
                      <div className={cn(
                        "max-w-[80%] rounded-lg p-3",
                        message.role === 'user' 
                          ? "bg-primary text-primary-foreground" 
                          : "bg-muted"
                      )}>
                        {/* 思考过程 */}
                        {message.thinking && (
                          <div className="mb-3 p-2 bg-yellow-100/50 dark:bg-yellow-900/20 rounded text-sm">
                            <div className="flex items-center gap-1 text-yellow-800 dark:text-yellow-200 mb-1">
                              <Brain className="w-3 h-3" />
                              <span className="font-medium">思考过程</span>
                            </div>
                            <div className="text-yellow-700 dark:text-yellow-300/80">
                              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {message.thinking}
                              </ReactMarkdown>
                            </div>
                          </div>
                        )}
                        
                        {/* 功能标签 */}
                        {(message.useDeepThinking || message.useWebSearch) && (
                          <div className="flex gap-2 mb-2">
                            {message.useDeepThinking && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
                                深度思考
                              </span>
                            )}
                            {message.useWebSearch && (
                              <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                                联网搜索
                              </span>
                            )}
                          </div>
                        )}
                        
                        {/* 知识库引用 */}
                        {message.knowledgeReferences && message.knowledgeReferences.length > 0 && (
                          <div className="mb-3 p-2 bg-green-100/50 dark:bg-green-900/20 rounded text-sm">
                            <div className="flex items-center gap-1 text-green-800 dark:text-green-200 mb-1">
                              <Database className="w-3 h-3" />
                              <span className="font-medium">知识库引用</span>
                            </div>
                            {message.knowledgeReferences.map((ref, idx) => (
                              <div key={idx} className="text-xs text-green-700 dark:text-green-300/80 mt-1">
                                [{idx + 1}] {ref.source} (相似度：{(ref.similarity * 100).toFixed(1)}%)
                              </div>
                            ))}
                          </div>
                        )}
                        
                        {message.images && message.images.length > 0 && (
                          <div className="flex gap-2 mb-2 flex-wrap">
                            {message.images.map((img, idx) => (
                              <img 
                                key={idx} 
                                src={img} 
                                alt="uploaded" 
                                className="w-20 h-20 object-cover rounded"
                              />
                            ))}
                          </div>
                        )}
                        
                        <div className={cn(
                          "prose prose-sm max-w-none",
                          message.role === 'user' && "prose-invert"
                        )}>
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content}
                          </ReactMarkdown>
                        </div>
                        
                        {/* 操作按钮 */}
                        {message.role === 'assistant' && (
                          <div className="flex items-center gap-2 mt-3 pt-2 border-t border-border/50">
                            <button
                              onClick={() => handleCopyMessage(message.content)}
                              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                            >
                              <Copy className="w-3 h-3" />
                              复制
                            </button>
                            <button
                              onClick={() => handleExportMessage(message.content)}
                              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                            >
                              <FileDown className="w-3 h-3" />
                              导出 MD
                            </button>
                          </div>
                        )}
                        
                        <span className="text-xs opacity-50 mt-2 block">
                          {formatDate(message.timestamp)}
                        </span>
                      </div>
                    </div>
                  ))}
                  
                  {/* 流式消息 */}
                  {streamingMessage && (
                    <div className="flex gap-3">
                      <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                        <span className="text-sm">🤖</span>
                      </div>
                      <div className="max-w-[80%] rounded-lg p-3 bg-muted">
                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {streamingMessage.content}
                          </ReactMarkdown>
                        </div>
                        <span className="text-xs opacity-50 mt-2 block animate-pulse">
                          生成中...
                        </span>
                      </div>
                    </div>
                  )}
                  
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>

              {/* 输入区域 */}
              <div className="p-4 border-t">
                {/* 知识库阈值调节 */}
                {useKnowledgeBase && (
                  <div className="flex items-center gap-4 mb-3 px-2">
                    <span className="text-sm text-muted-foreground">召回阈值:</span>
                    <Slider
                      value={[knowledgeThreshold]}
                      onValueChange={([v]) => setKnowledgeThreshold(v)}
                      min={0}
                      max={1}
                      step={0.05}
                      className="w-48"
                    />
                    <span className="text-sm font-medium">{(knowledgeThreshold * 100).toFixed(0)}%</span>
                  </div>
                )}
                
                {/* 待发送图片预览 */}
                {pendingImages.length > 0 && (
                  <div className="flex gap-2 mb-2 flex-wrap">
                    {pendingImages.map((img, idx) => (
                      <div key={idx} className="relative">
                        <img 
                          src={img} 
                          alt="pending" 
                          className="w-16 h-16 object-cover rounded"
                        />
                        <button
                          onClick={() => removePendingImage(idx)}
                          className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full flex items-center justify-center text-xs"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
                
                <div className="flex gap-2">
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    className="hidden"
                    ref={fileInputRef}
                    onChange={handleImageUpload}
                  />
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <ImageIcon className="w-4 h-4" />
                  </Button>
                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="输入消息... (Enter 发送，Shift+Enter 换行)"
                    className="flex-1 min-h-[44px] max-h-[200px] p-2 rounded-md border border-input bg-background text-sm resize-none"
                    rows={1}
                  />
                  <Button 
                    onClick={handleSend}
                    disabled={isLoading || (!input.trim() && pendingImages.length === 0)}
                  >
                    {isLoading ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Send className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-muted-foreground">
              <div className="text-center">
                <MessageSquare className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>选择一个会话或创建新会话开始聊天</p>
                <Button className="mt-4" onClick={createSession}>
                  <Plus className="w-4 h-4 mr-2" />
                  新建会话
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 设置弹窗 */}
      <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <SlidersHorizontal className="w-5 h-5" />
              AI 设置
            </DialogTitle>
          </DialogHeader>
          <AISettingsPanel 
            llmConfigs={llmConfigs}
            currentConfigId={currentLLMConfigId}
            onConfigChange={setCurrentLLMConfig}
            onSaveConfig={updateAIConfig}
          />
        </DialogContent>
      </Dialog>

      {/* 新建分组弹窗 */}
      <Dialog open={showGroupDialog} onOpenChange={setShowGroupDialog}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>新建分组</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Input
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              placeholder="分组名称"
              onKeyDown={(e) => e.key === 'Enter' && handleCreateGroup()}
            />
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowGroupDialog(false)}>
                取消
              </Button>
              <Button onClick={handleCreateGroup}>
                创建
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* 移动会话弹窗 */}
      <Dialog open={showMoveDialog} onOpenChange={setShowMoveDialog}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>移动到分组</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">选择目标分组</label>
              <select
                value={targetGroupId}
                onChange={(e) => setTargetGroupId(e.target.value)}
                className="w-full p-2 border rounded-md bg-background"
              >
                <option value="">未分组</option>
                {sessionGroups.map(group => (
                  <option key={group.id} value={group.id}>{group.name}</option>
                ))}
              </select>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowMoveDialog(false)}>
                取消
              </Button>
              <Button onClick={handleMoveSession} disabled={!targetGroupId}>
                移动
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// 会话项组件
function SessionItem({ 
  session, 
  isActive, 
  isEditing, 
  editTitle,
  onSelect, 
  onStartRename, 
  onSaveRename,
  onDelete,
  onMoveToGroup,
  onEditChange
}: {
  session: ChatSession
  isActive: boolean
  isEditing: boolean
  editTitle: string
  onSelect: () => void
  onStartRename: () => void
  onSaveRename: () => void
  onDelete: () => void
  onMoveToGroup: () => void
  onEditChange: (title: string) => void
}) {
  const [showMenu, setShowMenu] = useState(false)

  if (isEditing) {
    return (
      <div className="flex items-center gap-2 p-2">
        <Input
          value={editTitle}
          onChange={(e) => onEditChange(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onSaveRename()}
          onBlur={onSaveRename}
          autoFocus
          className="h-8 text-sm text-foreground bg-background"
        />
      </div>
    )
  }

  return (
    <div
      onClick={onSelect}
      className={cn(
        "flex items-center gap-2 p-2 rounded-lg cursor-pointer group",
        isActive 
          ? "bg-primary text-white" 
          : "hover:bg-muted"
      )}
    >
      <div className="flex-1 min-w-0">
        <span className={cn(
          "text-sm truncate block",
          isActive ? "text-white font-medium" : "text-foreground"
        )}>{session.title || '新会话'}</span>
        <span className={cn(
          "text-xs",
          isActive ? "text-white/80" : "opacity-60"
        )}>
          {session.messages.length} 条消息
        </span>
      </div>
      
      {/* 上下文指示器 */}
      <ContextCircle 
        current={session.contextLength} 
        max={session.maxContextLength} 
      />
      
      <div className="relative">
        <button
          onClick={(e) => {
            e.stopPropagation()
            setShowMenu(!showMenu)
          }}
          className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-muted-foreground/20"
        >
          <MoreVertical className="w-4 h-4" />
        </button>
        
        {showMenu && (
          <div className="absolute right-0 top-full mt-1 w-32 bg-popover border rounded-lg shadow-lg z-10">
            <button
              onClick={(e) => {
                e.stopPropagation()
                onStartRename()
                setShowMenu(false)
              }}
              className="w-full px-3 py-2 text-sm text-left hover:bg-muted flex items-center gap-2"
            >
              <Edit2 className="w-3 h-3" />
              重命名
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onMoveToGroup()
                setShowMenu(false)
              }}
              className="w-full px-3 py-2 text-sm text-left hover:bg-muted flex items-center gap-2"
            >
              <Folder className="w-3 h-3" />
              移动到
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onDelete()
                setShowMenu(false)
              }}
              className="w-full px-3 py-2 text-sm text-left hover:bg-muted text-red-500 flex items-center gap-2"
            >
              <Trash2 className="w-3 h-3" />
              删除
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// AI 设置面板
function AISettingsPanel({ 
  llmConfigs,
  currentConfigId,
  onConfigChange,
  onSaveConfig
}: {
  llmConfigs: LLMAPIConfig[]
  currentConfigId: string
  onConfigChange: (id: string) => void
  onSaveConfig: (config: any) => Promise<void>
}) {
  const [activeTab, setActiveTab] = useState<'general' | 'models'>('general')
  const [editingConfig, setEditingConfig] = useState<LLMAPIConfig | null>(null)

  return (
    <div className="space-y-4">
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('general')}
          className={cn(
            "px-4 py-2 text-sm font-medium border-b-2 transition-colors",
            activeTab === 'general' 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          通用设置
        </button>
        <button
          onClick={() => setActiveTab('models')}
          className={cn(
            "px-4 py-2 text-sm font-medium border-b-2 transition-colors",
            activeTab === 'models' 
              ? "border-primary text-primary" 
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
        >
          模型配置
        </button>
      </div>

      {activeTab === 'general' ? (
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">默认启用深度思考</label>
            <div className="flex items-center gap-2 mt-1">
              <input type="checkbox" className="rounded" />
              <span className="text-sm text-muted-foreground">新会话默认开启深度思考模式</span>
            </div>
          </div>
          
          <div>
            <label className="text-sm font-medium">默认启用联网搜索</label>
            <div className="flex items-center gap-2 mt-1">
              <input type="checkbox" className="rounded" />
              <span className="text-sm text-muted-foreground">新会话默认开启联网搜索</span>
            </div>
          </div>
          
          <div>
            <label className="text-sm font-medium">知识库召回阈值</label>
            <div className="flex items-center gap-4 mt-1">
              <Slider defaultValue={[0.7]} min={0} max={1} step={0.05} className="w-48" />
              <span className="text-sm">70%</span>
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="space-y-2">
            {llmConfigs.map(config => (
              <div 
                key={config.id}
                className={cn(
                  "flex items-center justify-between p-3 rounded-lg border cursor-pointer",
                  currentConfigId === config.id ? "border-primary bg-primary/5" : "hover:bg-muted"
                )}
                onClick={() => onConfigChange(config.id)}
              >
                <div>
                  <span className="font-medium">{config.name}</span>
                  <p className="text-xs text-muted-foreground">{config.model}</p>
                </div>
                <div className="flex gap-2">
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      setEditingConfig(config)
                    }}
                  >
                    编辑
                  </Button>
                  {currentConfigId === config.id && (
                    <Check className="w-5 h-5 text-primary" />
                  )}
                </div>
              </div>
            ))}
          </div>
          
          <Button 
            variant="outline" 
            className="w-full"
            onClick={() => setEditingConfig({
              id: '',
              name: '新配置',
              apiKey: '',
              baseUrl: 'https://api.openai.com/v1',
              model: 'gpt-3.5-turbo',
              requestFormat: 'openai',
              backupConfigs: []
            })}
          >
            <Plus className="w-4 h-4 mr-2" />
            添加模型配置
          </Button>
        </div>
      )}
    </div>
  )
}
