import { History, Pencil, Play, Square, Trash2 } from "lucide-react";
import { EmptyState, TooltipIconButton } from "@/components/common";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { formatDateTime } from "@/lib/datetime";
import type { Task } from "@/types";

export interface TaskTableProps {
  /**
   * 任务列表。
   */
  tasks: Task[];
  /**
   * 是否首次加载中。
   */
  loading: boolean;
  /**
   * 正在运行的任务 ID 集合。
   */
  runningTaskIds: Set<number>;
  /**
   * 是否有任务操作正在提交。
   */
  actionPending: boolean;
  /**
   * 启停任务回调。
   */
  onToggle: (task: Task, isActive: boolean) => void;
  /**
   * 执行任务回调。
   */
  onExecute: (task: Task) => void;
  /**
   * 取消任务回调。
   */
  onCancel: (task: Task) => void;
  /**
   * 查看执行记录回调。
   */
  onExecutions: (task: Task) => void;
  /**
   * 编辑任务回调。
   */
  onEdit: (task: Task) => void;
  /**
   * 删除任务回调。
   */
  onDelete: (task: Task) => void;
}

/**
 * 任务列表表格。
 */
export function TaskTable({ tasks, loading, runningTaskIds, actionPending, onToggle, onExecute, onCancel, onExecutions, onEdit, onDelete }: TaskTableProps): JSX.Element {
  return (
    <div className="table-shell">
      <table className="data-table">
        <thead>
          <tr>
            <th>任务</th>
            <th>执行命令</th>
            <th>调度</th>
            <th>状态</th>
            <th>下次运行</th>
            <th>重试</th>
            <th className="w-48 text-right">操作</th>
          </tr>
        </thead>
        <tbody>
          {loading ? <TaskTableSkeleton /> : null}
          {tasks.map((task) => {
            const running = runningTaskIds.has(task.id);
            return (
              <tr key={task.id}>
                <td className="min-w-[16rem]">
                  <div className="font-medium">{task.name}</div>
                </td>
                <td className="w-[24rem] max-w-[24rem]">
                  <div className="truncate font-mono text-xs text-muted-foreground" title={task.command}>
                    {task.command}
                  </div>
                </td>
                <td className="font-mono text-xs">{task.cron_expression}</td>
                <td>
                  <div className="flex flex-wrap items-center gap-2">
                    <Switch checked={task.is_active} onCheckedChange={(checked) => onToggle(task, checked)} aria-label={task.is_active ? "停用任务" : "启用任务"} />
                    <span className="text-xs text-muted-foreground">{running ? "运行中" : task.is_active ? "启用" : "停用"}</span>
                  </div>
                </td>
                <td>{formatDateTime(task.next_run_time)}</td>
                <td>{task.retry_count} 次 / {task.retry_interval}s</td>
                <td>
                  <div className="flex justify-end gap-1">
                    <TooltipIconButton label="执行任务" variant="ghost" disabled={actionPending || running} onClick={() => onExecute(task)}>
                      <Play className="h-4 w-4" />
                    </TooltipIconButton>
                    <TooltipIconButton label="取消任务" variant="ghost" disabled={actionPending || !running} onClick={() => onCancel(task)}>
                      <Square className="h-4 w-4" />
                    </TooltipIconButton>
                    <TooltipIconButton label="执行记录" variant="ghost" onClick={() => onExecutions(task)}>
                      <History className="h-4 w-4" />
                    </TooltipIconButton>
                    <TooltipIconButton label="编辑任务" variant="ghost" onClick={() => onEdit(task)}>
                      <Pencil className="h-4 w-4" />
                    </TooltipIconButton>
                    <TooltipIconButton label="删除任务" variant="ghost" disabled={actionPending} onClick={() => onDelete(task)}>
                      <Trash2 className="h-4 w-4" />
                    </TooltipIconButton>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      {!loading && !tasks.length ? (
        <div className="p-4">
          <EmptyState title="暂无任务" description="点击新建任务开始配置调度。" />
        </div>
      ) : null}
    </div>
  );
}

/**
 * 任务表格骨架屏。
 */
function TaskTableSkeleton(): JSX.Element {
  return (
    <>
      {Array.from({ length: 8 }).map((_, index) => (
        <tr key={index}>
          <td>
            <Skeleton className="h-4 w-40" />
          </td>
          <td>
            <Skeleton className="h-4 w-72" />
          </td>
          <td>
            <Skeleton className="h-4 w-24" />
          </td>
          <td>
            <Skeleton className="h-6 w-24" />
          </td>
          <td>
            <Skeleton className="h-4 w-36" />
          </td>
          <td>
            <Skeleton className="h-4 w-20" />
          </td>
          <td>
            <div className="flex justify-end gap-1">
              <Skeleton className="h-8 w-8 rounded-md" />
              <Skeleton className="h-8 w-8 rounded-md" />
              <Skeleton className="h-8 w-8 rounded-md" />
              <Skeleton className="h-8 w-8 rounded-md" />
              <Skeleton className="h-8 w-8 rounded-md" />
            </div>
          </td>
        </tr>
      ))}
    </>
  );
}
