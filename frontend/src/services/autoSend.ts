/**
 * 自动发送配置 API 服务
 */

import api from './api'
import type { ApiResponse } from '@/types/api'

// ==================== 类型定义 ====================

export interface AutoSendConfig {
  id: number
  session_id: number
  message_content: string
  interval_ms: number
  is_enabled: boolean
  sort_order: number
  description: string | null
  created_at: string
  updated_at: string
}

export interface AutoSendConfigListResponse {
  items: AutoSendConfig[]
  total: number
}

export interface AutoSendConfigCreate {
  session_id: number
  message_content: string
  interval_ms?: number
  is_enabled?: boolean
  sort_order?: number
  description?: string
}

export interface AutoSendConfigUpdate {
  message_content?: string
  interval_ms?: number
  is_enabled?: boolean
  sort_order?: number
  description?: string
}

export interface AutoSendConfigBatchCreate {
  session_id: number
  configs: AutoSendConfigItem[]
}

export interface AutoSendConfigItem {
  message_content: string
  interval_ms?: number
  is_enabled?: boolean
  sort_order?: number
  description?: string
}

export interface AutoSendConfigBatchUpdate {
  configs: Array<{ id: number } & AutoSendConfigUpdate>
}

// ==================== API 服务 ====================

export const autoSendService = {
  /**
   * 创建自动发送配置
   */
  create: (data: AutoSendConfigCreate) => {
    return api.post<ApiResponse<AutoSendConfig>>('/auto-send', data)
  },

  /**
   * 获取会话的自动发送配置列表
   */
  getListBySession: (sessionId: number) => {
    return api.get<ApiResponse<AutoSendConfigListResponse>>(`/auto-send/session/${sessionId}`)
  },

  /**
   * 获取自动发送配置详情
   */
  getById: (configId: number) => {
    return api.get<ApiResponse<AutoSendConfig>>(`/auto-send/${configId}`)
  },

  /**
   * 更新自动发送配置
   */
  update: (configId: number, data: AutoSendConfigUpdate) => {
    return api.put<ApiResponse<AutoSendConfig>>(`/auto-send/${configId}`, data)
  },

  /**
   * 删除自动发送配置
   */
  delete: (configId: number) => {
    return api.delete<ApiResponse<null>>(`/auto-send/${configId}`)
  },

  /**
   * 批量创建自动发送配置
   */
  batchCreate: (data: AutoSendConfigBatchCreate) => {
    return api.post<ApiResponse<AutoSendConfig[]>>('/auto-send/batch', data)
  },

  /**
   * 批量更新自动发送配置
   */
  batchUpdate: (data: AutoSendConfigBatchUpdate) => {
    return api.put<ApiResponse<AutoSendConfig[]>>('/auto-send/batch', data)
  },

  /**
   * 清空会话的自动发送配置
   */
  clearBySession: (sessionId: number) => {
    return api.delete<ApiResponse<null>>(`/auto-send/session/${sessionId}`)
  },

  /**
   * 重新排序
   */
  reorder: (orderedIds: number[]) => {
    return api.post<ApiResponse<null>>('/auto-send/reorder', { ordered_ids: orderedIds })
  },
}