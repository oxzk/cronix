import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthRoute } from "@/auth/auth-route";
import { LoginRoute } from "@/auth/login-route";
import { SessionProvider } from "@/auth/session-provider";
import { Layout } from "@/components/layouts";
import { NotFound } from "@/pages/not-found";
import { LOGIN_PATH, menuRoutes, RootRedirect, toNestedRoutePath } from "@/routes";

/**
 * Cronix 前端主应用。
 */
export default function App(): JSX.Element {
  return (
    <BrowserRouter>
      <SessionProvider>
        <Layout>
          <Routes>
            <Route path={LOGIN_PATH} element={<LoginRoute />} />
            <Route path="/" element={<AuthRoute />}>
              <Route index element={<RootRedirect />} />
              {menuRoutes.map((route) => (
                <Route key={route.key} path={toNestedRoutePath(route.path)} element={route.element} />
              ))}
              <Route path="*" element={<NotFound />} />
            </Route>
          </Routes>
        </Layout>
      </SessionProvider>
    </BrowserRouter>
  );
}
