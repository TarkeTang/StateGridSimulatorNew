/**
 * 会话详情页面
 *
 * 展示会话信息、连接状态、通信记录和发送配置
 * 支持实时 WebSocket 通信
 */

import { useState, useCallback, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui'
import { ArrowLeft, RefreshCw, WifiOff } from 'lucide-react'

// 组件
import {
  SessionInfoPanel,
  ConnectionStatusPanel,
  MessageLog,
  SendPanel,
  AutoSendDialog,
} from '@/components/session'

// Hooks
import { useSessionDetail } from '@/hooks/useSessionDetail'
import { useAutoSend } from '@/hooks/useAutoSend'

// 服务
import { dictService, type DictData } from '@/services/dict'

function SessionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const sessionId = id ? Number(id) : null

  // 面板尺寸状态
  const [leftPanelWidth, setLeftPanelWidth] = useState(320)
  const [bottomPanelHeight, setBottomPanelHeight] = useState(200)

  // 拖动状态
  const [isDraggingH, setIsDraggingH] = useState(false)
  const [isDraggingV, setIsDraggingV] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)

  // 字典数据
  const [protocolTypes, setProtocolTypes] = useState<DictData[]>([])

  // 发送配置
  const [sendData, setSendData] = useState('')
  const [sendMode, setSendMode] = useState<'text' | 'xml' | 'json'>('text')

  // 消息显示选项
  const [showTimestamp, setShowTimestamp] = useState(true)
  const [showHex, setShowHex] = useState(false)

  // 自动发送弹窗
  const [autoSendDialogOpen, setAutoSendDialogOpen] = useState(false)
  const [currentSendIndex, setCurrentSendIndex] = useState(0)

  // 会话详情 Hook
  const {
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
    handleConnect,
    handleSend,
    clearMessages,
    addLocalMessage,
  } = useSessionDetail({ sessionId })

  // 自动发送 Hook
  const {
    configs: autoSendConfigs,
    isActive: autoSendActive,
    addConfig: addAutoSendConfig,
    updateConfig: updateAutoSendConfig,
    removeConfig: removeAutoSendConfig,
    startAutoSend,
    stopAutoSend,
  } = useAutoSend({
    sessionId,
    isConnected,
    onSendMessage: (msg) => addLocalMessage('system', msg),
  })

  // 加载字典数据
  useEffect(() => {
    const loadDictData = async () => {
      try {
        const response = await dictService.getProtocolTypes()
        if (response.code === 200 && response.data) {
          setProtocolTypes(response.data)
        }
      } catch (err) {
        console.error('加载字典数据失败:', err)
      }
    }
    loadDictData()
  }, [])

  // 水平拖动处理
  useEffect(() => {
    if (!isDraggingH) return

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.min(500, Math.max(250, e.clientX))
      setLeftPanelWidth(newWidth)
    }

    const handleMouseUp = () => {
      setIsDraggingH(false)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.body.style.cursor = 'ew-resize'
    document.body.style.userSelect = 'none'
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDraggingH])

  // 垂直拖动处理
  useEffect(() => {
    if (!isDraggingV || !containerRef.current) return

    const handleMouseMove = (e: MouseEvent) => {
      const container = containerRef.current
      if (!container) return

      const containerRect = container.getBoundingClientRect()
      const mouseFromBottom = containerRect.bottom - e.clientY
      const newHeight = Math.min(400, Math.max(120, mouseFromBottom))
      setBottomPanelHeight(newHeight)
    }

    const handleMouseUp = () => {
      setIsDraggingV(false)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.body.style.cursor = 'ns-resize'
    document.body.style.userSelect = 'none'
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDraggingV])

  // 发送数据
  const onSend = useCallback(async () => {
    const success = await handleSend(sendData)
    if (success) {
      setSendData('')
    }
  }, [handleSend, sendData])

  // 导出日志
  const exportLog = useCallback(() => {
    const log = messages
      .map((msg) => {
        const typeLabel =
          msg.direction === 'send' ? '发送' : msg.direction === 'receive' ? '接收' : '系统'
        const extraData = msg.extra_data ? JSON.parse(msg.extra_data) : {}
        const isAutoSend = extraData.is_auto_send ? '自动发送' : typeLabel
        return `[${msg.timestamp}] [${msg.direction === 'send' ? isAutoSend : typeLabel}] ${msg.content}`
      })
      .join('\n')
    const blob = new Blob([log], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `session_${id}_${new Date().toISOString().slice(0, 10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }, [messages, id])

  // 启动自动发送
  const onStartAutoSend = useCallback(async () => {
    const success = await startAutoSend()
    if (success) {
      setCurrentSendIndex(0)
    }
  }, [startAutoSend])

  // 加载中
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    )
  }

  // 错误或会话不存在
  if (error || !session) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-400">
        <WifiOff className="w-12 h-12 mb-4 opacity-30" />
        <p>{error || '会话不存在'}</p>
        <Button variant="secondary" className="mt-4" onClick={() => navigate('/data/session')}>
          <ArrowLeft className="w-4 h-4" />
          返回列表
        </Button>
      </div>
    )
  }

  return (
    <div
      className="h-full flex animate-fadeIn"
      ref={containerRef}
      style={{ overflow: isDraggingH || isDraggingV ? 'hidden' : 'visible' }}
    >
      {/* 左侧：会话信息和连接状态 */}
      <div
        className="flex-shrink-0 flex flex-col gap-4 relative"
        style={{ width: leftPanelWidth }}
      >
        {/* 返回按钮 */}
        <Button variant="secondary" onClick={() => navigate('/data/session')}>
          <ArrowLeft className="w-4 h-4" />
          返回列表
        </Button>

        {/* 会话信息 */}
        <SessionInfoPanel session={session} protocolTypes={protocolTypes} />

        {/* 连接状态 */}
        <ConnectionStatusPanel
          session={session}
          isConnected={isConnected}
          isConnecting={isConnecting}
          operating={operating}
          connectTime={connectTime}
          sendCount={sendCount}
          receiveCount={receiveCount}
          onConnect={handleConnect}
        />

        {/* 水平拖动手柄 */}
        <div
          className={`absolute top-0 right-0 w-1 h-full cursor-ew-resize z-10 group ${
            isDraggingH ? 'bg-signal-blue' : 'hover:bg-signal-blue/50'
          }`}
          onMouseDown={(e) => {
            e.preventDefault()
            setIsDraggingH(true)
          }}
        >
          <div className="absolute top-1/2 right-0 w-1 h-12 -translate-y-1/2 bg-gray-500 rounded opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      </div>

      {/* 右侧：通信记录和发送配置 */}
      <div className="flex-1 flex flex-col min-w-0 ml-1">
        {/* 上部：通信记录 */}
        <div className="flex-1 min-h-0">
          <MessageLog
            messages={messages}
            loading={false}
            showTimestamp={showTimestamp}
            showHex={showHex}
            onClear={clearMessages}
            onExport={exportLog}
            onToggleTimestamp={() => setShowTimestamp((v) => !v)}
            onToggleHex={() => setShowHex((v) => !v)}
          />
        </div>

        {/* 垂直拖动手柄 */}
        <div
          className={`h-1 cursor-ns-resize z-10 group flex-shrink-0 my-1 ${
            isDraggingV ? 'bg-signal-blue' : 'hover:bg-signal-blue/50'
          }`}
          onMouseDown={(e) => {
            e.preventDefault()
            setIsDraggingV(true)
          }}
        >
          <div className="mx-auto w-12 h-1 bg-gray-500 rounded opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>

        {/* 下部：发送配置 */}
        <div
          className="flex-shrink-0"
          style={{ height: bottomPanelHeight, minHeight: 120, maxHeight: 400 }}
        >
          <SendPanel
            sendData={sendData}
            sendMode={sendMode}
            isConnected={isConnected}
            autoSendActive={autoSendActive}
            session={session}
            onSendDataChange={setSendData}
            onSendModeChange={setSendMode}
            onSend={onSend}
            onOpenAutoSend={() => setAutoSendDialogOpen(true)}
            onStopAutoSend={stopAutoSend}
          />
        </div>
      </div>

      {/* 自动发送设置弹窗 */}
      <AutoSendDialog
        open={autoSendDialogOpen}
        configs={autoSendConfigs}
        isActive={autoSendActive}
        currentSendIndex={currentSendIndex}
        onClose={() => setAutoSendDialogOpen(false)}
        onAdd={addAutoSendConfig}
        onUpdate={updateAutoSendConfig}
        onRemove={removeAutoSendConfig}
        onStart={onStartAutoSend}
      />
    </div>
  )
}

export default SessionDetailPage