import { BrowserRouter, Routes, Route } from 'react-router-dom'
import MainLayout from './components/layout/MainLayout'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import TcpDebugPage from './pages/protocol/TcpDebugPage'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="protocol/tcp" element={<TcpDebugPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App