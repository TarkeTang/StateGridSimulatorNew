/**
 * 会话信息面板组件
 */

import { Panel } from '@/components/ui'
import { getDictName, type DictData } from '@/services/dict'
import type { SessionConfig, StateGrid57Config } from '@/services/session'

interface SessionInfoPanelProps {
  session: SessionConfig
  protocolTypes: DictData[]
}

// 设备模式映射
const deviceModeMap: Record<string, string> = {
  Superior: '上级系统',
  Area: '区域主机',
  Edge: '边缘节点',
  Robot: '机器人',
  Drone: '无人机',
  Algo: '算法管理平台',
}

// 节点类型映射
const nodeTypeMap: Record<string, string> = {
  PatrolHost: '巡检主机',
  PatrolDevice: '巡检设备',
  CloudHost: '云主机',
}

// 配置项组件
function ConfigItem({ label, value }: { label: string; value: string | number | boolean }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-gray-400 text-sm">{label}</span>
      <span className="text-gray-300 text-sm">
        {typeof value === 'boolean' ? (value ? '是' : '否') : value}
      </span>
    </div>
  )
}

// 国网57号文协议配置展示组件
function StateGrid57ConfigPanel({ config }: { config: StateGrid57Config }) {
  return (
    <div className="mt-4 pt-4 border-t border-panel-border">
      <h4 className="text-sm font-medium text-signal-blue mb-3">国网57号文协议配置</h4>
      <div className="space-y-2">
        {/* 身份标识 */}
        <div className="pb-2 border-b border-panel-border/50">
          <span className="text-xs text-gray-500">身份标识</span>
        </div>
        <ConfigItem label="发送身份标识" value={config.send_code} />
        <ConfigItem label="接收身份标识" value={config.receive_code} />

        {/* 设备信息 */}
        <div className="pt-2 pb-2 border-t border-panel-border/50">
          <span className="text-xs text-gray-500">设备信息</span>
        </div>
        <ConfigItem label="设备模式" value={deviceModeMap[config.device_mode] || config.device_mode} />
        <ConfigItem label="节点类型" value={nodeTypeMap[config.node_type] || config.node_type} />

        {/* 心跳配置 */}
        <div className="pt-2 pb-2 border-t border-panel-border/50">
          <span className="text-xs text-gray-500">心跳配置</span>
        </div>
        <ConfigItem label="心跳间隔" value={`${config.heart_beat_interval}秒`} />
        <ConfigItem label="自动发送心跳" value={config.auto_heartbeat} />

        {/* 数据上报间隔 */}
        <div className="pt-2 pb-2 border-t border-panel-border/50">
          <span className="text-xs text-gray-500">数据上报间隔</span>
        </div>
        <ConfigItem label="巡视装置运行数据" value={`${config.patroldevice_run_interval}秒`} />
        <ConfigItem label="无人机机巢运行数据" value={`${config.nest_run_interval}秒`} />
        <ConfigItem label="环境数据" value={`${config.weather_interval}秒`} />
        <ConfigItem label="环境数据上报" value={`${config.env_interval}秒`} />
        <ConfigItem label="运行参数" value={`${config.run_params_interval}秒`} />

        {/* 自动行为 */}
        <div className="pt-2 pb-2 border-t border-panel-border/50">
          <span className="text-xs text-gray-500">自动行为</span>
        </div>
        <ConfigItem label="自动注册" value={config.auto_register} />
        <ConfigItem label="自动响应请求" value={config.auto_response} />
      </div>
    </div>
  )
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

        {/* 国网57号文协议配置 */}
        {(session.protocol_type === 'STATEGRID57' || session.protocol_type === '57StateGrid') && session.stategrid57_config && (
          <StateGrid57ConfigPanel config={session.stategrid57_config} />
        )}
      </div>
    </Panel>
  )
}