import { AppDialog } from '@/components/ui/app-dialog'
import { Button } from '@/components/ui/button'
import { DialogClose } from '@/components/ui/dialog'

export function ConfirmDialog({
    open,
    onOpenChange,
    title,
    confirmLabel = '删除',
    loading,
    onConfirm,
}: {
    open: boolean
    onOpenChange: (open: boolean) => void
    title: string
    confirmLabel?: string
    loading?: boolean
    onConfirm: () => void
}) {
    return (
        <AppDialog
            open={open}
            onOpenChange={onOpenChange}
            title={title}
            footer={
                <>
                    <DialogClose render={<Button variant="secondary" type="button" />}>
                        取消
                    </DialogClose>
                    <Button variant="danger" type="button" loading={loading} onClick={onConfirm}>
                        {confirmLabel}
                    </Button>
                </>
            }
        >
            <p className="text-sm text-slate-600">此操作不可撤销, 请确认。</p>
        </AppDialog>
    )
}
