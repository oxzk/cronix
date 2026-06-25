import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import { authApi } from "@/lib/api";
import { storage } from "@/lib/storage";
import { LOGIN_PATH, buildLoginPath, isLoginPath, readProtectedPath } from "@/routes";

export interface SessionContextValue {
  /**
   * 当前是否已登录。
   */
  loggedIn: boolean;
  /**
   * 完成登录状态同步。
   */
  completeLogin: () => void;
  /**
   * 退出登录并清理本地会话。
   */
  logout: () => void;
}

export interface SessionProviderProps {
  /**
   * 需要访问会话状态的子节点。
   */
  children: ReactNode;
}

const SessionContext = createContext<SessionContextValue | null>(null);

/**
 * 登录会话状态提供器。
 */
export function SessionProvider({ children }: SessionProviderProps): JSX.Element {
  const [loggedIn, setLoggedIn] = useState(() => Boolean(storage.getToken()));
  const { toast } = useToast();
  const location = useLocation();
  const navigate = useNavigate();
  const unauthorizedHandledRef = useRef(false);

  useEffect(() => {
    if (!storage.getToken()) return;

    let ignore = false;

    /**
     * 校验本地令牌仍然可用。
     */
    async function validateSession(): Promise<void> {
      try {
        await authApi.me();
        if (!ignore) setLoggedIn(true);
      } catch {
        if (ignore) return;
        storage.removeToken();
        setLoggedIn(false);
      }
    }

    void validateSession();
    return () => {
      ignore = true;
    };
  }, []);

  useEffect(() => {
    const onUnauthorized = () => {
      if (unauthorizedHandledRef.current) return;
      unauthorizedHandledRef.current = true;
      storage.removeToken();
      setLoggedIn(false);
      if (!isLoginPath(location.pathname)) {
        navigate(buildLoginPath(readProtectedPath(location)), { replace: true });
        toast({ title: "登录已失效", description: "请重新登录", variant: "destructive" });
      }
    };
    window.addEventListener("cronix:unauthorized", onUnauthorized);
    return () => window.removeEventListener("cronix:unauthorized", onUnauthorized);
  }, [location, navigate, toast]);

  const completeLogin = useCallback((): void => {
    unauthorizedHandledRef.current = false;
    setLoggedIn(true);
  }, []);

  const logout = useCallback((): void => {
    unauthorizedHandledRef.current = false;
    storage.removeToken();
    setLoggedIn(false);
    navigate(LOGIN_PATH, { replace: true });
    toast({ title: "已退出登录" });
  }, [navigate, toast]);

  const value = useMemo<SessionContextValue>(() => ({ loggedIn, completeLogin, logout }), [completeLogin, loggedIn, logout]);

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

/**
 * 读取当前登录会话状态。
 */
export function useSession(): SessionContextValue {
  const value = useContext(SessionContext);
  if (!value) throw new Error("useSession must be used within SessionProvider");
  return value;
}
