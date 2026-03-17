/**
 * WebSocket 服务
 *
 * 提供实时消息推送功能，支持：
- 会话状态变更推送
- 通信消息实时推送
- 系统通知推送
- 自动重连
 */

// ==================== 类型定义 ====================

export interface WSMessage {
  type: 'connected' | 'subscribed' | 'unsubscribed' | 'session_status' | 'communication' | 'notification' | 'pong'
  data: Record<string, any>
  timestamp?: string
}

export interface SessionStatusData {
  session_id: number
  status: 'disconnected' | 'connected' | 'connecting' | 'error'
  error_message?: string
  timestamp: string
}

export interface CommunicationData {
  session_id: number
  direction: 'send' | 'receive' | 'system'
  content: string
  content_hex?: string
  timestamp: string
  is_auto_send?: boolean
}

export interface NotificationData {
  title: string
  message: string
  level: 'info' | 'warning' | 'error' | 'success'
  timestamp: string
}

export type MessageHandler = (message: WSMessage) => void
export type SessionStatusHandler = (data: SessionStatusData) => void
export type CommunicationHandler = (data: CommunicationData) => void
export type NotificationHandler = (data: NotificationData) => void

// ==================== WebSocket 客户端 ====================

class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string = ''
  private reconnectAttempts: number = 0
  private maxReconnectAttempts: number = 5
  private reconnectInterval: number = 3000
  private pingInterval: ReturnType<typeof setInterval> | null = null
  private isConnecting: boolean = false
  private isManualClose: boolean = false

  // 事件处理器
  private messageHandlers: Set<MessageHandler> = new Set()
  private sessionStatusHandlers: Map<number, Set<SessionStatusHandler>> = new Map()
  private communicationHandlers: Map<number, Set<CommunicationHandler>> = new Map()
  private notificationHandlers: Set<NotificationHandler> = new Set()
  private connectionHandlers: Set<(connected: boolean) => void> = new Set()

  // 已订阅的会话
  private subscribedSessions: Set<number> = new Set()

  /**
   * 初始化 WebSocket 连接
   */
  connect(): Promise<boolean> {
    return new Promise((resolve) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve(true)
        return
      }

      if (this.isConnecting) {
        resolve(false)
        return
      }

      this.isConnecting = true
      this.isManualClose = false

      // 构建 WebSocket URL
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      this.url = `${protocol}//${window.location.host}/api/v1/ws`

      try {
        this.ws = new WebSocket(this.url)

        this.ws.onopen = () => {
          console.log('[WebSocket] 连接成功')
          this.isConnecting = false
          this.reconnectAttempts = 0
          this.startPing()
          this.notifyConnectionChange(true)

          // 重新订阅之前的会话
          this.subscribedSessions.forEach((sessionId) => {
            this.subscribeSession(sessionId)
          })

          resolve(true)
        }

        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data)
            this.handleMessage(message)
          } catch (e) {
            console.error('[WebSocket] 解析消息失败:', e)
          }
        }

        this.ws.onerror = (error) => {
          console.error('[WebSocket] 连接错误:', error)
          this.isConnecting = false
          resolve(false)
        }

        this.ws.onclose = () => {
          console.log('[WebSocket] 连接关闭')
          this.isConnecting = false
          this.stopPing()
          this.notifyConnectionChange(false)

          // 自动重连
          if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect()
          }
        }
      } catch (e) {
        console.error('[WebSocket] 创建连接失败:', e)
        this.isConnecting = false
        resolve(false)
      }
    })
  }

  /**
   * 断开连接
   */
  disconnect() {
    this.isManualClose = true
    this.stopPing()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.subscribedSessions.clear()
    this.notifyConnectionChange(false)
  }

  /**
   * 订阅会话消息
   */
  subscribeSession(sessionId: number) {
    this.subscribedSessions.add(sessionId)
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.send({
        type: 'subscribe',
        data: { session_id: sessionId },
      })
    }
  }

  /**
   * 取消订阅会话消息
   */
  unsubscribeSession(sessionId: number) {
    this.subscribedSessions.delete(sessionId)
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.send({
        type: 'unsubscribe',
        data: { session_id: sessionId },
      })
    }
  }

  /**
   * 检查是否已连接
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  /**
   * 添加消息处理器
   */
  onMessage(handler: MessageHandler) {
    this.messageHandlers.add(handler)
    return () => this.messageHandlers.delete(handler)
  }

  /**
   * 添加会话状态处理器
   */
  onSessionStatus(sessionId: number, handler: SessionStatusHandler) {
    if (!this.sessionStatusHandlers.has(sessionId)) {
      this.sessionStatusHandlers.set(sessionId, new Set())
    }
    this.sessionStatusHandlers.get(sessionId)!.add(handler)
    return () => {
      this.sessionStatusHandlers.get(sessionId)?.delete(handler)
    }
  }

  /**
   * 添加通信消息处理器
   */
  onCommunication(sessionId: number, handler: CommunicationHandler) {
    if (!this.communicationHandlers.has(sessionId)) {
      this.communicationHandlers.set(sessionId, new Set())
    }
    this.communicationHandlers.get(sessionId)!.add(handler)
    return () => {
      this.communicationHandlers.get(sessionId)?.delete(handler)
    }
  }

  /**
   * 添加通知处理器
   */
  onNotification(handler: NotificationHandler) {
    this.notificationHandlers.add(handler)
    return () => this.notificationHandlers.delete(handler)
  }

  /**
   * 添加连接状态处理器
   */
  onConnection(handler: (connected: boolean) => void) {
    this.connectionHandlers.add(handler)
    return () => this.connectionHandlers.delete(handler)
  }

  // ==================== 私有方法 ====================

  private send(message: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  private handleMessage(message: WSMessage) {
    // 通知所有消息处理器
    this.messageHandlers.forEach((handler) => {
      try {
        handler(message)
      } catch (e) {
        console.error('[WebSocket] 消息处理器执行失败:', e)
      }
    })

    // 根据消息类型分发
    switch (message.type) {
      case 'session_status': {
        const data = message.data as SessionStatusData
        const handlers = this.sessionStatusHandlers.get(data.session_id)
        if (handlers) {
          handlers.forEach((handler) => handler(data))
        }
        break
      }
      case 'communication': {
        const data = message.data as CommunicationData
        const handlers = this.communicationHandlers.get(data.session_id)
        if (handlers) {
          handlers.forEach((handler) => handler(data))
        }
        break
      }
      case 'notification': {
        const data = message.data as NotificationData
        this.notificationHandlers.forEach((handler) => handler(data))
        break
      }
    }
  }

  private startPing() {
    this.pingInterval = setInterval(() => {
      this.send({ type: 'ping', data: {} })
    }, 30000)
  }

  private stopPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }

  private scheduleReconnect() {
    this.reconnectAttempts++
    console.log(`[WebSocket] 尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
    setTimeout(() => {
      this.connect()
    }, this.reconnectInterval)
  }

  private notifyConnectionChange(connected: boolean) {
    this.connectionHandlers.forEach((handler) => handler(connected))
  }
}

// 全局实例
export const wsClient = new WebSocketClient()

// ==================== 便捷 Hook ====================

import { useEffect, useState, useCallback } from 'react'

/**
 * WebSocket 连接状态 Hook
 */
export function useWebSocketConnection() {
  const [isConnected, setIsConnected] = useState(wsClient.isConnected())

  useEffect(() => {
    const unsubscribe = wsClient.onConnection(setIsConnected)
    return () => {
      unsubscribe()
    }
  }, [])

  const connect = useCallback(() => wsClient.connect(), [])
  const disconnect = useCallback(() => wsClient.disconnect(), [])

  return { isConnected, connect, disconnect }
}

/**
 * 会话消息订阅 Hook
 */
export function useSessionMessages(sessionId: number | null) {
  const [messages, setMessages] = useState<CommunicationData[]>([])
  const [sessionStatus, setSessionStatus] = useState<SessionStatusData | null>(null)

  useEffect(() => {
    if (!sessionId) return

    // 订阅会话
    wsClient.subscribeSession(sessionId)

    // 监听通信消息
    const unsubComm = wsClient.onCommunication(sessionId, (data) => {
      setMessages((prev) => [...prev, data])
    })

    // 监听会话状态
    const unsubStatus = wsClient.onSessionStatus(sessionId, (data) => {
      setSessionStatus(data)
    })

    return () => {
      unsubComm()
      unsubStatus()
      wsClient.unsubscribeSession(sessionId)
    }
  }, [sessionId])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return { messages, sessionStatus, clearMessages }
}