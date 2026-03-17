/**
 * 参数化管理页面
 */

import { useState, useEffect, useCallback } from 'react'
import { Panel, Button, Input } from '@/components/ui'
import {
  Plus,
  Edit3,
  Trash2,
  Save,
  X,
  Search,
  RefreshCw,
  Play,
  Info,
} from 'lucide-react'
import {
  parameterService,
  type ParameterConfig,
  type ParameterConfigCreate,
  PARAM_TYPES,
  BUILTIN_PARAMS,
} from '@/services/parameter'

// 初始表单数据
const initialFormData: ParameterConfigCreate = {
  name: '',
  param_type: 'static',
  static_value: '',
  config: '',
  description: '',
  is_enabled: true,
  sort_order: 0,
}

const ParameterManagePage = () => {
  // 数据状态
  const [parameters, setParameters] = useState<ParameterConfig[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 搜索
  const [searchName, setSearchName] = useState('')

  // 编辑状态
  const [editingId, setEditingId] = useState<number | null>(null)
  const [formData, setFormData] = useState<ParameterConfigCreate>(initialFormData)
  const [saving, setSaving] = useState(false)

  // 预览
  const [previewContent, setPreviewContent] = useState('')
  const [previewResult, setPreviewResult] = useState('')
  const [previewing, setPreviewing] = useState(false)

  // 加载数据
  const loadParameters = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await parameterService.getList({
        name: searchName || undefined,
      })
      if (response.code === 200 && response.data) {
        setParameters(response.data.items)
      } else {
        setError(response.message || '加载失败')
      }
    } catch (err: any) {
      setError(err.message || '网络错误')
    } finally {
      setLoading(false)
    }
  }, [searchName])

  useEffect(() => {
    loadParameters()
  }, [loadParameters])

  // 新建
  const handleCreate = () => {
    setEditingId(null)
    setFormData(initialFormData)
  }

  // 编辑
  const handleEdit = (param: ParameterConfig) => {
    setEditingId(param.id)
    setFormData({
      name: param.name,
      param_type: param.param_type,
      static_value: param.static_value || '',
      config: param.config || '',
      description: param.description || '',
      is_enabled: param.is_enabled,
      sort_order: param.sort_order,
    })
  }

  // 取消编辑
  const handleCancel = () => {
    setEditingId(null)
    setFormData(initialFormData)
  }

  // 保存
  const handleSave = async () => {
    if (!formData.name.trim()) {
      alert('请输入参数名称')
      return
    }

    setSaving(true)
    try {
      let response
      if (editingId) {
        response = await parameterService.update(editingId, formData)
      } else {
        response = await parameterService.create(formData)
      }

      if (response.code === 200) {
        handleCancel()
        loadParameters()
      } else {
        alert(response.message || '保存失败')
      }
    } catch (err: any) {
      alert(err.message || '网络错误')
    } finally {
      setSaving(false)
    }
  }

  // 删除
  const handleDelete = async (id: number) => {
    if (!confirm('确定要删除此参数配置吗？')) return

    try {
      const response = await parameterService.delete(id)
      if (response.code === 200) {
        loadParameters()
      } else {
        alert(response.message || '删除失败')
      }
    } catch (err: any) {
      alert(err.message || '网络错误')
    }
  }

  // 预览
  const handlePreview = async () => {
    if (!previewContent.trim()) return

    setPreviewing(true)
    try {
      const response = await parameterService.preview(previewContent)
      if (response.code === 200 && response.data) {
        setPreviewResult(response.data)
      } else {
        setPreviewResult('预览失败: ' + (response.message || '未知错误'))
      }
    } catch (err: any) {
      setPreviewResult('预览失败: ' + err.message)
    } finally {
      setPreviewing(false)
    }
  }

  // 渲染配置输入
  const renderConfigInput = () => {
    const paramType = formData.param_type

    if (paramType === 'timestamp') {
      return (
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs text-gray-400 mb-1">格式</label>
            <Input
              value={(() => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  return config.format || '%Y%m%d%H%M%S'
                } catch {
                  return '%Y%m%d%H%M%S'
                }
              })()}
              onChange={(e) => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  config.format = e.target.value
                  setFormData({ ...formData, config: JSON.stringify(config) })
                } catch {
                  setFormData({ ...formData, config: JSON.stringify({ format: e.target.value }) })
                }
              }}
              placeholder="%Y%m%d%H%M%S"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">单位</label>
            <select
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
              value={(() => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  return config.unit || 'formatted'
                } catch {
                  return 'formatted'
                }
              })()}
              onChange={(e) => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  config.unit = e.target.value
                  setFormData({ ...formData, config: JSON.stringify(config) })
                } catch {
                  setFormData({ ...formData, config: JSON.stringify({ unit: e.target.value }) })
                }
              }}
            >
              <option value="formatted">格式化</option>
              <option value="ms">毫秒</option>
              <option value="s">秒</option>
            </select>
          </div>
        </div>
      )
    }

    if (paramType === 'random') {
      return (
        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="block text-xs text-gray-400 mb-1">类型</label>
            <select
              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
              value={(() => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  return config.type || 'int'
                } catch {
                  return 'int'
                }
              })()}
              onChange={(e) => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  config.type = e.target.value
                  setFormData({ ...formData, config: JSON.stringify(config) })
                } catch {
                  setFormData({ ...formData, config: JSON.stringify({ type: e.target.value }) })
                }
              }}
            >
              <option value="int">整数</option>
              <option value="float">小数</option>
              <option value="string">字符串</option>
              <option value="hex">十六进制</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">最小值/长度</label>
            <Input
              type="number"
              value={(() => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  return config.min ?? config.length ?? 0
                } catch {
                  return 0
                }
              })()}
              onChange={(e) => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  config.min = parseInt(e.target.value)
                  setFormData({ ...formData, config: JSON.stringify(config) })
                } catch {
                  setFormData({ ...formData, config: JSON.stringify({ min: parseInt(e.target.value) }) })
                }
              }}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">最大值</label>
            <Input
              type="number"
              value={(() => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  return config.max ?? 100
                } catch {
                  return 100
                }
              })()}
              onChange={(e) => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  config.max = parseInt(e.target.value)
                  setFormData({ ...formData, config: JSON.stringify(config) })
                } catch {
                  setFormData({ ...formData, config: JSON.stringify({ max: parseInt(e.target.value) }) })
                }
              }}
            />
          </div>
        </div>
      )
    }

    if (paramType === 'counter') {
      return (
        <div className="grid grid-cols-3 gap-2">
          <div>
            <label className="block text-xs text-gray-400 mb-1">起始值</label>
            <Input
              type="number"
              value={(() => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  return config.start ?? 1
                } catch {
                  return 1
                }
              })()}
              onChange={(e) => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  config.start = parseInt(e.target.value)
                  setFormData({ ...formData, config: JSON.stringify(config) })
                } catch {
                  setFormData({ ...formData, config: JSON.stringify({ start: parseInt(e.target.value) }) })
                }
              }}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">增量</label>
            <Input
              type="number"
              value={(() => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  return config.increment ?? 1
                } catch {
                  return 1
                }
              })()}
              onChange={(e) => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  config.increment = parseInt(e.target.value)
                  setFormData({ ...formData, config: JSON.stringify(config) })
                } catch {
                  setFormData({ ...formData, config: JSON.stringify({ increment: parseInt(e.target.value) }) })
                }
              }}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">最大值</label>
            <Input
              type="number"
              value={(() => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  return config.max ?? 999999
                } catch {
                  return 999999
                }
              })()}
              onChange={(e) => {
                try {
                  const config = formData.config ? JSON.parse(formData.config) : {}
                  config.max = parseInt(e.target.value)
                  setFormData({ ...formData, config: JSON.stringify(config) })
                } catch {
                  setFormData({ ...formData, config: JSON.stringify({ max: parseInt(e.target.value) }) })
                }
              }}
            />
          </div>
        </div>
      )
    }

    return null
  }

  return (
    <div className="h-full flex flex-col gap-4 animate-fadeIn">
      {/* 标题栏 */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-white">参数化管理</h1>
        <div className="flex items-center gap-2">
          <Button variant="primary" onClick={handleCreate}>
            <Plus className="w-4 h-4" />
            新建参数
          </Button>
          <Button variant="secondary" onClick={loadParameters}>
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </div>

      <div className="flex-1 flex gap-4 min-h-0">
        {/* 左侧：参数列表 */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* 搜索栏 */}
          <div className="mb-4 flex items-center gap-2">
            <div className="relative flex-1 max-w-xs">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                value={searchName}
                onChange={(e) => setSearchName(e.target.value)}
                placeholder="搜索参数名称..."
                className="pl-10"
              />
            </div>
          </div>

          {/* 参数列表 */}
          <Panel title="自定义参数" className="flex-1 overflow-auto">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
              </div>
            ) : error ? (
              <div className="flex items-center justify-center h-32 text-red-400">
                {error}
              </div>
            ) : parameters.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-gray-400">
                <Info className="w-8 h-8 mb-2 opacity-30" />
                <p>暂无参数配置</p>
                <p className="text-xs mt-1">点击"新建参数"添加</p>
              </div>
            ) : (
              <div className="space-y-2">
                {parameters.map((param) => (
                  <div
                    key={param.id}
                    className="p-3 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    {editingId === param.id ? (
                      /* 编辑模式 */
                      <div className="space-y-3">
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            <label className="block text-xs text-gray-400 mb-1">参数名称</label>
                            <Input
                              value={formData.name}
                              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                              placeholder="参数名称"
                            />
                          </div>
                          <div>
                            <label className="block text-xs text-gray-400 mb-1">参数类型</label>
                            <select
                              className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
                              value={formData.param_type}
                              onChange={(e) => setFormData({ ...formData, param_type: e.target.value })}
                            >
                              {Object.entries(PARAM_TYPES).map(([key, label]) => (
                                <option key={key} value={key}>
                                  {label}
                                </option>
                              ))}
                            </select>
                          </div>
                        </div>

                        {formData.param_type === 'static' && (
                          <div>
                            <label className="block text-xs text-gray-400 mb-1">静态值</label>
                            <Input
                              value={formData.static_value || ''}
                              onChange={(e) => setFormData({ ...formData, static_value: e.target.value })}
                              placeholder="静态值"
                            />
                          </div>
                        )}

                        {renderConfigInput()}

                        <div>
                          <label className="block text-xs text-gray-400 mb-1">描述</label>
                          <Input
                            value={formData.description || ''}
                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                            placeholder="参数描述"
                          />
                        </div>

                        <div className="flex items-center gap-2">
                          <label className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={formData.is_enabled}
                              onChange={(e) => setFormData({ ...formData, is_enabled: e.target.checked })}
                              className="accent-signal-blue"
                            />
                            <span className="text-sm text-gray-300">启用</span>
                          </label>
                        </div>

                        <div className="flex justify-end gap-2">
                          <Button variant="secondary" size="sm" onClick={handleCancel}>
                            <X className="w-3 h-3" />
                            取消
                          </Button>
                          <Button variant="primary" size="sm" onClick={handleSave} disabled={saving}>
                            <Save className="w-3 h-3" />
                            {saving ? '保存中...' : '保存'}
                          </Button>
                        </div>
                      </div>
                    ) : (
                      /* 显示模式 */
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <code className="text-signal-blue font-mono">${'{'}{param.name}{'}'}</code>
                            <span className="text-xs px-1.5 py-0.5 bg-gray-600 rounded">
                              {PARAM_TYPES[param.param_type] || param.param_type}
                            </span>
                            {!param.is_enabled && (
                              <span className="text-xs px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded">
                                已禁用
                              </span>
                            )}
                          </div>
                          {param.description && (
                            <p className="text-sm text-gray-400 mt-1">{param.description}</p>
                          )}
                          {param.param_type === 'static' && param.static_value && (
                            <p className="text-xs text-gray-500 mt-1 font-mono">
                              值: {param.static_value}
                            </p>
                          )}
                        </div>
                        <div className="flex items-center gap-1">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleEdit(param)}
                          >
                            <Edit3 className="w-3 h-3" />
                          </Button>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleDelete(param.id)}
                          >
                            <Trash2 className="w-3 h-3 text-red-400" />
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* 新建表单 */}
            {editingId === null && (
              <div className="mt-4 p-3 bg-gray-700/30 rounded-lg border border-dashed border-gray-600">
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">参数名称</label>
                      <Input
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder="例如: my_param"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">参数类型</label>
                      <select
                        className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
                        value={formData.param_type}
                        onChange={(e) => setFormData({ ...formData, param_type: e.target.value })}
                      >
                        {Object.entries(PARAM_TYPES).map(([key, label]) => (
                          <option key={key} value={key}>
                            {label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {formData.param_type === 'static' && (
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">静态值</label>
                      <Input
                        value={formData.static_value || ''}
                        onChange={(e) => setFormData({ ...formData, static_value: e.target.value })}
                        placeholder="静态值"
                      />
                    </div>
                  )}

                  {renderConfigInput()}

                  <div>
                    <label className="block text-xs text-gray-400 mb-1">描述</label>
                    <Input
                      value={formData.description || ''}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="参数描述"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.is_enabled}
                        onChange={(e) => setFormData({ ...formData, is_enabled: e.target.checked })}
                        className="accent-signal-blue"
                      />
                      <span className="text-sm text-gray-300">启用</span>
                    </label>
                    <Button variant="primary" size="sm" onClick={handleSave} disabled={saving}>
                      <Save className="w-3 h-3" />
                      {saving ? '保存中...' : '保存'}
                    </Button>
                  </div>
                </div>
              </div>
            )}
          </Panel>
        </div>

        {/* 右侧：内置参数和预览 */}
        <div className="w-80 flex flex-col gap-4">
          {/* 内置参数 */}
          <Panel title="内置参数" className="flex-shrink-0">
            <div className="space-y-2">
              {BUILTIN_PARAMS.map((param) => (
                <div
                  key={param.name}
                  className="p-2 bg-gray-700/50 rounded hover:bg-gray-700 transition-colors"
                >
                  <code className="text-signal-green font-mono text-sm">{param.example}</code>
                  <p className="text-xs text-gray-400 mt-1">{param.description}</p>
                </div>
              ))}
            </div>
          </Panel>

          {/* 预览 */}
          <Panel title="参数预览" className="flex-1">
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">输入内容</label>
                <textarea
                  className="w-full h-24 bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm font-mono resize-none"
                  value={previewContent}
                  onChange={(e) => setPreviewContent(e.target.value)}
                  placeholder="输入包含 ${参数名} 的内容..."
                />
              </div>
              <Button
                variant="primary"
                size="sm"
                onClick={handlePreview}
                disabled={!previewContent.trim() || previewing}
                className="w-full"
              >
                <Play className="w-3 h-3" />
                {previewing ? '预览中...' : '预览替换结果'}
              </Button>
              {previewResult && (
                <div>
                  <label className="block text-xs text-gray-400 mb-1">替换结果</label>
                  <div className="p-2 bg-gray-700/50 rounded font-mono text-sm text-signal-green break-all">
                    {previewResult}
                  </div>
                </div>
              )}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  )
}

export default ParameterManagePage