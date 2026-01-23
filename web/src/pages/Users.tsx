import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Avatar, AvatarFallback } from '../components/ui/avatar'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table'
import { Search, Plus, MoreHorizontal, Shield, ShieldCheck, Trash2 } from 'lucide-react'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu'

interface User {
  id: number
  name: string
  email: string
  role: 'admin' | 'user' | 'editor'
  status: 'active' | 'inactive'
  createdAt: string
}

const mockUsers: User[] = [
  { id: 1, name: '张三', email: 'zhangsan@example.com', role: 'admin', status: 'active', createdAt: '2024-01-15' },
  { id: 2, name: '李四', email: 'lisi@example.com', role: 'user', status: 'active', createdAt: '2024-01-16' },
  { id: 3, name: '王五', email: 'wangwu@example.com', role: 'editor', status: 'inactive', createdAt: '2024-01-17' },
  { id: 4, name: '赵六', email: 'zhaoliu@example.com', role: 'user', status: 'active', createdAt: '2024-01-18' },
  { id: 5, name: '孙七', email: 'sunqi@example.com', role: 'user', status: 'active', createdAt: '2024-01-19' },
  { id: 6, name: '周八', email: 'zhouba@example.com', role: 'editor', status: 'inactive', createdAt: '2024-01-20' },
]

const roleMap = {
  admin: { label: '管理员', icon: Shield, className: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300' },
  editor: { label: '编辑', icon: ShieldCheck, className: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300' },
  user: { label: '普通用户', className: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300' },
}

const statusMap = {
  active: { label: '活跃', className: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' },
  inactive: { label: '禁用', className: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300' },
}

export default function Users() {
  const [users, setUsers] = useState<User[]>(mockUsers)
  const [searchQuery, setSearchQuery] = useState('')

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleDelete = (id: number) => {
    setUsers(users.filter(user => user.id !== id))
  }

  const getInitials = (name: string) => {
    return name.slice(0, 2).toUpperCase()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">用户管理</h1>
          <p className="text-muted-foreground mt-1">
            管理系统用户及权限
          </p>
        </div>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          添加用户
        </Button>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>用户列表</CardTitle>
            <div className="relative w-64">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="搜索用户..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>用户</TableHead>
                <TableHead>角色</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>创建时间</TableHead>
                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredUsers.map((user) => {
                const roleInfo = roleMap[user.role]
                const statusInfo = statusMap[user.status]
                const RoleIcon = roleInfo.icon

                return (
                  <TableRow key={user.id}>
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-9 w-9">
                          <AvatarFallback className="bg-primary/10 text-primary font-semibold">
                            {getInitials(user.name)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-medium">{user.name}</div>
                          <div className="text-sm text-muted-foreground">
                            {user.email}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${roleInfo.className}`}>
                        {roleInfo.icon && <RoleIcon className="h-3 w-3" />}
                        {roleInfo.label}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${statusInfo.className}`}>
                        {statusInfo.label}
                      </div>
                    </TableCell>
                    <TableCell>{user.createdAt}</TableCell>
                    <TableCell className="text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>编辑</DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-red-600 dark:text-red-500"
                            onClick={() => handleDelete(user.id)}
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            删除
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
          {filteredUsers.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">没有找到用户</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
