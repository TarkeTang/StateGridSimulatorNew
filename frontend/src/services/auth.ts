import api from './api'
import type { ApiResponse, HealthResponse } from '@/types/api'

/**
 * 健康检查服务
 */
export const healthService = {
  /**
   * 获取系统健康状态
   */
  getHealth: () => {
    return api.get<ApiResponse<HealthResponse>>('/health')
  },

  /**
   * 存活检查
   */
  getLiveness: () => {
    return api.get<ApiResponse<{ status: string }>>('/health/live')
  },

  /**
   * 就绪检查
   */
  getReadiness: () => {
    return api.get<ApiResponse<{ status: string }>>('/health/ready')
  },
}

/**
 * 认证服务
 */
export const authService = {
  /**
   * 用户登录
   */
  login: (username: string, password: string) => {
    return api.post<ApiResponse<{ access_token: string; refresh_token: string }>>('/auth/login', {
      username,
      password,
    })
  },

  /**
   * 刷新令牌
   */
  refreshToken: (refreshToken: string) => {
    return api.post<ApiResponse<{ access_token: string }>>('/auth/refresh', {
      refresh_token: refreshToken,
    })
  },

  /**
   * 用户登出
   */
  logout: () => {
    return api.post<ApiResponse<null>>('/auth/logout')
  },
}