import { Pencil, Plus, Trash2, UserCog } from "lucide-react";
import { EmptyState, TooltipIconButton } from "@/components/common";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDateTime } from "@/lib/datetime";
import type { SettingsUser } from "@/types";

export interface UsersPanelProps {
  /**
   * 用户列表。
   */
  users: SettingsUser[];
  /**
   * 是否加载中。
   */
  loading: boolean;
  /**
   * 是否有删除操作提交中。
   */
  deletePending: boolean;
  /**
   * 新建用户回调。
   */
  onCreate: () => void;
  /**
   * 编辑用户回调。
   */
  onEdit: (user: SettingsUser) => void;
  /**
   * 删除用户回调。
   */
  onDelete: (user: SettingsUser) => void;
}

/**
 * 用户配置面板。
 */
export function UsersPanel({ users, loading, deletePending, onCreate, onEdit, onDelete }: UsersPanelProps): JSX.Element {
  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-4">
        <div className="space-y-1.5">
          <CardTitle>用户配置</CardTitle>
          <CardDescription>维护可登录 Cronix 的系统用户。</CardDescription>
        </div>
        <Button size="sm" onClick={onCreate}>
          <Plus className="h-4 w-4" />
          新建用户
        </Button>
      </CardHeader>
      <CardContent>
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>用户</th>
                <th>创建时间</th>
                <th>更新时间</th>
                <th className="text-right">操作</th>
              </tr>
            </thead>
            <tbody>
              {loading ? <UserTableSkeleton /> : null}
              {users.map((user) => (
                <tr key={user.id}>
                  <td>
                    <div className="flex items-center gap-2">
                      <UserCog className="h-4 w-4 text-primary" />
                      <span className="font-medium">{user.username}</span>
                      {user.username === "admin" ? <Badge variant="outline">Admin</Badge> : null}
                    </div>
                  </td>
                  <td>{formatDateTime(user.created_at)}</td>
                  <td>{formatDateTime(user.updated_at)}</td>
                  <td>
                    <div className="flex justify-end gap-1">
                      <TooltipIconButton label="编辑用户" variant="ghost" onClick={() => onEdit(user)}>
                        <Pencil className="h-4 w-4" />
                      </TooltipIconButton>
                      <TooltipIconButton label="删除用户" variant="ghost" disabled={deletePending} onClick={() => onDelete(user)}>
                        <Trash2 className="h-4 w-4" />
                      </TooltipIconButton>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && !users.length ? (
            <div className="p-4">
              <EmptyState title="暂无用户" />
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * 用户表格骨架屏。
 */
function UserTableSkeleton(): JSX.Element {
  return (
    <>
      {Array.from({ length: 5 }).map((_, index) => (
        <tr key={index}>
          <td>
            <Skeleton className="h-4 w-40" />
          </td>
          <td>
            <Skeleton className="h-4 w-36" />
          </td>
          <td>
            <Skeleton className="h-4 w-36" />
          </td>
          <td>
            <div className="flex justify-end gap-1">
              <Skeleton className="h-8 w-8 rounded-md" />
              <Skeleton className="h-8 w-8 rounded-md" />
            </div>
          </td>
        </tr>
      ))}
    </>
  );
}
