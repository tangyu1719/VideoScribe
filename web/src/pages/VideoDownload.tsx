import { useState, useEffect } from 'react'
import { 
  Download, 
  Loader2, 
  Trash2, 
  RefreshCw, 
  FileText, 
  CheckCircle, 
  XCircle, 
  Clock,
  Play,
  Link as LinkIcon
} from 'lucide-react'
import { useVideoStore } from '@/store/useVideoStore'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Progress } from '@/components/ui/Progress'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/Dialog'
import { cn, formatDate, truncateText } from '@/lib/utils'
import type { Platform, VideoTask } from '@/types'

const platforms: { value: Platform; label: string; icon: string }[] = [
  { value: 'douyin', label: '抖音', icon: '🎵' },
  { value: 'bilibili', label: 'B站', icon: '📺' },
  { value: 'xiaohongshu', label: '小红书', icon: '📕' },
  { value: 'youtube', label: 'YouTube', icon: '📹' },
  { value: 'other', label: '其他', icon: '🔗' },
]

const statusConfig = {
  pending: { label: '等待中', color: 'bg-gray-500', icon: Clock },
  downloading: { label: '下载中', color: 'bg-blue-500', icon: Download },
  transcribing: { label: '转录中', color: 'bg-yellow-500', icon: Loader2 },
  analyzing: { label: '分析中', color: 'bg-purple-500', icon: Loader2 },
  completed: { label: '已完成', color: 'bg-green-500', icon: CheckCircle },
  failed: { label: '失败', color: 'bg-red-500', icon: XCircle },
}

export default function VideoDownload() {
  const [url, setUrl] = useState('')
  const [platform, setPlatform] = useState<Platform>('douyin')
  const [selectedTask, setSelectedTask] = useState<VideoTask | null>(null)
  const [detailOpen, setDetailOpen] = useState(false)
  
  const { tasks, isLoading, fetchTasks, createTask, deleteTask, retryTask } = useVideoStore()

  useEffect(() => {
    fetchTasks()
    // 轮询更新任务状态
    const interval = setInterval(fetchTasks, 5000)
    return () => clearInterval(interval)
  }, [fetchTasks])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return
    
    await createTask(url, platform)
    setUrl('')
  }

  const handleDelete = async (id: string) => {
    if (confirm('确定要删除这个任务吗？')) {
      await deleteTask(id)
    }
  }

  const handleRetry = async (id: string) => {
    await retryTask(id)
  }

  const openDetail = (task: VideoTask) => {
    setSelectedTask(task)
    setDetailOpen(true)
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* 输入表单 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="w-5 h-5" />
            新建下载任务
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-4">
              <Select
                value={platform}
                onValueChange={(value) => setPlatform(value as Platform)}
                options={platforms.map(p => ({ value: p.value, label: `${p.icon} ${p.label}` }))}
                className="w-full sm:w-40"
              />
              <div className="flex-1 flex gap-2">
                <Input
                  type="url"
                  placeholder="粘贴视频链接..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="flex-1"
                  leftIcon={<LinkIcon className="w-4 h-4" />}
                />
                <Button 
                  type="submit" 
                  disabled={isLoading || !url.trim()}
                  className="whitespace-nowrap"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  ) : (
                    <Download className="w-4 h-4 mr-2" />
                  )}
                  开始下载
                </Button>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* 任务列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              任务列表
            </span>
            <Button variant="outline" size="sm" onClick={fetchTasks}>
              <RefreshCw className="w-4 h-4 mr-2" />
              刷新
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {tasks.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Download className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>暂无任务，请在上方添加视频链接</p>
            </div>
          ) : (
            <div className="space-y-3">
              {tasks.map((task) => {
                const status = statusConfig[task.status]
                const StatusIcon = status.icon
                
                return (
                  <div
                    key={task.id}
                    className="flex items-center gap-4 p-4 rounded-lg border hover:bg-muted/50 transition-colors cursor-pointer"
                    onClick={() => openDetail(task)}
                  >
                    {/* 状态图标 */}
                    <div className={cn('w-10 h-10 rounded-full flex items-center justify-center', status.color)}>
                      <StatusIcon className={cn('w-5 h-5 text-white', task.status === 'downloading' && 'animate-spin')} />
                    </div>
                    
                    {/* 任务信息 */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium truncate">
                          {task.title || truncateText(task.url, 50)}
                        </h3>
                        <Badge variant={task.status === 'completed' ? 'default' : 'secondary'}>
                          {status.label}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <span>{platforms.find(p => p.value === task.platform)?.label}</span>
                        <span>•</span>
                        <span>{formatDate(task.createdAt)}</span>
                        {task.error && (
                          <>
                            <span>•</span>
                            <span className="text-red-500">{task.error}</span>
                          </>
                        )}
                      </div>
                      {(task.status === 'downloading' || task.status === 'transcribing' || task.status === 'analyzing') && (
                        <div className="mt-2">
                          <Progress value={task.progress || 0} className="h-2" />
                          <span className="text-xs text-muted-foreground mt-1">{task.progress || 0}%</span>
                        </div>
                      )}
                    </div>
                    
                    {/* 操作按钮 */}
                    <div className="flex items-center gap-2">
                      {task.status === 'failed' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleRetry(task.id)
                          }}
                        >
                          <RefreshCw className="w-4 h-4" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(task.id)
                        }}
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 任务详情弹窗 */}
      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>任务详情</DialogTitle>
          </DialogHeader>
          {selectedTask && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">状态:</span>
                  <Badge className="ml-2">{statusConfig[selectedTask.status].label}</Badge>
                </div>
                <div>
                  <span className="text-muted-foreground">平台:</span>
                  <span className="ml-2">{platforms.find(p => p.value === selectedTask.platform)?.label}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">创建时间:</span>
                  <span className="ml-2">{formatDate(selectedTask.createdAt)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">进度:</span>
                  <span className="ml-2">{selectedTask.progress || 0}%</span>
                </div>
              </div>
              
              <div>
                <span className="text-muted-foreground text-sm">链接:</span>
                <p className="mt-1 p-2 bg-muted rounded text-sm break-all">{selectedTask.url}</p>
              </div>

              {selectedTask.transcript && (
                <div>
                  <span className="text-muted-foreground text-sm">转录内容:</span>
                  <div className="mt-1 p-3 bg-muted rounded max-h-60 overflow-auto">
                    <pre className="text-sm whitespace-pre-wrap">{selectedTask.transcript}</pre>
                  </div>
                </div>
              )}

              {selectedTask.summary && (
                <div>
                  <span className="text-muted-foreground text-sm">AI分析:</span>
                  <div className="mt-1 p-3 bg-muted rounded max-h-60 overflow-auto">
                    <div className="markdown-content text-sm" dangerouslySetInnerHTML={{ __html: selectedTask.summary }} />
                  </div>
                </div>
              )}

              {selectedTask.error && (
                <div>
                  <span className="text-red-500 text-sm">错误信息:</span>
                  <p className="mt-1 p-2 bg-red-50 text-red-700 rounded text-sm">{selectedTask.error}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
