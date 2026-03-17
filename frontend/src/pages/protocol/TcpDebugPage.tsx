import { useState, useRef, useCallback } from 'react'
import { Panel, Button, Input } from '@/components/ui'
import {
  Play,
  Square,
  Send,
  Trash2,
  Download,
  Wifi,
  Clock,
  ArrowUpRight,
  ArrowDownLeft,
  Activity,
} from 'lucide-react'

interface MessageItem {
  id: number
  type: 'send' | 'receive' | 'system'
  content: string
  timestamp: string
  hex?: string
}

const TcpDebugPage = () => {
  // 连接配置
  const [host, setHost] = useState('127.0.0.1')
  const [port, setPort] = useState('8080')
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)

  // 发送配置
  const [sendData, setSendData] = useState('')
  const [sendMode, setSendMode] = useState<'text' | 'hex'>('text')
  const [autoSend, setAutoSend] = useState(false)
  const [autoSendInterval, setAutoSendInterval] = useState(1000)

  // 消息记录
  const [messages, setMessages] = useState<MessageItem[]>([])
  const [showTimestamp, setShowTimestamp] = useState(true)
  const [showHex, setShowHex] = useState(false)

  // 统计信息
  const [sendCount, setSendCount] = useState(0)
  const [receiveCount, setReceiveCount] = useState(0)
  const [connectTime, setConnectTime] = useState<string | null>(null)

  const messageIdRef = useRef(0)
  const autoSendTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 获取当前时间戳
  const getTimestamp = () => {
    const now = new Date()
    return now.toLocaleTimeString('zh-CN', { hour12: false }) + '.' + now.getMilliseconds().toString().padStart(3, '0')
  }

  // 字符串转十六进制
  const stringToHex = (str: string) => {
    return str
      .split('')
      .map((char) => char.charCodeAt(0).toString(16).toUpperCase().padStart(2, '0'))
      .join(' ')
  }

  // 十六进制转字符串
  const hexToString = (hex: string) => {
    const hexArray = hex.replace(/\s+/g, '').match(/.{1,2}/g) || []
    return hexArray.map((byte) => String.fromCharCode(parseInt(byte, 16))).join('')
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

    // 滚动到底部
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, 10)
  }, [])

  // 连接
  const handleConnect = async () => {
    if (isConnected) {
      // 断开连接
      setIsConnected(false)
      setConnectTime(null)
      stopAutoSend()
      addMessage('system', '连接已断开')
    } else {
      // 建立连接
      setIsConnecting(true)
      // 模拟连接过程
      await new Promise((resolve) => setTimeout(resolve, 500))
      setIsConnecting(false)
      setIsConnected(true)
      setConnectTime(new Date().toLocaleTimeString('zh-CN', { hour12: false }))
      addMessage('system', `已连接到 ${host}:${port}`)
    }
  }

  // 发送数据
  const handleSend = () => {
    if (!isConnected || !sendData.trim()) return

    const content = sendMode === 'hex' ? hexToString(sendData) : sendData
    addMessage('send', content)
    setSendData('')
  }

  // 开始自动发送
  const startAutoSend = () => {
    if (!sendData.trim()) return
    setAutoSend(true)
    autoSendTimerRef.current = setInterval(() => {
      const content = sendMode === 'hex' ? hexToString(sendData) : sendData
      addMessage('send', content)
    }, autoSendInterval)
  }

  // 停止自动发送
  const stopAutoSend = () => {
    setAutoSend(false)
    if (autoSendTimerRef.current) {
      clearInterval(autoSendTimerRef.current)
      autoSendTimerRef.current = null
    }
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
        const typeLabel = msg.type === 'send' ? '发送' : msg.type === 'receive' ? '接收' : '系统'
        return `[${msg.timestamp}] [${typeLabel}] ${msg.content}`
      })
      .join('\n')
    const blob = new Blob([log], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tcp_debug_${new Date().toISOString().slice(0, 10)}.txt`
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

  return (
    <div className="h-full flex gap-4 animate-fadeIn">
      {/* 左侧：配置和状态 */}
      <div className="w-80 flex-shrink-0 flex flex-col gap-4">
        {/* 连接配置 */}
        <Panel title="连接配置">
          <div className="space-y-4">
            <Input
              label="服务器地址"
              value={host}
              onChange={(e) => setHost(e.target.value)}
              placeholder="127.0.0.1"
              disabled={isConnected}
            />
            <Input
              label="端口"
              value={port}
              onChange={(e) => setPort(e.target.value)}
              placeholder="8080"
              disabled={isConnected}
            />
            <Button
              variant={isConnected ? 'danger' : 'success'}
              onClick={handleConnect}
              disabled={isConnecting}
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

        {/* 连接状态 */}
        <Panel title="连接状态">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-400 text-sm">状态</span>
              <div className="flex items-center gap-2">
                {isConnected ? (
                  <>
                    <span className="status-indicator online" />
                    <span className="text-signal-green text-sm">已连接</span>
                  </>
                ) : (
                  <>
                    <span className="status-indicator offline" />
                    <span className="text-gray-500 text-sm">未连接</span>
                  </>
                )}
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
        </Panel>

        {/* 发送配置 */}
        <Panel title="发送配置">
          <div className="space-y-4">
            {/* 发送模式 */}
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="sendMode"
                  checked={sendMode === 'text'}
                  onChange={() => setSendMode('text')}
                  className="accent-signal-blue"
                />
                <span className="text-sm text-gray-300">文本</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="sendMode"
                  checked={sendMode === 'hex'}
                  onChange={() => setSendMode('hex')}
                  className="accent-signal-blue"
                />
                <span className="text-sm text-gray-300">HEX</span>
              </label>
            </div>

            {/* 发送内容 */}
            <textarea
              value={sendData}
              onChange={(e) => setSendData(e.target.value)}
              placeholder={sendMode === 'hex' ? '输入十六进制，如: 01 02 03' : '输入发送数据...'}
              className="input-field h-20 resize-none font-mono text-sm"
              disabled={!isConnected}
            />

            {/* 发送按钮 */}
            <Button
              variant="primary"
              onClick={handleSend}
              disabled={!isConnected || !sendData.trim()}
              className="w-full"
            >
              <Send className="w-4 h-4" />
              发送数据
            </Button>

            {/* 自动发送 */}
            <div className="pt-2 border-t border-panel-border">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoSend}
                  onChange={(e) => (e.target.checked ? startAutoSend() : stopAutoSend())}
                  disabled={!isConnected || !sendData.trim()}
                  className="accent-signal-blue"
                />
                <span className="text-sm text-gray-300">自动发送</span>
              </label>
              {autoSend && (
                <div className="mt-2 flex items-center gap-2">
                  <input
                    type="number"
                    value={autoSendInterval}
                    onChange={(e) => setAutoSendInterval(Number(e.target.value))}
                    className="input-field flex-1 text-sm py-1"
                    min={100}
                    step={100}
                  />
                  <span className="text-sm text-gray-400">ms</span>
                </div>
              )}
            </div>
          </div>
        </Panel>
      </div>

      {/* 右侧：通信记录 */}
      <div className="flex-1 flex flex-col min-w-0">
        <Panel
          title="通信记录"
          className="flex-1 flex flex-col"
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
          <div className="flex-1 overflow-y-auto bg-black/40 rounded p-3 font-mono text-sm">
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
                      {/* 图标 */}
                      {msg.type === 'send' ? (
                        <ArrowUpRight className="w-4 h-4 mt-0.5 flex-shrink-0 text-signal-blue" />
                      ) : msg.type === 'receive' ? (
                        <ArrowDownLeft className="w-4 h-4 mt-0.5 flex-shrink-0 text-signal-green" />
                      ) : (
                        <Wifi className="w-4 h-4 mt-0.5 flex-shrink-0 text-yellow-500" />
                      )}
                      
                      <div className="flex-1 min-w-0">
                        {/* 时间戳和类型 */}
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
                            [{msg.type === 'send' ? '发送' : msg.type === 'receive' ? '接收' : '系统'}]
                          </span>
                        </div>
                        
                        {/* 内容 */}
                        <div className="text-gray-200 break-all">{msg.content}</div>
                        
                        {/* HEX显示 */}
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
    </div>
  )
}

export default TcpDebugPage