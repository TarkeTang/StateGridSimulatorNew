/**
 * 自动发送配置弹窗组件
 */

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui'
import { X, Plus, GripVertical, Trash2 } from 'lucide-react'
import type { AutoSendConfig } from '@/services/autoSend'

interface AutoSendDialogProps {
  open: boolean
  configs: AutoSendConfig[]
  isActive: boolean
  currentSendIndex: number
  onClose: () => void
  onAdd: () => void
  onUpdate: (configId: number, field: keyof AutoSendConfig, value: any) => void
  onRemove: (configId: number) => void
  onStart: () => void
}

export function AutoSendDialog({
  open,
  configs,
  isActive,
  currentSendIndex,
  onClose,
  onAdd,
  onUpdate,
  onRemove,
  onStart,
}: AutoSendDialogProps) {
  // 输入框临时值（字符串），用于支持自由编辑
  const [inputValues, setInputValues] = useState<Record<number, string>>({})

  // 同步 configs 到 inputValues
  useEffect(() => {
    const newValues: Record<number, string> = {}
    configs.forEach((config) => {
      if (!(config.id in inputValues)) {
        newValues[config.id] = String(config.interval_ms)
      }
    })
    if (Object.keys(newValues).length > 0) {
      setInputValues((prev) => ({ ...prev, ...newValues }))
    }
  }, [configs])

  if (!open) return null

  const enabledCount = configs.filter((c) => c.is_enabled && c.message_content.trim()).length

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-panel-card border border-panel-border rounded-lg w-[600px] max-h-[80vh] flex flex-col">
        {/* 头部 */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-panel-border flex-shrink-0">
          <h3 className="text-base font-medium">自动发送配置</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* 内容 */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          <p className="text-sm text-gray-400">
            配置多条消息，每条消息按独立间隔循环发送。
          </p>

          {configs.map((config, index) => (
            <div
              key={config.id}
              className={`p-3 rounded border ${
                isActive && currentSendIndex === index
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
                    value={config.message_content}
                    onChange={(e) => onUpdate(config.id, 'message_content', e.target.value)}
                    placeholder="输入消息内容..."
                    className="input-field h-16 resize-none font-mono text-sm w-full"
                    disabled={isActive}
                  />

                  {/* 间隔和启用 */}
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-gray-400">发送后等待</span>
                      <input
                        type="number"
                        value={inputValues[config.id] ?? String(config.interval_ms)}
                        onChange={(e) => {
                          // 更新临时输入值，允许自由编辑
                          setInputValues((prev) => ({
                            ...prev,
                            [config.id]: e.target.value,
                          }))
                        }}
                        onBlur={(e) => {
                          const val = Number(e.target.value)
                          // 失焦时校验并更新实际值
                          const finalValue = isNaN(val) || val < 100 ? 100 : val
                          onUpdate(config.id, 'interval_ms', finalValue)
                          setInputValues((prev) => ({
                            ...prev,
                            [config.id]: String(finalValue),
                          }))
                        }}
                        className="input-field w-20 text-sm py-1"
                        disabled={isActive}
                      />
                      <span className="text-xs text-gray-400">ms</span>
                    </div>

                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.is_enabled}
                        onChange={(e) => onUpdate(config.id, 'is_enabled', e.target.checked)}
                        className="accent-signal-blue"
                        disabled={isActive}
                      />
                      <span className="text-xs text-gray-300">启用</span>
                    </label>

                    <button
                      onClick={() => onRemove(config.id)}
                      disabled={isActive || configs.length <= 1}
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
            onClick={onAdd}
            disabled={isActive}
            className="w-full py-2 border border-dashed border-panel-border rounded text-gray-400 hover:text-signal-blue hover:border-signal-blue transition-colors disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            <Plus className="w-4 h-4" />
            添加消息
          </button>
        </div>

        {/* 底部 */}
        <div className="flex items-center justify-end gap-3 px-4 py-3 border-t border-panel-border flex-shrink-0">
          <Button variant="secondary" onClick={onClose}>
            取消
          </Button>
          <Button
            variant="success"
            onClick={() => {
              onClose()
              onStart()
            }}
            disabled={enabledCount === 0}
          >
            开始发送
          </Button>
        </div>
      </div>
    </div>
  )
}