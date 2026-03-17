/**
 * 会话信息面板组件
 */

import { Panel } from '@/components/ui'
import { getDictName, type DictData } from '@/services/dict'
import type { SessionConfig } from '@/services/session'

interface SessionInfoPanelProps {
  session: SessionConfig
  protocolTypes: DictData[]
}

export function SessionInfoPanel({ session, protocolTypes }: SessionInfoPanelProps) {
  return (
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
  )
}