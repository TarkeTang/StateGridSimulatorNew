/**
 * 会话详情 Hook
 *
 * 管理会话详情页的核心逻辑：
 * - 会话数据加载
 * - 连接/断开操作
 * - 消息发送
 * - WebSocket 实时通信
 * - 加载旧连接消息
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import { sessionService, type SessionConfig } from '@/services/session'
import { messageService, type SessionMessage } from '@/services/message'
import { wsClient, type CommunicationData, type SessionStatusData } from '@/services/websocket'
import { stringToHex } from '@/utils/formatters'

export interface UseSessionDetailOptions {
  sessionId: number | null
}

export interface UseSessionDetailReturn {
  // 会话数据
  session: SessionConfig | null
  loading: boolean
  error: string | null

  // 连接状态
  isConnected: boolean
  isConnecting: boolean
  operating: boolean
  connectTime: string | null

  // 消息
  messages: SessionMessage[]
  sendCount: number
  receiveCount: number

  // 操作
  loadSession: () => Promise<void>
  handleConnect: () => Promise<void>
  handleSend: (data: string) => Promise<boolean>
  clearMessages: () => Promise<void>
  addLocalMessage: (direction: 'send' | 'receive' | 'system', content: string, isAutoSend?: boolean) => void
}

export function useSessionDetail({ sessionId }: UseSessionDetailOptions): UseSessionDetailReturn {
  // 会话数据
  const [session, setSession] = useState<SessionConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 连接状态
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [operating, setOperating] = useState(false)
  const [connectTime, setConnectTime] = useState<string | null>(null)

  // 消息
  const [messages, setMessages] = useState<SessionMessage[]>([])
  const [sendCount, setSendCount] = useState(0)
  const [receiveCount, setReceiveCount] = useState(0)

  // 消息结束引用
  const messagesEndRef = useRef<HTMLDivElement | null>(null)

  // 加载会话配置
  const loadSession = useCallback(async () => {
    if (!sessionId) return

    setLoading(true)
    setError(null)
    try {
      const response = await sessionService.getById(sessionId)
      if (response.code === 200 && response.data) {
        setSession(response.data)
        setIsConnected(response.data.status === 'connected')
      } else {
        setError(response.message || '获取会话配置失败')
      }
    } catch (err: any) {
      setError(err.message || '网络错误')
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  // 加载最近消息（旧连接最后10条）
  const loadRecentMessages = useCallback(async () => {
    if (!sessionId) return

    try {
      const response = await messageService.getRecentByConfig(sessionId, 10)
      if (response.code === 200 && response.data) {
        setMessages(response.data)

        let send = 0
        let receive = 0
        response.data.forEach((msg) => {
          if (msg.direction === 'send') send++
          else if (msg.direction === 'receive') receive++
        })
        setSendCount(send)
        setReceiveCount(receive)
      }
    } catch (err) {
      console.error('加载最近消息失败:', err)
    }
  }, [sessionId])

  // 添加本地消息
  const addLocalMessage = useCallback(
    (direction: 'send' | 'receive' | 'system', content: string, isAutoSend = false) => {
      if (!sessionId || !session) return

      const now = new Date()
      const timestamp = now.toISOString()

      const newMessage: SessionMessage = {
        id: Date.now(),
        connection_id: 0,
        session_id: `${sessionId}_${now.getTime()}`,
        config_id: sessionId,
        direction,
        content,
        content_hex: direction !== 'system' ? stringToHex(content) : null,
        content_length: content.length,
        message_type: 'data',
        protocol_type: session.protocol_type,
        source_address: null,
        source_port: null,
        target_address: null,
        target_port: null,
        status: 'processed',
        error_message: null,
        parsed_data: null,
        extra_data: isAutoSend ? JSON.stringify({ is_auto_send: true }) : null,
        timestamp,
        created_at: timestamp,
      }

      setMessages((prev) => [...prev, newMessage])

      if (direction === 'send') {
        setSendCount((prev) => prev + 1)
      } else if (direction === 'receive') {
        setReceiveCount((prev) => prev + 1)
      }

      // 滚动到底部
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      }, 10)
    },
    [sessionId, session]
  )

  // 连接/断开
  const handleConnect = useCallback(async () => {
    if (!sessionId) return

    setOperating(true)
    try {
      if (isConnected) {
        const response = await sessionService.disconnect(sessionId)
        if (response.code === 200) {
          setIsConnected(false)
          setConnectTime(null)
          addLocalMessage('system', '连接已断开')
          if (session) {
            setSession({ ...session, status: 'disconnected' })
          }
        } else {
          alert(response.message || '断开失败')
        }
      } else {
        setIsConnecting(true)
        const response = await sessionService.connect(sessionId)
        setIsConnecting(false)

        if (response.code === 200) {
          setIsConnected(true)
          setConnectTime(new Date().toLocaleTimeString('zh-CN', { hour12: false }))
          addLocalMessage('system', `已连接到 ${session?.host}:${session?.port}`)
          if (session) {
            setSession({ ...session, status: 'connected' })
          }
        } else {
          addLocalMessage('system', `连接失败: ${response.message || '未知错误'}`)
        }
      }
    } catch (err: any) {
      setIsConnecting(false)
      addLocalMessage('system', `操作失败: ${err.message || '网络错误'}`)
    } finally {
      setOperating(false)
    }
  }, [sessionId, isConnected, session, addLocalMessage])

  // 发送数据
  const handleSend = useCallback(
    async (data: string): Promise<boolean> => {
      if (!isConnected || !data.trim() || !sessionId) return false

      try {
        const response = await sessionService.send(sessionId, data)
        if (response.code === 200) {
          // 消息已由后端处理并推送，这里不再手动添加
          return true
        } else {
          alert(response.message || '发送失败')
          return false
        }
      } catch (err: any) {
        alert(err.message || '发送失败')
        return false
      }
    },
    [isConnected, sessionId]
  )

  // 清空消息
  const clearMessages = useCallback(async () => {
    if (!sessionId) return

    try {
      await messageService.clearBySession(sessionId)
      setMessages([])
      setSendCount(0)
      setReceiveCount(0)
    } catch (err) {
      console.error('清空消息失败:', err)
    }
  }, [sessionId])

  // 初始化
  useEffect(() => {
    loadSession()
    loadRecentMessages()
  }, [loadSession, loadRecentMessages])

  // WebSocket 连接和订阅
  useEffect(() => {
    if (!sessionId) return

    // 连接 WebSocket 并等待完成后订阅
    const initWebSocket = async () => {
      const connected = await wsClient.connect()
      if (connected) {
        console.log('[SessionDetail] WebSocket 连接成功，订阅会话:', sessionId)
        wsClient.subscribeSession(sessionId)
      } else {
        console.log('[SessionDetail] WebSocket 连接失败')
      }
    }

    initWebSocket()

    // 监听通信消息
    const unsubComm = wsClient.onCommunication(sessionId, (data: CommunicationData) => {
      console.log('[SessionDetail] 收到通信消息:', data.direction, data.content.substring(0, 50), 'is_auto_send:', data.is_auto_send)
      
      // 构建 extra_data
      const extraData = data.is_auto_send ? JSON.stringify({ is_auto_send: true }) : null
      
      const newMessage: SessionMessage = {
        id: Date.now(),
        connection_id: 0,
        session_id: String(data.session_id),
        config_id: sessionId,
        direction: data.direction,
        content: data.content,
        content_hex: data.content_hex || null,
        content_length: data.content.length,
        message_type: 'data',
        protocol_type: session?.protocol_type || 'TCP',
        source_address: null,
        source_port: null,
        target_address: null,
        target_port: null,
        status: 'processed',
        error_message: null,
        parsed_data: null,
        extra_data: extraData,
        timestamp: data.timestamp,
        created_at: data.timestamp,
      }

      setMessages((prev) => [...prev, newMessage])

      if (data.direction === 'send') {
        setSendCount((prev) => prev + 1)
      } else if (data.direction === 'receive') {
        setReceiveCount((prev) => prev + 1)
      }

      // 滚动到底部
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      }, 10)
    })

    // 监听会话状态
    const unsubStatus = wsClient.onSessionStatus(sessionId, (data: SessionStatusData) => {
      if (data.status === 'connected') {
        setIsConnected(true)
        setConnectTime(new Date().toLocaleTimeString('zh-CN', { hour12: false }))
      } else if (data.status === 'disconnected' || data.status === 'error') {
        setIsConnected(false)
        setConnectTime(null)
      } else if (data.status === 'reconnecting') {
        // 重连中，保持当前状态，但显示提示
        setIsConnected(false)
      }
      if (session) {
        setSession({ ...session, status: data.status, last_error: data.error_message || null })
      }
    })

    return () => {
      unsubComm()
      unsubStatus()
      wsClient.unsubscribeSession(sessionId)
    }
  }, [sessionId]) // 移除 session 依赖，避免重复执行

  return {
    session,
    loading,
    error,
    isConnected,
    isConnecting,
    operating,
    connectTime,
    messages,
    sendCount,
    receiveCount,
    loadSession,
    handleConnect,
    handleSend,
    clearMessages,
    addLocalMessage,
  }
}