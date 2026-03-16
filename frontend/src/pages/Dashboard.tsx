import { useState, useEffect } from 'react'
import { Panel, Button } from '@/components/ui'
import { Play, Pause, RotateCcw, Download } from 'lucide-react'

const Dashboard = () => {
  const [isRunning, setIsRunning] = useState(false)
  const [time, setTime] = useState(0)

  useEffect(() => {
    let interval: NodeJS.Timeout
    if (isRunning) {
      interval = setInterval(() => {
        setTime((t) => t + 1)
      }, 1000)
    }
    return () => clearInterval(interval)
  }, [isRunning])

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* 控制面板 */}
      <Panel title="仿真控制">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="text-center">
              <p className="data-label">运行时间</p>
              <p className="font-mono text-3xl text-signal-blue mt-1">{formatTime(time)}</p>
            </div>
            <div className="h-12 w-px bg-panel-border" />
            <div className="text-center">
              <p className="data-label">仿真状态</p>
              <p className={`mt-1 ${isRunning ? 'text-signal-green' : 'text-gray-400'}`}>
                {isRunning ? '运行中' : '已停止'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant={isRunning ? 'danger' : 'success'}
              onClick={() => setIsRunning(!isRunning)}
            >
              {isRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              {isRunning ? '暂停' : '启动'}
            </Button>
            <Button variant="secondary" onClick={() => { setIsRunning(false); setTime(0) }}>
              <RotateCcw className="w-4 h-4" />
              重置
            </Button>
            <Button variant="secondary">
              <Download className="w-4 h-4" />
              导出
            </Button>
          </div>
        </div>
      </Panel>

      {/* 数据监控 */}
      <div className="grid grid-cols-3 gap-4">
        <Panel title="电压监测">
          <div className="space-y-3">
            {[
              { name: 'A相电压', value: 220.5, unit: 'V', status: 'normal' },
              { name: 'B相电压', value: 219.8, unit: 'V', status: 'normal' },
              { name: 'C相电压', value: 221.2, unit: 'V', status: 'normal' },
            ].map((item) => (
              <div key={item.name} className="flex items-center justify-between">
                <span className="text-gray-400">{item.name}</span>
                <span className="font-mono text-signal-green">
                  {item.value} {item.unit}
                </span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="电流监测">
          <div className="space-y-3">
            {[
              { name: 'A相电流', value: 15.2, unit: 'A', status: 'normal' },
              { name: 'B相电流', value: 14.8, unit: 'A', status: 'normal' },
              { name: 'C相电流', value: 15.5, unit: 'A', status: 'normal' },
            ].map((item) => (
              <div key={item.name} className="flex items-center justify-between">
                <span className="text-gray-400">{item.name}</span>
                <span className="font-mono text-signal-blue">
                  {item.value} {item.unit}
                </span>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="功率监测">
          <div className="space-y-3">
            {[
              { name: '有功功率', value: 2450, unit: 'MW', status: 'normal' },
              { name: '无功功率', value: 320, unit: 'MVar', status: 'normal' },
              { name: '功率因数', value: 0.95, unit: '', status: 'normal' },
            ].map((item) => (
              <div key={item.name} className="flex items-center justify-between">
                <span className="text-gray-400">{item.name}</span>
                <span className="font-mono text-signal-yellow">
                  {item.value} {item.unit}
                </span>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      {/* 图表区域占位 */}
      <Panel title="实时曲线">
        <div className="h-64 flex items-center justify-center text-gray-500">
          实时数据曲线图表区域（待接入 ECharts/Recharts）
        </div>
      </Panel>
    </div>
  )
}

export default Dashboard