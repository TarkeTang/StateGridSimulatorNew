/**
 * 字典 API 服务
 */

import api from './api'

// ==================== 类型定义 ====================

export interface DictData {
  id: number
  type_code: string
  code: string
  name: string
  value: string | null
  parent_code: string | null
  description: string | null
  sort: number
  status: boolean
  extra_data: string | null
  created_at: string | null
  updated_at: string | null
}

export interface DictType {
  id: number
  code: string
  name: string
  description: string | null
  sort: number
  status: boolean
  created_at: string | null
  updated_at: string | null
}

// ==================== API 服务 ====================

export const dictService = {
  /**
   * 获取字典类型列表
   */
  getTypes: () => {
    return api.get<DictType[]>('/dict/types')
  },

  /**
   * 根据类型编码获取字典数据
   */
  getDataByType: (typeCode: string) => {
    return api.get<DictData[]>(`/dict/data/${typeCode}`)
  },

  /**
   * 获取协议类型字典
   */
  getProtocolTypes: () => {
    return dictService.getDataByType('protocol_type')
  },
}

// ==================== 字典缓存 ====================

const dictCache = new Map<string, DictData[]>()

/**
 * 获取字典数据（带缓存）
 */
export const getDictData = async (typeCode: string): Promise<DictData[]> => {
  if (dictCache.has(typeCode)) {
    return dictCache.get(typeCode)!
  }

  const response = await dictService.getDataByType(typeCode)
  if (response.code === 200 && response.data) {
    dictCache.set(typeCode, response.data)
    return response.data
  }
  return []
}

/**
 * 根据编码获取字典名称
 */
export const getDictName = (dataList: DictData[], code: string): string => {
  const item = dataList.find((d) => d.code === code)
  return item?.name || code
}