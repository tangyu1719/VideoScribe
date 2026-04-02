import axios, { AxiosInstance, AxiosError } from 'axios'
import type { ApiResponse, PaginationParams, PaginatedResult } from '@/types'

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error: AxiosError<ApiResponse<unknown>>) => {
    const message = error.response?.data?.error || error.message || '请求失败'
    console.error('API Error:', message)
    return Promise.reject(new Error(message))
  }
)

// 通用请求方法
export async function get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const response = await apiClient.get<ApiResponse<T>>(url, { params })
  if (!response.data.success) {
    throw new Error(response.data.error || '请求失败')
  }
  return response.data.data as T
}

export async function post<T>(url: string, data?: unknown): Promise<T> {
  const response = await apiClient.post<ApiResponse<T>>(url, data)
  if (!response.data.success) {
    throw new Error(response.data.error || '请求失败')
  }
  return response.data.data as T
}

export async function put<T>(url: string, data?: unknown): Promise<T> {
  const response = await apiClient.put<ApiResponse<T>>(url, data)
  if (!response.data.success) {
    throw new Error(response.data.error || '请求失败')
  }
  return response.data.data as T
}

export async function del<T>(url: string): Promise<T> {
  const response = await apiClient.delete<ApiResponse<T>>(url)
  if (!response.data.success) {
    throw new Error(response.data.error || '请求失败')
  }
  return response.data.data as T
}

// 文件上传
export async function uploadFile<T>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
  const formData = new FormData()
  formData.append('file', file)
  
  const response = await apiClient.post<ApiResponse<T>>(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        onProgress(progress)
      }
    },
  })
  
  if (!response.data.success) {
    throw new Error(response.data.error || '上传失败')
  }
  return response.data.data as T
}

// 分页请求辅助函数
export async function getPaginated<T>(
  url: string,
  params: PaginationParams & Record<string, unknown> = { page: 1, pageSize: 20 }
): Promise<PaginatedResult<T>> {
  return get<PaginatedResult<T>>(url, params)
}

export default apiClient
