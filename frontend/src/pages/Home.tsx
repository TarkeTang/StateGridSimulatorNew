import { Activity, Zap, Database, TrendingUp } from 'lucide-react'
import { Panel } from '@/components/ui'

const Home = () => {
  const stats = [
    { label: '在线设备', value: '128', unit: '台', icon: Activity, color: 'text-signal-green' },
    { label: '实时功率', value: '2,450', unit: 'MW', icon: Zap, color: 'text-signal-blue' },
    { label: '数据节点', value: '1,024', unit: '个', icon: Database, color: 'text-signal-yellow' },
    { label: '系统效率', value: '98.5', unit: '%', icon: TrendingUp, color: 'text-signal-green' },
  ]

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* 欢迎区域 */}
      <div className="panel p-6">
        <h1 className="text-2xl font-display tracking-wider text-white mb-2">
          欢迎使用电网模拟系统
        </h1>
        <p className="text-gray-400">
          实时监控电网运行状态，进行电力系统仿真分析
        </p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Panel key={stat.label}>
            <div className="flex items-center justify-between">
              <div>
                <p className="data-label">{stat.label}</p>
                <p className="data-value highlight mt-1">
                  {stat.value}
                  <span className="text-sm text-gray-400 ml-1">{stat.unit}</span>
                </p>
              </div>
              <stat.icon className={`w-10 h-10 ${stat.color} opacity-50`} />
            </div>
          </Panel>
        ))}
      </div>

      {/* 快速操作 */}
      <div className="grid grid-cols-2 gap-4">
        <Panel title="系统状态">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-400">数据库连接</span>
              <div className="flex items-center gap-2">
                <span className="status-indicator online" />
                <span className="text-signal-green text-sm">正常</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">Redis 缓存</span>
              <div className="flex items-center gap-2">
                <span className="status-indicator online" />
                <span className="text-signal-green text-sm">正常</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-400">消息队列</span>
              <div className="flex items-center gap-2">
                <span className="status-indicator warning" />
                <span className="text-signal-yellow text-sm">警告</span>
              </div>
            </div>
          </div>
        </Panel>

        <Panel title="最近活动">
          <div className="space-y-3">
            {[
              { time: '15:30:25', event: '用户登录成功', type: 'info' },
              { time: '15:28:10', event: '数据同步完成', type: 'success' },
              { time: '15:25:00', event: '系统启动', type: 'info' },
            ].map((log, index) => (
              <div key={index} className="flex items-center gap-3 text-sm">
                <span className="text-gray-500 font-mono">{log.time}</span>
                <span className={log.type === 'success' ? 'text-signal-green' : 'text-gray-300'}>
                  {log.event}
                </span>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  )
}

export default Home