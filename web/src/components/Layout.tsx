import { useState } from 'react'
import { Outlet, NavLink, useLocation } from 'react-router-dom'
import { 
  Video, 
  MessageSquare, 
  Database, 
  Link2, 
  Settings, 
  Menu, 
  X,
  Moon,
  Sun,
  ChevronLeft,
  ChevronRight,
  FileText
} from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { cn } from '@/lib/utils'

const navigation = [
  { name: '视频下载', href: '/video', icon: Video },
  { name: 'AI 对话', href: '/chat', icon: MessageSquare },
  { name: '链接分析', href: '/link', icon: Link2 },
  { name: '知识库', href: '/knowledge', icon: Database },
  { name: '日志', href: '/logs', icon: FileText },
]

export default function Layout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const { sidebarCollapsed, toggleSidebar, theme, toggleTheme } = useAppStore()
  const location = useLocation()

  return (
    <div className="min-h-screen bg-background">
      {/* 移动端顶部导航 */}
      <div className="lg:hidden flex items-center justify-between p-4 border-b bg-card">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Video className="w-5 h-5 text-primary-foreground" />
          </div>
          <span className="font-bold text-lg">SuperBizAgent</span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-lg hover:bg-muted"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* 移动端菜单 */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-50 bg-background pt-16">
          <nav className="p-4 space-y-2">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted'
                  )
                }
              >
                <item.icon className="w-5 h-5" />
                <span className="font-medium">{item.name}</span>
              </NavLink>
            ))}
            <NavLink
              to="/settings"
              onClick={() => setMobileMenuOpen(false)}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-muted'
                )
              }
            >
              <Settings className="w-5 h-5" />
              <span className="font-medium">设置</span>
            </NavLink>
          </nav>
        </div>
      )}

      <div className="flex h-screen overflow-hidden">
        {/* 侧边栏 - 桌面端 */}
        <aside
          className={cn(
            'hidden lg:flex flex-col border-r bg-card transition-all duration-300',
            sidebarCollapsed ? 'w-16' : 'w-64'
          )}
        >
          {/* Logo区域 */}
          <div className="flex items-center justify-between p-4 border-b h-16">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
                <Video className="w-5 h-5 text-primary-foreground" />
              </div>
              {!sidebarCollapsed && (
                <span className="font-bold text-lg whitespace-nowrap">SuperBizAgent</span>
              )}
            </div>
            <button
              onClick={toggleSidebar}
              className="p-1 rounded hover:bg-muted flex-shrink-0"
            >
              {sidebarCollapsed ? (
                <ChevronRight className="w-4 h-4" />
              ) : (
                <ChevronLeft className="w-4 h-4" />
              )}
            </button>
          </div>

          {/* 导航菜单 */}
          <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'hover:bg-muted text-muted-foreground hover:text-foreground',
                    sidebarCollapsed && 'justify-center px-2'
                  )
                }
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!sidebarCollapsed && <span className="font-medium whitespace-nowrap">{item.name}</span>}
              </NavLink>
            ))}
          </nav>

          {/* 底部操作区 */}
          <div className="p-3 border-t space-y-1">
            {/* 主题切换 */}
            <button
              onClick={toggleTheme}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors w-full hover:bg-muted text-muted-foreground hover:text-foreground',
                sidebarCollapsed && 'justify-center px-2'
              )}
            >
              {theme === 'dark' ? (
                <Sun className="w-5 h-5 flex-shrink-0" />
              ) : (
                <Moon className="w-5 h-5 flex-shrink-0" />
              )}
              {!sidebarCollapsed && <span className="font-medium whitespace-nowrap">{theme === 'dark' ? '浅色模式' : '深色模式'}</span>}
            </button>

            {/* 设置 */}
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-muted text-muted-foreground hover:text-foreground',
                  sidebarCollapsed && 'justify-center px-2'
                )
              }
            >
              <Settings className="w-5 h-5 flex-shrink-0" />
              {!sidebarCollapsed && <span className="font-medium whitespace-nowrap">设置</span>}
            </NavLink>
          </div>
        </aside>

        {/* 主内容区 */}
        <main className="flex-1 overflow-hidden flex flex-col">
          {/* 页面标题栏 */}
          <header className="flex items-center justify-between px-6 py-4 border-b bg-card h-16 flex-shrink-0">
            <h1 className="text-xl font-semibold">
              {navigation.find(n => n.href === location.pathname)?.name || '设置'}
            </h1>
            <div className="flex items-center gap-4">
              {/* 可以在这里添加全局操作按钮 */}
            </div>
          </header>

          {/* 页面内容 */}
          <div className="flex-1 overflow-auto p-6">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
