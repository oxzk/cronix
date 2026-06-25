import { FormEvent, useState } from "react";
import { LockKeyhole } from "lucide-react";
import { Field } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { authApi, getErrorMessage } from "@/lib/api";
import { storage } from "@/lib/storage";

export interface LoginPageProps {
  /**
   * 登录成功后的回调。
   */
  onLogin: () => void;
}

/**
 * 管理员登录页面。
 */
export function LoginPage({ onLogin }: LoginPageProps): JSX.Element {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  /**
   * 提交登录表单。
   */
  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    setLoading(true);
    try {
      const token = await authApi.login(username.trim(), password);
      storage.setToken(token.access_token);
      toast({ title: "登录成功" });
      onLogin();
    } catch (error) {
      toast({ title: "登录失败", description: getErrorMessage(error), variant: "destructive" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-10">
      <Card className="w-full max-w-md">
        <CardHeader className="items-center text-center">
          <img src="/logo.svg" alt="Cronix" width="64" height="64" className="mb-2 h-16 w-16 rounded-2xl" />
          <CardTitle>Cronix</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4" onSubmit={submit}>
            <Field label="用户名">
              <Input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" required />
            </Field>
            <Field label="密码">
              <Input value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete="current-password" required />
            </Field>
            <Button type="submit" loading={loading} className="mt-2">
              <LockKeyhole className="h-4 w-4" />
              登录
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
