/**
 * 参数化配置服务
 */

import api from './api'
import type { ApiResponse } from '@/types/api'

// 参数类型
export interface ParameterConfig {
  id: number
  name: string
  param_type: string
  static_value: string | null
  config: string | null
  description: string | null
  is_enabled: boolean
  sort_order: number
  created_at: string | null
  updated_at: string | null
}

export interface ParameterConfigCreate {
  name: string
  param_type: string
  static_value?: string | null
  config?: string | null
  description?: string | null
  is_enabled?: boolean
  sort_order?: number
}

export interface ParameterListResponse {
  items: ParameterConfig[]
  total: number
}

// 参数类型映射
export const PARAM_TYPES: Record<string, string> = {
  static: '静态值',
  timestamp: '时间戳',
  random: '随机数',
  uuid: 'UUID',
  counter: '计数器',
  custom: '自定义函数',
}

// 内置参数列表
export const BUILTIN_PARAMS = [
  { name: 'timestamp', description: '当前时间戳（毫秒）', example: '${timestamp}' },
  { name: 'timestamp_s', description: '当前时间戳（秒）', example: '${timestamp_s}' },
  { name: 'datetime', description: '当前日期时间', example: '${datetime}' },
  { name: 'date', description: '当前日期', example: '${date}' },
  { name: 'time', description: '当前时间', example: '${time}' },
  { name: 'uuid', description: 'UUID', example: '${uuid}' },
  { name: 'uuid_short', description: 'UUID（无横线）', example: '${uuid_short}' },
  { name: 'random_int', description: '随机整数', example: '${random_int}' },
  { name: 'random_str', description: '随机字符串', example: '${random_str}' },
]

class ParameterService {
  private baseUrl = '/parameters'

  /**
   * 获取参数类型列表
   */
  async getTypes(): Promise<ApiResponse<Record<string, string>>> {
    return api.get(`${this.baseUrl}/types`)
  }

  /**
   * 获取参数配置列表
   */
  async getList(params?: {
    page?: number
    page_size?: number
    name?: string
    param_type?: string
    is_enabled?: boolean
  }): Promise<ApiResponse<ParameterListResponse>> {
    return api.get(this.baseUrl, { params })
  }

  /**
   * 获取所有启用的参数配置
   */
  async getEnabled(): Promise<ApiResponse<ParameterConfig[]>> {
    return api.get(`${this.baseUrl}/enabled`)
  }

  /**
   * 获取单个参数配置
   */
  async getById(id: number): Promise<ApiResponse<ParameterConfig>> {
    return api.get(`${this.baseUrl}/${id}`)
  }

  /**
   * 创建参数配置
   */
  async create(data: ParameterConfigCreate): Promise<ApiResponse<ParameterConfig>> {
    return api.post(this.baseUrl, data)
  }

  /**
   * 更新参数配置
   */
  async update(id: number, data: Partial<ParameterConfigCreate>): Promise<ApiResponse<ParameterConfig>> {
    return api.put(`${this.baseUrl}/${id}`, data)
  }

  /**
   * 删除参数配置
   */
  async delete(id: number): Promise<ApiResponse<boolean>> {
    return api.delete(`${this.baseUrl}/${id}`)
  }

  /**
   * 预览参数替换结果
   */
  async preview(content: string): Promise<ApiResponse<string>> {
    return api.post(`${this.baseUrl}/preview`, null, { params: { content } })
  }
}

export const parameterService = new ParameterService()