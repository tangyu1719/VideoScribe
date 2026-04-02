import { get, post, del, uploadFile } from './api'
import type { KnowledgeBaseFile, KnowledgeBaseStats, SearchResult, PaginatedResult } from '@/types'

export const knowledgeBaseApi = {
  // 获取统计信息
  getStats: () =>
    get<KnowledgeBaseStats>('/kb/stats'),

  // 获取文件列表
  getFiles: (page = 1, pageSize = 20) =>
    get<PaginatedResult<KnowledgeBaseFile>>('/kb/files', { page, pageSize }),

  // 上传文件
  uploadFile: (file: File, onProgress?: (progress: number) => void) =>
    uploadFile<KnowledgeBaseFile>('/kb/files', file, onProgress),

  // 上传文件夹（多个文件）
  uploadFiles: (files: File[], onProgress?: (progress: number) => void) =>
    Promise.all(files.map(file => uploadFile<KnowledgeBaseFile>('/kb/files', file, onProgress))),

  // 删除文件
  deleteFile: (id: string) =>
    del<void>(`/kb/files/${id}`),

  // 重建索引
  rebuildIndex: () =>
    post<void>('/kb/rebuild'),

  // 搜索知识库
  search: (query: string, topK = 5) =>
    get<SearchResult[]>('/kb/search', { query, topK }),

  // 获取文件内容
  getFileContent: (id: string) =>
    get<{ content: string }>(`/kb/files/${id}/content`),
}
