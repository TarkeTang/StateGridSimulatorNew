/**
 * 国网57号文协议配置组件
 */

import { Input } from '@/components/ui'
import type { StateGrid57Config } from '@/services/session'

interface StateGrid57ConfigFormProps {
  value: StateGrid57Config
  onChange: (config: StateGrid57Config) => void
}

const deviceModes = [
  { value: 'Superior', label: '上级系统' },
  { value: 'Area', label: '区域主机' },
  { value: 'Edge', label: '边缘节点' },
  { value: 'Robot', label: '机器人' },
  { value: 'Drone', label: '无人机' },
  { value: 'Algo', label: '算法管理平台' },
]

const nodeTypes = [
  { value: 'PatrolHost', label: '巡检主机' },
  { value: 'PatrolDevice', label: '巡检设备' },
  { value: 'CloudHost', label: '云主机' },
]

export function StateGrid57ConfigForm({ value, onChange }: StateGrid57ConfigFormProps) {
  const updateField = <K extends keyof StateGrid57Config>(field: K, val: StateGrid57Config[K]) => {
    onChange({ ...value, [field]: val })
  }

  return (
    <div className="space-y-4 p-4 bg-industrial-800/50 rounded-lg border border-panel-border">
      <h4 className="text-sm font-medium text-signal-blue mb-3">国网57号文协议配置</h4>

      {/* 身份标识 */}
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="发送身份标识"
          value={value.send_code}
          onChange={(e) => updateField('send_code', e.target.value)}
          placeholder="Device01"
        />
        <Input
          label="接收身份标识"
          value={value.receive_code}
          onChange={(e) => updateField('receive_code', e.target.value)}
          placeholder="Server01"
        />
      </div>

      {/* 设备模式 */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm text-gray-400 mb-1.5">设备模式</label>
          <select
            value={value.device_mode}
            onChange={(e) => updateField('device_mode', e.target.value)}
            className="input-field"
          >
            {deviceModes.map((mode) => (
              <option key={mode.value} value={mode.value}>
                {mode.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-sm text-gray-400 mb-1.5">节点类型</label>
          <select
            value={value.node_type}
            onChange={(e) => updateField('node_type', e.target.value)}
            className="input-field"
          >
            {nodeTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 心跳配置 */}
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="心跳间隔(ms)"
          type="number"
          value={value.heart_beat_interval}
          onChange={(e) => updateField('heart_beat_interval', parseInt(e.target.value) || 100000)}
          placeholder="100000"
        />
        <div className="flex items-center gap-4 pt-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={value.auto_heartbeat}
              onChange={(e) => updateField('auto_heartbeat', e.target.checked)}
              className="accent-signal-blue"
            />
            <span className="text-sm text-gray-300">自动发送心跳</span>
          </label>
        </div>
      </div>

      {/* 数据上报间隔 */}
      <div className="border-t border-panel-border pt-4 mt-4">
        <h5 className="text-xs text-gray-400 mb-3">数据上报间隔配置(ms)</h5>
        <div className="grid grid-cols-3 gap-4">
          <Input
            label="巡视装置运行数据"
            type="number"
            value={value.patroldevice_run_interval}
            onChange={(e) => updateField('patroldevice_run_interval', parseInt(e.target.value) || 300000)}
            placeholder="300000"
          />
          <Input
            label="无人机机巢运行数据"
            type="number"
            value={value.nest_run_interval}
            onChange={(e) => updateField('nest_run_interval', parseInt(e.target.value) || 300000)}
            placeholder="300000"
          />
          <Input
            label="环境数据上报"
            type="number"
            value={value.env_interval}
            onChange={(e) => updateField('env_interval', parseInt(e.target.value) || 300000)}
            placeholder="300000"
          />
        </div>
      </div>

      {/* 自动行为 */}
      <div className="border-t border-panel-border pt-4 mt-4">
        <div className="flex items-center gap-6">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={value.auto_register}
              onChange={(e) => updateField('auto_register', e.target.checked)}
              className="accent-signal-blue"
            />
            <span className="text-sm text-gray-300">连接后自动发送注册指令</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={value.auto_response}
              onChange={(e) => updateField('auto_response', e.target.checked)}
              className="accent-signal-blue"
            />
            <span className="text-sm text-gray-300">自动响应请求消息</span>
          </label>
        </div>
      </div>
    </div>
  )
}

// 默认配置（单位：ms）
export const defaultStateGrid57Config: StateGrid57Config = {
  send_code: 'Device01',
  receive_code: 'Server01',
  device_mode: 'Edge',
  node_type: 'PatrolDevice',
  heart_beat_interval: 100000,      // 100秒 = 100000ms
  auto_heartbeat: true,
  patroldevice_run_interval: 300000, // 300秒 = 300000ms
  nest_run_interval: 300000,
  env_interval: 300000,
  auto_register: true,
  auto_response: true,
}