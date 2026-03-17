import { BrowserRouter, Routes, Route } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import TcpDebugPage from './pages/protocol/TcpDebugPage'
import SessionManagePage from './pages/data/SessionManagePage'
import SessionDetailPage from './pages/data/SessionDetailPage'
import ParameterManagePage from './pages/data/ParameterManagePage'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="protocol/tcp" element={<TcpDebugPage />} />
          <Route path="data/session" element={<SessionManagePage />} />
          <Route path="data/session/:id" element={<SessionDetailPage />} />
          <Route path="data/parameter" element={<ParameterManagePage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App