import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Panel, Button, Input } from '@/components/ui'
import {
  Plus,
  Edit3,
  Trash2,
  Save,
  X,
  Search,
  RefreshCw,
  Wifi,
  WifiOff,
  Server,
  Play,
  Square,
  Eye,
  AlertCircle,
} from 'lucide-react'
import { sessionService, type SessionConfig, type SessionConfigCreate, type SessionConfigUpdate } from '@/services/session'

const initialFormData: SessionConfigCreate = {
  name: '',
  host: '127.0.0.1',
  port: 8080,
  protocol_type: 'TCP',
  connection_mode: 'client',
  description: '',
  auto_reconnect: false,
  reconnect_interval: 5000,
  timeout: 30000,
  is_enabled: true,
}

const TcpSessionPage = () => {
  const navigate = useNavigate()

  // 数据状态
  const [sessions, setSessions] = useState<SessionConfig[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 搜索和分页
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(20)

  // 弹窗状态
  const [showModal, setShowModal] = useState(false)
  const [editingSession, setEditingSession] = useState<SessionConfig | null>(null)
  const [formData, setFormData] = useState<SessionConfigCreate>(initialFormData)
  const [saving, setSaving] = useState(false)

  // 操作状态
  const [operatingId, setOperatingId] = useState<number | null>(null)

  // 加载数据
  const loadSessions = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await sessionService.getList({
        page: currentPage,
        page_size: pageSize,
        keyword: searchTerm || undefined,
        protocol_type: 'TCP', // 当前页面只显示TCP会话
      })
      if (response.code === 200 && response.data) {
        setSessions(response.data.items)
        setTotal(response.data.total)
      } else {
        setError(response.message || '获取数据失败')
      }
    } catch (err: any) {
      setError(err.message || '网络错误')
    } finally {
      setLoading(false)
    }
  }, [currentPage, pageSize, searchTerm])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  // 打开新增弹窗
  const handleAdd = () => {
    setEditingSession(null)
    setFormData(initialFormData)
    setShowModal(true)
  }

  // 打开编辑弹窗
  const handleEdit = (session: SessionConfig) => {
    setEditingSession(session)
    setFormData({
      name: session.name,
      host: session.host || '127.0.0.1',
      port: session.port || 8080,
      protocol_type: session.protocol_type,
      connection_mode: session.connection_mode,
      description: session.description || '',
      auto_reconnect: session.auto_reconnect,
      reconnect_interval: session.reconnect_interval,
      timeout: session.timeout,
      is_enabled: session.is_enabled,
    })
    setShowModal(true)
  }

  // 保存会话
  const handleSave = async () => {
    if (!formData.name.trim()) {
      alert('请输入会话名称')
      return
    }

    setSaving(true)
    try {
      if (editingSession) {
        // 更新
        const updateData: SessionConfigUpdate = {}
        Object.keys(formData).forEach((key) => {
          const k = key as keyof SessionConfigCreate
          if (formData[k] !== undefined) {
            (updateData as Record<string, unknown>)[k] = formData[k]
          }
        })
        const response = await sessionService.update(editingSession.id, updateData)
        if (response.code === 200) {
          setShowModal(false)
          loadSessions()
        } else {
          alert(response.message || '更新失败')
        }
      } else {
        // 新增
        const response = await sessionService.create(formData)
        if (response.code === 201 || response.code === 200) {
          setShowModal(false)
          loadSessions()
        } else {
          alert(response.message || '创建失败')
        }
      }
    } catch (err: any) {
      alert(err.message || '操作失败')
    } finally {
      setSaving(false)
    }
  }

  // 删除会话
  const handleDelete = async (session: SessionConfig) => {
    if (!confirm(`确定要删除会话 "${session.name}" 吗？`)) {
      return
    }

    setOperatingId(session.id)
    try {
      const response = await sessionService.delete(session.id)
      if (response.code === 200) {
        loadSessions()
      } else {
        alert(response.message || '删除失败')
      }
    } catch (err: any) {
      alert(err.message || '删除失败')
    } finally {
      setOperatingId(null)
    }
  }

  // 连接会话
  const handleConnect = async (session: SessionConfig) => {
    setOperatingId(session.id)
    try {
      const response = await sessionService.connect(session.id)
      if (response.code === 200) {
        loadSessions()
      } else {
        alert(response.message || '连接失败')
      }
    } catch (err: any) {
      alert(err.message || '连接失败')
    } finally {
      setOperatingId(null)
    }
  }

  // 断开会话
  const handleDisconnect = async (session: SessionConfig) => {
    setOperatingId(session.id)
    try {
      const response = await sessionService.disconnect(session.id)
      if (response.code === 200) {
        loadSessions()
      } else {
        alert(response.message || '断开失败')
      }
    } catch (err: any) {
      alert(err.message || '断开失败')
    } finally {
      setOperatingId(null)
    }
  }

  // 获取状态样式
  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'connected':
        return { color: 'text-signal-green', bg: 'bg-signal-green/10', label: '已连接' }
      case 'connecting':
        return { color: 'text-signal-yellow', bg: 'bg-signal-yellow/10', label: '连接中' }
      case 'error':
        return { color: 'text-signal-red', bg: 'bg-signal-red/10', label: '连接错误' }
      default:
        return { color: 'text-gray-400', bg: 'bg-gray-500/10', label: '未连接' }
    }
  }

  return (
    <div className="space-y-4 animate-fadeIn">
      {/* 工具栏 */}
      <Panel>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value)
                  setCurrentPage(1)
                }}
                placeholder="搜索会话名称或地址..."
                className="input-field pl-10 w-64"
              />
            </div>
            <Button variant="secondary" onClick={loadSessions} disabled={loading}>
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>
          </div>
          <Button variant="success" onClick={handleAdd}>
            <Plus className="w-4 h-4" />
            新增会话
          </Button>
        </div>
      </Panel>

      {/* 错误提示 */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-signal-red/10 border border-signal-red/30 rounded-lg text-signal-red">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
          <button onClick={loadSessions} className="ml-auto underline hover:no-underline">
            重试
          </button>
        </div>
      )}

      {/* 会话列表 */}
      <Panel title={`TCP会话列表 (共 ${total} 条)`}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-panel-border">
                <th className="text-left py-3 px-4 text-gray-400 font-medium">状态</th>
                <th className="text-left py-3 px-4 text-gray-400 font-medium">会话名称</th>
                <th className="text-left py-3 px-4 text-gray-400 font-medium">连接地址</th>
                <th className="text-left py-3 px-4 text-gray-400 font-medium">模式</th>
                <th className="text-left py-3 px-4 text-gray-400 font-medium">协议类型</th>
                <th className="text-left py-3 px-4 text-gray-400 font-medium">自动重连</th>
                <th className="text-left py-3 px-4 text-gray-400 font-medium">描述</th>
                <th className="text-left py-3 px-4 text-gray-400 font-medium">更新时间</th>
                <th className="text-center py-3 px-4 text-gray-400 font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} className="text-center py-8 text-gray-400">
                    加载中...
                  </td>
                </tr>
              ) : sessions.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-8 text-gray-500">
                    暂无会话配置，点击"新增会话"添加
                  </td>
                </tr>
              ) : (
                sessions.map((session) => {
                  const statusStyle = getStatusStyle(session.status)
                  const isOperating = operatingId === session.id
                  
                  return (
                    <tr
                      key={session.id}
                      className="border-b border-panel-border/50 hover:bg-industrial-800/50 transition-colors"
                    >
                      <td className="py-3 px-4">
                        <div className={`flex items-center gap-2 ${statusStyle.color}`}>
                          {session.status === 'connected' ? (
                            <Wifi className="w-4 h-4" />
                          ) : (
                            <WifiOff className="w-4 h-4" />
                          )}
                          <span className={`px-2 py-0.5 rounded text-xs ${statusStyle.bg}`}>
                            {statusStyle.label}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <Server className="w-4 h-4 text-gray-400" />
                          <span className="font-medium">{session.name}</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 font-mono text-signal-blue">
                        {session.host}:{session.port}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-xs ${
                            session.connection_mode === 'server'
                              ? 'bg-purple-500/20 text-purple-400'
                              : 'bg-signal-blue/20 text-signal-blue'
                          }`}
                        >
                          {session.connection_mode === 'server' ? '服务端' : '客户端'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-300">{session.protocol_type}</td>
                      <td className="py-3 px-4">
                        {session.auto_reconnect ? (
                          <span className="text-signal-green">是 ({session.reconnect_interval}ms)</span>
                        ) : (
                          <span className="text-gray-500">否</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-gray-400 max-w-xs truncate">
                        {session.description || '-'}
                      </td>
                      <td className="py-3 px-4 text-gray-400 text-xs">
                        {session.updated_at ? new Date(session.updated_at).toLocaleString('zh-CN') : '-'}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center justify-center gap-1">
                          {/* 连接/断开按钮 */}
                          <button
                            onClick={() => 
                              session.status === 'connected' 
                                ? handleDisconnect(session) 
                                : handleConnect(session)
                            }
                            disabled={isOperating || session.status === 'connecting'}
                            className={`p-1.5 rounded transition-colors disabled:opacity-50 ${
                              session.status === 'connected'
                                ? 'text-signal-red hover:bg-signal-red/20'
                                : 'text-signal-green hover:bg-signal-green/20'
                            }`}
                            title={session.status === 'connected' ? '断开' : '连接'}
                          >
                            {isOperating ? (
                              <RefreshCw className="w-4 h-4 animate-spin" />
                            ) : session.status === 'connected' ? (
                              <Square className="w-4 h-4" />
                            ) : (
                              <Play className="w-4 h-4" />
                            )}
                          </button>
                          {/* 编辑按钮 */}
                          <button
                            onClick={() => handleEdit(session)}
                            className="p-1.5 rounded text-gray-400 hover:text-signal-blue hover:bg-signal-blue/20 transition-colors"
                            title="编辑"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          {/* 删除按钮 */}
                          <button
                            onClick={() => handleDelete(session)}
                            disabled={session.status === 'connected'}
                            className="p-1.5 rounded text-gray-400 hover:text-signal-red hover:bg-signal-red/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            title={session.status === 'connected' ? '请先断开连接' : '删除'}
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                          {/* 查看详情按钮 */}
                          <button
                            onClick={() => navigate(`/data/session/${session.id}`)}
                            className="p-1.5 rounded text-gray-400 hover:text-signal-yellow hover:bg-signal-yellow/20 transition-colors"
                            title="查看详情"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* 分页 */}
        {total > pageSize && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-panel-border">
            <div className="text-sm text-gray-400">
              共 {total} 条记录，第 {currentPage} 页
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => p - 1)}
              >
                上一页
              </Button>
              <Button
                variant="secondary"
                size="sm"
                disabled={currentPage * pageSize >= total}
                onClick={() => setCurrentPage((p) => p + 1)}
              >
                下一页
              </Button>
            </div>
          </div>
        )}
      </Panel>

      {/* 新增/编辑弹窗 */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-panel-card border border-panel-border rounded-lg w-[600px] max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-panel-border">
              <h3 className="text-lg font-medium">
                {editingSession ? '编辑会话' : '新增会话'}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="会话名称 *"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="请输入会话名称"
                />
                <div>
                  <label className="block text-sm text-gray-400 mb-1.5">连接模式</label>
                  <select
                    value={formData.connection_mode}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        connection_mode: e.target.value as 'client' | 'server',
                      })
                    }
                    className="input-field"
                  >
                    <option value="client">客户端</option>
                    <option value="server">服务端</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <Input
                  label="服务器地址"
                  value={formData.host || ''}
                  onChange={(e) => setFormData({ ...formData, host: e.target.value })}
                  placeholder="127.0.0.1"
                />
                <Input
                  label="端口"
                  type="number"
                  value={formData.port || ''}
                  onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) || 0 })}
                  placeholder="8080"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-1.5">协议类型</label>
                  <select
                    value={formData.protocol_type}
                    onChange={(e) => setFormData({ ...formData, protocol_type: e.target.value })}
                    className="input-field"
                  >
                    <option value="TCP">TCP</option>
                    <option value="UDP">UDP</option>
                    <option value="WebSocket">WebSocket</option>
                  </select>
                </div>
                <Input
                  label="超时时间(ms)"
                  type="number"
                  value={formData.timeout || ''}
                  onChange={(e) =>
                    setFormData({ ...formData, timeout: parseInt(e.target.value) || 0 })
                  }
                  placeholder="30000"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-4 pt-6">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.auto_reconnect}
                      onChange={(e) =>
                        setFormData({ ...formData, auto_reconnect: e.target.checked })
                      }
                      className="accent-signal-blue"
                    />
                    <span className="text-sm text-gray-300">自动重连</span>
                  </label>
                </div>
                {formData.auto_reconnect && (
                  <Input
                    label="重连间隔(ms)"
                    type="number"
                    value={formData.reconnect_interval || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        reconnect_interval: parseInt(e.target.value) || 0,
                      })
                    }
                    placeholder="5000"
                  />
                )}
              </div>

              <div>
                <label className="block text-sm text-gray-400 mb-1.5">描述</label>
                <textarea
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="请输入会话描述..."
                  className="input-field h-20 resize-none"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-panel-border">
              <Button variant="secondary" onClick={() => setShowModal(false)} disabled={saving}>
                取消
              </Button>
              <Button variant="success" onClick={handleSave} disabled={saving}>
                {saving ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    保存中...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    保存
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TcpSessionPage