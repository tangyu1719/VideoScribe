import { useState, useEffect, useCallback, useRef } from 'react'
import { 
  Link2, 
  Loader2, 
  ExternalLink, 
  Download,
  Image as ImageIcon,
  Video,
  FileText,
  Settings,
  Sparkles,
  Key,
  MessageSquare,
  Save,
  X,
  ChevronDown,
  ChevronUp,
  Copy,
  FileDown,
  FolderOpen,
  CheckCircle2,
  AlertCircle,
  Clock,
  ListTodo,
  Upload,
  File,
  Music,
  Table,
  Trash2
} from 'lucide-react'
import { linkAnalyzerApi, type LinkTask } from '@/services/linkAnalyzer'
import { chatApi } from '@/services/chat'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/Dialog'
import { Select } from '@/components/ui/Select'
import { Progress } from '@/components/ui/Progress'
import { cn } from '@/lib/utils'
import type { LLMAPIConfig, DocumentParser } from '@/types'
import { useToast } from '@/hooks/useToast'

// 阶段配置
const stageConfig: Record<string, { label: string; icon: React.ElementType; description: string }> = {
  detect_type: { 
    label: '检测链接类型', 
    icon: Link2, 
    description: '识别平台类型（小红书/抖音等）和内容类型（视频/图文）'
  },
  extract_content: { 
    label: '提取内容', 
    icon: FileText, 
    description: '提取图文内容或下载视频文件'
  },
  transcribe: { 
    label: '语音转文字', 
    icon: MessageSquare, 
    description: '将视频语音转换为文字（仅视频）'
  },
  ai_analysis: { 
    label: 'AI分析', 
    icon: Sparkles, 
    description: '使用AI分析内容并生成摘要'
  },
  generate_md: { 
    label: '生成Markdown', 
    icon: FileDown, 
    description: '根据模板生成Markdown文档'
  },
  export: { 
    label: '导出完成', 
    icon: CheckCircle2, 
    description: '文件已保存到指定位置'
  }
}

// 文件类型配置
const fileTypeConfig: Record<string, { label: string; icon: React.ElementType; accept: string; color: string }> = {
  image: { 
    label: '图片', 
    icon: ImageIcon, 
    accept: '.jpg,.jpeg,.png,.gif,.webp,.bmp',
    color: 'text-purple-500'
  },
  pdf: { 
    label: 'PDF', 
    icon: FileText, 
    accept: '.pdf',
    color: 'text-red-500'
  },
  docx: { 
    label: 'Word', 
    icon: FileText, 
    accept: '.docx,.doc',
    color: 'text-blue-500'
  },
  markdown: { 
    label: 'Markdown', 
    icon: FileText, 
    accept: '.md,.markdown',
    color: 'text-gray-500'
  },
  csv: { 
    label: 'CSV', 
    icon: Table, 
    accept: '.csv',
    color: 'text-green-500'
  },
  audio: { 
    label: '音频', 
    icon: Music, 
    accept: '.mp3,.wav,.m4a,.flac,.ogg,.aac',
    color: 'text-orange-500'
  },
  video: { 
    label: '视频', 
    icon: Video, 
    accept: '.mp4,.avi,.mov,.mkv,.flv,.wmv',
    color: 'text-pink-500'
  }
}

// 支持的文件类型列表
const supportedFileTypes = [
  { type: 'image', extensions: ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'], maxSize: 10 * 1024 * 1024 },
  { type: 'pdf', extensions: ['pdf'], maxSize: 50 * 1024 * 1024 },
  { type: 'docx', extensions: ['docx', 'doc'], maxSize: 20 * 1024 * 1024 },
  { type: 'markdown', extensions: ['md', 'markdown'], maxSize: 5 * 1024 * 1024 },
  { type: 'csv', extensions: ['csv'], maxSize: 10 * 1024 * 1024 },
  { type: 'audio', extensions: ['mp3', 'wav', 'm4a', 'flac', 'ogg', 'aac'], maxSize: 100 * 1024 * 1024 },
  { type: 'video', extensions: ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'], maxSize: 500 * 1024 * 1024 }
]

export default function LinkAnalyzer() {
  const { toast } = useToast()
  
  // 输入模式: 'link' | 'file'
  const [inputMode, setInputMode] = useState<'link' | 'file'>('link')
  
  // 链接输入
  const [url, setUrl] = useState('')
  
  // 文件上传状态
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [dragActive, setDragActive] = useState(false)
  
  // 通用状态
  const [isLoading, setIsLoading] = useState(false)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [llmConfigs, setLlmConfigs] = useState<LLMAPIConfig[]>([])
  const [currentConfigId, setCurrentConfigId] = useState('')

  // 解析器选择
  const [parsers, setParsers] = useState<DocumentParser[]>([])
  const [currentParserId, setCurrentParserId] = useState('')

  // 输出目录
  const [outputDir, setOutputDir] = useState('')

  // 任务状态
  const [currentTask, setCurrentTask] = useState<LinkTask | null>(null)
  const [taskPollInterval, setTaskPollInterval] = useState<NodeJS.Timeout | null>(null)

  // 任务列表
  const [taskList, setTaskList] = useState<LinkTask[]>([])
  const [showTaskList, setShowTaskList] = useState(false)

  // 配置状态
  const [config, setConfig] = useState({
    userPrompt: '',
    systemPrompt: '你是一个专业的内容分析助手，擅长分析社交媒体内容。',
    enableImageAnalysis: true,
    enableCommentExtraction: false,
  })

  // API配置编辑
  const [editingApiConfig, setEditingApiConfig] = useState<LLMAPIConfig | null>(null)
  const [showApiConfigDialog, setShowApiConfigDialog] = useState(false)

  useEffect(() => {
    loadLLMConfigs()
    loadParsers()
    loadTaskList()
  }, [])

  // 清理轮询
  useEffect(() => {
    return () => {
      if (taskPollInterval) {
        clearInterval(taskPollInterval)
      }
    }
  }, [taskPollInterval])

  const loadLLMConfigs = async () => {
    try {
      const configs = await chatApi.getLLMConfigs()
      setLlmConfigs(configs)
      if (configs.length > 0 && !currentConfigId) {
        setCurrentConfigId(configs[0].id)
      }
    } catch (err) {
      console.error('加载LLM配置失败:', err)
    }
  }

  const loadParsers = async () => {
    try {
      const parserList = await linkAnalyzerApi.getParsers()
      setParsers(parserList)
      if (parserList.length > 0 && !currentParserId) {
        setCurrentParserId(parserList[0].id)
      }
    } catch (err) {
      console.error('加载解析器列表失败:', err)
    }
  }

  const loadTaskList = async () => {
    try {
      console.log('[LinkAnalyzer] 开始加载任务列表...')
      const response = await linkAnalyzerApi.listTasks()
      console.log('[LinkAnalyzer] 任务列表响应:', response)
      if (response.success) {
        console.log('[LinkAnalyzer] 任务列表数据:', response.data)
        setTaskList(response.data)
      } else {
        console.error('[LinkAnalyzer] 加载任务列表失败:', response.error)
      }
    } catch (err) {
      console.error('[LinkAnalyzer] 加载任务列表异常:', err)
    }
  }

  const pollTaskStatus = useCallback(async (taskId: string) => {
    try {
      const response = await linkAnalyzerApi.getTask(taskId)
      if (response.success) {
        const task = response.data
        setCurrentTask(task)
        
        // 如果任务完成或失败，停止轮询
        if (task.status === 'completed' || task.status === 'failed') {
          if (taskPollInterval) {
            clearInterval(taskPollInterval)
            setTaskPollInterval(null)
          }
          setIsLoading(false)
          
          if (task.status === 'completed') {
            toast({
              title: '分析完成',
              description: `文件已保存: ${task.result?.filename || ''}`
            })
          } else if (task.status === 'failed') {
            toast({
              title: '分析失败',
              description: task.error || '未知错误',
              variant: 'destructive'
            })
          }
          
          // 刷新任务列表
          loadTaskList()
        }
      }
    } catch (err) {
      console.error('获取任务状态失败:', err)
    }
  }, [taskPollInterval, toast])

  // 链接分析处理
  const handleAnalyze = async () => {
    if (!url.trim()) return
    if (!currentConfigId) {
      toast({
        title: '请先配置LLM API',
        variant: 'destructive'
      })
      return
    }

    setIsLoading(true)
    
    try {
      const response = await linkAnalyzerApi.createTask({
        url: url.trim(),
        config: {
          parserId: currentParserId || undefined,
          llmConfigId: currentConfigId,
          outputDir: outputDir || undefined,
          userPrompt: config.userPrompt
        }
      })

      if (response.success) {
        const taskId = response.data.taskId
        
        // 立即获取一次任务状态
        await pollTaskStatus(taskId)
        
        // 开始轮询任务状态
        const interval = setInterval(() => pollTaskStatus(taskId), 1000)
        setTaskPollInterval(interval)
        
        toast({
          title: '任务已创建',
          description: '开始分析链接...'
        })
      } else {
        throw new Error(response.error || '创建任务失败')
      }
    } catch (err) {
      console.error('创建任务失败:', err)
      toast({
        title: '创建任务失败',
        description: err instanceof Error ? err.message : '未知错误',
        variant: 'destructive'
      })
      setIsLoading(false)
    }
  }

  // 文件上传处理
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(Array.from(e.dataTransfer.files))
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(Array.from(e.target.files))
    }
  }

  const handleFiles = (files: File[]) => {
    const validFiles: File[] = []
    
    files.forEach(file => {
      const ext = file.name.split('.').pop()?.toLowerCase() || ''
      const fileType = supportedFileTypes.find(type => type.extensions.includes(ext))
      
      if (!fileType) {
        toast({
          title: '不支持的文件类型',
          description: `${file.name} 不是支持的文件类型`,
          variant: 'destructive'
        })
        return
      }
      
      if (file.size > fileType.maxSize) {
        toast({
          title: '文件过大',
          description: `${file.name} 超过最大限制 (${(fileType.maxSize / 1024 / 1024).toFixed(0)}MB)`,
          variant: 'destructive'
        })
        return
      }
      
      validFiles.push(file)
    })
    
    setUploadedFiles(prev => [...prev, ...validFiles])
  }

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const getFileTypeIcon = (filename: string) => {
    const ext = filename.split('.').pop()?.toLowerCase() || ''
    
    if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext)) {
      return <ImageIcon className="w-5 h-5 text-purple-500" />
    } else if (ext === 'pdf') {
      return <FileText className="w-5 h-5 text-red-500" />
    } else if (['docx', 'doc'].includes(ext)) {
      return <FileText className="w-5 h-5 text-blue-500" />
    } else if (['md', 'markdown'].includes(ext)) {
      return <FileText className="w-5 h-5 text-gray-500" />
    } else if (ext === 'csv') {
      return <Table className="w-5 h-5 text-green-500" />
    } else if (['mp3', 'wav', 'm4a', 'flac', 'ogg', 'aac'].includes(ext)) {
      return <Music className="w-5 h-5 text-orange-500" />
    } else if (['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'].includes(ext)) {
      return <Video className="w-5 h-5 text-pink-500" />
    }
    return <File className="w-5 h-5 text-gray-500" />
  }

  const handleUploadAndProcess = async () => {
    if (uploadedFiles.length === 0) {
      toast({
        title: '请先选择文件',
        variant: 'destructive'
      })
      return
    }
    
    if (!currentConfigId) {
      toast({
        title: '请先配置LLM API',
        variant: 'destructive'
      })
      return
    }

    setIsUploading(true)
    
    try {
      for (const file of uploadedFiles) {
        const formData = new FormData()
        formData.append('file', file)
        if (currentParserId) {
          formData.append('parser_id', currentParserId)
        }
        if (currentConfigId) {
          formData.append('llm_config_id', currentConfigId)
        }
        if (outputDir) {
          formData.append('output_dir', outputDir)
        }
        if (config.userPrompt) {
          formData.append('user_prompt', config.userPrompt)
        }

        // 使用fetch进行上传以支持进度
        const xhr = new XMLHttpRequest()
        
        await new Promise<void>((resolve, reject) => {
          xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
              const progress = Math.round((e.loaded / e.total) * 100)
              setUploadProgress(prev => ({ ...prev, [file.name]: progress }))
            }
          })
          
          xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
              const response = JSON.parse(xhr.responseText)
              if (response.success) {
                toast({
                  title: `${file.name} 上传成功`,
                  description: '开始处理...'
                })
                resolve()
              } else {
                reject(new Error(response.error || '上传失败'))
              }
            } else {
              reject(new Error(`HTTP ${xhr.status}`))
            }
          })
          
          xhr.addEventListener('error', () => reject(new Error('上传失败')))
          
          xhr.open('POST', '/api/documents/upload')
          xhr.send(formData)
        })
      }
      
      // 清空已上传文件
      setUploadedFiles([])
      setUploadProgress({})
      
      // 刷新任务列表
      loadTaskList()
      
      toast({
        title: '所有文件上传完成',
        description: '请查看任务列表了解处理进度'
      })
    } catch (err) {
      console.error('上传失败:', err)
      toast({
        title: '上传失败',
        description: err instanceof Error ? err.message : '未知错误',
        variant: 'destructive'
      })
    } finally {
      setIsUploading(false)
    }
  }

  const getStageStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />
      case 'in_progress':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />
      default:
        return <Clock className="w-5 h-5 text-gray-400" />
    }
  }

  const handleAddApiConfig = () => {
    const newConfig: LLMAPIConfig = {
      id: Date.now().toString(),
      name: '新配置',
      apiKey: '',
      baseUrl: 'https://api.openai.com/v1',
      model: 'gpt-3.5-turbo',
      requestFormat: 'openai'
    }
    setEditingApiConfig(newConfig)
    setShowApiConfigDialog(true)
  }

  const handleSaveApiConfig = async () => {
    if (!editingApiConfig) return
    
    try {
      await chatApi.saveLLMConfig(editingApiConfig)
      await loadLLMConfigs()
      setShowApiConfigDialog(false)
      setEditingApiConfig(null)
    } catch (err) {
      console.error('保存配置失败:', err)
    }
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* 主输入区域 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Link2 className="w-5 h-5" />
            链接分析
            <div className="ml-auto flex gap-2">
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => {
                  loadTaskList()
                  setShowTaskList(true)
                }}
              >
                <ListTodo className="w-4 h-4 mr-2" />
                任务列表
              </Button>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setSettingsOpen(true)}
              >
                <Settings className="w-4 h-4 mr-2" />
                配置
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 输入模式切换 */}
          <div className="flex gap-2 p-1 bg-muted rounded-lg">
            <Button
              variant={inputMode === 'link' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setInputMode('link')}
              className="flex-1"
            >
              <Link2 className="w-4 h-4 mr-2" />
              链接
            </Button>
            <Button
              variant={inputMode === 'file' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setInputMode('file')}
              className="flex-1"
            >
              <Upload className="w-4 h-4 mr-2" />
              文件
            </Button>
          </div>

          {/* 输出目录 */}
          <div>
            <label className="text-sm font-medium mb-2 block flex items-center gap-2">
              <FolderOpen className="w-4 h-4" />
              输出目录（可选）
            </label>
            <Input
              type="text"
              placeholder="留空使用默认 OUTPUT 目录"
              value={outputDir}
              onChange={(e) => setOutputDir(e.target.value)}
            />
          </div>

          {/* User Prompt 输入 */}
          <div>
            <label className="text-sm font-medium mb-2 block">分析要求（可选）</label>
            <textarea
              value={config.userPrompt}
              onChange={(e) => setConfig({ ...config, userPrompt: e.target.value })}
              placeholder="输入自定义分析要求，例如：提取关键信息、分析情感倾向、总结要点..."
              className="w-full min-h-[80px] p-3 rounded-md border border-input bg-background text-sm resize-none"
            />
          </div>

          {/* 链接输入模式 */}
          {inputMode === 'link' && (
            <div className="flex gap-2">
              <Input
                type="url"
                placeholder="粘贴小红书、抖音等链接..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                leftIcon={<Link2 className="w-4 h-4" />}
                className="flex-1"
                disabled={isLoading}
              />
              <Button 
                onClick={handleAnalyze}
                disabled={isLoading || !url.trim() || !currentConfigId}
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                ) : (
                  <Sparkles className="w-4 h-4 mr-2" />
                )}
                分析
              </Button>
            </div>
          )}

          {/* 文件上传模式 */}
          {inputMode === 'file' && (
            <div className="space-y-4">
              {/* 文件拖放区域 */}
              <div
                className={cn(
                  "relative border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer",
                  dragActive 
                    ? "border-primary bg-primary/5" 
                    : "border-gray-300 hover:border-gray-400 hover:bg-gray-50"
                )}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  className="hidden"
                  onChange={handleFileInput}
                  accept=".jpg,.jpeg,.png,.gif,.webp,.bmp,.pdf,.docx,.doc,.md,.markdown,.csv,.mp3,.wav,.m4a,.flac,.ogg,.aac,.mp4,.avi,.mov,.mkv,.flv,.wmv"
                />
                <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p className="text-lg font-medium mb-2">
                  拖拽文件到此处，或点击选择文件
                </p>
                <p className="text-sm text-muted-foreground">
                  支持：图片、PDF、Word、Markdown、CSV、音频、视频
                </p>
              </div>

              {/* 支持的文件类型说明 */}
              <div className="grid grid-cols-4 gap-3">
                {Object.entries(fileTypeConfig).map(([key, config]) => (
                  <div key={key} className="flex items-center gap-2 p-2 rounded bg-muted/50">
                    <config.icon className={cn("w-4 h-4", config.color)} />
                    <span className="text-xs">{config.label}</span>
                  </div>
                ))}
              </div>

              {/* 已选择文件列表 */}
              {uploadedFiles.length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-sm font-medium">已选择文件 ({uploadedFiles.length})</h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {uploadedFiles.map((file, index) => (
                      <div 
                        key={index}
                        className="flex items-center gap-3 p-3 rounded-lg border bg-muted/30"
                      >
                        {getFileTypeIcon(file.name)}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{file.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {(file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                          {uploadProgress[file.name] !== undefined && (
                            <div className="mt-1">
                              <Progress value={uploadProgress[file.name]} className="h-1" />
                              <p className="text-xs text-muted-foreground mt-0.5">
                                {uploadProgress[file.name]}%
                              </p>
                            </div>
                          )}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            removeFile(index)
                          }}
                          disabled={isUploading}
                        >
                          <Trash2 className="w-4 h-4 text-red-500" />
                        </Button>
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex gap-2 pt-2">
                    <Button
                      variant="outline"
                      onClick={() => setUploadedFiles([])}
                      disabled={isUploading}
                      className="flex-1"
                    >
                      <X className="w-4 h-4 mr-2" />
                      清空
                    </Button>
                    <Button
                      onClick={handleUploadAndProcess}
                      disabled={isUploading || !currentConfigId}
                      className="flex-1"
                    >
                      {isUploading ? (
                        <Loader2 className="w-4 h-4 animate-spin mr-2" />
                      ) : (
                        <Sparkles className="w-4 h-4 mr-2" />
                      )}
                      上传并处理
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 任务进度显示 */}
      {currentTask && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <ListTodo className="w-5 h-5" />
                任务进度
                <Badge variant={currentTask.status === 'completed' ? 'default' : 
                               currentTask.status === 'failed' ? 'destructive' : 'secondary'}>
                  {currentTask.status === 'completed' ? '已完成' :
                   currentTask.status === 'failed' ? '失败' :
                   currentTask.status === 'running' ? '进行中' : '等待中'}
                </Badge>
              </span>
              <span className="text-2xl font-bold text-primary">
                {currentTask.overall_progress}%
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* 总体进度条 */}
            <div className="mb-6">
              <Progress value={currentTask.overall_progress} className="h-3" />
            </div>
            
            {/* 阶段进度 */}
            <div className="space-y-3">
              {Object.entries(currentTask.stages).map(([stageKey, stage], index) => {
                const config = stageConfig[stageKey]
                const Icon = config?.icon || Clock
                const stageNumber = index + 1
                
                return (
                  <div 
                    key={stageKey}
                    className={cn(
                      "relative flex items-start gap-4 p-4 rounded-lg border-2 transition-all",
                      stage.status === 'in_progress' && "bg-blue-50 border-blue-400 shadow-sm",
                      stage.status === 'completed' && "bg-green-50 border-green-300",
                      stage.status === 'failed' && "bg-red-50 border-red-300",
                      stage.status === 'pending' && "bg-gray-50 border-gray-200 opacity-60"
                    )}
                  >
                    {/* 阶段编号 */}
                    <div className={cn(
                      "flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold",
                      stage.status === 'in_progress' && "bg-blue-500 text-white animate-pulse",
                      stage.status === 'completed' && "bg-green-500 text-white",
                      stage.status === 'failed' && "bg-red-500 text-white",
                      stage.status === 'pending' && "bg-gray-300 text-gray-600"
                    )}>
                      {stage.status === 'completed' ? (
                        <CheckCircle2 className="w-5 h-5" />
                      ) : stage.status === 'failed' ? (
                        <AlertCircle className="w-5 h-5" />
                      ) : (
                        stageNumber
                      )}
                    </div>
                    
                    {/* 阶段内容 */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-base">{config?.label || stageKey}</span>
                        {stage.status === 'in_progress' && (
                          <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
                        )}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {stage.message || config?.description}
                      </div>
                      
                      {/* 阶段结果 */}
                      {stage.result && stage.status === 'completed' && (
                        <div className="mt-2 flex flex-wrap gap-2">
                          {stageKey === 'detect_type' && stage.result.platform && (
                            <Badge variant="outline" className="bg-white">
                              平台: {stage.result.platform}
                            </Badge>
                          )}
                          {stageKey === 'detect_type' && stage.result.type && (
                            <Badge variant="outline" className="bg-white">
                              类型: {stage.result.type === 'video' ? '视频' : 
                                     stage.result.type === 'xiaohongshu' ? '小红书图文' : 
                                     stage.result.type === 'douyin_image' ? '抖音图文' : stage.result.type}
                            </Badge>
                          )}
                          {stageKey === 'extract_content' && stage.result.image_links && (
                            <Badge variant="outline" className="bg-white">
                              提取 {stage.result.image_links.length} 张图片
                            </Badge>
                          )}
                          {stageKey === 'ai_analysis' && stage.result.title && (
                            <Badge variant="outline" className="bg-white truncate max-w-[200px]">
                              标题: {stage.result.title}
                            </Badge>
                          )}
                          {stageKey === 'generate_md' && stage.result.filename && (
                            <Badge variant="outline" className="bg-white">
                              {stage.result.filename}
                            </Badge>
                          )}
                        </div>
                      )}
                      
                      {/* 阶段进度条 */}
                      {stage.status === 'in_progress' && (
                        <div className="mt-2">
                          <Progress value={stage.progress} className="h-1.5" />
                        </div>
                      )}
                    </div>
                    
                    {/* 阶段状态 */}
                    <div className="flex-shrink-0">
                      {getStageStatusIcon(stage.status)}
                    </div>
                  </div>
                )
              })}
            </div>

            {/* 完成结果 */}
            {currentTask.result && currentTask.status === 'completed' && (
              <div className="mt-6 p-4 bg-green-100 rounded-lg border-2 border-green-300">
                <div className="flex items-center gap-2 text-green-800">
                  <CheckCircle2 className="w-6 h-6" />
                  <span className="font-bold text-lg">分析完成</span>
                </div>
                <p className="text-sm text-green-700 mt-2">
                  文件已保存到: <code className="bg-green-200 px-2 py-0.5 rounded">{currentTask.result.file_path}</code>
                </p>
              </div>
            )}

            {/* 失败结果 */}
            {currentTask.error && currentTask.status === 'failed' && (
              <div className="mt-6 p-4 bg-red-100 rounded-lg border-2 border-red-300">
                <div className="flex items-center gap-2 text-red-800">
                  <AlertCircle className="w-6 h-6" />
                  <span className="font-bold text-lg">分析失败</span>
                </div>
                <p className="text-sm text-red-700 mt-2">
                  {currentTask.error}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* 任务列表弹窗 */}
      <Dialog open={showTaskList} onOpenChange={setShowTaskList}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ListTodo className="w-5 h-5" />
              任务列表
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-2">
            {taskList.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <ListTodo className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>暂无任务</p>
              </div>
            ) : (
              taskList.map((task) => (
                <div 
                  key={task.id}
                  className={cn(
                    "p-4 rounded-lg border cursor-pointer hover:bg-muted",
                    currentTask?.id === task.id && "border-primary bg-primary/5"
                  )}
                  onClick={() => {
                    setCurrentTask(task)
                    setShowTaskList(false)
                    // 如果任务还在运行，开始轮询
                    if (task.status === 'running' || task.status === 'pending') {
                      const interval = setInterval(() => pollTaskStatus(task.id), 1000)
                      setTaskPollInterval(interval)
                      setIsLoading(true)
                    }
                  }}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{task.url}</div>
                      <div className="text-sm text-muted-foreground flex items-center gap-2">
                        <span>{new Date(task.created_at).toLocaleString()}</span>
                        <span>•</span>
                        <span>{task.overall_progress}%</span>
                      </div>
                    </div>
                    <Badge variant={task.status === 'completed' ? 'default' : 
                                    task.status === 'failed' ? 'destructive' : 'secondary'}>
                      {task.status === 'completed' ? '已完成' :
                       task.status === 'failed' ? '失败' :
                       task.status === 'running' ? '进行中' : '等待中'}
                    </Badge>
                  </div>
                  {task.result?.filename && (
                    <div className="text-sm text-muted-foreground mt-2">
                      {task.result.filename}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* AI 配置弹窗 */}
      <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="w-5 h-5" />
              链接分析配置
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6">
            {/* 解析器选择 */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="text-sm font-medium">选择解析器</label>
                <Button size="sm" onClick={() => window.location.href = '/settings?tab=parsers'}>
                  <Settings className="w-4 h-4 mr-2" />
                  添加解析器
                </Button>
              </div>
              <div className="space-y-2">
                {parsers.map((parser) => (
                  <div
                    key={parser.id}
                    className={cn(
                      "flex items-center justify-between p-3 rounded-lg border cursor-pointer",
                      currentParserId === parser.id ? "border-primary bg-primary/5" : "hover:bg-muted"
                    )}
                    onClick={() => setCurrentParserId(parser.id)}
                  >
                    <div>
                      <div className="font-medium">{parser.name}</div>
                      {parser.description && (
                        <p className="text-xs text-muted-foreground">{parser.description}</p>
                      )}
                    </div>
                    {currentParserId === parser.id && (
                      <Badge variant="default">已选择</Badge>
                    )}
                  </div>
                ))}
                {parsers.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    暂无解析器配置，请点击上方"添加解析器"按钮
                  </p>
                )}
              </div>
            </div>

            {/* LLM API 配置列表 */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="text-sm font-medium">LLM API 配置</label>
                <Button size="sm" onClick={handleAddApiConfig}>
                  <Key className="w-4 h-4 mr-2" />
                  添加配置
                </Button>
              </div>
              
              <div className="space-y-2">
                {llmConfigs.map((cfg) => (
                  <div 
                    key={cfg.id} 
                    className={cn(
                      "flex items-center justify-between p-3 rounded-lg border cursor-pointer",
                      currentConfigId === cfg.id ? "border-primary bg-primary/5" : "hover:bg-muted"
                    )}
                    onClick={() => setCurrentConfigId(cfg.id)}
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{cfg.name}</span>
                        {cfg.enabled && <Badge variant="default">启用</Badge>}
                      </div>
                      <p className="text-xs text-muted-foreground">{cfg.model} • {cfg.baseUrl}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          setEditingApiConfig(cfg)
                          setShowApiConfigDialog(true)
                        }}
                      >
                        编辑
                      </Button>
                    </div>
                  </div>
                ))}
                {llmConfigs.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    暂无配置，请点击上方"添加配置"按钮
                  </p>
                )}
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* API配置编辑弹窗 */}
      <Dialog open={showApiConfigDialog} onOpenChange={setShowApiConfigDialog}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingApiConfig?.id ? '编辑' : '添加'} API配置</DialogTitle>
          </DialogHeader>
          
          {editingApiConfig && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">配置名称</label>
                <Input
                  value={editingApiConfig.name}
                  onChange={(e) => setEditingApiConfig({ ...editingApiConfig, name: e.target.value })}
                  placeholder="例如：OpenAI、火山引擎"
                  className="mt-1"
                />
              </div>
              
              <div>
                <label className="text-sm font-medium">API Key</label>
                <Input
                  type="password"
                  value={editingApiConfig.apiKey}
                  onChange={(e) => setEditingApiConfig({ ...editingApiConfig, apiKey: e.target.value })}
                  placeholder="sk-..."
                  className="mt-1"
                />
              </div>
              
              <div>
                <label className="text-sm font-medium">Base URL</label>
                <Input
                  value={editingApiConfig.baseUrl}
                  onChange={(e) => setEditingApiConfig({ ...editingApiConfig, baseUrl: e.target.value })}
                  placeholder="https://api.openai.com/v1"
                  className="mt-1"
                />
              </div>
              
              <div>
                <label className="text-sm font-medium">模型</label>
                <Input
                  value={editingApiConfig.model}
                  onChange={(e) => setEditingApiConfig({ ...editingApiConfig, model: e.target.value })}
                  placeholder="gpt-3.5-turbo"
                  className="mt-1"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setShowApiConfigDialog(false)}>
                  取消
                </Button>
                <Button onClick={handleSaveApiConfig}>
                  <Save className="w-4 h-4 mr-2" />
                  保存
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
