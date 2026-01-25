import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../lib/components'
import { Users, Activity, DollarSign, TrendingUp, ArrowUpRight, ArrowDownRight } from 'lucide-react'

const stats = [
  {
    title: '总用户数',
    value: '12,345',
    change: '+20.1%',
    trend: 'up',
    icon: Users,
  },
  {
    title: '活跃用户',
    value: '8,234',
    change: '+15.3%',
    trend: 'up',
    icon: Activity,
  },
  {
    title: '总收入',
    value: '¥234,567',
    change: '+8.2%',
    trend: 'up',
    icon: DollarSign,
  },
  {
    title: '增长率',
    value: '12.5%',
    change: '-2.4%',
    trend: 'down',
    icon: TrendingUp,
  },
]

const recentActivity = [
  { id: 1, user: '张三', action: '创建了新项目', time: '5分钟前' },
  { id: 2, user: '李四', action: '更新了用户资料', time: '15分钟前' },
  { id: 3, user: '王五', action: '删除了评论', time: '30分钟前' },
  { id: 4, user: '赵六', action: '发布了新文章', time: '1小时前' },
  { id: 5, user: '孙七', action: '修改了系统设置', time: '2小时前' },
]

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">仪表盘</h1>
        <p className="text-muted-foreground mt-1">欢迎回来，这是今天的概览</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <p className={`text-xs mt-1 flex items-center ${
                  stat.trend === 'up' ? 'text-green-600 dark:text-green-500' : 'text-red-600 dark:text-red-500'
                }`}>
                  {stat.trend === 'up' ? (
                    <ArrowUpRight className="h-3 w-3 mr-1" />
                  ) : (
                    <ArrowDownRight className="h-3 w-3 mr-1" />
                  )}
                  较上月 {stat.change}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* 内容区域 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>数据趋势</CardTitle>
            <CardDescription>
              过去 30 天的用户活动统计
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] flex items-center justify-center bg-muted/20 rounded-lg">
              <div className="text-center space-y-2">
                <Activity className="h-12 w-12 mx-auto text-muted-foreground" />
                <p className="text-sm text-muted-foreground">
                  图表区域 - 可以集成 Chart.js 或 Recharts
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>最近活动</CardTitle>
            <CardDescription>
              最新的系统动态
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity) => (
                <div key={activity.id} className="flex items-start gap-3">
                  <div className="w-2 h-2 mt-2 rounded-full bg-primary" />
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium leading-none">
                      {activity.user} {activity.action}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {activity.time}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
