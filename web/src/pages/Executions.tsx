import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table'
import { Select } from '../components/ui/select'
import { Tooltip } from '../components/ui/tooltip'
import { Dialog, DialogContent, DialogFooter } from '../components/ui/dialog'
import { ConfirmDialog } from '../components/ui/confirm-dialog'
import { Pagination } from '../components/ui/pagination'
import { Eye, XCircle } from 'lucide-react'
import { getExecutions, getExecution, cancelTask, type TaskExecutionDetailResponse, ExecutionStatus } from '../api'
import { useDialog, usePagination, useAsync } from '../hooks'

export default function Executions() {
  const [statusFilter, setStatusFilter] = useState<ExecutionStatus | ''>('')
  const [taskIdFilter, setTaskIdFilter] = useState('')
  
  const filters = {
    ...(statusFilter && { status: statusFilter }),
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN')
  }

  const formatDuration = (seconds: number | null) => {
    if (seconds === null || seconds === undefined) return '-'
    if (seconds < 60) return `${seconds}秒`
    if (seconds < 3600) return `${Math.floor(seconds / 60)}分${seconds % 60}秒`
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60
    return `${hours}时${minutes}分${secs}秒`
  }

  const getStatusBadge = (status: ExecutionStatus) => {
    const statusMap: Record<ExecutionStatus, { label: string; bgClass: string; textClass: string }> = {
      pending: { label: '等待中', bgClass: 'bg-muted', textClass: 'text-muted-foreground' },
      running: { label: '运行中', bgClass: 'bg-blue-500', textClass: 'text-white' },
      success: { label: '成功', bgClass: 'bg-primary', textClass: 'text-primary-foreground' },
      failed: { label: '失败', bgClass: 'bg-red-500', textClass: 'text-white' },
      timeout: { label: '超时', bgClass: 'bg-yellow-500', textClass: 'text-white' },
      cancelled: { label: '已取消', bgClass: 'bg-muted', textClass: 'text-muted-foreground' },
    }
    const { label, bgClass, textClass } = statusMap[status]
    return <span className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium ${bgClass} ${textClass}`}>{label}</span>
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">执行记录</h1>
        </div>
      </div>

      <Dialog 
        open={detailDialog.open && detailDialog.data !== null} 
        onClose={detailDialog.closeDialog} 
        title={`执行详情 #${detailDialog.data?.id || ''}`}
        maxWidth="4xl"
      >
        {detailDialog.data && (
          <>
            <DialogContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">任务ID</Label>
                  <p className="font-mono">{detailDialog.data.task_id}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">状态</Label>
                  <div className="mt-1">{getStatusBadge(detailDialog.data.status)}</div>
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
            </DialogContent>

            <DialogFooter>
              <Button variant="outline" onClick={detailDialog.closeDialog}>
                关闭
              </Button>
            </DialogFooter>
          </>
        )}
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
                  onChange={(e) => setStatusFilter(e.target.value as ExecutionStatus | '')}
                  options={[
                    { value: '', label: '全部状态' },
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
              <div className="relative w-32">
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
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            </div>
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
                      <TableCell>{getStatusBadge(exec.status)}</TableCell>
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
              {executions.length === 0 && !loading && (
                <div className="text-center py-12">
                  <p className="text-muted-foreground">没有找到执行记录</p>
                </div>
              )}
              
              <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={setCurrentPage} />
            </>
          )}
        </CardContent>
      </Card>

      <ConfirmDialog
        open={cancelDialog.open}
        onClose={cancelDialog.closeDialog}
        onConfirm={handleCancel}
        title="确认取消"
        message="确定要取消这个正在执行的任务吗？"
        confirmText="取消任务"
        cancelText="返回"
        loading={cancelling}
      />
    </div>
  )
}
