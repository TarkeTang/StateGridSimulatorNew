/**
 * 自动发送配置 API 服务
 */

import api from './api'

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

export interface AutoSendStatus {
  session_id: number
  is_active: boolean
  task_count: number
  started_at?: string
  tasks?: Array<{
    config_id: number
    is_running: boolean
    send_count: number
    last_send_at?: string
  }>
}

// ==================== API 服务 ====================

export const autoSendService = {
  /**
   * 创建自动发送配置
   */
  create: (data: AutoSendConfigCreate) => {
    return api.post<AutoSendConfig>('/auto-send', data)
  },

  /**
   * 获取会话的自动发送配置列表
   */
  getListBySession: (sessionId: number) => {
    return api.get<AutoSendConfigListResponse>(`/auto-send/session/${sessionId}`)
  },

  /**
   * 获取自动发送配置详情
   */
  getById: (configId: number) => {
    return api.get<AutoSendConfig>(`/auto-send/${configId}`)
  },

  /**
   * 更新自动发送配置
   */
  update: (configId: number, data: AutoSendConfigUpdate) => {
    return api.put<AutoSendConfig>(`/auto-send/${configId}`, data)
  },

  /**
   * 删除自动发送配置
   */
  delete: (configId: number) => {
    return api.delete<null>(`/auto-send/${configId}`)
  },

  /**
   * 批量创建自动发送配置
   */
  batchCreate: (data: AutoSendConfigBatchCreate) => {
    return api.post<AutoSendConfig[]>('/auto-send/batch', data)
  },

  /**
   * 批量更新自动发送配置
   */
  batchUpdate: (data: AutoSendConfigBatchUpdate) => {
    return api.put<AutoSendConfig[]>('/auto-send/batch', data)
  },

  /**
   * 清空会话的自动发送配置
   */
  clearBySession: (sessionId: number) => {
    return api.delete<null>(`/auto-send/session/${sessionId}`)
  },

  /**
   * 重新排序
   */
  reorder: (orderedIds: number[]) => {
    return api.post<null>('/auto-send/reorder', { ordered_ids: orderedIds })
  },

  // ==================== 自动发送任务控制 ====================

  /**
   * 启动自动发送
   */
  start: (sessionId: number) => {
    return api.post<AutoSendStatus>(`/auto-send/session/${sessionId}/start`)
  },

  /**
   * 停止自动发送
   */
  stop: (sessionId: number) => {
    return api.post<AutoSendStatus>(`/auto-send/session/${sessionId}/stop`)
  },

  /**
   * 获取自动发送状态
   */
  getStatus: (sessionId: number) => {
    return api.get<AutoSendStatus>(`/auto-send/session/${sessionId}/status`)
  },
}