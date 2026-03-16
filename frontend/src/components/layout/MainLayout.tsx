import { Outlet } from 'react-router-dom'
import Header from './Header'
import Sidebar from './Sidebar'

const MainLayout = () => {
  return (
    <div className="h-screen flex flex-col overflow-hidden bg-panel-bg">
      {/* 顶部导航 */}
      <Header />
      
      {/* 主内容区 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧边栏 */}
        <Sidebar />
        
        {/* 内容区域 */}
        <main className="flex-1 overflow-hidden p-4">
          <div className="h-full overflow-y-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}

export default MainLayout