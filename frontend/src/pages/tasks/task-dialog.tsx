import { FormEvent, useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Field } from "@/components/common";
import { Button } from "@/components/ui/button";
import { CheckboxGroup, type CheckboxOption } from "@/components/ui/checkbox-group";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { settingsApi } from "@/lib/api";
import type { NotifyStrategy, Task, TaskPayload } from "@/types";
import { defaultTaskPayload, formatNotificationName, normalizeNotificationIds, notifyStrategyOptions, toTaskDialogPayload } from "./task-utils";

export interface TaskDialogProps {
  /**
   * 是否显示弹窗。
   */
  open: boolean;
  /**
   * 正在编辑的任务。
   */
  task: Task | null;
  /**
   * 是否保存中。
   */
  loading: boolean;
  /**
   * 弹窗开关回调。
   */
  onOpenChange: (open: boolean) => void;
  /**
   * 表单提交回调。
   */
  onSubmit: (payload: TaskPayload) => void;
}

/**
 * 任务编辑弹窗。
 */
export function TaskDialog({ open, task, loading, onOpenChange, onSubmit }: TaskDialogProps): JSX.Element {
  const [payload, setPayload] = useState<TaskPayload>(defaultTaskPayload);
  const notificationsQuery = useQuery({
    queryKey: ["settings", "notifications"],
    queryFn: settingsApi.listNotifications,
    enabled: open,
  });

  const notificationOptions: CheckboxOption[] = useMemo(
    () =>
      (notificationsQuery.data ?? []).map((notification) => ({
        value: notification.id,
        label: formatNotificationName(notification),
      })),
    [notificationsQuery.data],
  );

  useEffect(() => {
    if (open) setPayload(toTaskDialogPayload(task));
  }, [task, open]);

  /**
   * 提交任务表单。
   */
  function submit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    onSubmit({
      ...payload,
      description: payload.description || null,
      notification_ids: normalizeNotificationIds(payload.notification_ids),
    });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{task ? "编辑任务" : "新建任务"}</DialogTitle>
        </DialogHeader>
        <form className="grid gap-4" onSubmit={submit}>
          <div className="grid gap-4 md:grid-cols-2">
            <Field label="任务名称">
              <Input value={payload.name} onChange={(event) => setPayload({ ...payload, name: event.target.value })} required />
            </Field>
            <Field label="Cron 表达式">
              <Input value={payload.cron_expression} onChange={(event) => setPayload({ ...payload, cron_expression: event.target.value })} required />
            </Field>
          </div>
          <Field label="命令">
            <Textarea value={payload.command} onChange={(event) => setPayload({ ...payload, command: event.target.value })} required className="min-h-24 font-mono" />
          </Field>
          <Field label="描述">
            <Input value={payload.description ?? ""} onChange={(event) => setPayload({ ...payload, description: event.target.value })} />
          </Field>
          <div className="flex items-center justify-between rounded-lg border p-3">
            <div>
              <div className="text-sm font-medium">启用任务</div>
              <div className="text-xs text-muted-foreground">关闭后任务不会被调度器自动执行</div>
            </div>
            <Switch checked={payload.is_active} onCheckedChange={(checked) => setPayload({ ...payload, is_active: checked })} />
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <Field label="超时秒数">
              <Input type="number" min={1} max={3600} value={payload.timeout} onChange={(event) => setPayload({ ...payload, timeout: Number(event.target.value) })} required />
            </Field>
            <Field label="重试次数">
              <Input type="number" min={0} max={5} value={payload.retry_count} onChange={(event) => setPayload({ ...payload, retry_count: Number(event.target.value) })} required />
            </Field>
            <Field label="重试间隔秒数">
              <Input type="number" min={1} max={600} value={payload.retry_interval} onChange={(event) => setPayload({ ...payload, retry_interval: Number(event.target.value) })} required />
            </Field>
          </div>
          <fieldset className="grid gap-3 rounded-lg border p-3">
            <legend className="-ml-1 px-1 text-sm font-medium">通知配置</legend>
            <div className="grid gap-4 md:grid-cols-2">
              <Field label="通知策略" required>
                <Select
                  value={payload.notify_strategy}
                  onValueChange={(value) => {
                    const strategy = value as NotifyStrategy;
                    setPayload({
                      ...payload,
                      notify_strategy: strategy,
                      notification_ids: strategy === "never" ? null : payload.notification_ids,
                    });
                  }}
                  options={notifyStrategyOptions}
                />
              </Field>
              <Field label="通知渠道">
                {notificationsQuery.isLoading ? (
                  <Skeleton className="h-10 w-full" />
                ) : payload.notify_strategy === "never" ? (
                  <div className="flex h-10 items-center text-sm text-muted-foreground">无需配置</div>
                ) : (
                  <CheckboxGroup
                    options={notificationOptions}
                    value={payload.notification_ids ?? []}
                    onChange={(value) => setPayload({ ...payload, notification_ids: value.length ? (value as number[]) : null })}
                    orientation="horizontal"
                  />
                )}
              </Field>
            </div>
          </fieldset>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              取消
            </Button>
            <Button type="submit" loading={loading}>
              保存
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
