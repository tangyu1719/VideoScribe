import { useState, useEffect, useCallback } from 'react'
import {
  FileText,
  RefreshCw,
  Search,
  Trash2,
  Download,
  Clock,
  AlertCircle,
  Info,
  AlertTriangle,
  Bug,
  ChevronLeft,
  ChevronRight,
  Calendar,
  X
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Select } from '@/components/ui/Select'
import { ScrollArea } from '@/components/ui/ScrollArea'
import { logApi } from '@/services/config'
import { cn, formatDate } from '@/lib/utils'
import type { SystemLog } from '@/types'

const levelConfig = {
  info: { icon: Info, color: 'bg-blue-500', label: '信息', textColor: 'text-blue-600' },
  warning: { icon: AlertTriangle, color: 'bg-yellow-500', label: '警告', textColor: 'text-yellow-600' },
  error: { icon: AlertCircle, color: 'bg-red-500', label: '错误', textColor: 'text-red-600' },
  debug: { icon: Bug, color: 'bg-purple-500', label: '调试', textColor: 'text-purple-600' }
}

const moduleOptions = [
  { value: '', label: '所有模块' },
  { value: 'system', label: '系统' },
  { value: 'config', label: '配置' },
  { value: 'chat', label: 'AI对话' },
  { value: 'video', label: '视频下载' },
  { value: 'link', label: '链接分析' },
  { value: 'knowledge', label: '知识库' },
  { value: 'api', label: 'API接口' }
]

export default function Logs() {
  const [logs, setLogs] = useState<SystemLog[]>([])
  const [loading, setLoading] = useState(false)
  const [levelFilter, setLevelFilter] = useState<string>('')
  const [moduleFilter, setModuleFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [startTime, setStartTime] = useState<string>('')
  const [endTime, setEndTime] = useState<string>('')
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [stats, setStats] = useState<{ byLevel: Record<string, number>; byModule: Record<string, number> } | null>(null)

  const loadLogs = useCallback(async () => {
    setLoading(true)
    try {
      const data = await logApi.getLogs({
        level: levelFilter || undefined,
        module: moduleFilter || undefined,
        search: searchQuery || undefined,
        startTime: startTime || undefined,
        endTime: endTime || undefined,
        page,
        pageSize
      })
      setLogs(data.items)
      setTotal(data.total)
      setTotalPages(data.totalPages)
    } catch (err) {
      console.error('加载日志失败:', err)
    } finally {
      setLoading(false)
    }
  }, [levelFilter, moduleFilter, searchQuery, startTime, endTime, page, pageSize])

  const loadStats = async () => {
    try {
      const data = await logApi.getLogStats()
      setStats(data)
    } catch (err) {
      console.error('加载统计失败:', err)
    }
  }

  useEffect(() => {
    loadLogs()
    loadStats()
  }, [loadLogs])

  // 当筛选条件改变时重置页码
  useEffect(() => {
    setPage(1)
  }, [levelFilter, moduleFilter, searchQuery, startTime, endTime])

  const handleClearLogs = async () => {
    if (!confirm('确定要清理所有日志吗？')) return
    try {
      await logApi.clearLogs()
      await loadLogs()
      await loadStats()
    } catch (err) {
      console.error('清理日志失败:', err)
    }
  }

  const handleExport = () => {
    const content = logs.map(log => {
      const detailsStr = log.details
        ? (typeof log.details === 'string' ? log.details : JSON.stringify(log.details, null, 2))
        : ''
      return `[${formatDate(log.timestamp)}] [${log.level.toUpperCase()}] [${log.module}] ${log.message}${detailsStr ? '\n' + detailsStr : ''}`
    }).join('\n')

    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs_${Date.now()}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const clearFilters = () => {
    setLevelFilter('')
    setModuleFilter('')
    setSearchQuery('')
    setStartTime('')
    setEndTime('')
    setPage(1)
  }

  const hasActiveFilters = levelFilter || moduleFilter || searchQuery || startTime || endTime

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* 统计卡片 */}
      {stats && stats.byLevel && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(stats.byLevel).map(([level, count]) => {
            const config = levelConfig[level as keyof typeof levelConfig]
            const Icon = config?.icon || Info
            return (
              <Card key={level} className="cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => setLevelFilter(level === levelFilter ? '' : level)}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{config?.label || level}</p>
                      <p className="text-2xl font-bold">{count}</p>
                    </div>
                    <div className={cn("w-10 h-10 rounded-full flex items-center justify-center", config?.color)}>
                      <Icon className="w-5 h-5 text-white" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* 日志列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              系统日志
              <Badge variant="secondary">{total} 条</Badge>
            </span>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleExport}>
                <Download className="w-4 h-4 mr-2" />
                导出
              </Button>
              <Button variant="outline" size="sm" onClick={handleClearLogs}>
                <Trash2 className="w-4 h-4 mr-2" />
                清理
              </Button>
              <Button variant="outline" size="sm" onClick={loadLogs}>
                <RefreshCw className={cn("w-4 h-4 mr-2", loading && "animate-spin")} />
                刷新
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* 筛选栏 */}
          <div className="flex flex-wrap gap-2 mb-4">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="搜索日志内容..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                leftIcon={<Search className="w-4 h-4" />}
              />
            </div>
            <Select
              value={levelFilter}
              onValueChange={setLevelFilter}
              options={[
                { value: '', label: '所有级别' },
                { value: 'info', label: '信息' },
                { value: 'warning', label: '警告' },
                { value: 'error', label: '错误' },
                { value: 'debug', label: '调试' }
              ]}
              className="w-28"
            />
            <Select
              value={moduleFilter}
              onValueChange={setModuleFilter}
              options={moduleOptions}
              className="w-32"
            />
            <div className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-muted-foreground" />
              <input
                type="datetime-local"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="px-2 py-1.5 border rounded-md text-sm bg-background"
                placeholder="开始时间"
              />
              <span className="text-muted-foreground">-</span>
              <input
                type="datetime-local"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="px-2 py-1.5 border rounded-md text-sm bg-background"
                placeholder="结束时间"
              />
            </div>
            {hasActiveFilters && (
              <Button variant="ghost" size="sm" onClick={clearFilters}>
                <X className="w-4 h-4 mr-1" />
                清除筛选
              </Button>
            )}
          </div>

          {/* 日志列表 */}
          <ScrollArea className="h-[500px]">
            <div className="space-y-2">
              {logs.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>暂无日志记录</p>
                  {hasActiveFilters && (
                    <p className="text-sm mt-2">尝试清除筛选条件</p>
                  )}
                </div>
              ) : (
                logs.map((log) => {
                  const config = levelConfig[log.level]
                  const Icon = config?.icon || Info
                  return (
                    <div
                      key={log.id}
                      className="p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <div className={cn("w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0", config?.color)}>
                          <Icon className="w-4 h-4 text-white" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <Badge variant="outline">{log.module}</Badge>
                            <span className={cn("text-xs font-medium", config?.textColor)}>
                              {config?.label || log.level}
                            </span>
                            <span className="text-xs text-muted-foreground flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {formatDate(log.timestamp)}
                            </span>
                          </div>
                          <p className="text-sm break-words">{log.message}</p>
                          {log.details && (
                            <details className="mt-2">
                              <summary className="text-xs text-muted-foreground cursor-pointer">查看详情</summary>
                              <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-auto whitespace-pre-wrap">
                                {typeof log.details === 'string' ? log.details : JSON.stringify(log.details, null, 2)}
                              </pre>
                            </details>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </ScrollArea>

          {/* 分页 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t">
              <div className="text-sm text-muted-foreground">
                第 {page} 页，共 {totalPages} 页 ({total} 条)
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page <= 1 || loading}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages || loading}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
