import type { ReactNode } from 'react'
import { AppDialog } from '@/components/ui/app-dialog'
import { Button } from '@/components/ui/button'
import { DialogClose } from '@/components/ui/dialog'

const FORM_ID = 'cronix-form-dialog'

export function FormDialog({
    open,
    onOpenChange,
    title,
    error,
    submitLabel = '保存',
    submitting,
    onSubmit,
    children,
    wide,
}: {
    open: boolean
    onOpenChange: (open: boolean) => void
    title: string
    error?: string | null
    submitLabel?: string
    submitting?: boolean
    onSubmit: () => void
    children: ReactNode
    wide?: boolean
}) {
    return (
        <AppDialog
            open={open}
            onOpenChange={onOpenChange}
            title={title}
            wide={wide}
            footer={
                <>
                    <DialogClose render={<Button variant="secondary" type="button" />}>
                        取消
                    </DialogClose>
                    <Button type="submit" form={FORM_ID} loading={submitting}>
                        {submitLabel}
                    </Button>
                </>
            }
        >
            <form
                id={FORM_ID}
                onSubmit={(event) => {
                    event.preventDefault()
                    onSubmit()
                }}
                className="space-y-4"
            >
                {children}
                {error && (
                    <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>
                )}
            </form>
        </AppDialog>
    )
}
