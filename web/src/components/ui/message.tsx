import { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { X } from 'lucide-react'
import { Button } from './button'

export type MessageType = 'success' | 'error' | 'warning' | 'info'

export interface MessageProps {
  type?: MessageType
  message: string
  duration?: number
  onClose?: () => void
}

const typeStyles = {
  success: {
    container: 'bg-primary text-primary-foreground',
    icon: '✓',
  },
  error: {
    container: 'bg-red-500 text-white',
    icon: '✗',
  },
  warning: {
    container: 'bg-yellow-500 text-white',
    icon: '!',
  },
  info: {
    container: 'bg-blue-500 text-white',
    icon: 'i',
  },
}

export function Message({ type = 'info', message, duration = 5000, onClose }: MessageProps) {
  const [visible, setVisible] = useState(true)
  const styles = typeStyles[type]

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        handleClose()
      }, duration)
      return () => clearTimeout(timer)
    }
  }, [duration])

  const handleClose = () => {
    setVisible(false)
    onClose?.()
  }

  if (!visible || !message) return null

  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 animate-in fade-in slide-in-from-top-5 duration-300">
      <div className={`flex items-center gap-3 rounded-md px-4 py-3 ${styles.container} shadow-lg min-w-[300px]`}>
        <div className="flex-shrink-0 w-5 h-5 flex items-center justify-center font-bold text-lg">
          {styles.icon}
        </div>
        <div className="flex-1 text-sm font-medium">
          {message}
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="flex-shrink-0 h-6 w-6 p-0 hover:bg-white/20 text-current"
          onClick={handleClose}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}

// 使用 useState 管理消息的全局 Hook
export function useMessage() {
  const [message, setMessage] = useState<{ text: string; type: MessageType } | null>(null)

  const showMessage = (text: string, type: MessageType = 'info') => {
    setMessage({ text, type })
  }

  const hideMessage = () => {
    setMessage(null)
  }

  const MessageComponent = () => (
    <Message
      type={message?.type}
      message={message?.text || ''}
      onClose={hideMessage}
    />
  )

  return { showMessage, hideMessage, MessageComponent }
}

// 全局消息管理器
class MessageManager {
  private container: HTMLElement | null = null
  private root: any = null

  private ensureContainer() {
    if (!this.container) {
      this.container = document.createElement('div')
      this.container.id = 'message-container'
      document.body.appendChild(this.container)
      this.root = createRoot(this.container)
    }
  }

  show(message: string, type: MessageType = 'info', duration = 5000) {
    this.ensureContainer()
    
    const handleClose = () => {
      if (this.root) {
        this.root.render(null)
      }
    }

    if (this.root) {
      this.root.render(
        <Message
          type={type}
          message={message}
          duration={duration}
          onClose={handleClose}
        />
      )
    }
  }

  success(message: string, duration?: number) {
    this.show(message, 'success', duration)
  }

  error(message: string, duration?: number) {
    this.show(message, 'error', duration)
  }

  warning(message: string, duration?: number) {
    this.show(message, 'warning', duration)
  }

  info(message: string, duration?: number) {
    this.show(message, 'info', duration)
  }
}

// 导出全局消息实例
export const message = new MessageManager()
