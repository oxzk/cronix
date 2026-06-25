import axios, { AxiosError, type AxiosInstance } from "axios";
import { storage } from "@/lib/storage";
import type {
  ApiResponse,
  Execution,
  ExecutionStatus,
  NotificationPayload,
  NotificationSetting,
  PaginatedResponse,
  SettingsUser,
  Task,
  TaskPayload,
  TaskStats,
  TokenResponse,
  User,
} from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "";
const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api";

/**
 * 创建 HTTP 客户端。
 */
function createHttpClient(): AxiosInstance {
  const instance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 60000,
  });

  instance.interceptors.request.use((config) => {
    const token = storage.getToken();
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  });

  instance.interceptors.response.use(
    (response) => response,
    (error: AxiosError<ApiResponse<unknown>>) => {
      if (error.response?.status === 401) {
        storage.removeToken();
        window.dispatchEvent(new CustomEvent("cronix:unauthorized"));
      }
      return Promise.reject(error);
    },
  );

  return instance;
}

const http = createHttpClient();

/**
 * 清理空查询参数。
 */
function compactParams(params: Record<string, unknown>): Record<string, unknown> {
  return Object.fromEntries(Object.entries(params).filter(([, value]) => value !== undefined && value !== null && value !== ""));
}

/**
 * 提取统一响应数据。
 */
async function unwrap<T>(request: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  const response = await request;
  if (response.data.code !== 0) throw new Error(response.data.message);
  return response.data.data as T;
}

/**
 * 提取错误消息。
 */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiResponse<unknown>>(error)) {
    return error.response?.data?.message || error.message || "请求失败";
  }
  if (error instanceof Error) return error.message;
  return "请求失败";
}

/**
 * 认证接口。
 */
export const authApi = {
  /**
   * 用户名密码登录。
   */
  login(username: string, password: string): Promise<TokenResponse> {
    return unwrap<TokenResponse>(http.post(`${API_PREFIX}/auth/login`, { username, password }));
  },

  /**
   * 读取当前用户。
   */
  me(): Promise<User> {
    return unwrap<User>(http.get(`${API_PREFIX}/auth/me`));
  },
};

/**
 * 统计接口。
 */
export const statsApi = {
  /**
   * 查询任务统计摘要。
   */
  tasksSummary(): Promise<TaskStats> {
    return unwrap<TaskStats>(http.get(`${API_PREFIX}/stats/tasks/summary`));
  },
};

/**
 * 任务接口。
 */
export const tasksApi = {
  list(query: { page?: number; page_size?: number; name?: string; is_active?: boolean | "" } = {}): Promise<PaginatedResponse<Task>> {
    return unwrap<PaginatedResponse<Task>>(http.get(`${API_PREFIX}/tasks`, { params: compactParams(query) }));
  },
  create(payload: TaskPayload): Promise<Task> {
    return unwrap<Task>(http.post(`${API_PREFIX}/tasks`, payload));
  },
  update(taskId: number, payload: TaskPayload): Promise<Task> {
    return unwrap<Task>(http.put(`${API_PREFIX}/tasks/${taskId}`, payload));
  },
  delete(taskId: number): Promise<null> {
    return unwrap<null>(http.delete(`${API_PREFIX}/tasks/${taskId}`));
  },
  execute(taskId: number): Promise<null> {
    return unwrap<null>(http.post(`${API_PREFIX}/tasks/${taskId}/execute`));
  },
  cancel(taskId: number): Promise<null> {
    return unwrap<null>(http.post(`${API_PREFIX}/tasks/${taskId}/cancel`));
  },
  listRunning(): Promise<number[]> {
    return unwrap<number[]>(http.get(`${API_PREFIX}/tasks/running/list`));
  },
};

/**
 * 执行记录接口。
 */
export const executionsApi = {
  list(query: { page?: number; page_size?: number; task_id?: number | ""; status?: ExecutionStatus | "" } = {}): Promise<PaginatedResponse<Execution>> {
    return unwrap<PaginatedResponse<Execution>>(http.get(`${API_PREFIX}/executions`, { params: compactParams(query) }));
  },
  get(executionId: number): Promise<Execution> {
    return unwrap<Execution>(http.get(`${API_PREFIX}/executions/${executionId}`));
  },
};

/**
 * 系统设置接口。
 */
export const settingsApi = {
  /**
   * 查询系统用户。
   */
  listUsers(): Promise<SettingsUser[]> {
    return unwrap<SettingsUser[]>(http.get(`${API_PREFIX}/settings/users`));
  },

  /**
   * 创建系统用户。
   */
  createUser(payload: { username: string; password: string }): Promise<SettingsUser> {
    return unwrap<SettingsUser>(http.post(`${API_PREFIX}/settings/users`, payload));
  },

  /**
   * 更新系统用户。
   */
  updateUser(userId: number, payload: { username?: string; password?: string }): Promise<SettingsUser> {
    return unwrap<SettingsUser>(http.put(`${API_PREFIX}/settings/users/${userId}`, payload));
  },

  /**
   * 删除系统用户。
   */
  deleteUser(userId: number): Promise<null> {
    return unwrap<null>(http.delete(`${API_PREFIX}/settings/users/${userId}`));
  },

  /**
   * 查询通知配置。
   */
  listNotifications(): Promise<NotificationSetting[]> {
    return unwrap<NotificationSetting[]>(http.get(`${API_PREFIX}/settings/notifications`));
  },

  /**
   * 创建通知配置。
   */
  createNotification(payload: NotificationPayload): Promise<NotificationSetting> {
    return unwrap<NotificationSetting>(http.post(`${API_PREFIX}/settings/notifications`, payload));
  },

  /**
   * 更新通知配置。
   */
  updateNotification(notificationId: number, payload: NotificationPayload): Promise<NotificationSetting> {
    return unwrap<NotificationSetting>(http.put(`${API_PREFIX}/settings/notifications/${notificationId}`, payload));
  },
};
