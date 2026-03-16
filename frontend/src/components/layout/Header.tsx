import { Activity, Settings, User } from 'lucide-react'

const Header = () => {
  return (
    <header className="h-14 flex-shrink-0 bg-panel-card border-b border-panel-border flex items-center justify-between px-4">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-gradient-to-br from-signal-blue to-signal-green flex items-center justify-center">
          <Activity className="w-5 h-5 text-industrial-950" />
        </div>
        <h1 className="font-display text-lg tracking-wider text-white">
          State Grid Simulator
        </h1>
      </div>

      {/* 右侧工具栏 */}
      <div className="flex items-center gap-4">
        {/* 系统状态 */}
        <div className="flex items-center gap-2">
          <span className="status-indicator online" />
          <span className="text-sm text-gray-400">系统在线</span>
        </div>

        {/* 用户信息 */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded bg-industrial-800">
          <User className="w-4 h-4 text-gray-400" />
          <span className="text-sm">Admin</span>
        </div>

        {/* 设置按钮 */}
        <button className="p-2 rounded hover:bg-industrial-700 transition-colors">
          <Settings className="w-5 h-5 text-gray-400" />
        </button>
      </div>
    </header>
  )
}

export default Header