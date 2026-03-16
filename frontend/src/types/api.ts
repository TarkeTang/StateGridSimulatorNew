/**
 * API 响应类型定义
 */

// 通用响应结构
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

// 分页数据
export interface PaginatedData<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 健康检查响应
export interface HealthResponse {
  status: 'healthy' | 'unhealthy'
  version: string
  timestamp: string
  components: {
    database: 'connected' | 'disconnected' | 'unknown'
    redis: 'connected' | 'disconnected' | 'unknown'
  }
}

// 用户信息
export interface User {
  id: number
  username: string
  email: string
  role: string
  created_at: string
  updated_at: string
}

// 登录响应
export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}