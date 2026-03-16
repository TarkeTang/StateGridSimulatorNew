import { NavLink } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Activity, 
  Settings,
  Database,
  LineChart,
  Zap
} from 'lucide-react'

const navItems = [
  { path: '/', label: '首页', icon: LayoutDashboard },
  { path: '/dashboard', label: '控制面板', icon: Activity },
  { path: '/data', label: '数据管理', icon: Database },
  { path: '/analysis', label: '数据分析', icon: LineChart },
  { path: '/power', label: '电力监控', icon: Zap },
  { path: '/settings', label: '系统设置', icon: Settings },
]

const Sidebar = () => {
  return (
    <aside className="w-56 flex-shrink-0 bg-panel-card border-r border-panel-border flex flex-col">
      {/* 导航菜单 */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded transition-all duration-200 ${
                isActive
                  ? 'bg-industrial-700 text-signal-blue'
                  : 'text-gray-400 hover:bg-industrial-800 hover:text-white'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="text-sm">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* 底部信息 */}
      <div className="p-3 border-t border-panel-border">
        <div className="text-xs text-gray-500">
          <p>Version 1.0.0</p>
          <p className="mt-1">© 2026 State Grid</p>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar