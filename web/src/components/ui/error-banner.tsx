export function ErrorBanner({ message }: { message: string | null }) {
    if (!message) return null
    return (
        <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{message}</div>
    )
}
