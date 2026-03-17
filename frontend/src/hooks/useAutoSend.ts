/**
 * 自动发送 Hook
 *
 * 管理自动发送功能：
 * - 配置加载和管理
 * - 启动/停止自动发送
 * - 状态同步
 */

import { useState, useCallback, useEffect } from 'react'
import { autoSendService, type AutoSendConfig, type AutoSendStatus } from '@/services/autoSend'

export interface UseAutoSendOptions {
  sessionId: number | null
  isConnected: boolean
  onSendMessage: (content: string) => void
}

export interface UseAutoSendReturn {
  // 配置
  configs: AutoSendConfig[]
  configsLoading: boolean

  // 状态
  isActive: boolean
  status: AutoSendStatus | null

  // 操作
  loadConfigs: () => Promise<void>
  addConfig: () => Promise<void>
  updateConfig: (configId: number, field: keyof AutoSendConfig, value: any) => Promise<void>
  removeConfig: (configId: number) => Promise<void>
  startAutoSend: () => Promise<boolean>
  stopAutoSend: () => Promise<void>
}

export function useAutoSend({ sessionId, isConnected, onSendMessage }: UseAutoSendOptions): UseAutoSendReturn {
  // 配置
  const [configs, setConfigs] = useState<AutoSendConfig[]>([])
  const [configsLoading, setConfigsLoading] = useState(false)

  // 状态
  const [isActive, setIsActive] = useState(false)
  const [status, setStatus] = useState<AutoSendStatus | null>(null)

  // 加载配置
  const loadConfigs = useCallback(async () => {
    if (!sessionId) return

    setConfigsLoading(true)
    try {
      const response = await autoSendService.getListBySession(sessionId)
      if (response.code === 200 && response.data) {
        setConfigs(response.data.items)
      }
    } catch (err) {
      console.error('加载自动发送配置失败:', err)
    } finally {
      setConfigsLoading(false)
    }
  }, [sessionId])

  // 加载状态
  const loadStatus = useCallback(async () => {
    if (!sessionId) return

    try {
      const response = await autoSendService.getStatus(sessionId)
      if (response.code === 200 && response.data) {
        setIsActive(response.data.is_active)
        setStatus(response.data)
      }
    } catch (err) {
      console.error('加载自动发送状态失败:', err)
    }
  }, [sessionId])

  // 添加配置
  const addConfig = useCallback(async () => {
    if (!sessionId) return

    try {
      const response = await autoSendService.create({
        session_id: sessionId,
        message_content: '',
        interval_ms: 1000,
        is_enabled: true,
        sort_order: configs.length,
      })
      if (response.code === 200 && response.data) {
        setConfigs((prev) => [...prev, response.data!])
      }
    } catch (err) {
      console.error('添加自动发送配置失败:', err)
    }
  }, [sessionId, configs.length])

  // 更新配置
  const updateConfig = useCallback(
    async (configId: number, field: keyof AutoSendConfig, value: any) => {
      try {
        await autoSendService.update(configId, { [field]: value })
        setConfigs((prev) =>
          prev.map((c) => (c.id === configId ? { ...c, [field]: value } : c))
        )
      } catch (err) {
        console.error('更新自动发送配置失败:', err)
      }
    },
    []
  )

  // 删除配置
  const removeConfig = useCallback(async (configId: number) => {
    try {
      await autoSendService.delete(configId)
      setConfigs((prev) => prev.filter((c) => c.id !== configId))
    } catch (err) {
      console.error('删除自动发送配置失败:', err)
    }
  }, [])

  // 启动自动发送
  const startAutoSend = useCallback(async (): Promise<boolean> => {
    if (!sessionId || !isConnected) return false

    try {
      const response = await autoSendService.start(sessionId)
      if (response.code === 200) {
        setIsActive(true)
        setStatus(response.data)
        onSendMessage(`自动发送已启动，共 ${configs.filter(c => c.is_enabled).length} 条消息`)
        return true
      } else {
        alert(response.message || '启动失败')
        return false
      }
    } catch (err: any) {
      alert(err.message || '启动失败')
      return false
    }
  }, [sessionId, isConnected, configs, onSendMessage])

  // 停止自动发送
  const stopAutoSend = useCallback(async () => {
    if (!sessionId) return

    try {
      const response = await autoSendService.stop(sessionId)
      if (response.code === 200) {
        setIsActive(false)
        setStatus(null)
        onSendMessage('自动发送已停止')
      }
    } catch (err) {
      console.error('停止自动发送失败:', err)
    }
  }, [sessionId, onSendMessage])

  // 初始化
  useEffect(() => {
    loadConfigs()
    loadStatus()
  }, [loadConfigs, loadStatus])

  // 连接断开时停止自动发送
  useEffect(() => {
    if (!isConnected && isActive) {
      stopAutoSend()
    }
  }, [isConnected, isActive, stopAutoSend])

  return {
    configs,
    configsLoading,
    isActive,
    status,
    loadConfigs,
    addConfig,
    updateConfig,
    removeConfig,
    startAutoSend,
    stopAutoSend,
  }
}