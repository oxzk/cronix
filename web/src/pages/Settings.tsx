import { useState, useEffect, useRef } from 'react'
import QRCode from 'qrcode'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Shield, Bell, Key, Edit, Save } from 'lucide-react'
import {
  getTwoFactorAuthInfo,
  getNotifications,
  updateUserSettings,
  updateNotification,
  type TwoFactorAuthInfo,
  type NotifyType,
  type NotificationListItem
} from '../api'
import { message } from '../components/ui/message'

export default function Settings() {
  const [activeTab, setActiveTab] = useState<'2fa' | 'notifications' | 'password'>('2fa')
  const [loading, setLoading] = useState(true)

  // 2FA 状态
  const [twoFactorInfo, setTwoFactorInfo] = useState<TwoFactorAuthInfo | null>(null)
  const [totpCode, setTotpCode] = useState('')
  const qrCodeRef = useRef<HTMLCanvasElement>(null)
  const [enabling2FA, setEnabling2FA] = useState(false)
  const [disabling2FA, setDisabling2FA] = useState(false)
  
  // 密码修改
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [changingPassword, setChangingPassword] = useState(false)

  // 通知配置
  const [notifications, setNotifications] = useState<Record<string, NotificationListItem>>({})
  const [editingNotification, setEditingNotification] = useState<string | null>(null)
  const [notificationForm, setNotificationForm] = useState<{
    webhook_url?: string
    secret?: string
    bot_token?: string
    chat_id?: string | number
    url?: string
  }>({})
  const [notificationSaving, setNotificationSaving] = useState(false)
  const [notificationError, setNotificationError] = useState('')

  useEffect(() => {
    const loadSettings = async () => {
      try {
        setLoading(true)
        console.log('Loading settings...')
        const [twoFactorData, notificationsData] = await Promise.all([
          getTwoFactorAuthInfo(),
          getNotifications(),
        ])
        setTwoFactorInfo(twoFactorData)
        setNotifications(notificationsData)
      } catch (error) {
        console.error('Failed to load settings:', error)
      } finally {
        setLoading(false)
      }
    }

    loadSettings()
  }, [])

  // 生成二维码
  useEffect(() => {
    if (twoFactorInfo?.totp_uri && qrCodeRef.current) {
      QRCode.toCanvas(qrCodeRef.current, twoFactorInfo.totp_uri, {
        width: 200,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#ffffff',
        },
      })
    }
  }, [twoFactorInfo])

  const handleEnable2FA = async () => {
    if (!totpCode) {
      message.warning('请输入 2FA 验证码')
      return
    }

    try {
      setEnabling2FA(true)
      await updateUserSettings({ is_2fa_enabled: true, totp_code: totpCode })
      message.success('2FA 已启用')
      setTotpCode('')
      window.location.reload()
    } catch (error: any) {
      message.error(error.message || '启用 2FA 失败')
    } finally {
      setEnabling2FA(false)
    }
  }

  const handleDisable2FA = async () => {
    if (!twoFactorInfo?.is_2fa_enabled) return

    const code = prompt('请输入 2FA 验证码以禁用:')
    if (!code) return

    try {
      setDisabling2FA(true)
      await updateUserSettings({ is_2fa_enabled: false, totp_code: code })
      message.success('2FA 已禁用')
      window.location.reload()
    } catch (error: any) {
      message.error(error.message || '禁用 2FA 失败')
    } finally {
      setDisabling2FA(false)
    }
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setPasswordError('')

    if (newPassword !== confirmPassword) {
      setPasswordError('两次输入的密码不一致')
      return
    }

    if (newPassword.length < 6) {
      setPasswordError('密码长度至少为 6 位')
      return
    }

    try {
      setChangingPassword(true)
      await updateUserSettings({ password: newPassword })
      message.success('密码修改成功')
      setNewPassword('')
      setConfirmPassword('')
    } catch (error: any) {
      setPasswordError(error.message || '密码修改失败')
    } finally {
      setChangingPassword(false)
    }
  }

  const handleEditNotification = (type: string) => {
    const config = notifications[type]
    setEditingNotification(type)
    setNotificationForm({
      webhook_url: config.webhook_url || '',
      secret: config.secret || '',
      bot_token: config.bot_token || '',
      chat_id: config.chat_id || '',
      url: config.url || '',
    })
    setNotificationError('')
    
  }

  const handleCancelEdit = () => {
    setEditingNotification(null)
    setNotificationForm({})
    setNotificationError('')
  }

  const handleSaveNotification = async () => {
    if (!editingNotification) return

    const notification = notifications[editingNotification]
    const config: Record<string, any> = {}

    if (editingNotification === 'webhook') {
      if (!notificationForm.url) {
        setNotificationError('请输入 Webhook URL')
        return
      }
      config.url = notificationForm.url
    } else if (editingNotification === 'telegram') {
      if (!notificationForm.bot_token) {
        setNotificationError('请输入 Bot Token')
        return
      }
      if (!notificationForm.chat_id) {
        setNotificationError('请输入 Chat ID')
        return
      }
      config.bot_token = notificationForm.bot_token
      config.chat_id = notificationForm.chat_id
    } else if (editingNotification === 'dingtalk') {
      if (!notificationForm.webhook_url) {
        setNotificationError('请输入 Webhook URL')
        return
      }
      if (!notificationForm.secret) {
        setNotificationError('请输入 Secret')
        return
      }
      config.webhook_url = notificationForm.webhook_url
      config.secret = notificationForm.secret
    }

    try {
      setNotificationSaving(true)
      await updateNotification(notification.id, {
        notify_type: editingNotification as NotifyType,
        config: config as any,
      })
      
      // 更新本地状态
      setNotifications({
        ...notifications,
        [editingNotification]: {
          ...notification,
          ...config,
        },
      })
      
      message.success('通知配置更新成功')
      setEditingNotification(null)
      setNotificationForm({})
    } catch (error: any) {
      setNotificationError(error.message || '更新失败')
    } finally {
      setNotificationSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex items-center justify-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">系统设置</h1>
        <p className="text-muted-foreground mt-1">
          管理您的账户和系统配置
        </p>
      </div>

      {/* 标签页导航 */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab('2fa')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === '2fa'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Shield className="inline w-4 h-4 mr-2" />
          双因素认证
        </button>
        <button
          onClick={() => setActiveTab('notifications')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'notifications'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Bell className="inline w-4 h-4 mr-2" />
          通知配置
        </button>
        <button
          onClick={() => setActiveTab('password')}
          className={`px-4 py-2 font-medium transition-colors ${
            activeTab === 'password'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Key className="inline w-4 h-4 mr-2" />
          修改密码
        </button>
      </div>

      {/* 2FA 设置 */}
      {activeTab === '2fa' && twoFactorInfo && (
        <Card>
          <CardHeader>
            <CardTitle>双因素认证 (2FA)</CardTitle>
            <CardDescription>
              使用 TOTP 应用程序（如 Google Authenticator）扫描下方二维码来启用双因素认证
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <div className="text-sm font-medium mb-2">当前状态:</div>
              <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                twoFactorInfo.is_2fa_enabled
                  ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300'
                  : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300'
              }`}>
                {twoFactorInfo.is_2fa_enabled ? '已启用' : '未启用'}
              </div>
            </div>

            {!twoFactorInfo.is_2fa_enabled && (
              <>
                  <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Secret Key:</Label>
                    <Input
                      value={twoFactorInfo.totp_secret_key}
                      readOnly
                      className="font-mono text-sm"
                    />
                  </div>

                  <div>
                    <div className="bg-white rounded-lg inline-block">
                      <canvas ref={qrCodeRef} />
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="totp-code">输入验证码以启用:</Label>
                  <Input
                    id="totp-code"
                    type="text"
                    placeholder="输入 6 位验证码"
                    value={totpCode}
                    onChange={(e) => setTotpCode(e.target.value)}
                    maxLength={6}
                    className="w-48"
                  />
                </div>

                <Button onClick={handleEnable2FA} disabled={!totpCode || enabling2FA}>
                  {enabling2FA ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                      启用中...
                    </>
                  ) : (
                    '启用 2FA'
                  )}
                </Button>
              </>
            )}

            {twoFactorInfo.is_2fa_enabled && (
              <Button onClick={handleDisable2FA} variant="outline" disabled={disabling2FA}>
                {disabling2FA ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                    禁用中...
                  </>
                ) : (
                  '禁用 2FA'
                )}
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* 通知配置 */}
      {activeTab === 'notifications' && (
        <Card>
          <CardHeader>
            <CardTitle>通知配置</CardTitle>
            <CardDescription>
              管理任务执行完成后的通知方式
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {notificationError && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
                  {notificationError}
                </div>
              )}

              {Object.entries(notifications).map(([type, config]: [string, NotificationListItem]) => (
                <div key={type} className="p-4 border rounded-lg">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium capitalize">{type}</h3>
                    {!editingNotification && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEditNotification(type)}
                      >
                        <Edit className="w-4 h-4 mr-1" />
                        编辑
                      </Button>
                    )}
                  </div>

                  {editingNotification === type ? (
                    <div className="space-y-3">
                      {type === 'webhook' && (
                        <div className="space-y-2">
                          <Label htmlFor="webhook-url">Webhook URL</Label>
                          <Input
                            id="webhook-url"
                            placeholder="https://example.com/webhook"
                            value={notificationForm.url || ''}
                            onChange={(e) => setNotificationForm({ ...notificationForm, url: e.target.value })}
                          />
                        </div>
                      )}

                      {type === 'telegram' && (
                        <>
                          <div className="space-y-2">
                            <Label htmlFor="telegram-bot-token">Bot Token</Label>
                            <Input
                              id="telegram-bot-token"
                              placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
                              value={notificationForm.bot_token || ''}
                              onChange={(e) => setNotificationForm({ ...notificationForm, bot_token: e.target.value })}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="telegram-chat-id">Chat ID</Label>
                            <Input
                              id="telegram-chat-id"
                              placeholder="-123456789"
                              value={notificationForm.chat_id || ''}
                              onChange={(e) => setNotificationForm({ ...notificationForm, chat_id: e.target.value })}
                            />
                          </div>
                        </>
                      )}

                      {type === 'dingtalk' && (
                        <>
                          <div className="space-y-2">
                            <Label htmlFor="dingtalk-webhook-url">Webhook URL</Label>
                            <Input
                              id="dingtalk-webhook-url"
                              placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxx"
                              value={notificationForm.webhook_url || ''}
                              onChange={(e) => setNotificationForm({ ...notificationForm, webhook_url: e.target.value })}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="dingtalk-secret">Secret</Label>
                            <Input
                              id="dingtalk-secret"
                              placeholder="SECxxxxxxxxxxxxxxxxxxxxxxxx"
                              value={notificationForm.secret || ''}
                              onChange={(e) => setNotificationForm({ ...notificationForm, secret: e.target.value })}
                            />
                          </div>
                        </>
                      )}

                      <div className="flex gap-2">
                        <Button onClick={handleSaveNotification} disabled={notificationSaving}>
                          {notificationSaving ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                              保存中...
                            </>
                          ) : (
                            <>
                              <Save className="w-4 h-4 mr-1" />
                              保存
                            </>
                          )}
                        </Button>
                        <Button onClick={handleCancelEdit} variant="outline" disabled={notificationSaving}>
                          取消
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-1 text-sm text-muted-foreground">
                      {type === 'webhook' && <div>URL: {config.url || '未配置'}</div>}
                      {type === 'telegram' && (
                        <>
                          <div>Bot Token: {config.bot_token ? '已配置' : '未配置'}</div>
                          <div>Chat ID: {config.chat_id || '未配置'}</div>
                        </>
                      )}
                      {type === 'dingtalk' && (
                        <>
                          <div>Webhook URL: {config.webhook_url ? '已配置' : '未配置'}</div>
                          <div>Secret: {config.secret ? '已配置' : '未配置'}</div>
                        </>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {Object.keys(notifications).length === 0 && (
                <p className="text-muted-foreground text-center py-8">暂无通知配置</p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 修改密码 */}
      {activeTab === 'password' && (
        <Card>
          <CardHeader>
            <CardTitle>修改密码</CardTitle>
            <CardDescription>
              为了安全起见，建议定期更换密码
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleChangePassword} className="space-y-4 max-w-md">
              {passwordError && (
                <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg text-sm">
                  {passwordError}
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="new-password">新密码</Label>
                <Input
                  id="new-password"
                  type="password"
                  placeholder="输入新密码"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm-password">确认新密码</Label>
                <Input
                  id="confirm-password"
                  type="password"
                  placeholder="再次输入新密码"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>
              <Button type="submit" disabled={changingPassword}>
                {changingPassword ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                    修改中...
                  </>
                ) : (
                  '修改密码'
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
