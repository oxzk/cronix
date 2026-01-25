import * as React from "react"
import { cn } from "@/lib/utils"

const DropdownMenuContext = React.createContext<{
  open: boolean
  setOpen: React.Dispatch<React.SetStateAction<boolean>>
} | null>(null)

const DropdownMenu = ({ children }: { children: React.ReactNode }) => {
  const [open, setOpen] = React.useState(false)
  const menuRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    if (open) {
      document.addEventListener('mousedown', handleClickOutside)
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [open])

  return (
    <DropdownMenuContext.Provider value={{ open, setOpen }}>
      <div ref={menuRef} className="relative inline-block">
        {children}
      </div>
    </DropdownMenuContext.Provider>
  )
}

interface DropdownMenuTriggerProps {
  children: React.ReactNode
  className?: string
  asChild?: boolean
}

const DropdownMenuTrigger = React.forwardRef<HTMLButtonElement, DropdownMenuTriggerProps>(
  ({ children, className, asChild }, ref) => {
    const context = React.useContext(DropdownMenuContext)
    if (!context) {
      throw new Error('DropdownMenuTrigger must be used within DropdownMenu')
    }
    const { open, setOpen } = context
    
    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children, {
        onClick: (e: React.MouseEvent) => {
          e.stopPropagation()
          setOpen(!open)
        },
        className: cn(className, children.props.className),
      } as any)
    }
    
    return (
      <button 
        ref={ref} 
        onClick={(e) => {
          e.stopPropagation()
          setOpen(!open)
        }} 
        className={className}
      >
        {children}
      </button>
    )
  }
)
DropdownMenuTrigger.displayName = 'DropdownMenuTrigger'

interface DropdownMenuContentProps {
  children: React.ReactNode
  className?: string
  align?: 'start' | 'end' | 'center'
}

const DropdownMenuContent = ({ children, className, align = 'end' }: DropdownMenuContentProps) => {
  const context = React.useContext(DropdownMenuContext)
  if (!context) {
    throw new Error('DropdownMenuContent must be used within DropdownMenu')
  }
  const { open } = context
  if (!open) return null
  
  const alignClass = align === 'end' ? 'right-0' : align === 'center' ? 'left-1/2 -translate-x-1/2' : 'left-0'
  
  return (
    <div className={cn(`absolute top-full mt-1 z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md ${alignClass}`, className)}>
      {children}
    </div>
  )
}

const DropdownMenuItem = ({ children, className, onClick }: { children: React.ReactNode, className?: string, onClick?: () => void }) => {
  const context = React.useContext(DropdownMenuContext)
  if (!context) {
    throw new Error('DropdownMenuItem must be used within DropdownMenu')
  }
  const { setOpen } = context
  
  return (
    <button
      onClick={(e) => {
        e.stopPropagation()
        onClick?.()
        setOpen(false)
      }}
      className={cn(
        "relative flex w-full cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
        className
      )}
    >
      {children}
    </button>
  )
}

export { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem }
