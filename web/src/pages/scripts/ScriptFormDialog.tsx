import { useEffect, useState } from 'react'
import { createScript, testScript, updateScript } from '@/api/scripts'
import type { Script, ScriptTestResult } from '@/api/types'
import { Button } from '@/components/ui/button'
import { FormField as Field, FormTextField as TextField } from '@/components/ui/form-field'
import { FormDialog } from '@/components/ui/form-dialog'
import { Input } from '@/components/ui/input'
import { JsonBlock } from '@/components/ui/json-block'
import { Textarea } from '@/components/ui/textarea'

function renderTestOutput(result: ScriptTestResult): string {
    const lines = [
        `exit_code: ${result.exit_code ?? '-'}`,
        `duration: ${result.duration_ms}ms`,
        `timed_out: ${result.timed_out}`,
        '',
        '--- stdout ---',
        result.stdout || '(空)',
        '--- stderr ---',
        result.stderr || '(空)',
    ]
    return lines.join('\n')
}

export default function ScriptFormDialog({
    open,
    script,
    onOpenChange,
    onSaved,
}: {
    open: boolean
    script: Script | null
    onOpenChange: (open: boolean) => void
    onSaved: () => void
}) {
    const [name, setName] = useState('')
    const [description, setDescription] = useState('')
    const [content, setContent] = useState('')
    const [fieldErrors, setFieldErrors] = useState<{ name?: string; content?: string }>({})
    const [error, setError] = useState<string | null>(null)
    const [submitting, setSubmitting] = useState(false)
    const [testing, setTesting] = useState(false)
    const [testResult, setTestResult] = useState<ScriptTestResult | null>(null)

    useEffect(() => {
        if (!open) return
        setError(null)
        setFieldErrors({})
        setTestResult(null)
        setName(script?.name ?? '')
        setDescription(script?.description ?? '')
        setContent(script?.content ?? '')
    }, [open, script])

    const handleSubmit = async () => {
        const next: { name?: string; content?: string } = {}
        if (!name.trim()) next.name = '脚本名不能为空'
        if (!content.trim()) next.content = '脚本内容不能为空'
        setFieldErrors(next)
        if (next.name || next.content) return
        setError(null)
        setSubmitting(true)
        try {
            const payload = {
                name: name.trim(),
                description: description.trim() || null,
                content,
            }
            if (script) {
                await updateScript(script.id, payload)
            } else {
                await createScript(payload)
            }
            onSaved()
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err))
        } finally {
            setSubmitting(false)
        }
    }

    const handleTest = async () => {
        if (!script) return
        setError(null)
        setTesting(true)
        try {
            setTestResult(await testScript(script.id))
        } catch (err) {
            setError(err instanceof Error ? err.message : String(err))
        } finally {
            setTesting(false)
        }
    }

    return (
        <FormDialog
            open={open}
            onOpenChange={onOpenChange}
            title={script ? '编辑脚本' : '新建脚本'}
            error={error}
            submitLabel={script ? '保存' : '创建'}
            submitting={submitting}
            onSubmit={() => void handleSubmit()}
            wide
        >
            <div className="grid grid-cols-2 gap-4">
                <Field label="名称" required error={fieldErrors.name}>
                    <Input
                        value={name}
                        onChange={(event) => {
                            setName(event.target.value)
                            setFieldErrors((prev) => ({ ...prev, name: undefined }))
                        }}
                    />
                </Field>
                <Field label="描述">
                    <Input
                        value={description}
                        onChange={(event) => setDescription(event.target.value)}
                        placeholder="可选"
                    />
                </Field>
            </div>
            <TextField
                label="脚本内容"
                required
                error={fieldErrors.content}
            >
                <Textarea
                    value={content}
                    onChange={(event) => {
                        setContent(event.target.value)
                        setFieldErrors((prev) => ({ ...prev, content: undefined }))
                    }}
                    rows={16}
                    spellCheck={false}
                    className="min-h-[320px]"
                    placeholder="支持多行, 最大 64KB; 任务引用时执行的是保存后的最新内容"
                />
            </TextField>
            {script && (
                <div className="space-y-2 rounded-lg border border-slate-200 px-3 py-3">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-slate-700">测试运行</p>
                            <p className="text-xs text-slate-400">执行已保存的内容(最长 15 秒), 不产生执行记录</p>
                        </div>
                        <Button
                            type="button"
                            variant="secondary"
                            size="sm"
                            loading={testing}
                            onClick={() => void handleTest()}
                        >
                            运行
                        </Button>
                    </div>
                    {testResult && <JsonBlock value={renderTestOutput(testResult)} className="max-h-64" />}
                </div>
            )}
        </FormDialog>
    )
}
