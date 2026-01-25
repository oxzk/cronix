import { useState } from 'react'
import { 
  Card, CardContent, CardHeader, CardTitle,
  Button, Input, Label,
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
  Pagination, LoadingSpinner, EmptyState, StatusBadge, PageHeader,
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from '../lib/components'
import { SimpleSelect as Select } from '../lib/simple-wrappers'
import { SimpleTooltip as Tooltip } from '../lib/simple-wrappers'
import { ConfirmDialog } from '../lib/simple-wrappers'
import { Eye, XCircle } from 'lucide-react'
import { getExecutions, getExecution, cancelTask, type TaskExecutionDetailResponse, ExecutionStatus } from '../api'
import { useDialog, usePagination, useAsync } from '../hooks'
import { formatDate, formatDuration } from '../utils/format'

export default function Executions() {
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [taskIdFilter, setTaskIdFilter] = useState('')
  
  const filters = {
    ...(statusFilter !== 'all' && { status: statusFilter }),
    ...(taskIdFilter && { task_id: parseInt(taskIdFilter) }),
  }
  
  const { data: executions, loading, currentPage, totalPages, setCurrentPage } = usePagination<TaskExecutionDetailResponse>(getExecutions, 20, filters)
  
  const detailDialog = useDialog<TaskExecutionDetailResponse>()
  const cancelDialog = useDialog<number>()
  
  const { loading: cancelling, execute: executeCancel } = useAsync()

  const handleViewDetail = async (executionId: number) => {
    const detail = await getExecution(executionId)
    detailDialog.openDialog(detail)
  }

  const handleCancel = async () => {
    if (!cancelDialog.data) return
    
    await executeCancel(
      async () => {
        await cancelTask(cancelDialog.data!)
        cancelDialog.closeDialog()
        setCurrentPage(prev => prev) // 触发重新加载
      },
      { successMessage: '任务已取消' }
    )
  }



  return (
    <div className="space-y-6">
      <PageHeader title="执行记录" />

      <Dialog 
        open={detailDialog.open && detailDialog.data !== null} 
        onOpenChange={detailDialog.closeDialog}
      >
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          {detailDialog.data && (
            <>
              <DialogHeader>
                <DialogTitle>执行详情 #{detailDialog.data.id}</DialogTitle>
              </DialogHeader>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-muted-foreground">任务ID</Label>
                    <p className="font-mono">{detailDialog.data.task_id}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">状态</Label>
                    <div className="mt-1"><StatusBadge status={detailDialog.data.status} /></div>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">开始时间</Label>
                    <p>{formatDate(detailDialog.data.started_at)}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">结束时间</Label>
                    <p>{detailDialog.data.finished_at ? formatDate(detailDialog.data.finished_at) : '-'}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">执行耗时</Label>
                    <p>{formatDuration(detailDialog.data.duration)}</p>
                  </div>
                  <div>
                    <Label className="text-muted-foreground">重试次数</Label>
                    <p>{detailDialog.data.retry_attempt}</p>
                  </div>
                  {detailDialog.data.task && (
                    <div>
                      <Label className="text-muted-foreground">任务名称</Label>
                      <p>{detailDialog.data.task.name}</p>
                    </div>
                  )}
                </div>

                {detailDialog.data.task && (
                  <div>
                    <Label className="text-muted-foreground">执行命令</Label>
                    <pre className="mt-2 p-4 bg-muted rounded-lg text-sm overflow-x-auto font-mono">
                      {detailDialog.data.task.command}
                    </pre>
                  </div>
                )}

                {detailDialog.data.output && (
                  <div>
                    <Label className="text-muted-foreground">执行结果</Label>
                    <pre className="mt-2 p-4 bg-muted rounded-lg text-sm overflow-x-auto whitespace-pre-wrap break-words">
                      {detailDialog.data.output}
                    </pre>
                  </div>
                )}

                {detailDialog.data.error && (
                  <div>
                    <Label className="text-muted-foreground text-red-600 dark:text-red-400">错误信息</Label>
                    <pre className="mt-2 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap break-words text-red-600 dark:text-red-400">
                      {detailDialog.data.error}
                    </pre>
                  </div>
                )}
              </div>

              <DialogFooter>
                <Button variant="outline" onClick={detailDialog.closeDialog}>
                  关闭
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>执行记录列表</CardTitle>
            <div className="flex items-center gap-3">
              <Tooltip content="筛选执行状态">
                <Select
                  id="status-filter"
                  value={statusFilter}
                  onChange={(value) => setStatusFilter(value)}
                  options={[
                    { value: 'all', label: '全部状态' },
                    { value: ExecutionStatus.PENDING, label: '等待中' },
                    { value: ExecutionStatus.RUNNING, label: '运行中' },
                    { value: ExecutionStatus.SUCCESS, label: '成功' },
                    { value: ExecutionStatus.FAILED, label: '失败' },
                    { value: ExecutionStatus.TIMEOUT, label: '超时' },
                    { value: ExecutionStatus.CANCELLED, label: '已取消' },
                  ]}
                  className="min-w-[120px]"
                />
              </Tooltip>
              <div className="relative w-48">
                <Tooltip content="按任务ID筛选">
                  <Input
                    id="task-id-filter"
                    type="number"
                    placeholder="任务ID"
                    value={taskIdFilter}
                    onChange={(e) => setTaskIdFilter(e.target.value)}
                    className="h-9"
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
                    <TableHead>ID</TableHead>
                    <TableHead>任务名称</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead>开始时间</TableHead>
                    <TableHead>结束时间</TableHead>
                    <TableHead>耗时</TableHead>
                    <TableHead>重试次数</TableHead>
                    <TableHead className="text-center">操作</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {executions.map((exec) => (
                    <TableRow key={exec.id}>
                      <TableCell className="font-mono">{exec.id}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span>{exec.task?.name || '未知任务'}</span>
                          <span className="font-mono text-xs text-muted-foreground">#{exec.task_id}</span>
                        </div>
                      </TableCell>
                      <TableCell><StatusBadge status={exec.status} /></TableCell>
                      <TableCell>{formatDate(exec.started_at)}</TableCell>
                      <TableCell>{exec.finished_at ? formatDate(exec.finished_at) : '-'}</TableCell>
                      <TableCell>{formatDuration(exec.duration)}</TableCell>
                      <TableCell>{exec.retry_attempt}</TableCell>
                      <TableCell>
                        <div className="flex items-center justify-center gap-1">
                          {exec.status === ExecutionStatus.RUNNING && (
                            <Tooltip content="取消执行">
                              <Button variant="ghost" size="icon" onClick={() => cancelDialog.openDialog(exec.task_id)}>
                                <XCircle className="h-4 w-4" />
                              </Button>
                            </Tooltip>
                          )}
                          <Tooltip content="查看执行结果">
                            <Button variant="ghost" size="icon" onClick={() => handleViewDetail(exec.id)}>
                              <Eye className="h-4 w-4" />
                            </Button>
                          </Tooltip>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              {executions.length === 0 && <EmptyState message="没有找到执行记录" />}
              
              <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />
            </>
          )}
        </CardContent>
      </Card>

      <ConfirmDialog
        open={cancelDialog.open}
        onOpenChange={cancelDialog.closeDialog}
        onConfirm={handleCancel}
        title="确认取消"
        description="确定要取消这个正在执行的任务吗？"
        confirmText="取消任务"
        cancelText="返回"
      />
    </div>
  )
}
