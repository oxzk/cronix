import { FormEvent } from "react";
import { Save } from "lucide-react";
import { Field } from "@/components/common";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import type { NotificationSetting, NotifyType } from "@/types";
import { indexNotifications, notificationOptions } from "./notification-options";

export interface NotificationsPanelProps {
  /**
   * 通知配置列表。
   */
  notifications: NotificationSetting[];
  /**
   * 表单草稿。
   */
  drafts: Record<NotifyType, Record<string, string>>;
  /**
   * 是否加载中。
   */
  loading: boolean;
  /**
   * 是否保存中。
   */
  savePending: boolean;
  /**
   * 更新草稿回调。
   */
  onDraftChange: (type: NotifyType, key: string, value: string) => void;
  /**
   * 保存通知配置回调。
   */
  onSave: (type: NotifyType) => void;
}

/**
 * 通知配置面板。
 */
export function NotificationsPanel({ notifications, drafts, loading, savePending, onDraftChange, onSave }: NotificationsPanelProps): JSX.Element {
  const notificationByType = indexNotifications(notifications);

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {notificationOptions.map((option) => {
        const existing = notificationByType[option.type];
        return (
          <Card key={option.type}>
            <CardHeader>
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1.5">
                  <CardTitle>{option.label}</CardTitle>
                  <CardDescription>{option.description}</CardDescription>
                </div>
                <Badge variant={existing ? "default" : "secondary"}>{existing ? "已配置" : "未配置"}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <NotificationCardSkeleton />
              ) : (
                <form className="grid gap-3" onSubmit={(event) => submitNotification(event, option.type, onSave)}>
                  {option.fields.map((field) => (
                    <Field key={field.key} label={field.label}>
                      <Input
                        type={field.type ?? "text"}
                        value={drafts[option.type][field.key] ?? ""}
                        onChange={(event) => onDraftChange(option.type, field.key, event.target.value)}
                        placeholder={field.placeholder}
                        required
                      />
                    </Field>
                  ))}
                  <Button type="submit" size="sm" loading={savePending}>
                    <Save className="h-4 w-4" />
                    保存配置
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

/**
 * 通知配置骨架屏。
 */
function NotificationCardSkeleton(): JSX.Element {
  return (
    <div className="grid gap-3">
      <Skeleton className="h-14 w-full" />
      <Skeleton className="h-14 w-full" />
      <Skeleton className="h-8 w-28" />
    </div>
  );
}

/**
 * 提交通知配置表单。
 */
function submitNotification(event: FormEvent<HTMLFormElement>, type: NotifyType, save: (type: NotifyType) => void): void {
  event.preventDefault();
  save(type);
}
