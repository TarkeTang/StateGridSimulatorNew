/**
 * 消息管理 API 服务
 */

import api from './api'

// ==================== 类型定义 ====================

export interface SessionMessage {
  id: number
  connection_id: number
  session_id: string  // 格式: {config_id}_{timestamp}
  config_id: number
  direction: 'send' | 'receive' | 'system'
  content: string
  content_hex: string | null
  content_length: number
  message_type: string
  protocol_type: string
  source_address: string | null
  source_port: number | null
  target_address: string | null
  target_port: number | null
  status: string
  error_message: string | null
  parsed_data: string | null
  extra_data: string | null
  timestamp: string
  created_at: string
}

export interface SessionMessageListResponse {
  items: SessionMessage[]
  total: number
  page: number
  page_size: number
}

export interface SessionMessageCreate {
  connection_id: number
  session_id: string
  config_id: number
  direction: 'send' | 'receive' | 'system'
  content: string
  content_hex?: string
  message_type?: string
  protocol_type: string
  source_address?: string
  source_port?: number
  target_address?: string
  target_port?: number
  extra_data?: string
}

export interface MessageListParams {
  page?: number
  page_size?: number
  direction?: string
  start_time?: string
  end_time?: string
}

// ==================== API 服务 ====================

export const messageService = {
  /**
   * 创建消息记录
   */
  create: (data: SessionMessageCreate) => {
    return api.post<SessionMessage>('/messages', data)
  },

  /**
   * 获取会话消息列表
   */
  getList: (sessionId: number, params: MessageListParams = {}) => {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.append('page', String(params.page))
    if (params.page_size) queryParams.append('page_size', String(params.page_size))
    if (params.direction) queryParams.append('direction', params.direction)
    if (params.start_time) queryParams.append('start_time', params.start_time)
    if (params.end_time) queryParams.append('end_time', params.end_time)

    return api.get<SessionMessageListResponse>(
      `/messages/session/${sessionId}?${queryParams.toString()}`
    )
  },

  /**
   * 获取配置的最近消息（用于显示旧连接消息）
   */
  getRecentByConfig: (configId: number, limit: number = 10) => {
    return api.get<SessionMessage[]>(`/messages/config/${configId}/recent?limit=${limit}`)
  },

  /**
   * 获取消息详情
   */
  getById: (messageId: number) => {
    return api.get<SessionMessage>(`/messages/${messageId}`)
  },

  /**
   * 清空会话消息
   */
  clearBySession: (sessionId: number) => {
    return api.delete<null>(`/messages/session/${sessionId}`)
  },
}