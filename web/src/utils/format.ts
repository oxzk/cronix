export const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN')
}

export const formatDuration = (seconds: number | null) => {
    if (seconds === null || seconds === undefined) return '-'
    if (seconds < 60) return `${seconds}秒`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hours}时${minutes}分${secs}秒`
}
