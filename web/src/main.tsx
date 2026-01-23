import React from 'react'
import ReactDOM from 'react-dom/client'
import { ThemeProvider } from './components/theme-provider'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider storageKey="admin-ui-theme" defaultTheme="system">
      <App />
    </ThemeProvider>
  </React.StrictMode>,
)
