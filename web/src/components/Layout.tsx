import { useState } from 'react'
import { Outlet, Link, useLocation } from 'react-router-dom'
import { Button } from './ui/button'
import { ThemeToggle } from './theme-toggle'
import {
  LayoutDashboard,
  Users,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  Menu,
  Home,
  UserCog,
  ChevronDown,
  FolderKanban,
  PlayCircle,
  FileCode,
  ListChecks,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface MenuItem {
  id: string
  label: string
  icon: React.ReactNode
  path?: string
  children?: MenuItem[]
}

const menuItems: MenuItem[] = [
  {
    id: 'dashboard',
    label: '仪表盘',
    icon: <LayoutDashboard className="h-5 w-5" />,
    path: '/',
  },
  {
    id: 'tasks',
    label: '任务管理',
    icon: <PlayCircle className="h-5 w-5" />,
    path: '/tasks',
  },
  {
    id: 'executions',
    label: '执行记录',
    icon: <ListChecks className="h-5 w-5" />,
    path: '/executions',
  },
  {
    id: 'scripts',
    label: '脚本管理',
    icon: <FileCode className="h-5 w-5" />,
    path: '/scripts',
  },
  {
    id: 'settings',
    label: '系统设置',
    icon: <Settings className="h-5 w-5" />,
    path: '/settings',
  },
]

interface SidebarProps {
  isCollapsed: boolean
  onToggle: () => void
}

function Sidebar({ isCollapsed, onToggle }: SidebarProps) {
  const location = useLocation()
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set())

  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedItems)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedItems(newExpanded)
  }

  const isActive = (path?: string) => {
    if (!path) return false
    return location.pathname === path
  }

  const renderMenuItem = (item: MenuItem, level: number = 0) => {
    const hasChildren = item.children && item.children.length > 0
    const isExpanded = expandedItems.has(item.id)

    return (
      <div key={item.id}>
        <Link
          to={item.path || '#'}
          onClick={(e) => {
            if (hasChildren) {
              e.preventDefault()
              toggleExpand(item.id)
            }
          }}
          className={`
            flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
            ${isActive(item.path) 
              ? 'bg-primary text-primary-foreground font-medium' 
              : 'text-muted-foreground hover:bg-accent hover:text-foreground'
            }
            ${isCollapsed && level === 0 ? 'justify-center' : ''}
          `}
        >
          {item.icon}
          {!isCollapsed && (
            <>
              <span className="flex-1 text-left">{item.label}</span>
              {hasChildren && (
                <ChevronDown 
                  className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
                />
              )}
            </>
          )}
        </Link>
        {hasChildren && isExpanded && !isCollapsed && (
          <div className="ml-4 mt-1 space-y-1">
            {item.children!.map((child) => renderMenuItem(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <aside
      className={`
        fixed left-0 top-0 h-screen bg-card border-r border-border
        transition-all duration-300 ease-in-out z-50
        ${isCollapsed ? 'w-16' : 'w-64'}
      `}
    >
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className={`flex items-center gap-3 ${isCollapsed ? 'justify-center w-full' : ''}`}>
            <div className="w-8 h-8 bg-gradient-to-br from-primary to-primary/70 rounded-lg flex items-center justify-center shadow-md">
              <svg className="w-5 h-5 text-primary-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            {!isCollapsed && (
              <span className="font-bold text-lg">管理后台</span>
            )}
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {menuItems.map((item) => renderMenuItem(item))}
        </nav>

        <div className="p-3 border-t border-border">
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className={isCollapsed ? 'w-full justify-center' : 'w-full justify-start'}
          >
            {isCollapsed ? (
              <ChevronRight className="h-5 w-5" />
            ) : (
              <>
                <ChevronLeft className="h-5 w-5 mr-2" />
                <span>收起菜单</span>
              </>
            )}
          </Button>
        </div>
      </div>
    </aside>
  )
}

interface HeaderProps {
  onLogout: () => void
}

function Header({ onLogout }: HeaderProps) {
  return (
    <header className="h-16 border-b border-border bg-card/80 backdrop-blur-sm sticky top-0 z-40">
      <div className="h-full px-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" className="lg:hidden">
            <Menu className="h-5 w-5" />
          </Button>
          <nav className="hidden sm:flex items-center gap-2 text-sm">
            <Link to="/" className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-accent transition-colors">
              <Home className="h-4 w-4" />
              <span>首页</span>
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Button variant="ghost" size="icon" onClick={onLogout}>
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  )
}

export default function Layout() {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const navigate = useNavigate()

  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated')
    localStorage.removeItem('auth_token')
    window.dispatchEvent(new Event('authChange'))
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar 
        isCollapsed={isSidebarCollapsed} 
        onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)} 
      />
      <main
        className={`
          transition-all duration-300 ease-in-out
          ${isSidebarCollapsed ? 'ml-16' : 'ml-64'}
        `}
      >
        <Header onLogout={handleLogout} />
        <div className="p-6">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
