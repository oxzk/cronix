import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, Users } from "lucide-react";
import { ConfirmDialog, SectionHeader } from "@/components/common";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { getErrorMessage, settingsApi } from "@/lib/api";
import type { NotifyType, SettingsUser } from "@/types";
import { buildNotificationPayload, createEmptyNotificationDrafts, createNotificationDrafts, indexNotifications, readNotificationLabel } from "./notification-options";
import { NotificationsPanel } from "./notifications-panel";
import { UserDialog, type UserFormState } from "./user-dialog";
import { UsersPanel } from "./users-panel";

/**
 * 系统设置页面。
 */
export function SettingsPage(): JSX.Element {
  const [userDialogOpen, setUserDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<SettingsUser | null>(null);
  const [userToDelete, setUserToDelete] = useState<SettingsUser | null>(null);
  const [notificationDrafts, setNotificationDrafts] = useState(() => createEmptyNotificationDrafts());
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const usersQuery = useQuery({ queryKey: ["settings", "users"], queryFn: settingsApi.listUsers });
  const notificationsQuery = useQuery({ queryKey: ["settings", "notifications"], queryFn: settingsApi.listNotifications });
  const notificationByType = useMemo(() => indexNotifications(notificationsQuery.data ?? []), [notificationsQuery.data]);

  const saveUserMutation = useMutation({
    mutationFn: (payload: UserFormState) => {
      if (!editingUser) return settingsApi.createUser(payload);
      return settingsApi.updateUser(editingUser.id, {
        username: payload.username,
        ...(payload.password ? { password: payload.password } : {}),
      });
    },
    onSuccess: () => {
      toast({ title: editingUser ? "用户已更新" : "用户已创建" });
      setUserDialogOpen(false);
      setEditingUser(null);
      void queryClient.invalidateQueries({ queryKey: ["settings", "users"] });
    },
    onError: (error) => toast({ title: "用户保存失败", description: getErrorMessage(error), variant: "destructive" }),
  });

  const deleteUserMutation = useMutation({
    mutationFn: settingsApi.deleteUser,
    onSuccess: () => {
      toast({ title: "用户已删除" });
      setUserToDelete(null);
      void queryClient.invalidateQueries({ queryKey: ["settings", "users"] });
    },
    onError: (error) => toast({ title: "用户删除失败", description: getErrorMessage(error), variant: "destructive" }),
  });

  const saveNotificationMutation = useMutation({
    mutationFn: (type: NotifyType) => {
      const payload = buildNotificationPayload(type, notificationDrafts[type]);
      const existing = notificationByType[type];
      return existing ? settingsApi.updateNotification(existing.id, payload) : settingsApi.createNotification(payload);
    },
    onSuccess: (_, type) => {
      toast({ title: `${readNotificationLabel(type)} 已保存` });
      void queryClient.invalidateQueries({ queryKey: ["settings", "notifications"] });
    },
    onError: (error) => toast({ title: "通知保存失败", description: getErrorMessage(error), variant: "destructive" }),
  });

  useEffect(() => {
    if (!notificationsQuery.data) return;
    setNotificationDrafts(createNotificationDrafts(notificationsQuery.data));
  }, [notificationsQuery.data]);

  /**
   * 打开新建用户弹窗。
   */
  function openCreateUser(): void {
    setEditingUser(null);
    setUserDialogOpen(true);
  }

  /**
   * 打开编辑用户弹窗。
   */
  function openEditUser(user: SettingsUser): void {
    setEditingUser(user);
    setUserDialogOpen(true);
  }

  /**
   * 更新通知配置草稿。
   */
  function updateNotificationDraft(type: NotifyType, key: string, value: string): void {
    setNotificationDrafts((drafts) => ({
      ...drafts,
      [type]: {
        ...drafts[type],
        [key]: value,
      },
    }));
  }

  return (
    <div className="space-y-4">
      <SectionHeader title="系统设置" description="配置登录用户和任务通知渠道。" loading={usersQuery.isFetching || notificationsQuery.isFetching} />

      <Tabs defaultValue="users" className="space-y-4">
        <TabsList>
          <TabsTrigger value="users">
            <Users className="h-4 w-4" />
            用户配置
          </TabsTrigger>
          <TabsTrigger value="notifications">
            <Bell className="h-4 w-4" />
            通知配置
          </TabsTrigger>
        </TabsList>

        <TabsContent value="users" className="space-y-4">
          <UsersPanel
            users={usersQuery.data ?? []}
            loading={usersQuery.isLoading}
            deletePending={deleteUserMutation.isPending}
            onCreate={openCreateUser}
            onEdit={openEditUser}
            onDelete={setUserToDelete}
          />
        </TabsContent>

        <TabsContent value="notifications">
          <NotificationsPanel
            notifications={notificationsQuery.data ?? []}
            drafts={notificationDrafts}
            loading={notificationsQuery.isLoading}
            savePending={saveNotificationMutation.isPending}
            onDraftChange={updateNotificationDraft}
            onSave={(type) => saveNotificationMutation.mutate(type)}
          />
        </TabsContent>
      </Tabs>

      <UserDialog
        open={userDialogOpen}
        user={editingUser}
        loading={saveUserMutation.isPending}
        onOpenChange={setUserDialogOpen}
        onSubmit={(payload) => saveUserMutation.mutate(payload)}
      />

      <ConfirmDialog
        open={Boolean(userToDelete)}
        title="删除用户"
        description={`确认删除用户 "${userToDelete?.username}"? 删除后该用户将无法继续登录。`}
        confirmText="删除"
        loading={deleteUserMutation.isPending}
        onOpenChange={(open) => {
          if (!open) setUserToDelete(null);
        }}
        onConfirm={() => {
          if (userToDelete) deleteUserMutation.mutate(userToDelete.id);
        }}
      />
    </div>
  );
}
