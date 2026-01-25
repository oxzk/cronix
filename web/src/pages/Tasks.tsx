import { useState } from 'react'
import { 
  Card, CardContent, CardHeader, CardTitle,
  Button, Input, Label,
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
  Pagination, LoadingSpinner, EmptyState, PageHeader,
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from '../lib/components'
import { SimpleSelect as Select } from '../lib/simple-wrappers'
import { SimpleTooltip as Tooltip } from '../lib/simple-wrappers'
import { ConfirmDialog } from '../lib/simple-wrappers'
import { Search, Plus, Trash2, Edit, Play } from 'lucide-react'
import { getTasks, deleteTask, createTask, updateTask, getTask, executeTask, type TaskResponse, type TaskSchema } from '../api'
import { useDialog, useForm, usePagination, useAsync } from '../hooks'
import { formatDate } from '../utils/format'

export default function Tasks() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  
  const filters = {
    ...(searchQuery && { name: searchQuery }),
    ...(statusFilter !== 'all' && { is_active: statusFilter === 'true' }),
  }
  
  const { data: tasks, loading, currentPage, totalPages, setCurrentPage } = usePagination<TaskResponse>(getTasks, 20, filters)
  
  const formDialog = useDialog<number>()
  const deleteDialog = useDialog<number>()
  const executeDialog = useDialog<number>()
  
  const { loading: saving, execute: executeSave } = useAsync()
  const { loading: deleting, execute: executeDelete } = useAsync()
  const { loading: executing, execute: executeRun } = useAsync()
  
  const form = useForm<Partial<TaskSchema>>({
    name: '',
    description: '',
    cron_expression: '',
    command: '',
    is_active: true,
    timeout: 60,
    retry_count: 0,
    retry_interval: 5,
    notification_ids: [],
  })

  const handleAdd = () => {
    form.reset()
    formDialog.openDialog()
  }

  const handleEdit = async (id: number) => {
    await executeSave(
      async () => {
        const task = await getTask(id)
        form.updateValues({
          name: task.name,
          description: task.description || '',
          cron_expression: task.cron_expression,
          command: task.command,
          is_active: task.is_active,
          timeout: task.timeout,
          retry_count: task.retry_count,
          retry_interval: task.retry_interval,
          notification_ids: task.notifications?.map(n => n.id) || [],
        })
        formDialog.openDialog(id)
      },
      { errorMessage: '加载任务失败' }
    )
  }

  const handleSave = async () => {
    const isValid = form.validate({
      name: (v) => !!formDialog.data || !!v,
      cron_expression: (v) => !!v,
      command: (v) => !!v,
    })

    if (!isValid) return

    await executeSave(
      async () => {
        if (formDialog.data) {
          await updateTask(formDialog.data, form.values as TaskSchema)
        } else {
          await createTask(form.values as TaskSchema)
        }
        formDialog.closeDialog()
        window.location.reload()
      },
      {
        successMessage: formDialog.data ? '任务更新成功' : '任务添加成功',
      }
    )
  }

  const handleDelete = async () => {
    if (!deleteDialog.data) return
    
    await executeDelete(
      async () => {
        await deleteTask(deleteDialog.data!)
        deleteDialog.closeDialog()
        window.location.reload()
      },
      { successMessage: '任务删除成功' }
    )
  }

  const handleExecute = async () => {
    if (!executeDialog.data) return
    
    await executeRun(
      async () => {
        await executeTask(executeDialog.data!)
        executeDialog.closeDialog()
      },
      { successMessage: '任务已开始执行' }
    )
  }



  return (
    <div className="space-y-6">
      <PageHeader 
        title="任务管理" 
        description="管理定时任务和执行计划"
        action={
          <Button className="gap-2" onClick={handleAdd}>
            <Plus className="h-4 w-4" />
            添加任务
          </Button>
        }
      />

      <Dialog 
        open={formDialog.open} 
        onOpenChange={formDialog.closeDialog}
      >
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{formDialog.data ? '编辑任务' : '添加新任务'}</DialogTitle>
          </DialogHeader>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="task-name">任务名称 <span className="text-red-500">*</span></Label>
                <Input
                  id="task-name"
                  placeholder="输入任务名称"
                  value={form.values.name || ''}
                  onChange={(e) => form.updateValue('name', e.target.value)}
                  className={form.errors.name ? 'border-red-500' : ''}
                  disabled={!!formDialog.data}
                />
                {formDialog.data && (
                  <p className="text-xs text-muted-foreground">任务名称不可修改</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="cron-expression">Cron 表达式 <span className="text-red-500">*</span></Label>
                <Input
                  id="cron-expression"
                  placeholder="如: */5 * * * * (每5分钟)"
                  value={form.values.cron_expression || ''}
                  onChange={(e) => form.updateValue('cron_expression', e.target.value)}
                  className={form.errors.cron_expression ? 'border-red-500' : ''}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="task-description">任务描述</Label>
              <Input
                id="task-description"
                placeholder="输入任务描述（可选）"
                value={form.values.description || ''}
                onChange={(e) => form.updateValue('description', e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="task-command">执行命令 <span className="text-red-500">*</span></Label>
              <Input
                id="task-command"
                placeholder="输入要执行的命令"
                value={form.values.command || ''}
                onChange={(e) => form.updateValue('command', e.target.value)}
                className={form.errors.command ? 'border-red-500' : ''}
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="task-timeout">超时时间（秒）</Label>
                <Input
                  id="task-timeout"
                  type="number"
                  placeholder="3600"
                  value={form.values.timeout || 3600}
                  onChange={(e) => form.updateValue('timeout', parseInt(e.target.value) || 3600)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="retry-count">重试次数</Label>
                <Input
                  id="retry-count"
                  type="number"
                  placeholder="0"
                  value={form.values.retry_count || 0}
                  onChange={(e) => form.updateValue('retry_count', parseInt(e.target.value) || 0)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="retry-interval">重试间隔（秒）</Label>
                <Input
                  id="retry-interval"
                  type="number"
                  placeholder="60"
                  value={form.values.retry_interval || 60}
                  onChange={(e) => form.updateValue('retry_interval', parseInt(e.target.value) || 60)}
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="task-active"
                  checked={form.values.is_active !== false}
                  onChange={(e) => form.updateValue('is_active', e.target.checked)}
                  className="rounded border-input"
                />
                <label htmlFor="task-active" className="text-sm">
                  任务启用
                </label>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={formDialog.closeDialog} disabled={saving}>
              取消
            </Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                  保存中...
                </>
              ) : (
                formDialog.data ? '更新任务' : '保存任务'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>任务列表</CardTitle>
            <div className="flex items-center gap-3">
              <Tooltip content="筛选任务状态">
                <Select
                  id="status-filter"
                  value={statusFilter}
                  onChange={(value) => {
                    setStatusFilter(value)
                    setCurrentPage(1)
                  }}
                  options={[
                    { value: 'all', label: '全部状态' },
                    { value: 'true', label: '启用' },
                    { value: 'false', label: '禁用' },
                  ]}
                  className="min-w-[120px]"
                />
              </Tooltip>
              <div className="relative w-80">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Tooltip content="搜索任务">
                  <Input
                    placeholder="搜索任务名称..."
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value)
                      setCurrentPage(1)
                    }}
                    className="pl-9"
                  />
                </Tooltip>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <LoadingSpinner />
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>任务名称</TableHead>
                    <TableHead>Cron 表达式</TableHead>
                    <TableHead>命令</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>下次执行</TableHead>
                    <TableHead>重试次数</TableHead>
                    <TableHead className="text-center">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tasks.map((task) => (
                    <TableRow key={task.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{task.name}</div>
                          {task.description && (
                            <div className="text-sm text-muted-foreground">{task.description}</div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="font-mono text-sm">{task.cron_expression}</TableCell>
                      <TableCell className="font-mono text-sm max-w-md">
                        <Tooltip content={task.command}>
                          <div className="truncate">{task.command}</div>
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium ${
                          task.is_active 
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted text-muted-foreground'
                        }`}>
                          {task.is_active ? '启用' : '禁用'}
                        </span>
                      </TableCell>
                      <TableCell>
                        {task.next_run_time ? (
                          <span className="text-sm">{formatDate(task.next_run_time)}</span>
                        ) : (
                          <span className="text-sm text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>{task.retry_count}</TableCell>
                      <TableCell>
                        <div className="flex items-center justify-center gap-1">
                          <Tooltip content="立即执行任务">
                            <Button variant="ghost" size="icon" onClick={() => executeDialog.openDialog(task.id)}>
                              <Play className="h-4 w-4" />
                            </Button>
                          </Tooltip>
                          <Tooltip content="编辑任务">
                            <Button variant="ghost" size="icon" onClick={() => handleEdit(task.id)}>
                              <Edit className="h-4 w-4" />
                            </Button>
                          </Tooltip>
                          <Tooltip content="删除任务">
                            <Button variant="ghost" size="icon" onClick={() => deleteDialog.openDialog(task.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </Tooltip>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {tasks.length === 0 && <EmptyState message="没有找到任务" />}
              
              <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />
            </>
          )}
        </CardContent>
      </Card>

      <ConfirmDialog
        open={deleteDialog.open}
        onOpenChange={deleteDialog.closeDialog}
        onConfirm={handleDelete}
        title="确认删除"
        description="确定要删除这个任务吗？"
        confirmText="删除"
        cancelText="取消"
      />

      <ConfirmDialog
        open={executeDialog.open}
        onOpenChange={executeDialog.closeDialog}
        onConfirm={handleExecute}
        title="确认执行"
        description="确定要立即执行这个任务吗？"
        confirmText="执行"
        cancelText="取消"
      />
    </div>
  )
}
