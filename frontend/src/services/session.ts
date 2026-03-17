/**
 * 会话管理 API 服务
 */

import api from './api'

// ==================== 类型定义 ====================

export interface SessionConfig {
  id: number
  name: string
  description: string | null
  protocol_type: string
  connection_mode: 'client' | 'server'
  host: string | null
  port: number | null
  local_host: string | null
  local_port: number | null
  serial_port: string | null
  baud_rate: number | null
  data_bits: number | null
  stop_bits: number | null
  parity: string | null
  timeout: number
  auto_reconnect: boolean
  reconnect_interval: number
  max_reconnect_times: number
  buffer_size: number
  send_buffer_size: number
  encoding: string
  line_ending: string
  status: 'disconnected' | 'connected' | 'connecting' | 'error'
  last_error: string | null
  last_connected_at: string | null
  extra_config: string | null
  group_name: string | null
  tags: string | null
  sort: number
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export interface SessionConfigListResponse {
  items: SessionConfig[]
  total: number
  page: number
  page_size: number
}

export interface SessionConfigCreate {
  name: string
  description?: string
  protocol_type?: string
  connection_mode?: 'client' | 'server'
  host?: string
  port?: number
  local_host?: string
  local_port?: number
  serial_port?: string
  baud_rate?: number
  data_bits?: number
  stop_bits?: number
  parity?: string
  timeout?: number
  auto_reconnect?: boolean
  reconnect_interval?: number
  max_reconnect_times?: number
  buffer_size?: number
  send_buffer_size?: number
  encoding?: string
  line_ending?: string
  extra_config?: string
  group_name?: string
  tags?: string
  sort?: number
  is_enabled?: boolean
}

export interface SessionConfigUpdate extends Partial<SessionConfigCreate> {}

export interface SessionListParams {
  page?: number
  page_size?: number
  protocol_type?: string
  status?: string
  keyword?: string
  is_enabled?: boolean
}

// ==================== API 服务 ====================

export const sessionService = {
  /**
   * 获取会话配置列表
   */
  getList: (params: SessionListParams = {}) => {
    const queryParams = new URLSearchParams()
    if (params.page) queryParams.append('page', String(params.page))
    if (params.page_size) queryParams.append('page_size', String(params.page_size))
    if (params.protocol_type) queryParams.append('protocol_type', params.protocol_type)
    if (params.status) queryParams.append('status', params.status)
    if (params.keyword) queryParams.append('keyword', params.keyword)
    if (params.is_enabled !== undefined) queryParams.append('is_enabled', String(params.is_enabled))

    return api.get<SessionConfigListResponse>(`/sessions?${queryParams.toString()}`)
  },

  /**
   * 获取会话配置详情
   */
  getById: (id: number) => {
    return api.get<SessionConfig>(`/sessions/${id}`)
  },

  /**
   * 创建会话配置
   */
  create: (data: SessionConfigCreate) => {
    return api.post<SessionConfig>('/sessions', data)
  },

  /**
   * 更新会话配置
   */
  update: (id: number, data: SessionConfigUpdate) => {
    return api.put<SessionConfig>(`/sessions/${id}`, data)
  },

  /**
   * 删除会话配置
   */
  delete: (id: number) => {
    return api.delete<null>(`/sessions/${id}`)
  },

  /**
   * 连接会话
   */
  connect: (id: number) => {
    return api.post<SessionConfig>(`/sessions/${id}/connect`)
  },

  /**
   * 断开会话
   */
  disconnect: (id: number) => {
    return api.post<SessionConfig>(`/sessions/${id}/disconnect`)
  },

  /**
   * 发送消息
   */
  send: (id: number, data: string) => {
    return api.post<null>(`/sessions/${id}/send`, { data })
  },
}