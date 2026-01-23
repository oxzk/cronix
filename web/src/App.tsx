import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Users from './pages/Users'
import Layout from './components/Layout'

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem('isAuthenticated') === 'true'
  })

  useEffect(() => {
    const handleAuthChange = () => {
      setIsAuthenticated(localStorage.getItem('isAuthenticated') === 'true')
    }

    window.addEventListener('storage', handleAuthChange)
    
    // 监听自定义事件
    window.addEventListener('authChange', handleAuthChange)
    
    return () => {
      window.removeEventListener('storage', handleAuthChange)
      window.removeEventListener('authChange', handleAuthChange)
    }
  }, [])

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={isAuthenticated ? <Layout /> : <Navigate to="/login" />}>
          <Route index element={<Dashboard />} />
          <Route path="users" element={<Users />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
