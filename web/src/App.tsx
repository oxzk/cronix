import { lazy, Suspense, type ReactNode } from 'react'
import { BrowserRouter, Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { SessionProvider, useSession } from '@/auth/session-provider'
import { ErrorBoundary } from '@/components/error-boundary'
import { AdminLayout } from '@/components/layouts/layout'
import { ToastProvider } from '@/components/ui/toast'

const DashboardPage = lazy(() => import('@/pages/dashboard'))
const LoginPage = lazy(() => import('@/pages/login'))
const MonitorsPage = lazy(() => import('@/pages/monitors'))
const RunDetailPage = lazy(() => import('@/pages/runs/detail'))
const RunsPage = lazy(() => import('@/pages/runs'))
const ScriptsPage = lazy(() => import('@/pages/scripts'))
const SettingsPage = lazy(() => import('@/pages/settings'))
const TasksPage = lazy(() => import('@/pages/tasks'))

function PageFallback() {
    return (
        <div className="flex min-h-[40vh] items-center justify-center">
            <span className="h-6 w-6 animate-spin rounded-full border-2 border-slate-200 border-t-slate-900" />
        </div>
    )
}

function LazyPage({ children }: { children: ReactNode }) {
    return <Suspense fallback={<PageFallback />}>{children}</Suspense>
}

function RequireAuth() {
    const { loading, authenticated } = useSession()
    if (loading) return null
    if (!authenticated) return <Navigate to="/login" replace />
    return <Outlet />
}

export default function App() {
    return (
        <ToastProvider>
            <BrowserRouter>
                <SessionProvider>
                    <ErrorBoundary>
                        <Routes>
                            <Route
                                path="/login"
                                element={
                                    <LazyPage>
                                        <LoginPage />
                                    </LazyPage>
                                }
                            />
                            <Route element={<RequireAuth />}>
                                <Route element={<AdminLayout />}>
                                    <Route
                                        index
                                        element={
                                            <LazyPage>
                                                <DashboardPage />
                                            </LazyPage>
                                        }
                                    />
                                    <Route
                                        path="/tasks"
                                        element={
                                            <LazyPage>
                                                <TasksPage />
                                            </LazyPage>
                                        }
                                    />
                                    <Route
                                        path="/runs"
                                        element={
                                            <LazyPage>
                                                <RunsPage />
                                            </LazyPage>
                                        }
                                    />
                                    <Route
                                        path="/runs/:id"
                                        element={
                                            <LazyPage>
                                                <RunDetailPage />
                                            </LazyPage>
                                        }
                                    />
                                    <Route
                                        path="/monitors"
                                        element={
                                            <LazyPage>
                                                <MonitorsPage />
                                            </LazyPage>
                                        }
                                    />
                                    <Route
                                        path="/scripts"
                                        element={
                                            <LazyPage>
                                                <ScriptsPage />
                                            </LazyPage>
                                        }
                                    />
                                    <Route
                                        path="/settings"
                                        element={
                                            <LazyPage>
                                                <SettingsPage />
                                            </LazyPage>
                                        }
                                    />
                                </Route>
                            </Route>
                            <Route path="*" element={<Navigate to="/" replace />} />
                        </Routes>
                    </ErrorBoundary>
                </SessionProvider>
            </BrowserRouter>
        </ToastProvider>
    )
}