import { Navigate, type Location } from "react-router-dom";
import { DashboardPage } from "@/pages/dashboard";
import { ExecutionsPage } from "@/pages/executions";
import { SettingsPage } from "@/pages/settings";
import { TasksPage } from "@/pages/tasks";

export const ROOT_PATH = "/dashboard";
export const LOGIN_PATH = "/login";

export interface MenuRoute {
  /**
   * 菜单唯一标识。
   */
  key: "dashboard" | "tasks" | "executions" | "settings";
  /**
   * 菜单展示名称。
   */
  label: string;
  /**
   * 路由路径。
   */
  path: string;
  /**
   * 路由页面元素。
   */
  element: JSX.Element;
}

export const menuRoutes: MenuRoute[] = [
  { key: "dashboard", label: "概览", path: "/dashboard", element: <DashboardPage /> },
  { key: "tasks", label: "任务管理", path: "/tasks", element: <TasksPage /> },
  { key: "executions", label: "执行记录", path: "/executions", element: <ExecutionsPage /> },
  { key: "settings", label: "系统设置", path: "/settings", element: <SettingsPage /> },
];

/**
 * 根路径重定向。
 */
export function RootRedirect(): JSX.Element {
  return <Navigate to={ROOT_PATH} replace />;
}

/**
 * 判断是否登录路径。
 */
export function isLoginPath(pathname: string): boolean {
  return pathname === LOGIN_PATH;
}

/**
 * 构建登录跳转路径。
 */
export function buildLoginPath(redirect: string): string {
  return `${LOGIN_PATH}?redirect=${encodeURIComponent(sanitizeRedirectPath(redirect))}`;
}

/**
 * 规范化登录后的站内跳转路径。
 */
export function sanitizeRedirectPath(redirect: string | null | undefined): string {
  if (!redirect) return ROOT_PATH;
  if (!redirect.startsWith("/") || redirect.startsWith("//")) return ROOT_PATH;
  if (/[\u0000-\u001F\u007F]/.test(redirect)) return ROOT_PATH;
  if (redirect === LOGIN_PATH) return ROOT_PATH;
  return redirect;
}

/**
 * 读取受保护页面路径。
 */
export function readProtectedPath(location: Location): string {
  return `${location.pathname}${location.search}`;
}

/**
 * 将绝对路径转换为嵌套路由路径。
 */
export function toNestedRoutePath(path: string): string {
  return path.replace(/^\//, "");
}

/**
 * 匹配当前菜单路由。
 */
export function resolveMenuRoute(pathname: string): MenuRoute | undefined {
  return menuRoutes.find((route) => pathname === route.path || pathname.startsWith(`${route.path}/`));
}
