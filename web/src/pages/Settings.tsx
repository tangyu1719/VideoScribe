import { useState, useEffect } from 'react'
import { 
  Settings as SettingsIcon, 
  Save, 
  RefreshCw,
  Key,
  MessageSquare,
  FileText,
  Database,
  Bell,
  Trash2,
  Plus,
  Edit2,
  Check,
  X,
  Cpu,
  User,
  FileCode
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/Dialog'
import { Slider } from '@/components/ui/Slider'
import { Badge } from '@/components/ui/Badge'
import { useToast } from '@/hooks/useToast'
import { cn } from '@/lib/utils'
import type { LLMAPIConfig, AIPersona, DocumentParser } from '@/types'
import { llmConfigApi, aiPersonaApi, parserApi, configApi } from '@/services/config'

export default function Settings() {
  const [activeTab, setActiveTab] = useState('llm')
  const { toast } = useToast()

  // LLM配置
  const [llmConfigs, setLlmConfigs] = useState<LLMAPIConfig[]>([])
  const [editingLLM, setEditingLLM] = useState<LLMAPIConfig | null>(null)
  const [showLLMDialog, setShowLLMDialog] = useState(false)

  // AI形象配置
  const [aiPersonas, setAiPersonas] = useState<AIPersona[]>([])
  const [editingPersona, setEditingPersona] = useState<AIPersona | null>(null)
  const [showPersonaDialog, setShowPersonaDialog] = useState(false)

  // 文档解析器配置
  const [parsers, setParsers] = useState<DocumentParser[]>([])
  const [editingParser, setEditingParser] = useState<DocumentParser | null>(null)
  const [showParserDialog, setShowParserDialog] = useState(false)

  // 应用配置
  const [appConfig, setAppConfig] = useState({
    currentLLMConfigId: '', // 统一模式下的配置
    chatLLMConfigId: '', // 分开模式下对话 AI 的配置
    parserLLMConfigId: '', // 分开模式下解析器 AI 的配置
    currentAIPersonaId: '',
    currentParserId: '',
    knowledgeBaseThreshold: 0.7,
    defaultDeepThinking: false,
    defaultWebSearch: false,
    useUnifiedAPIConfig: true, // true=统一配置，false=分开配置
  })

  useEffect(() => {
    loadAllConfigs()
  }, [])

  const loadAllConfigs = async () => {
    try {
      const [llmData, personasData, parsersData, appConfigData] = await Promise.all([
        llmConfigApi.getConfigs(),
        aiPersonaApi.getPersonas(),
        parserApi.getParsers(),
        configApi.getAppConfig()
      ])
      setLlmConfigs(llmData)
      setAiPersonas(personasData)
      setParsers(parsersData)
      setAppConfig({
        ...appConfig,
        ...appConfigData
      })
    } catch (err) {
      console.error('加载配置失败:', err)
    }
  }

  // LLM 配置操作
  const handleAddLLM = () => {
    const newConfig: LLMAPIConfig = {
      id: Date.now().toString(),
      name: '新配置',
      apiKey: '',
      baseUrl: 'https://api.openai.com/v1',
      model: 'gpt-3.5-turbo',
      endpointId: '',
      requestFormat: 'openai',
      enabled: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      backupConfigs: []
    }
    setEditingLLM(newConfig)
    setShowLLMDialog(true)
  }

  const handleSaveLLM = async () => {
    console.log('=== 开始保存 LLM 配置 ===')
    console.log('editingLLM:', editingLLM)
    if (!editingLLM) {
      console.error('editingLLM 为空！')
      return
    }
    try {
      console.log('调用 llmConfigApi.saveConfig...')
      await llmConfigApi.saveConfig(editingLLM)
      console.log('保存成功！')
      await loadAllConfigs()
      setShowLLMDialog(false)
      toast({ title: '保存成功', description: 'LLM 配置已保存' })
    } catch (err) {
      console.error('保存失败:', err)
      toast({ title: '保存失败', description: err instanceof Error ? err.message : '未知错误', variant: 'destructive' })
    }
  }

  const handleDeleteLLM = async (id: string) => {
    if (!confirm('确定要删除这个LLM配置吗？')) return
    try {
      await llmConfigApi.deleteConfig(id)
      await loadAllConfigs()
      toast({ title: '删除成功', description: 'LLM配置已删除' })
    } catch (err) {
      toast({ title: '删除失败', description: err instanceof Error ? err.message : '未知错误', variant: 'destructive' })
    }
  }

  // AI形象操作
  const handleAddPersona = () => {
    const newPersona: AIPersona = {
      id: Date.now().toString(),
      name: '新形象',
      description: '',
      systemPrompt: '你是一个专业的AI助手。',
      thinkingSystemPrompt: '你是一个善于分析的 AI 助手。',
      temperature: 0.7,
      maxTokens: 4096,
      topP: 0.9,
      enabled: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    setEditingPersona(newPersona)
    setShowPersonaDialog(true)
  }

  const handleSavePersona = async () => {
    if (!editingPersona) return
    try {
      await aiPersonaApi.savePersona(editingPersona)
      await loadAllConfigs()
      setShowPersonaDialog(false)
      toast({ title: '保存成功', description: 'AI 形象已保存' })
    } catch (err) {
      toast({ title: '保存失败', description: err instanceof Error ? err.message : '未知错误', variant: 'destructive' })
    }
  }

  const handleDeletePersona = async (id: string) => {
    if (!confirm('确定要删除这个AI形象吗？')) return
    try {
      await aiPersonaApi.deletePersona(id)
      await loadAllConfigs()
      toast({ title: '删除成功', description: 'AI 形象已删除' })
    } catch (err) {
      toast({ title: '删除失败', description: err instanceof Error ? err.message : '未知错误', variant: 'destructive' })
    }
  }

  // 文档解析器操作
  const handleAddParser = () => {
    const newParser: DocumentParser = {
      id: Date.now().toString(),
      name: '新解析器',
      description: '',
      systemPrompt: '你是一个专业的视频内容分析助手，擅长从视频转写内容中提取关键信息并进行结构化分析。你的输出格式要求：\n1. 第一行是简洁的中文标题（不超过 20 字符，不要包含#号，不要包含 markdown 语法标记）\n2. 后续是结构化的分析内容',
      rules: '1. 第一行必须是简洁的中文标题（不超过 20 字符，不要包含#号）\n2. 提取视频中的关键知识点和核心信息\n3. 保持客观中立的分析态度\n4. 结构化呈现分析结果\n5. 重点关注视频中的技术讲解和实用信息',
      fileNamingRule: '总记录序号 - 月 - 日 - 文档名称（文档名称从 AI 生成的第一行标题中提取）',
      outputTemplate: '# {platform}视频分析\n\n## 视频信息\n- 分析时间：{datetime}\n- 原始链接：{link}\n- 平台：{platform}\n\n## 语音转文字内容\n{transcript}\n\n## AI 分析摘要\n{summary}',
      userPrompt: '',
      summaryPrompt: '请对以下文本进行总结，提取关键知识点，整理成结构化的格式。\n要求：\n1. 第一行必须是一个简洁的中文标题（不超过 20 个字符，不要包含#号）\n2. 后续内容按逻辑分段整理\n{text}',
      enabled: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    }
    setEditingParser(newParser)
    setShowParserDialog(true)
  }

  const handleSaveParser = async () => {
    if (!editingParser) return
    try {
      await parserApi.saveParser(editingParser)
      await loadAllConfigs()
      setShowParserDialog(false)
      toast({ title: '保存成功', description: '文档解析器已保存' })
    } catch (err) {
      toast({ title: '保存失败', description: err instanceof Error ? err.message : '未知错误', variant: 'destructive' })
    }
  }

  const handleDeleteParser = async (id: string) => {
    if (!confirm('确定要删除这个解析器吗？')) return
    try {
      await parserApi.deleteParser(id)
      await loadAllConfigs()
      toast({ title: '删除成功', description: '解析器已删除' })
    } catch (err) {
      toast({ title: '删除失败', description: err instanceof Error ? err.message : '未知错误', variant: 'destructive' })
    }
  }

  const handleSaveAppConfig = async () => {
    try {
      await configApi.updateAppConfig(appConfig)
      toast({ title: '保存成功', description: '应用配置已保存' })
    } catch (err) {
      toast({ title: '保存失败', description: err instanceof Error ? err.message : '未知错误', variant: 'destructive' })
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <SettingsIcon className="w-5 h-5" />
            系统设置
          </CardTitle>
          <CardDescription>
            统一管理LLM配置、AI形象、文档解析器等配置
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="llm" className="flex items-center gap-2">
                <Key className="w-4 h-4" />
                LLM配置
              </TabsTrigger>
              <TabsTrigger value="persona" className="flex items-center gap-2">
                <User className="w-4 h-4" />
                AI形象
              </TabsTrigger>
              <TabsTrigger value="parser" className="flex items-center gap-2">
                <FileText className="w-4 h-4" />
                文档解析器
              </TabsTrigger>
              <TabsTrigger value="app" className="flex items-center gap-2">
                <Cpu className="w-4 h-4" />
                应用设置
              </TabsTrigger>
            </TabsList>

            {/* LLM 配置 */}
            <TabsContent value="llm" className="space-y-4">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h3 className="text-lg font-medium">LLM API 配置</h3>
                  <p className="text-sm text-muted-foreground">配置多个 LLM API，可在应用设置中选择使用哪个配置</p>
                </div>
                <Button onClick={handleAddLLM}>
                  <Plus className="w-4 h-4 mr-2" />
                  添加配置
                </Button>
              </div>

              <div className="space-y-2">
                {llmConfigs.map((cfg) => (
                  <div 
                    key={cfg.id}
                    className={cn(
                      "flex items-center justify-between p-4 rounded-lg border",
                      appConfig.currentLLMConfigId === cfg.id && "border-primary bg-primary/5"
                    )}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{cfg.name}</span>
                        {cfg.enabled && <Badge variant="default">启用</Badge>}
                        {appConfig.currentLLMConfigId === cfg.id && (
                          <Badge variant="secondary">当前使用</Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{cfg.model}</p>
                      <p className="text-xs text-muted-foreground mt-0.5">{cfg.baseUrl}</p>
                      {/* 备用配置指示 */}
                      {(cfg.backupConfigs || []).length > 0 && (
                        <p className="text-xs text-muted-foreground mt-1">
                          +{(cfg.backupConfigs || []).length} 个备用配置
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" onClick={() => {
                        setEditingLLM(cfg)
                        setShowLLMDialog(true)
                      }}>编辑</Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDeleteLLM(cfg.id)}>
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                ))}
                {llmConfigs.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    暂无 LLM API 配置，请点击上方"添加配置"按钮
                  </p>
                )}
              </div>
            </TabsContent>

            {/* AI形象配置 */}
            <TabsContent value="persona" className="space-y-4">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h3 className="text-lg font-medium">AI形象定义</h3>
                  <p className="text-sm text-muted-foreground">配置AI对话的形象和提示词</p>
                </div>
                <Button onClick={handleAddPersona}>
                  <Plus className="w-4 h-4 mr-2" />
                  添加形象
                </Button>
              </div>

              <div className="space-y-2">
                {aiPersonas.map((persona) => (
                  <div 
                    key={persona.id}
                    className={cn(
                      "flex items-center justify-between p-4 rounded-lg border",
                      appConfig.currentAIPersonaId === persona.id && "border-primary bg-primary/5"
                    )}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{persona.name}</span>
                        {persona.enabled && <Badge variant="default">启用</Badge>}
                        {appConfig.currentAIPersonaId === persona.id && (
                          <Badge variant="secondary">默认</Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1 truncate max-w-xl">{persona.description}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" onClick={() => {
                        setEditingPersona(persona)
                        setShowPersonaDialog(true)
                      }}>编辑</Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDeletePersona(persona.id)}>
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>

            {/* 文档解析器配置 */}
            <TabsContent value="parser" className="space-y-4">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h3 className="text-lg font-medium">文档解析器</h3>
                  <p className="text-sm text-muted-foreground">配置链接分析的解析规则和模板</p>
                </div>
                <Button onClick={handleAddParser}>
                  <Plus className="w-4 h-4 mr-2" />
                  添加解析器
                </Button>
              </div>

              <div className="space-y-2">
                {parsers.map((parser) => (
                  <div 
                    key={parser.id}
                    className={cn(
                      "flex items-center justify-between p-4 rounded-lg border",
                      appConfig.currentParserId === parser.id && "border-primary bg-primary/5"
                    )}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{parser.name}</span>
                        {parser.enabled && <Badge variant="default">启用</Badge>}
                        {appConfig.currentParserId === parser.id && (
                          <Badge variant="secondary">默认</Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1 truncate max-w-xl">{parser.description}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="ghost" size="sm" onClick={() => {
                        setEditingParser(parser)
                        setShowParserDialog(true)
                      }}>编辑</Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDeleteParser(parser.id)}>
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </TabsContent>

            {/* 应用设置 */}
            <TabsContent value="app" className="space-y-4">
              <div className="space-y-6">
                {/* API KEY 配置模式切换 */}
                <div>
                  <h3 className="text-lg font-medium mb-4">API KEY 配置模式</h3>
                  <div className="flex items-center gap-4 p-4 border rounded-lg">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        checked={appConfig.useUnifiedAPIConfig === true}
                        onChange={() => setAppConfig({ ...appConfig, useUnifiedAPIConfig: true })}
                        className="w-4 h-4"
                      />
                      <div>
                        <span className="text-sm font-medium">统一配置</span>
                        <p className="text-xs text-muted-foreground">AI 对话和链接分析共用同一个 LLM API 配置</p>
                      </div>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        checked={appConfig.useUnifiedAPIConfig === false}
                        onChange={() => setAppConfig({ ...appConfig, useUnifiedAPIConfig: false })}
                        className="w-4 h-4"
                      />
                      <div>
                        <span className="text-sm font-medium">分开配置</span>
                        <p className="text-xs text-muted-foreground">AI 对话和链接分析使用不同的 LLM API 配置</p>
                      </div>
                    </label>
                  </div>
                </div>

                {/* 根据模式显示不同的配置选择器 */}
                {appConfig.useUnifiedAPIConfig ? (
                  // 统一模式：只选择一个配置
                  <div>
                    <label className="text-sm font-medium">统一 LLM 配置</label>
                    <select
                      value={appConfig.currentLLMConfigId}
                      onChange={(e) => setAppConfig({ ...appConfig, currentLLMConfigId: e.target.value })}
                      className="mt-1 w-full p-2 border rounded-md bg-background"
                    >
                      <option value="">请选择配置</option>
                      {llmConfigs.map(cfg => (
                        <option key={cfg.id} value={cfg.id}>{cfg.name}</option>
                      ))}
                    </select>
                  </div>
                ) : (
                  // 分开模式：选择两个配置
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium">对话 AI 配置</label>
                      <select
                        value={appConfig.chatLLMConfigId}
                        onChange={(e) => setAppConfig({ ...appConfig, chatLLMConfigId: e.target.value })}
                        className="mt-1 w-full p-2 border rounded-md bg-background"
                      >
                        <option value="">请选择配置</option>
                        {llmConfigs.map(cfg => (
                          <option key={cfg.id} value={cfg.id}>{cfg.name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="text-sm font-medium">解析器 AI 配置</label>
                      <select
                        value={appConfig.parserLLMConfigId}
                        onChange={(e) => setAppConfig({ ...appConfig, parserLLMConfigId: e.target.value })}
                        className="mt-1 w-full p-2 border rounded-md bg-background"
                      >
                        <option value="">请选择配置</option>
                        {llmConfigs.map(cfg => (
                          <option key={cfg.id} value={cfg.id}>{cfg.name}</option>
                        ))}
                      </select>
                    </div>
                  </div>
                )}

                <div>
                  <h3 className="text-lg font-medium mb-4">AI对话设置</h3>
                  <div className="space-y-3">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={appConfig.defaultDeepThinking}
                        onChange={(e) => setAppConfig({ ...appConfig, defaultDeepThinking: e.target.checked })}
                        className="rounded"
                      />
                      <span className="text-sm">默认启用深度思考</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={appConfig.defaultWebSearch}
                        onChange={(e) => setAppConfig({ ...appConfig, defaultWebSearch: e.target.checked })}
                        className="rounded"
                      />
                      <span className="text-sm">默认启用联网搜索</span>
                    </label>
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium mb-4">知识库设置</h3>
                  <div className="space-y-3">
                    <div className="flex items-center gap-4">
                      <span className="text-sm">召回阈值:</span>
                      <Slider
                        value={[appConfig.knowledgeBaseThreshold]}
                        onValueChange={([v]) => setAppConfig({ ...appConfig, knowledgeBaseThreshold: v })}
                        min={0}
                        max={1}
                        step={0.05}
                        className="w-48"
                      />
                      <span className="text-sm font-medium">{(appConfig.knowledgeBaseThreshold * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end pt-4">
                  <Button onClick={handleSaveAppConfig}>
                    <Save className="w-4 h-4 mr-2" />
                    保存设置
                  </Button>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* LLM配置编辑弹窗 */}
      <Dialog open={showLLMDialog} onOpenChange={setShowLLMDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>{editingLLM?.id ? '编辑' : '添加'}LLM 配置</DialogTitle>
          </DialogHeader>
          {editingLLM && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">配置名称</label>
                <Input
                  value={editingLLM.name}
                  onChange={(e) => setEditingLLM({ ...editingLLM, name: e.target.value })}
                  placeholder="例如：火山引擎、OpenAI"
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">API Key</label>
                <Input
                  type="password"
                  value={editingLLM.apiKey}
                  onChange={(e) => setEditingLLM({ ...editingLLM, apiKey: e.target.value })}
                  placeholder="sk-..."
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Base URL</label>
                <Input
                  value={editingLLM.baseUrl}
                  onChange={(e) => setEditingLLM({ ...editingLLM, baseUrl: e.target.value })}
                  placeholder="https://api.openai.com/v1"
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">模型</label>
                <Input
                  value={editingLLM.model}
                  onChange={(e) => setEditingLLM({ ...editingLLM, model: e.target.value })}
                  placeholder="gpt-3.5-turbo"
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">
                  接入点 ID
                  <span className="text-xs text-muted-foreground ml-2">（火山引擎专用，可选）</span>
                </label>
                <Input
                  value={editingLLM.endpointId || ''}
                  onChange={(e) => setEditingLLM({ ...editingLLM, endpointId: e.target.value })}
                  placeholder="ep-xxxxxxxxxxxxx"
                  className="mt-1"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  火山引擎接入点 ID，不使用火山引擎可留空
                </p>
              </div>
              <div>
                <label className="text-sm font-medium">请求格式</label>
                <select
                  value={editingLLM.requestFormat}
                  onChange={(e) => setEditingLLM({ ...editingLLM, requestFormat: e.target.value as 'openai' | 'custom' })}
                  className="mt-1 w-full p-2 border rounded-md bg-background"
                >
                  <option value="openai">OpenAI 格式</option>
                  <option value="custom">自定义格式</option>
                </select>
              </div>

              {/* 备用配置管理 */}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <label className="text-sm font-medium">备用配置（1-5 个，按优先级路由）</label>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => {
                      const currentBackups = editingLLM.backupConfigs || []
                      if (currentBackups.length < 5) {
                        setEditingLLM({
                          ...editingLLM,
                          backupConfigs: [
                            ...currentBackups,
                            {
                              id: `backup-${Date.now()}`,
                              name: `备用${currentBackups.length + 1}`,
                              apiKey: '',
                              baseUrl: editingLLM.baseUrl,
                              model: editingLLM.model,
                              enabled: true,
                              priority: currentBackups.length + 1
                            }
                          ]
                        })
                      }
                    }}
                    disabled={(editingLLM.backupConfigs || []).length >= 5}
                  >
                    <Plus className="w-3 h-3 mr-1" />
                    添加备用
                  </Button>
                </div>
                
                <div className="space-y-2">
                  {(editingLLM.backupConfigs || []).map((backup, index) => (
                    <div key={backup.id} className="p-3 border rounded-lg bg-muted/30">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary">优先级 {index + 1}</Badge>
                          <Input
                            value={backup.name}
                            onChange={(e) => {
                              const newBackups = [...(editingLLM.backupConfigs || [])]
                              newBackups[index].name = e.target.value
                              setEditingLLM({ ...editingLLM, backupConfigs: newBackups })
                            }}
                            className="w-32 h-7 text-xs"
                            placeholder="备用名称"
                          />
                        </div>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            const newBackups = (editingLLM.backupConfigs || []).filter((_, i) => i !== index)
                            setEditingLLM({ ...editingLLM, backupConfigs: newBackups })
                          }}
                        >
                          <X className="w-3 h-3 text-red-500" />
                        </Button>
                      </div>
                      <div className="grid grid-cols-3 gap-2">
                        <div>
                          <label className="text-xs text-muted-foreground">API Key</label>
                          <Input
                            type="password"
                            value={backup.apiKey}
                            onChange={(e) => {
                              const newBackups = [...(editingLLM.backupConfigs || [])]
                              newBackups[index].apiKey = e.target.value
                              setEditingLLM({ ...editingLLM, backupConfigs: newBackups })
                            }}
                            className="h-7 text-xs"
                            placeholder="sk-..."
                          />
                        </div>
                        <div>
                          <label className="text-xs text-muted-foreground">Base URL</label>
                          <Input
                            value={backup.baseUrl}
                            onChange={(e) => {
                              const newBackups = [...(editingLLM.backupConfigs || [])]
                              newBackups[index].baseUrl = e.target.value
                              setEditingLLM({ ...editingLLM, backupConfigs: newBackups })
                            }}
                            className="h-7 text-xs"
                            placeholder="Base URL"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-muted-foreground">模型</label>
                          <Input
                            value={backup.model}
                            onChange={(e) => {
                              const newBackups = [...(editingLLM.backupConfigs || [])]
                              newBackups[index].model = e.target.value
                              setEditingLLM({ ...editingLLM, backupConfigs: newBackups })
                            }}
                            className="h-7 text-xs"
                            placeholder="模型"
                          />
                        </div>
                      </div>
                      <div className="mt-2">
                        <label className="text-xs text-muted-foreground">接入点 ID（可选）</label>
                        <Input
                          value={backup.endpointId || ''}
                          onChange={(e) => {
                            const newBackups = [...(editingLLM.backupConfigs || [])]
                            newBackups[index].endpointId = e.target.value
                            setEditingLLM({ ...editingLLM, backupConfigs: newBackups })
                          }}
                          className="h-7 text-xs"
                          placeholder="ep-xxxxxxxxxxxxx"
                        />
                      </div>
                    </div>
                  ))}
                  {(!editingLLM.backupConfigs || editingLLM.backupConfigs.length === 0) && (
                    <p className="text-sm text-muted-foreground text-center py-4">
                      暂无备用配置，点击"添加备用"按钮添加
                    </p>
                  )}
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setShowLLMDialog(false)}>取消</Button>
                <Button onClick={handleSaveLLM}>保存</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* AI形象编辑弹窗 */}
      <Dialog open={showPersonaDialog} onOpenChange={setShowPersonaDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>{editingPersona?.id ? '编辑' : '添加'}AI形象</DialogTitle>
          </DialogHeader>
          {editingPersona && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">形象名称</label>
                <Input
                  value={editingPersona.name}
                  onChange={(e) => setEditingPersona({ ...editingPersona, name: e.target.value })}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">描述</label>
                <Input
                  value={editingPersona.description}
                  onChange={(e) => setEditingPersona({ ...editingPersona, description: e.target.value })}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">系统提示词</label>
                <textarea
                  value={editingPersona.systemPrompt}
                  onChange={(e) => setEditingPersona({ ...editingPersona, systemPrompt: e.target.value })}
                  className="mt-1 w-full min-h-[100px] p-2 border rounded-md bg-background text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium">思考过程提示词</label>
                <textarea
                  value={editingPersona.thinkingSystemPrompt}
                  onChange={(e) => setEditingPersona({ ...editingPersona, thinkingSystemPrompt: e.target.value })}
                  className="mt-1 w-full min-h-[80px] p-2 border rounded-md bg-background text-sm"
                />
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium">Temperature</label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="2"
                    value={editingPersona.temperature}
                    onChange={(e) => setEditingPersona({ ...editingPersona, temperature: parseFloat(e.target.value) })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Max Tokens</label>
                  <Input
                    type="number"
                    value={editingPersona.maxTokens}
                    onChange={(e) => setEditingPersona({ ...editingPersona, maxTokens: parseInt(e.target.value) })}
                    className="mt-1"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Top P</label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={editingPersona.topP}
                    onChange={(e) => setEditingPersona({ ...editingPersona, topP: parseFloat(e.target.value) })}
                    className="mt-1"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setShowPersonaDialog(false)}>取消</Button>
                <Button onClick={handleSavePersona}>保存</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* 文档解析器编辑弹窗 */}
      <Dialog open={showParserDialog} onOpenChange={setShowParserDialog}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>{editingParser?.id ? '编辑' : '添加'}文档解析器</DialogTitle>
          </DialogHeader>
          {editingParser && (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">解析器名称</label>
                <Input
                  value={editingParser.name}
                  onChange={(e) => setEditingParser({ ...editingParser, name: e.target.value })}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">描述</label>
                <Input
                  value={editingParser.description}
                  onChange={(e) => setEditingParser({ ...editingParser, description: e.target.value })}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">系统提示词</label>
                <textarea
                  value={editingParser.systemPrompt}
                  onChange={(e) => setEditingParser({ ...editingParser, systemPrompt: e.target.value })}
                  className="mt-1 w-full min-h-[100px] p-2 border rounded-md bg-background text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium">规则</label>
                <textarea
                  value={editingParser.rules}
                  onChange={(e) => setEditingParser({ ...editingParser, rules: e.target.value })}
                  className="mt-1 w-full min-h-[80px] p-2 border rounded-md bg-background text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium">输出模板</label>
                <textarea
                  value={editingParser.outputTemplate}
                  onChange={(e) => setEditingParser({ ...editingParser, outputTemplate: e.target.value })}
                  className="mt-1 w-full min-h-[80px] p-2 border rounded-md bg-background text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium">用户提示词</label>
                <textarea
                  value={editingParser.userPrompt}
                  onChange={(e) => setEditingParser({ ...editingParser, userPrompt: e.target.value })}
                  className="mt-1 w-full min-h-[60px] p-2 border rounded-md bg-background text-sm"
                />
              </div>
              <div>
                <label className="text-sm font-medium">文件命名规则</label>
                <Input
                  value={editingParser.fileNamingRule}
                  onChange={(e) => setEditingParser({ ...editingParser, fileNamingRule: e.target.value })}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">总结提示词</label>
                <textarea
                  value={editingParser.summaryPrompt}
                  onChange={(e) => setEditingParser({ ...editingParser, summaryPrompt: e.target.value })}
                  className="mt-1 w-full min-h-[60px] p-2 border rounded-md bg-background text-sm"
                />
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setShowParserDialog(false)}>取消</Button>
                <Button onClick={handleSaveParser}>保存</Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
