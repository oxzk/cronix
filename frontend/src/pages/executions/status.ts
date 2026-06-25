import type { ExecutionStatus } from "@/types";

/**
 * 执行状态中文文案。
 */
export function executionStatusLabel(status: ExecutionStatus): string {
  const labels: Record<ExecutionStatus, string> = {
    pending: "等待中",
    running: "运行中",
    success: "成功",
    failed: "失败",
    timeout: "超时",
    cancelled: "已取消",
  };
  return labels[status];
}

/**
 * 执行状态徽标样式。
 */
export function executionStatusVariant(status: ExecutionStatus): "default" | "secondary" | "destructive" | "outline" {
  if (status === "success") return "default";
  if (status === "failed" || status === "timeout") return "destructive";
  if (status === "running") return "outline";
  return "secondary";
}
