import { BrowserRouter, Routes, Route } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import TcpDebugPage from './pages/protocol/TcpDebugPage'
import TcpSessionPage from './pages/data/TcpSessionPage'
import SessionDetailPage from './pages/data/SessionDetailPage'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="protocol/tcp" element={<TcpDebugPage />} />
          <Route path="data/tcp-session" element={<TcpSessionPage />} />
          <Route path="data/session/:id" element={<SessionDetailPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App