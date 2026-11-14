import { Component, type ErrorInfo, type ReactNode } from 'react'

interface State {
    error: Error | null
}

/** 全局渲染错误兜底, 避免单个组件异常导致整页空白。 */
export class ErrorBoundary extends Component<{ children: ReactNode }, State> {
    state: State = { error: null }

    static getDerivedStateFromError(error: Error): State {
        return { error }
    }

    componentDidCatch(error: Error, info: ErrorInfo): void {
        console.error('Unhandled render error', error, info)
    }

    render(): ReactNode {
        if (this.state.error) {
            return (
                <div className="flex min-h-screen items-center justify-center px-4">
                    <div className="surface max-w-md p-6 text-center">
                        <p className="text-base font-semibold text-slate-900">页面出现异常</p>
                        <p className="mt-2 text-sm text-slate-500">
                            请刷新页面重试; 若持续出现, 请查看服务端日志。
                        </p>
                        {import.meta.env.DEV && (
                            <pre className="mt-3 max-h-40 overflow-auto rounded-md bg-slate-50 p-3 text-left text-[11px] leading-relaxed whitespace-pre-wrap text-rose-600">
                                {this.state.error.message}
                            </pre>
                        )}
                        <button
                            type="button"
                            onClick={() => window.location.reload()}
                            className="mt-4 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
                        >
                            刷新页面
                        </button>
                    </div>
                </div>
            )
        }
        return this.props.children
    }
}
