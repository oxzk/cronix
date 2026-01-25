import { useState, useEffect } from 'react'
import { 
  Card, CardContent, CardHeader, CardTitle,
  Button, Input, Label,
  LoadingSpinner, PageHeader,
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from '../lib/components'
import { SimpleSelect as Select } from '../lib/simple-wrappers'
import { ConfirmDialog } from '../lib/simple-wrappers'
import { Plus } from 'lucide-react'
import { ScriptTreeView } from '../components/ScriptTreeView'
import { CodeEditor } from '../components/CodeEditor'
import { getScripts, deleteScript, createScript, updateScript, getScript, type ScriptTreeNode, type ScriptSchema, type ScriptResponse, ScriptType } from '../api'
import { message } from '../lib/message'

export default function Scripts() {
  const [nodes, setNodes] = useState<ScriptTreeNode[]>([])
  const [loading, setLoading] = useState(true)
  const [showDialog, setShowDialog] = useState(false)
  const [dialogMode, setDialogMode] = useState<'add' | 'edit'>('add')
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)
  const [deletingScriptName, setDeletingScriptName] = useState<string | null>(null)
  const [editingScriptName, setEditingScriptName] = useState<string | null>(null)
  const [scriptForm, setScriptForm] = useState<Partial<ScriptSchema>>({
    name: '',
    type: ScriptType.PYTHON,
    content: '',
  })
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [validationErrors, setValidationErrors] = useState<Record<string, boolean>>({})

  useEffect(() => {
    const loadScripts = async () => {
      try {
        setLoading(true)
        console.log('Loading scripts...')
        const response = await getScripts() as ScriptTreeNode[]
        setNodes(response)
      } catch (error) {
        console.error('Failed to load scripts:', error)
      } finally {
        setLoading(false)
      }
    }

    loadScripts()
  }, [])

  const handleDeleteClick = (name: string) => {
    setDeletingScriptName(name)
    setShowDeleteDialog(true)
  }

  const handleDeleteConfirm = async () => {
    if (!deletingScriptName) return

    setDeleting(true)
    try {
      await deleteScript(deletingScriptName)
      message.success('脚本删除成功')
      setShowDeleteDialog(false)
      setDeletingScriptName(null)
      window.location.reload()
    } catch (error) {
      console.error('Failed to delete script:', error)
      message.error('删除脚本失败')
    } finally {
      setDeleting(false)
    }
  }

  const handleDeleteCancel = () => {
    setShowDeleteDialog(false)
    setDeletingScriptName(null)
  }

  const handleAddScript = () => {
    setDialogMode('add')
    setEditingScriptName(null)
    setScriptForm({
      name: '',
      type: ScriptType.PYTHON,
      content: '',
    })
    setValidationErrors({})
    setShowDialog(true)
  }

  const handleEditScript = async (name: string) => {
    console.log('handleEditScript called with name:', name)
    try {
      console.log('Fetching script details...')
      const script = await getScript(name)
      console.log('Script loaded:', script)
      setDialogMode('edit')
      setEditingScriptName(name)
      setScriptForm({
        name: script.name,
        type: script.type,
        content: script.content,
      })
      setValidationErrors({})
      setShowDialog(true)
      console.log('Edit dialog should be visible now')
    } catch (error) {
      console.error('Failed to load script:', error)
      message.error('加载脚本失败')
    }
  }

  const handleCancel = () => {
    setShowDialog(false)
    setEditingScriptName(null)
    setScriptForm({
      name: '',
      type: ScriptType.PYTHON,
      content: '',
    })
    setValidationErrors({})
  }

  const handleSave = async () => {
    const errors: Record<string, boolean> = {}

    if (dialogMode === 'add') {
      if (!scriptForm.name) errors.name = true
    }

    if (!scriptForm.content) errors.content = true

    if (Object.keys(errors).length > 0) {
      setValidationErrors(errors)
      return
    }

    setSaving(true)
    setValidationErrors({})

    try {
      if (dialogMode === 'add') {
        await createScript(scriptForm as ScriptSchema)
        message.success('脚本添加成功')
      } else {
        if (!editingScriptName) return
        const updateData: ScriptSchema = {
          name: scriptForm.name!,
          type: scriptForm.type!,
          content: scriptForm.content!,
        }
        await updateScript(editingScriptName, updateData)
        message.success('脚本更新成功')
      }
      setShowDialog(false)
      setEditingScriptName(null)
      window.location.reload()
    } catch (error: any) {
      if (dialogMode === 'add') {
        message.error(error.message || '保存脚本失败')
      } else {
        message.error(error.message || '更新脚本失败')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader 
        title="脚本管理" 
        description="管理执行脚本文件"
        action={
          <Button className="gap-2" onClick={handleAddScript}>
            <Plus className="h-4 w-4" />
            添加脚本
          </Button>
        }
      />

      <Dialog
        open={showDialog}
        onOpenChange={(open) => !open && handleCancel()}
      >
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{dialogMode === 'add' ? '添加新脚本' : '编辑脚本'}</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="script-name">脚本名称 {dialogMode === 'add' && <span className="text-red-500">*</span>}</Label>
                <Input
                  id="script-name"
                  placeholder="输入脚本名称（如：my_script.py）"
                  value={scriptForm.name || ''}
                  onChange={(e) => {
                    setScriptForm({ ...scriptForm, name: e.target.value })
                    if (validationErrors.name) {
                      setValidationErrors({ ...validationErrors, name: false })
                    }
                  }}
                  disabled={dialogMode === 'edit'}
                  className={validationErrors.name ? 'border-red-500' : ''}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="script-type">脚本类型 {dialogMode === 'add' && <span className="text-red-500">*</span>}</Label>
                <Select
                  id="script-type"
                  options={[
                    { value: ScriptType.PYTHON, label: 'Python' },
                    { value: ScriptType.NODE, label: 'Node.js' },
                    { value: ScriptType.SHELL, label: 'Shell' },
                  ]}
                  value={scriptForm.type || ScriptType.PYTHON}
                  onChange={(value) => setScriptForm({ ...scriptForm, type: value as ScriptType })}
                  disabled={dialogMode === 'edit'}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="script-content">脚本内容 <span className="text-red-500">*</span></Label>
              <CodeEditor
                value={scriptForm.content || ''}
                onChange={(value) => {
                  setScriptForm({ ...scriptForm, content: value || '' })
                  if (validationErrors.content) {
                    setValidationErrors({ ...validationErrors, content: false })
                  }
                }}
                language={scriptForm.type === ScriptType.PYTHON ? 'python' : scriptForm.type === ScriptType.NODE ? 'javascript' : 'shell'}
                height="300px"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleCancel} disabled={saving}>
              取消
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                  保存中...
                </>
              ) : (
                dialogMode === 'add' ? '保存脚本' : '更新脚本'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <ConfirmDialog
        open={showDeleteDialog}
        onOpenChange={(open) => !open && handleDeleteCancel()}
        onConfirm={handleDeleteConfirm}
        title="确认删除"
        description={`确定要删除脚本 ${deletingScriptName} 吗？`}
        confirmText="删除"
        cancelText="取消"
      />

      <Card>
        <CardHeader>
          <CardTitle>脚本列表</CardTitle>
        </CardHeader>
        <CardContent className="relative overflow-visible">
          {loading ? <LoadingSpinner /> : (
            <ScriptTreeView
              nodes={nodes}
              onEdit={handleEditScript}
              onDelete={handleDeleteClick}
            />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
