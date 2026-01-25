import { useState } from 'react'

/**
 * 通用对话框状态管理 Hook
 */
export function useDialog<T = any>() {
    const [open, setOpen] = useState(false)
    const [data, setData] = useState<T | null>(null)

    const openDialog = (dialogData?: T) => {
        if (dialogData) setData(dialogData)
        setOpen(true)
    }

    const closeDialog = () => {
        setOpen(false)
        setData(null)
    }

    return {
        open,
        data,
        openDialog,
        closeDialog,
    }
}
