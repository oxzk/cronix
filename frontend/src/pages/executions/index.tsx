import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Eye, Search } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { EmptyState, SectionHeader, TooltipIconButton } from "@/components/common";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { getErrorMessage, executionsApi } from "@/lib/api";
import { formatDateTime, formatDuration } from "@/lib/datetime";
import { executionStatusLabel, executionStatusVariant } from "@/pages/executions/status";
import type { Execution, ExecutionStatus } from "@/types";

const statusOptions: Array<{ value: ExecutionStatus | ""; label: string }> = [
  { value: "", label: "全部状态" },
  { value: "pending", label: "等待中" },
  { value: "running", label: "运行中" },
  { value: "success", label: "成功" },
  { value: "failed", label: "失败" },
  { value: "timeout", label: "超时" },
  { value: "cancelled", label: "已取消" },
];

/**
 * 执行记录页面。
 */
export function ExecutionsPage(): JSX.Element {
  const [page, setPage] = useState(1);
  const [searchParams, setSearchParams] = useSearchParams();
  const [taskId, setTaskId] = useState(() => searchParams.get("task_id") ?? "");
  const [status, setStatus] = useState<ExecutionStatus | "">("");
  const [selected, setSelected] = useState<Execution | null>(null);
  const debouncedTaskId = useDebouncedValue(taskId, 300);
  const query = useQuery({
    queryKey: ["executions", page, debouncedTaskId, status],
    queryFn: () => executionsApi.list({ page, page_size: 20, task_id: debouncedTaskId ? Number(debouncedTaskId) : "", status }),
    refetchInterval: status === "running" ? 3000 : false,
  });

  useEffect(() => {
    setTaskId(searchParams.get("task_id") ?? "");
    setPage(1);
  }, [searchParams]);

  useEffect(() => {
    setPage(1);
  }, [debouncedTaskId, status]);

  /**
   * 更新任务 ID 筛选条件。
   */
  function updateTaskId(value: string): void {
    setTaskId(value);
    const nextParams = new URLSearchParams(searchParams);
    if (value) {
      nextParams.set("task_id", value);
    } else {
      nextParams.delete("task_id");
    }
    setSearchParams(nextParams, { replace: true });
  }

  return (
    <div className="space-y-4">
      <SectionHeader title="执行记录" description="查询任务运行历史, 输出和错误信息。" loading={query.isFetching} onRefresh={() => void query.refetch()} />
      {query.error ? <EmptyState title="执行记录加载失败" description={getErrorMessage(query.error)} /> : null}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-end">
        <div className="relative md:w-64">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input value={taskId} onChange={(event) => updateTaskId(event.target.value)} placeholder="按任务 ID 查询" className="pl-9" />
        </div>
        <Select value={status} onValueChange={(value) => setStatus(value as ExecutionStatus | "")} options={statusOptions} className="md:w-36" />
      </div>
      <div className="table-shell">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>任务</th>
              <th>状态</th>
              <th>开始时间</th>
              <th>结束时间</th>
              <th>耗时</th>
              <th className="text-right">详情</th>
            </tr>
          </thead>
          <tbody>
            {query.isLoading ? <ExecutionTableSkeleton /> : null}
            {(query.data?.items ?? []).map((item) => (
              <tr key={item.id}>
                <td>#{item.id}</td>
                <td>{item.task?.name ?? `任务 #${item.task_id}`}</td>
                <td>
                  <Badge variant={executionStatusVariant(item.status)}>{executionStatusLabel(item.status)}</Badge>
                </td>
                <td>{formatDateTime(item.started_at)}</td>
                <td>{formatDateTime(item.finished_at)}</td>
                <td>{formatDuration(item.duration)}</td>
                <td>
                  <div className="flex justify-end">
                    <TooltipIconButton label="查看详情" variant="ghost" onClick={() => setSelected(item)}>
                      <Eye className="h-4 w-4" />
                    </TooltipIconButton>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!query.isLoading && !query.data?.items.length ? (
          <div className="p-4">
            <EmptyState title="暂无执行记录" />
          </div>
        ) : null}
      </div>
      <div className="flex items-center justify-end gap-2">
        <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
          上一页
        </Button>
        <div className="text-sm text-muted-foreground">第 {query.data?.page ?? page} 页, 共 {query.data?.total ?? 0} 条</div>
        <Button variant="outline" size="sm" disabled={!query.data || page * query.data.page_size >= query.data.total} onClick={() => setPage((value) => value + 1)}>
          下一页
        </Button>
      </div>

      <Dialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>执行详情</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4">
            <div className="grid gap-3 text-sm md:grid-cols-2">
              <div>
                <span className="text-muted-foreground">任务: </span>
                <span className="font-medium">{selected?.task?.name ?? selected?.task_id}</span>
              </div>
              <div>
                <span className="text-muted-foreground">状态: </span>
                <span className="font-medium">{selected ? executionStatusLabel(selected.status) : "-"}</span>
              </div>
              <div>
                <span className="text-muted-foreground">开始: </span>
                <span>{formatDateTime(selected?.started_at)}</span>
              </div>
              <div>
                <span className="text-muted-foreground">结束: </span>
                <span>{formatDateTime(selected?.finished_at)}</span>
              </div>
            </div>
            <div>
              <div className="field-label mb-2">输出</div>
              <pre className="code-block">{selected?.output || "-"}</pre>
            </div>
            <div>
              <div className="field-label mb-2">错误</div>
              <pre className="code-block">{selected?.error || "-"}</pre>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

/**
 * 执行记录表格骨架屏。
 */
function ExecutionTableSkeleton(): JSX.Element {
  return (
    <>
      {Array.from({ length: 10 }).map((_, index) => (
        <tr key={index}>
          <td>
            <Skeleton className="h-4 w-12" />
          </td>
          <td>
            <Skeleton className="h-4 w-36" />
          </td>
          <td>
            <Skeleton className="h-6 w-16" />
          </td>
          <td>
            <Skeleton className="h-4 w-40" />
          </td>
          <td>
            <Skeleton className="h-4 w-40" />
          </td>
          <td>
            <Skeleton className="h-4 w-16" />
          </td>
          <td>
            <div className="flex justify-end">
              <Skeleton className="h-8 w-8 rounded-md" />
            </div>
          </td>
        </tr>
      ))}
    </>
  );
}
