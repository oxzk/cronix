import { FormEvent, useEffect, useState } from "react";
import { Field } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import type { SettingsUser } from "@/types";

export interface UserFormState {
  /**
   * 用户名。
   */
  username: string;
  /**
   * 用户密码。
   */
  password: string;
}

const emptyUserForm: UserFormState = { username: "", password: "" };

export interface UserDialogProps {
  /**
   * 是否显示弹窗。
   */
  open: boolean;
  /**
   * 正在编辑的用户。
   */
  user: SettingsUser | null;
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
  onSubmit: (payload: UserFormState) => void;
}

/**
 * 用户编辑弹窗。
 */
export function UserDialog({ open, user, loading, onOpenChange, onSubmit }: UserDialogProps): JSX.Element {
  const [form, setForm] = useState<UserFormState>(emptyUserForm);

  useEffect(() => {
    setForm(user ? { username: user.username, password: "" } : emptyUserForm);
  }, [open, user]);

  /**
   * 提交用户表单。
   */
  function submit(event: FormEvent<HTMLFormElement>): void {
    event.preventDefault();
    onSubmit(form);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{user ? "编辑用户" : "新建用户"}</DialogTitle>
        </DialogHeader>
        <form className="grid gap-4" onSubmit={submit}>
          <Field label="用户名">
            <Input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} required />
          </Field>
          <Field label={user ? "新密码" : "密码"} required={!user}>
            <Input
              type="password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              minLength={6}
              required={!user}
              placeholder={user ? "留空则不修改密码" : undefined}
            />
          </Field>
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
