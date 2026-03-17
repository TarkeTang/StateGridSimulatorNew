import { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  LayoutDashboard,
  Activity,
  Settings,
  Database,
  LineChart,
  Zap,
  ChevronDown,
  ChevronRight,
  Cpu,
  Network,
  Usb,
  Radio,
  Server,
  Variable,
} from 'lucide-react'

interface NavItem {
  path?: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  children?: NavItem[]
}

const navItems: NavItem[] = [
  { path: '/', label: '首页', icon: LayoutDashboard },
  { path: '/dashboard', label: '控制面板', icon: Activity },
  {
    label: '数据管理',
    icon: Database,
    children: [
      { path: '/data/session', label: '会话管理', icon: Server },
      { path: '/data/parameter', label: '参数化', icon: Variable },
    ],
  },
  { path: '/analysis', label: '数据分析', icon: LineChart },
  { path: '/power', label: '电力监控', icon: Zap },
  {
    label: '协议调试',
    icon: Cpu,
    children: [
      { path: '/protocol/tcp', label: 'TCP传输协议', icon: Network },
      { path: '/protocol/serial', label: '串口通信', icon: Usb },
      { path: '/protocol/modbus', label: 'Modbus协议', icon: Radio },
    ],
  },
  { path: '/settings', label: '系统设置', icon: Settings },
]

const Sidebar = () => {
  const location = useLocation()
  const [expandedMenus, setExpandedMenus] = useState<string[]>(['数据管理', '协议调试'])

  const toggleMenu = (label: string) => {
    setExpandedMenus((prev) =>
      prev.includes(label)
        ? prev.filter((item) => item !== label)
        : [...prev, label]
    )
  }

  const isMenuActive = (item: NavItem): boolean => {
    if (item.path && location.pathname === item.path) {
      return true
    }
    if (item.children) {
      return item.children.some((child) => child.path === location.pathname)
    }
    return false
  }

  const isChildActive = (child: NavItem): boolean => {
    return child.path === location.pathname
  }

  return (
    <aside className="w-56 flex-shrink-0 bg-panel-card border-r border-panel-border flex flex-col">
      {/* 导航菜单 */}
      <nav className="flex-1 p-3 space-y-1">
        {navItems.map((item) => (
          <div key={item.label}>
            {item.children ? (
              // 有子菜单的一级菜单
              <>
                <button
                  onClick={() => toggleMenu(item.label)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded transition-all duration-200 ${
                    isMenuActive(item)
                      ? 'bg-industrial-700 text-signal-blue'
                      : 'text-gray-400 hover:bg-industrial-800 hover:text-white'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <item.icon className="w-5 h-5" />
                    <span className="text-sm">{item.label}</span>
                  </div>
                  {expandedMenus.includes(item.label) ? (
                    <ChevronDown className="w-4 h-4" />
                  ) : (
                    <ChevronRight className="w-4 h-4" />
                  )}
                </button>
                {/* 二级菜单 */}
                {expandedMenus.includes(item.label) && (
                  <div className="ml-4 mt-1 space-y-1 border-l border-panel-border pl-2">
                    {item.children.map((child) => (
                      <NavLink
                        key={child.path}
                        to={child.path!}
                        className={`flex items-center gap-3 px-3 py-2 rounded transition-all duration-200 ${
                          isChildActive(child)
                            ? 'bg-industrial-700 text-signal-blue'
                            : 'text-gray-400 hover:bg-industrial-800 hover:text-white'
                        }`}
                      >
                        <child.icon className="w-4 h-4" />
                        <span className="text-sm">{child.label}</span>
                      </NavLink>
                    ))}
                  </div>
                )}
              </>
            ) : (
              // 无子菜单的一级菜单
              <NavLink
                to={item.path!}
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
            )}
          </div>
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