import { useState, useRef, useCallback } from 'react'
import { Panel, Button, Input } from '@/components/ui'
import {
  Play,
  Square,
  Send,
  Trash2,
  Download,
  Upload,
  Wifi,
  WifiOff,
  Clock,
  ArrowUpRight,
  ArrowDownLeft,
} from 'lucide-react'

interface MessageItem {
  id: number
  type: 'send' | 'receive'
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

  const messageIdRef = useRef(0)
  const autoSendTimerRef = useRef<NodeJS.Timeout | null>(null)

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
  const addMessage = useCallback((type: 'send' | 'receive', content: string) => {
    const newMessage: MessageItem = {
      id: ++messageIdRef.current,
      type,
      content,
      timestamp: getTimestamp(),
      hex: stringToHex(content),
    }
    setMessages((prev) => [...prev, newMessage])
    
    if (type === 'send') {
      setSendCount((prev) => prev + 1)
    } else {
      setReceiveCount((prev) => prev + 1)
    }
  }, [])

  // 连接
  const handleConnect = async () => {
    if (isConnected) {
      // 断开连接
      setIsConnected(false)
      stopAutoSend()
      addMessage('receive', '[系统] 连接已断开')
    } else {
      // 建立连接
      setIsConnecting(true)
      // 模拟连接过程
      await new Promise((resolve) => setTimeout(resolve, 500))
      setIsConnecting(false)
      setIsConnected(true)
      addMessage('receive', `[系统] 已连接到 ${host}:${port}`)
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
      .map((msg) => `[${msg.timestamp}] ${msg.type === 'send' ? '发送' : '接收'}: ${msg.content}`)
      .join('\n')
    const blob = new Blob([log], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `tcp_debug_${new Date().toISOString().slice(0, 10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4 animate-fadeIn">
      {/* 连接配置 */}
      <Panel title="连接配置">
        <div className="flex items-end gap-4">
          <div className="flex-1">
            <Input
              label="服务器地址"
              value={host}
              onChange={(e) => setHost(e.target.value)}
              placeholder="127.0.0.1"
              disabled={isConnected}
            />
          </div>
          <div className="w-32">
            <Input
              label="端口"
              value={port}
              onChange={(e) => setPort(e.target.value)}
              placeholder="8080"
              disabled={isConnected}
            />
          </div>
          <Button
            variant={isConnected ? 'danger' : 'success'}
            onClick={handleConnect}
            disabled={isConnecting}
          >
            {isConnecting ? (
              <>
                <Clock className="w-4 h-4 animate-spin" />
                连接中...
              </>
            ) : isConnected ? (
              <>
                <Square className="w-4 h-4" />
                断开
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                连接
              </>
            )}
          </Button>
        </div>

        {/* 连接状态 */}
        <div className="mt-4 flex items-center gap-6">
          <div className="flex items-center gap-2">
            {isConnected ? (
              <>
                <Wifi className="w-5 h-5 text-signal-green" />
                <span className="text-signal-green">已连接</span>
              </>
            ) : (
              <>
                <WifiOff className="w-5 h-5 text-gray-500" />
                <span className="text-gray-500">未连接</span>
              </>
            )}
          </div>
          <div className="text-sm text-gray-400">
            发送: <span className="text-signal-blue">{sendCount}</span> 条 | 
            接收: <span className="text-signal-green">{receiveCount}</span> 条
          </div>
        </div>
      </Panel>

      {/* 发送区域 */}
      <Panel title="发送数据">
        <div className="space-y-4">
          {/* 发送模式选择 */}
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-400">发送模式:</span>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="sendMode"
                checked={sendMode === 'text'}
                onChange={() => setSendMode('text')}
                className="accent-signal-blue"
              />
              <span className="text-sm">文本</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="sendMode"
                checked={sendMode === 'hex'}
                onChange={() => setSendMode('hex')}
                className="accent-signal-blue"
              />
              <span className="text-sm">十六进制</span>
            </label>
          </div>

          {/* 发送内容 */}
          <textarea
            value={sendData}
            onChange={(e) => setSendData(e.target.value)}
            placeholder={sendMode === 'hex' ? '输入十六进制数据，如: 01 02 03 04' : '输入要发送的数据...'}
            className="input-field h-24 resize-none font-mono"
            disabled={!isConnected}
          />

          {/* 发送按钮 */}
          <div className="flex items-center gap-4">
            <Button
              variant="primary"
              onClick={handleSend}
              disabled={!isConnected || !sendData.trim()}
            >
              <Send className="w-4 h-4" />
              发送
            </Button>
            
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoSend}
                  onChange={(e) => e.target.checked ? startAutoSend() : stopAutoSend()}
                  disabled={!isConnected || !sendData.trim()}
                  className="accent-signal-blue"
                />
                <span className="text-sm text-gray-400">自动发送</span>
              </label>
              {autoSend && (
                <input
                  type="number"
                  value={autoSendInterval}
                  onChange={(e) => setAutoSendInterval(Number(e.target.value))}
                  className="input-field w-24 text-sm py-1"
                  min={100}
                  step={100}
                />
              )}
              {autoSend && <span className="text-sm text-gray-400">ms</span>}
            </div>
          </div>
        </div>
      </Panel>

      {/* 接收区域 */}
      <Panel
        title="通信记录"
        headerAction={
          <div className="flex items-center gap-2">
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
        <div className="h-80 overflow-y-auto bg-black/30 rounded p-3 font-mono text-sm">
          {messages.length === 0 ? (
            <div className="text-gray-500 text-center py-8">暂无通信记录</div>
          ) : (
            messages.map((msg) => (
              <div
                key={msg.id}
                className={`py-1 border-b border-panel-border/30 last:border-0 ${
                  msg.type === 'send' ? 'text-signal-blue' : 'text-signal-green'
                }`}
              >
                <div className="flex items-start gap-2">
                  {msg.type === 'send' ? (
                    <ArrowUpRight className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  ) : (
                    <ArrowDownLeft className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1">
                    {showTimestamp && (
                      <span className="text-gray-500 text-xs mr-2">[{msg.timestamp}]</span>
                    )}
                    <span>{msg.content}</span>
                    {showHex && msg.hex && (
                      <div className="text-gray-500 text-xs mt-1">HEX: {msg.hex}</div>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </Panel>
    </div>
  )
}

export default TcpDebugPage