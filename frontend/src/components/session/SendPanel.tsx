/**
 * 发送面板组件
 */

import { Panel, Button } from '@/components/ui'
import { Send, Timer } from 'lucide-react'
import { formatXml, formatJson } from '@/utils/formatters'

interface SendPanelProps {
  sendData: string
  sendMode: 'text' | 'xml' | 'json'
  isConnected: boolean
  autoSendActive: boolean
  onSendDataChange: (data: string) => void
  onSendModeChange: (mode: 'text' | 'xml' | 'json') => void
  onSend: () => void
  onOpenAutoSend: () => void
  onStopAutoSend: () => void
}

export function SendPanel({
  sendData,
  sendMode,
  isConnected,
  autoSendActive,
  onSendDataChange,
  onSendModeChange,
  onSend,
  onOpenAutoSend,
  onStopAutoSend,
}: SendPanelProps) {
  const getDisplayContent = (content: string): string => {
    if (sendMode === 'xml') {
      return formatXml(content)
    } else if (sendMode === 'json') {
      return formatJson(content)
    }
    return content
  }

  return (
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
                onChange={() => onSendModeChange('text')}
                className="accent-signal-blue"
              />
              <span className="text-sm text-gray-300">文本</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="radio"
                name="sendMode"
                checked={sendMode === 'xml'}
                onChange={() => onSendModeChange('xml')}
                className="accent-signal-blue"
              />
              <span className="text-sm text-gray-300">XML</span>
            </label>
            <label className="flex items-center gap-1.5 cursor-pointer">
              <input
                type="radio"
                name="sendMode"
                checked={sendMode === 'json'}
                onChange={() => onSendModeChange('json')}
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
            onChange={(e) => onSendDataChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.ctrlKey) {
                onSend()
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
            onClick={onSend}
            disabled={!isConnected || !sendData.trim()}
          >
            <Send className="w-4 h-4" />
            发送
          </Button>
          <Button
            variant={autoSendActive ? 'danger' : 'secondary'}
            onClick={() => {
              if (autoSendActive) {
                onStopAutoSend()
              } else {
                onOpenAutoSend()
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
  )
}