/**
 * 消息记录组件
 */

import { useRef } from 'react'
import { Panel, Button } from '@/components/ui'
import { Trash2, Download, RefreshCw, Activity, ArrowUpRight, ArrowDownLeft, Wifi } from 'lucide-react'
import type { SessionMessage } from '@/services/message'

interface MessageLogProps {
  messages: SessionMessage[]
  loading: boolean
  showTimestamp: boolean
  onClear: () => void
  onExport: () => void
  onToggleTimestamp: () => void
}

export function MessageLog({
  messages,
  loading,
  showTimestamp,
  onClear,
  onExport,
  onToggleTimestamp,
}: MessageLogProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  return (
    <Panel
      title="通信记录"
      className="h-full is-flex"
      headerAction={
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showTimestamp}
              onChange={onToggleTimestamp}
              className="accent-signal-blue"
            />
            <span className="text-xs text-gray-400">时间戳</span>
          </label>
          <Button variant="secondary" size="sm" onClick={onClear}>
            <Trash2 className="w-3 h-3" />
            清空
          </Button>
          <Button variant="secondary" size="sm" onClick={onExport}>
            <Download className="w-3 h-3" />
            导出
          </Button>
        </div>
      }
    >
      <div className="h-full overflow-y-auto bg-black/40 rounded p-3 font-mono text-sm">
        {loading ? (
          <div className="h-full flex items-center justify-center text-gray-500">
            <RefreshCw className="w-6 h-6 animate-spin" />
          </div>
        ) : messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-500">
            <Activity className="w-8 h-8 mb-2 opacity-30" />
            <p>暂无通信记录</p>
            <p className="text-xs mt-1">建立连接后开始通信</p>
          </div>
        ) : (
          <div className="space-y-1">
            {messages.map((msg) => {
              const extraData = msg.extra_data ? JSON.parse(msg.extra_data) : {}
              const isAutoSend = extraData.is_auto_send

              return (
                <div
                  key={msg.id}
                  className={`py-1.5 px-2 rounded ${
                    msg.direction === 'send'
                      ? 'bg-signal-blue/10 border-l-2 border-signal-blue'
                      : msg.direction === 'receive'
                      ? 'bg-signal-green/10 border-l-2 border-signal-green'
                      : 'bg-yellow-500/10 border-l-2 border-yellow-500'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    {msg.direction === 'send' ? (
                      <ArrowUpRight className="w-4 h-4 mt-0.5 flex-shrink-0 text-signal-blue" />
                    ) : msg.direction === 'receive' ? (
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
                            msg.direction === 'send'
                              ? 'text-signal-blue'
                              : msg.direction === 'receive'
                              ? 'text-signal-green'
                              : 'text-yellow-500'
                          }`}
                        >
                          [
                          {msg.direction === 'send'
                            ? isAutoSend
                              ? '自动发送'
                              : '发送'
                            : msg.direction === 'receive'
                            ? '接收'
                            : '系统'}
                          ]
                        </span>
                      </div>

                      <div className="text-gray-200 break-all whitespace-pre-wrap">
                        {msg.content}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
    </Panel>
  )
}