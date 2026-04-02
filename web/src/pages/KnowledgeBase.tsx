import { useState, useEffect, useRef } from 'react'
import { 
  Upload, 
  Trash2, 
  RefreshCw, 
  Search, 
  FileText, 
  FolderOpen,
  Loader2,
  Database,
  File
} from 'lucide-react'
import { knowledgeBaseApi } from '@/services/knowledgeBase'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Progress } from '@/components/ui/Progress'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/Dialog'
import { cn, formatFileSize, formatDate } from '@/lib/utils'
import type { KnowledgeBaseFile, KnowledgeBaseStats, SearchResult } from '@/types'

export default function KnowledgeBase() {
  const [files, setFiles] = useState<KnowledgeBaseFile[]>([])
  const [stats, setStats] = useState<KnowledgeBaseStats | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searchOpen, setSearchOpen] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const folderInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setIsLoading(true)
    try {
      const [filesData, statsData] = await Promise.all([
        knowledgeBaseApi.getFiles(1, 100),
        knowledgeBaseApi.getStats()
      ])
      setFiles(filesData.items)
      setStats(statsData)
    } catch (err) {
      console.error('加载数据失败:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files) return

    for (const file of Array.from(files)) {
      try {
        setUploadProgress(prev => ({ ...prev, [file.name]: 0 }))
        await knowledgeBaseApi.uploadFile(file, (progress) => {
          setUploadProgress(prev => ({ ...prev, [file.name]: progress }))
        })
      } catch (err) {
        console.error('上传失败:', err)
      } finally {
        setUploadProgress(prev => {
          const newProgress = { ...prev }
          delete newProgress[file.name]
          return newProgress
        })
      }
    }
    
    await loadData()
  }

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这个文件吗？')) return
    
    try {
      await knowledgeBaseApi.deleteFile(id)
      await loadData()
    } catch (err) {
      console.error('删除失败:', err)
    }
  }

  const handleRebuild = async () => {
    if (!confirm('重建索引可能需要一些时间，确定要继续吗？')) return
    
    setIsLoading(true)
    try {
      await knowledgeBaseApi.rebuildIndex()
      await loadData()
    } catch (err) {
      console.error('重建索引失败:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    
    try {
      const results = await knowledgeBaseApi.search(searchQuery, 10)
      setSearchResults(results)
      setSearchOpen(true)
    } catch (err) {
      console.error('搜索失败:', err)
    }
  }

  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return '📄'
    if (type.includes('word') || type.includes('document')) return '📝'
    if (type.includes('text')) return '📃'
    if (type.includes('markdown')) return '📑'
    return '📎'
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* 统计卡片 */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">总文件数</p>
                  <p className="text-2xl font-bold">{stats.totalFiles}</p>
                </div>
                <Database className="w-8 h-8 text-primary opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">已索引</p>
                  <p className="text-2xl font-bold">{stats.indexedFiles}</p>
                </div>
                <FileText className="w-8 h-8 text-green-500 opacity-50" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">总大小</p>
                  <p className="text-2xl font-bold">{formatFileSize(stats.totalSize)}</p>
                </div>
                <FolderOpen className="w-8 h-8 text-blue-500 opacity-50" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 操作栏 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>文件管理</span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => fileInputRef.current?.click()}
              >
                <Upload className="w-4 h-4 mr-2" />
                上传文件
              </Button>
              <Button
                variant="outline"
                onClick={() => folderInputRef.current?.click()}
              >
                <FolderOpen className="w-4 h-4 mr-2" />
                上传文件夹
              </Button>
              <Button
                variant="outline"
                onClick={handleRebuild}
                disabled={isLoading}
              >
                <RefreshCw className={cn("w-4 h-4 mr-2", isLoading && "animate-spin")} />
                重建索引
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* 搜索框 */}
          <div className="flex gap-2 mb-4">
            <Input
              placeholder="搜索知识库..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              leftIcon={<Search className="w-4 h-4" />}
            />
            <Button onClick={handleSearch}>
              <Search className="w-4 h-4 mr-2" />
              搜索
            </Button>
          </div>

          <input
            type="file"
            multiple
            className="hidden"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".txt,.md,.pdf,.doc,.docx"
          />
          <input
            type="file"
            multiple
            directory=""
            webkitdirectory=""
            className="hidden"
            ref={folderInputRef}
            onChange={handleFileUpload}
          />

          {/* 上传进度 */}
          {Object.entries(uploadProgress).length > 0 && (
            <div className="space-y-2 mb-4">
              {Object.entries(uploadProgress).map(([filename, progress]) => (
                <div key={filename} className="flex items-center gap-2">
                  <span className="text-sm flex-1 truncate">{filename}</span>
                  <Progress value={progress} className="w-32 h-2" />
                  <span className="text-sm text-muted-foreground w-12">{progress}%</span>
                </div>
              ))}
            </div>
          )}

          {/* 文件列表 */}
          {files.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <File className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>暂无文件，请上传文档到知识库</p>
            </div>
          ) : (
            <div className="space-y-2">
              {files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center gap-4 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                >
                  <span className="text-2xl">{getFileIcon(file.type)}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium truncate">{file.name}</span>
                      <Badge variant={file.status === 'indexed' ? 'default' : 'secondary'}>
                        {file.status === 'indexed' ? '已索引' : file.status === 'pending' ? '待处理' : '失败'}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>{formatFileSize(file.size)}</span>
                      <span>•</span>
                      <span>{formatDate(file.createdAt)}</span>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(file.id)}
                  >
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 搜索结果弹窗 */}
      <Dialog open={searchOpen} onOpenChange={setSearchOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-auto">
          <DialogHeader>
            <DialogTitle>搜索结果</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            {searchResults.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">未找到相关结果</p>
            ) : (
              searchResults.map((result, idx) => (
                <div key={idx} className="p-4 rounded-lg border">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium">{result.source}</span>
                    <Badge>相似度: {(result.similarity * 100).toFixed(1)}%</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-3">{result.content}</p>
                </div>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
