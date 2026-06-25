import { Gauge, History, LogOut, Moon, Settings, Sun, Timer } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useSession } from "@/auth/session-provider";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { menuRoutes, resolveMenuRoute } from "@/routes";

const iconMap = {
  dashboard: Gauge,
  tasks: Timer,
  executions: History,
  settings: Settings,
};

export interface HeaderProps {
  /**
   * 是否启用暗色主题。
   */
  dark: boolean;
  /**
   * 切换主题回调。
   */
  onToggleTheme: () => void;
}

/**
 * 全局顶部导航。
 */
export function Header({ dark, onToggleTheme }: HeaderProps): JSX.Element {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useSession();
  const activeRoute = resolveMenuRoute(location.pathname);

  return (
    <header className="glass sticky top-0 z-40 w-full">
      <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between px-4 md:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <img src="/logo.svg" alt="" width="36" height="36" aria-hidden="true" className="h-9 w-9 shrink-0 rounded-lg" />
          <div className="truncate font-semibold tracking-normal">Cronix</div>
          <nav className="ml-2 hidden items-center gap-1 md:flex" aria-label="主菜单">
            {menuRoutes.map((route) => {
              const Icon = iconMap[route.key];
              return (
                <Button
                  key={route.key}
                  size="sm"
                  variant={activeRoute?.path === route.path ? "default" : "ghost"}
                  className="h-8 rounded-full"
                  aria-current={activeRoute?.path === route.path ? "page" : undefined}
                  onClick={() => navigate(route.path)}
                >
                  <Icon className="h-4 w-4" />
                  {route.label}
                </Button>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-1">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" onClick={onToggleTheme} aria-label="切换主题">
                {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
              </Button>
            </TooltipTrigger>
            <TooltipContent>切换主题</TooltipContent>
          </Tooltip>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" onClick={logout} aria-label="退出登录">
                <LogOut className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>退出登录</TooltipContent>
          </Tooltip>
        </div>
      </div>
      <nav className="mx-auto flex max-w-[1400px] items-center gap-1 px-4 pb-2 md:hidden" aria-label="主菜单">
        {menuRoutes.map((route) => {
          const Icon = iconMap[route.key];
          return (
            <Button
              key={route.key}
              size="sm"
              variant={activeRoute?.path === route.path ? "default" : "ghost"}
              className="h-8 flex-1 rounded-full px-2"
              aria-current={activeRoute?.path === route.path ? "page" : undefined}
              onClick={() => navigate(route.path)}
            >
              <Icon className="h-4 w-4" />
              <span className="hidden sm:inline">{route.label}</span>
            </Button>
          );
        })}
      </nav>
    </header>
  );
}
