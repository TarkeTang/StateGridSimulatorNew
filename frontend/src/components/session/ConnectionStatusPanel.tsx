/**
 * 连接状态面板组件
 */

import { Panel, Button } from '@/components/ui'
import { Play, Square, Clock } from 'lucide-react'
import { getConnectionDuration, getStatusStyle } from '@/utils/formatters'
import type { SessionConfig } from '@/services/session'

interface ConnectionStatusPanelProps {
  session: SessionConfig
  isConnected: boolean
  isConnecting: boolean
  operating: boolean
  connectTime: string | null
  sendCount: number
  receiveCount: number
  onConnect: () => void
}

export function ConnectionStatusPanel({
  session,
  isConnected,
  isConnecting,
  operating,
  connectTime,
  sendCount,
  receiveCount,
  onConnect,
}: ConnectionStatusPanelProps) {
  const statusStyle = getStatusStyle(session.status)

  return (
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
          <span className="text-white font-mono text-sm">{getConnectionDuration(connectTime)}</span>
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
          onClick={onConnect}
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
  )
}