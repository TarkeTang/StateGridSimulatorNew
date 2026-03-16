import { useState, useRef, useCallback, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Panel, Button } from '@/components/ui'
import {
  Play,
  Square,
  Send,
  Trash2,
  Download,
  Clock,
  ArrowUpRight,
  ArrowDownLeft,
  Activity,
  ArrowLeft,
  Wifi,
  WifiOff,
  RefreshCw,
  Timer,
  X,
  Plus,
  GripVertical,
} from 'lucide-react'
import { sessionService, type SessionConfig } from '@/services/session'
import { getDictName, type DictData } from '@/services/dict'

interface MessageItem {
  id: number
  type: 'send' | 'receive' | 'system'
  content: string
  timestamp: string
  hex?: string
}

// 自动发送消息配置
interface AutoSendItem {
  id: number
  content: string
  interval: number | '' // 毫秒，允许空值便于输入
  enabled: boolean
}

// 格式化 XML
const formatXml = (xml: string): string => {
  try {
    let formatted = ''
    let indent = ''
    const nodes = xml.replace(/>\s*</g, '><').split(/(<[^>]+>)/g)

    for (const node of nodes) {
      if (!node.trim()) continue

      if (node.startsWith('</')) {
        indent = indent.slice(2)
        formatted += indent + node + '\n'
      } else if (node.startsWith('<') && !node.startsWith('<?') && !node.endsWith('/>')) {
        formatted += indent + node + '\n'
        if (!node.includes('</')) {
          indent += '  '
        }
      } else if (node.startsWith('<?') || node.endsWith('/>')) {
        formatted += indent + node + '\n'
      } else {
        formatted += indent + node.trim() + '\n'
      }
    }

    return formatted.trim()
  } catch {
    return xml
  }
}

// 格式化 JSON
const formatJson = (json: string): string => {
  try {
    const obj = JSON.parse(json)
    return JSON.stringify(obj, null, 2)
  } catch {
    return json
  }
}

const SessionDetailPage = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  // 面板尺寸状态
  const [leftPanelWidth, setLeftPanelWidth] = useState(320)
  const [bottomPanelHeight, setBottomPanelHeight] = useState(200)

  // 拖动状态
  const [isDraggingH, setIsDraggingH] = useState(false)
  const [isDraggingV, setIsDraggingV] = useState(false)

  // 会话配置
  const [session, setSession] = useState<SessionConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 字典数据
  const [protocolTypes, setProtocolTypes] = useState<DictData[]>([])

  // 连接状态
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [operating, setOperating] = useState(false)

  // 发送配置
  const [sendData, setSendData] = useState('')
  const [sendMode, setSendMode] = useState<'text' | 'xml' | 'json'>('text')

  // 自动发送配置
  const [autoSendDialogOpen, setAutoSendDialogOpen] = useState(false)
  const [autoSendItems, setAutoSendItems] = useState<AutoSendItem[]>([
    { id: 1, content: '', interval: 1000, enabled: true },
  ])
  const [autoSendActive, setAutoSendActive] = useState(false)
  const [currentSendIndex, setCurrentSendIndex] = useState(0)

  // 消息记录
  const [messages, setMessages] = useState<MessageItem[]>([])
  const [showTimestamp, setShowTimestamp] = useState(true)
  const [showHex, setShowHex] = useState(false)

  // 统计信息
  const [sendCount, setSendCount] = useState(0)
  const [receiveCount, setReceiveCount] = useState(0)
  const [connectTime, setConnectTime] = useState<string | null>(null)

  const messageIdRef = useRef(0)
  const autoSendTimerRef = useRef<NodeJS.Timeout | NodeJS.Timeout[] | null>(null)
  const autoSendRunningRef = useRef(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const autoSendItemIdRef = useRef(2)

  // 加载字典数据
  const loadDictData = useCallback(async () => {
    try {
      const { dictService } = await import('@/services/dict')
      const response = await dictService.getProtocolTypes()
      if (response.code === 200 && response.data) {
        setProtocolTypes(response.data)
      }
    } catch (err) {
      console.error('加载字典数据失败:', err)
    }
  }, [])

  // 加载会话配置
  const loadSession = useCallback(async () => {
    if (!id) return

    setLoading(true)
    setError(null)
    try {
      const response = await sessionService.getById(Number(id))
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
  }, [id])

  useEffect(() => {
    loadDictData()
    loadSession()
  }, [loadDictData, loadSession])

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

  // 获取当前时间戳
  const getTimestamp = () => {
    const now = new Date()
    return (
      now.toLocaleTimeString('zh-CN', { hour12: false }) +
      '.' +
      now.getMilliseconds().toString().padStart(3, '0')
    )
  }

  // 字符串转十六进制
  const stringToHex = (str: string) => {
    return str
      .split('')
      .map((char) => char.charCodeAt(0).toString(16).toUpperCase().padStart(2, '0'))
      .join(' ')
  }

  // 添加消息
  const addMessage = useCallback((type: 'send' | 'receive' | 'system', content: string) => {
    const newMessage: MessageItem = {
      id: ++messageIdRef.current,
      type,
      content,
      timestamp: getTimestamp(),
      hex: type !== 'system' ? stringToHex(content) : undefined,
    }
    setMessages((prev) => [...prev, newMessage])

    if (type === 'send') {
      setSendCount((prev) => prev + 1)
    } else if (type === 'receive') {
      setReceiveCount((prev) => prev + 1)
    }

    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, 10)
  }, [])

  // 连接
  const handleConnect = async () => {
    if (!id) return

    setOperating(true)
    try {
      if (isConnected) {
        const response = await sessionService.disconnect(Number(id))
        if (response.code === 200) {
          setIsConnected(false)
          setConnectTime(null)
          stopAutoSend()
          addMessage('system', '连接已断开')
        } else {
          alert(response.message || '断开失败')
        }
      } else {
        setIsConnecting(true)
        const response = await sessionService.connect(Number(id))
        setIsConnecting(false)

        if (response.code === 200) {
          setIsConnected(true)
          setConnectTime(new Date().toLocaleTimeString('zh-CN', { hour12: false }))
          addMessage('system', `已连接到 ${session?.host}:${session?.port}`)
        } else {
          addMessage('system', `连接失败: ${response.message || '未知错误'}`)
        }
      }
      loadSession()
    } catch (err: any) {
      setIsConnecting(false)
      addMessage('system', `操作失败: ${err.message || '网络错误'}`)
    } finally {
      setOperating(false)
    }
  }

  // 发送数据
  const handleSend = async () => {
    if (!isConnected || !sendData.trim() || !id) return

    try {
      const response = await sessionService.send(Number(id), sendData)
      if (response.code === 200) {
        addMessage('send', sendData)
        setSendData('')
      } else {
        alert(response.message || '发送失败')
      }
    } catch (err: any) {
      alert(err.message || '发送失败')
    }
  }

  // 发送单条消息
  const sendSingleMessage = async (content: string) => {
    if (!content.trim() || !id) return false

    try {
      const response = await sessionService.send(Number(id), content)
      if (response.code === 200) {
        addMessage('send', content)
        return true
      }
      return false
    } catch {
      return false
    }
  }

  // 开始自动发送
  const startAutoSend = () => {
    const enabledItems = autoSendItems.filter(
      (item) => item.enabled && item.content.trim() && item.interval !== '' && item.interval >= 100
    )
    if (enabledItems.length === 0) {
      alert('请至少添加一条有效的发送消息（间隔时间需 >= 100ms）')
      return
    }

    setAutoSendActive(true)
    autoSendRunningRef.current = true
    addMessage('system', `自动发送已启动，共 ${enabledItems.length} 条消息`)

    // 每条消息独立按自己的间隔发送
    enabledItems.forEach((item, index) => {
      const interval = typeof item.interval === 'number' ? item.interval : 100

      const sendMessage = () => {
        if (!autoSendRunningRef.current) return

        setCurrentSendIndex(index)
        sendSingleMessage(item.content)
      }

      // 立即发送第一条
      sendMessage()

      // 设置定时器循环发送
      const timerId = setInterval(() => {
        if (autoSendRunningRef.current) {
          sendMessage()
        }
      }, interval)

      // 保存定时器引用以便停止
      if (!autoSendTimerRef.current) {
        autoSendTimerRef.current = [] as any
      }
      ;(autoSendTimerRef.current as any[]).push(timerId)
    })
  }

  // 停止自动发送
  const stopAutoSend = () => {
    autoSendRunningRef.current = false
    if (autoSendTimerRef.current) {
      if (Array.isArray(autoSendTimerRef.current)) {
        autoSendTimerRef.current.forEach((timer) => clearInterval(timer))
      }
      autoSendTimerRef.current = null
    }
    setAutoSendActive(false)
    setCurrentSendIndex(0)
    addMessage('system', '自动发送已停止')
  }

  // 清空消息
  const clearMessages = () => {
    setMessages([])
    setSendCount(0)
    setReceiveCount(0)
  }

  // 导出日志
  const exportLog = () => {
    const log = messages
      .map((msg) => {
        const typeLabel =
          msg.type === 'send' ? '发送' : msg.type === 'receive' ? '接收' : '系统'
        return `[${msg.timestamp}] [${typeLabel}] ${msg.content}`
      })
      .join('\n')
    const blob = new Blob([log], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `session_${id}_${new Date().toISOString().slice(0, 10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  // 计算连接时长
  const getConnectionDuration = () => {
    if (!connectTime) return '--'
    const start = new Date()
    const [h, m, s] = connectTime.split(':')
    start.setHours(parseInt(h), parseInt(m), parseInt(s))
    const now = new Date()
    const diff = Math.floor((now.getTime() - start.getTime()) / 1000)
    const hours = Math.floor(diff / 3600)
    const minutes = Math.floor((diff % 3600) / 60)
    const seconds = diff % 60
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
  }

  // 获取状态样式
  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'connected':
        return { color: 'text-signal-green', label: '已连接' }
      case 'connecting':
        return { color: 'text-signal-yellow', label: '连接中' }
      case 'error':
        return { color: 'text-signal-red', label: '连接错误' }
      default:
        return { color: 'text-gray-400', label: '未连接' }
    }
  }

  // 格式化显示内容
  const getDisplayContent = (content: string): string => {
    if (sendMode === 'xml') {
      return formatXml(content)
    } else if (sendMode === 'json') {
      return formatJson(content)
    }
    return content
  }

  // 添加自动发送项
  const addAutoSendItem = () => {
    setAutoSendItems((prev) => [
      ...prev,
      { id: autoSendItemIdRef.current++, content: '', interval: 1000, enabled: true },
    ])
  }

  // 删除自动发送项
  const removeAutoSendItem = (itemId: number) => {
    if (autoSendItems.length <= 1) return
    setAutoSendItems((prev) => prev.filter((item) => item.id !== itemId))
  }

  // 更新自动发送项
  const updateAutoSendItem = (itemId: number, field: keyof AutoSendItem, value: any) => {
    setAutoSendItems((prev) =>
      prev.map((item) => (item.id === itemId ? { ...item, [field]: value } : item))
    )
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <RefreshCw className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    )
  }

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

  const statusStyle = getStatusStyle(session.status)

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
        <Panel title="会话信息" className="flex-1 min-h-0 overflow-auto">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">会话名称</span>
              <span className="text-white text-sm font-medium">{session.name}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">协议类型</span>
              <span className="text-gray-300 text-sm">
                {getDictName(protocolTypes, session.protocol_type)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">连接模式</span>
              <span
                className={`text-sm px-2 py-0.5 rounded ${
                  session.connection_mode === 'server'
                    ? 'bg-purple-500/20 text-purple-400'
                    : 'bg-signal-blue/20 text-signal-blue'
                }`}
              >
                {session.connection_mode === 'server' ? '服务端' : '客户端'}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">服务器地址</span>
              <span className="text-signal-blue font-mono text-sm">
                {session.host}:{session.port}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">超时时间</span>
              <span className="text-gray-300 text-sm">{session.timeout}ms</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">自动重连</span>
              <span className="text-gray-300 text-sm">
                {session.auto_reconnect ? `是 (${session.reconnect_interval}ms)` : '否'}
              </span>
            </div>
            {session.description && (
              <div className="pt-2 border-t border-panel-border">
                <span className="text-gray-400 text-sm">描述</span>
                <p className="text-gray-300 text-sm mt-1">{session.description}</p>
              </div>
            )}
          </div>
        </Panel>

        {/* 连接状态 */}
        <Panel title="连接状态" className="flex-shrink-0">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">状态</span>
              <div className="flex items-center gap-2">
                <span className={`status-indicator ${isConnected ? 'online' : 'offline'}`} />
                <span className={`${statusStyle.color} text-sm`}>{statusStyle.label}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">连接时长</span>
              <span className="text-white font-mono text-sm">{getConnectionDuration()}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">发送计数</span>
              <span className="text-signal-blue font-mono text-sm">{sendCount}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">接收计数</span>
              <span className="text-signal-green font-mono text-sm">{receiveCount}</span>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-panel-border">
            <Button
              variant={isConnected ? 'danger' : 'success'}
              onClick={handleConnect}
              disabled={isConnecting || operating}
              className="w-full"
            >
              {isConnecting ? (
                <>
                  <Clock className="w-4 h-4 animate-spin" />
                  连接中...
                </>
              ) : isConnected ? (
                <>
                  <Square className="w-4 h-4" />
                  断开连接
                </>
              ) : (
                <>
                  <Play className="w-4 h-4" />
                  建立连接
                </>
              )}
            </Button>
          </div>
        </Panel>

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
          <Panel
            title="通信记录"
            className="h-full is-flex"
            headerAction={
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showTimestamp}
                    onChange={(e) => setShowTimestamp(e.target.checked)}
                    className="accent-signal-blue"
                  />
                  <span className="text-xs text-gray-400">时间戳</span>
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showHex}
                    onChange={(e) => setShowHex(e.target.checked)}
                    className="accent-signal-blue"
                  />
                  <span className="text-xs text-gray-400">HEX</span>
                </label>
                <Button variant="secondary" size="sm" onClick={clearMessages}>
                  <Trash2 className="w-3 h-3" />
                  清空
                </Button>
                <Button variant="secondary" size="sm" onClick={exportLog}>
                  <Download className="w-3 h-3" />
                  导出
                </Button>
              </div>
            }
          >
            <div className="h-full overflow-y-auto bg-black/40 rounded p-3 font-mono text-sm">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-gray-500">
                  <Activity className="w-12 h-12 mb-3 opacity-30" />
                  <p>暂无通信记录</p>
                  <p className="text-xs mt-1">建立连接后开始通信</p>
                </div>
              ) : (
                <div className="space-y-1">
                  {messages.map((msg) => (
                    <div
                      key={msg.id}
                      className={`py-1.5 px-2 rounded ${
                        msg.type === 'send'
                          ? 'bg-signal-blue/10 border-l-2 border-signal-blue'
                          : msg.type === 'receive'
                          ? 'bg-signal-green/10 border-l-2 border-signal-green'
                          : 'bg-yellow-500/10 border-l-2 border-yellow-500'
                      }`}
                    >
                      <div className="flex items-start gap-2">
                        {msg.type === 'send' ? (
                          <ArrowUpRight className="w-4 h-4 mt-0.5 flex-shrink-0 text-signal-blue" />
                        ) : msg.type === 'receive' ? (
                          <ArrowDownLeft className="w-4 h-4 mt-0.5 flex-shrink-0 text-signal-green" />
                        ) : (
                          <Wifi className="w-4 h-4 mt-0.5 flex-shrink-0 text-yellow-500" />
                        )}

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            {showTimestamp && (
                              <span className="text-gray-500 text-xs">{msg.timestamp}</span>
                            )}
                            <span
                              className={`text-xs ${
                                msg.type === 'send'
                                  ? 'text-signal-blue'
                                  : msg.type === 'receive'
                                  ? 'text-signal-green'
                                  : 'text-yellow-500'
                              }`}
                            >
                              [
                              {msg.type === 'send'
                                ? '发送'
                                : msg.type === 'receive'
                                ? '接收'
                                : '系统'}
                              ]
                            </span>
                          </div>

                          <div className="text-gray-200 break-all whitespace-pre-wrap">
                            {msg.content}
                          </div>

                          {showHex && msg.hex && (
                            <div className="text-gray-500 text-xs mt-1 font-mono">
                              HEX: {msg.hex}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
          </Panel>
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
          <Panel title="发送配置" className="h-full is-flex">
            <div className="flex gap-4 h-full">
              {/* 发送模式 */}
              <div className="flex flex-col gap-2 flex-shrink-0">
                <span className="text-xs text-gray-400">格式</span>
                <div className="flex flex-col gap-1">
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="sendMode"
                      checked={sendMode === 'text'}
                      onChange={() => setSendMode('text')}
                      className="accent-signal-blue"
                    />
                    <span className="text-sm text-gray-300">文本</span>
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="sendMode"
                      checked={sendMode === 'xml'}
                      onChange={() => setSendMode('xml')}
                      className="accent-signal-blue"
                    />
                    <span className="text-sm text-gray-300">XML</span>
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="sendMode"
                      checked={sendMode === 'json'}
                      onChange={() => setSendMode('json')}
                      className="accent-signal-blue"
                    />
                    <span className="text-sm text-gray-300">JSON</span>
                  </label>
                </div>
              </div>

              {/* 发送内容 */}
              <div className="flex-1 min-w-0 h-full">
                <textarea
                  value={getDisplayContent(sendData)}
                  onChange={(e) => setSendData(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.ctrlKey) {
                      handleSend()
                    }
                  }}
                  placeholder="输入发送数据... (Ctrl+Enter发送)"
                  className="input-field h-full resize-none font-mono text-sm w-full"
                  disabled={!isConnected}
                />
              </div>

              {/* 发送按钮 */}
              <div className="flex flex-col gap-2 flex-shrink-0">
                <Button
                  variant="primary"
                  onClick={handleSend}
                  disabled={!isConnected || !sendData.trim()}
                >
                  <Send className="w-4 h-4" />
                  发送
                </Button>
                <Button
                  variant={autoSendActive ? 'danger' : 'secondary'}
                  onClick={() => {
                    if (autoSendActive) {
                      stopAutoSend()
                    } else {
                      setAutoSendDialogOpen(true)
                    }
                  }}
                  disabled={!isConnected}
                >
                  <Timer className="w-4 h-4" />
                  {autoSendActive ? '停止' : '自动发送'}
                </Button>
              </div>
            </div>
          </Panel>
        </div>
      </div>

      {/* 自动发送设置弹窗 */}
      {autoSendDialogOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-panel-card border border-panel-border rounded-lg w-[600px] max-h-[80vh] flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-panel-border flex-shrink-0">
              <h3 className="text-base font-medium">自动发送配置</h3>
              <button
                onClick={() => setAutoSendDialogOpen(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              <p className="text-sm text-gray-400">
                配置多条消息，按顺序循环发送。每条消息可设置独立的发送间隔。
              </p>

              {autoSendItems.map((item, index) => (
                <div
                  key={item.id}
                  className={`p-3 rounded border ${
                    autoSendActive && currentSendIndex === index
                      ? 'border-signal-blue bg-signal-blue/10'
                      : 'border-panel-border bg-industrial-800/50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {/* 序号 */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <GripVertical className="w-4 h-4 text-gray-500" />
                      <span className="text-sm text-gray-400 w-6">{index + 1}.</span>
                    </div>

                    <div className="flex-1 space-y-2">
                      {/* 消息内容 */}
                      <textarea
                        value={item.content}
                        onChange={(e) => updateAutoSendItem(item.id, 'content', e.target.value)}
                        placeholder="输入消息内容..."
                        className="input-field h-16 resize-none font-mono text-sm w-full"
                        disabled={autoSendActive}
                      />

                      {/* 间隔和启用 */}
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400">发送后等待</span>
                          <input
                            type="number"
                            value={item.interval}
                            onChange={(e) => {
                              const val = e.target.value
                              if (val === '') {
                                updateAutoSendItem(item.id, 'interval', '' as any)
                              } else {
                                const num = Number(val)
                                if (num <= 86400000) {
                                  updateAutoSendItem(item.id, 'interval', num)
                                }
                              }
                            }}
                            onBlur={(e) => {
                              const val = Number(e.target.value)
                              if (val < 100) {
                                updateAutoSendItem(item.id, 'interval', 100)
                              }
                            }}
                            className="input-field w-20 text-sm py-1"
                            min={0}
                            max={86400000}
                            step={100}
                            disabled={autoSendActive}
                          />
                          <span className="text-xs text-gray-400">ms</span>
                        </div>

                        <label className="flex items-center gap-1.5 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={item.enabled}
                            onChange={(e) => updateAutoSendItem(item.id, 'enabled', e.target.checked)}
                            className="accent-signal-blue"
                            disabled={autoSendActive}
                          />
                          <span className="text-xs text-gray-300">启用</span>
                        </label>

                        <button
                          onClick={() => removeAutoSendItem(item.id)}
                          disabled={autoSendActive || autoSendItems.length <= 1}
                          className="p-1 rounded text-gray-400 hover:text-signal-red hover:bg-signal-red/20 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}

              {/* 添加按钮 */}
              <button
                onClick={addAutoSendItem}
                disabled={autoSendActive}
                className="w-full py-2 border border-dashed border-panel-border rounded text-gray-400 hover:text-signal-blue hover:border-signal-blue transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Plus className="w-4 h-4" />
                添加消息
              </button>
            </div>

            <div className="flex items-center justify-end gap-3 px-4 py-3 border-t border-panel-border flex-shrink-0">
              <Button variant="secondary" onClick={() => setAutoSendDialogOpen(false)}>
                取消
              </Button>
              <Button
                variant="success"
                onClick={() => {
                  setAutoSendDialogOpen(false)
                  startAutoSend()
                }}
                disabled={autoSendItems.filter((i) => i.enabled && i.content.trim()).length === 0}
              >
                开始发送
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SessionDetailPage