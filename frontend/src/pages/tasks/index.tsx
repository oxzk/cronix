import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { ConfirmDialog, SectionHeader } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { useToast } from "@/hooks/use-toast";
import { getErrorMessage, tasksApi } from "@/lib/api";
import type { Task, TaskPayload } from "@/types";
import { TaskDialog } from "./task-dialog";
import { TaskTable } from "./task-table";
import { buildTaskPayload } from "./task-utils";

type TaskAction = "execute" | "cancel" | "delete" | "toggle";

interface ConfirmState {
  /**
   * 待确认任务。
   */
  task: Task;
  /**
   * 待确认操作。
   */
  action: Extract<TaskAction, "cancel" | "delete">;
}

/**
 * 任务管理页面。
 */
export function TasksPage(): JSX.Element {
  const [page, setPage] = useState(1);
  const [name, setName] = useState("");
  const [active, setActive] = useState<boolean | "">("");
  const [editing, setEditing] = useState<Task | null>(null);
  const [open, setOpen] = useState(false);
  const [confirmState, setConfirmState] = useState<ConfirmState | null>(null);
  const debouncedName = useDebouncedValue(name, 300);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const query = useQuery({
    queryKey: ["tasks", page, debouncedName, active],
    queryFn: () => tasksApi.list({ page, page_size: 20, name: debouncedName, is_active: active }),
  });

  const runningQuery = useQuery({
    queryKey: ["tasks", "running"],
    queryFn: tasksApi.listRunning,
    refetchInterval: 3000,
  });

  const runningTaskIds = useMemo(() => new Set(runningQuery.data ?? []), [runningQuery.data]);

  useEffect(() => {
    setPage(1);
  }, [debouncedName, active]);

  const saveMutation = useMutation({
    mutationFn: (payload: TaskPayload) => (editing ? tasksApi.update(editing.id, payload) : tasksApi.create(payload)),
    onSuccess: () => {
      toast({ title: editing ? "任务已更新" : "任务已创建" });
      setOpen(false);
      setEditing(null);
      void queryClient.invalidateQueries({ queryKey: ["tasks"] });
      void queryClient.invalidateQueries({ queryKey: ["task-stats"] });
    },
    onError: (error) => toast({ title: "保存失败", description: getErrorMessage(error), variant: "destructive" }),
  });

  const actionMutation = useMutation({
    mutationFn: ({ task, action, isActive }: { task: Task; action: TaskAction; isActive?: boolean }) => {
      if (action === "execute") return tasksApi.execute(task.id);
      if (action === "cancel") return tasksApi.cancel(task.id);
      if (action === "toggle") return tasksApi.update(task.id, buildTaskPayload(task, Boolean(isActive)));
      return tasksApi.delete(task.id);
    },
    onSuccess: (_, variables) => {
      const title =
        variables.action === "execute"
          ? "已触发执行"
          : variables.action === "cancel"
            ? "已发送取消请求"
            : variables.action === "toggle"
              ? variables.isActive
                ? "任务已启用"
                : "任务已停用"
              : "任务已删除";
      toast({ title });
      setConfirmState(null);
      void queryClient.invalidateQueries({ queryKey: ["tasks"] });
      void queryClient.invalidateQueries({ queryKey: ["executions"] });
      void queryClient.invalidateQueries({ queryKey: ["task-stats"] });
    },
    onError: (error) => toast({ title: "操作失败", description: getErrorMessage(error), variant: "destructive" }),
  });

  /**
   * 打开创建任务弹窗。
   */
  function createTask(): void {
    setEditing(null);
    setOpen(true);
  }

  /**
   * 跳转到当前任务的执行记录。
   */
  function openExecutions(task: Task): void {
    navigate(`/executions?task_id=${task.id}`);
  }

  /**
   * 执行已确认的任务操作。
   */
  function runConfirmedAction(): void {
    if (!confirmState) return;
    actionMutation.mutate({ task: confirmState.task, action: confirmState.action });
  }

  return (
    <div className="space-y-4">
      <SectionHeader
        title="任务管理"
        description="维护 cron 调度任务, 控制启停和手动执行。"
        loading={query.isFetching || runningQuery.isFetching}
        onRefresh={() => {
          void query.refetch();
          void runningQuery.refetch();
        }}
        actions={
          <Button size="sm" onClick={createTask}>
            <Plus className="h-4 w-4" />
            新建任务
          </Button>
        }
      />

      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-end">
        <div className="relative md:w-80">
          <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="按任务名搜索" className="pl-9" />
        </div>
        <Select
          value={String(active)}
          onValueChange={(value) => setActive(value === "" ? "" : value === "true")}
          options={[
            { value: "", label: "全部状态" },
            { value: "true", label: "启用" },
            { value: "false", label: "停用" },
          ]}
          className="md:w-36"
        />
      </div>

      <TaskTable
        tasks={query.data?.items ?? []}
        loading={query.isLoading}
        runningTaskIds={runningTaskIds}
        actionPending={actionMutation.isPending}
        onToggle={(task, isActive) => actionMutation.mutate({ task, action: "toggle", isActive })}
        onExecute={(task) => actionMutation.mutate({ task, action: "execute" })}
        onCancel={(task) => setConfirmState({ task, action: "cancel" })}
        onExecutions={openExecutions}
        onEdit={(task) => {
          setEditing(task);
          setOpen(true);
        }}
        onDelete={(task) => setConfirmState({ task, action: "delete" })}
      />

      <div className="flex items-center justify-end gap-2">
        <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
          上一页
        </Button>
        <div className="text-sm text-muted-foreground">第 {query.data?.page ?? page} 页, 共 {query.data?.total ?? 0} 条</div>
        <Button variant="outline" size="sm" disabled={!query.data || page * query.data.page_size >= query.data.total} onClick={() => setPage((value) => value + 1)}>
          下一页
        </Button>
      </div>

      <TaskDialog
        open={open}
        task={editing}
        loading={saveMutation.isPending}
        onOpenChange={(isOpen) => {
          setOpen(isOpen);
          if (!isOpen) setEditing(null);
        }}
        onSubmit={(payload) => saveMutation.mutate(payload)}
      />

      <ConfirmDialog
        open={Boolean(confirmState)}
        title={confirmState?.action === "delete" ? "删除任务" : "取消任务"}
        description={confirmState?.action === "delete" ? `确认删除任务 "${confirmState.task.name}"? 相关执行记录也会被删除。` : `确认取消任务 "${confirmState?.task.name}" 的当前执行?`}
        confirmText={confirmState?.action === "delete" ? "删除" : "取消任务"}
        loading={actionMutation.isPending}
        onOpenChange={(isOpen) => {
          if (!isOpen) setConfirmState(null);
        }}
        onConfirm={runConfirmedAction}
      />
    </div>
  );
}
