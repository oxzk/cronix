import * as React from "react"
import { cn } from "@/lib/utils"
import { ButtonHTMLAttributes } from 'react'

const DropdownMenuContext = React.createContext<{
  open: boolean
  setOpen: React.Dispatch<React.SetStateAction<boolean>>
} | null>(null)

const DropdownMenu = ({ children }: { children: React.ReactNode }) => {
  const [open, setOpen] = React.useState(false)
  return (
    <DropdownMenuContext.Provider value={{ open, setOpen }}>
      {children}
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
    const { open, setOpen } = React.useContext(DropdownMenuContext)!
    
    if (asChild && React.isValidElement(children)) {
      return React.cloneElement(children, {
        onClick: () => setOpen(!open),
        className: cn(className, children.props.className),
      } as any)
    }
    
    return (
      <button ref={ref} onClick={() => setOpen(!open)} className={className}>
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
  const { open, setOpen } = React.useContext(DropdownMenuContext)!
  if (!open) return null
  
  const alignClass = align === 'end' ? 'right-0' : align === 'center' ? 'left-1/2 -translate-x-1/2' : 'left-0'
  
  return (
    <div className={cn(`absolute top-full z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md ${alignClass}`, className)}>
      {children}
    </div>
  )
}

const DropdownMenuItem = ({ children, className, onClick }: { children: React.ReactNode, className?: string, onClick?: () => void }) => {
  const { setOpen } = React.useContext(DropdownMenuContext)!
  return (
    <button
      onClick={() => {
        onClick?.()
        setOpen(false)
      }}
      className={cn(
        "relative flex cursor-default select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
        className
      )}
    >
      {children}
    </button>
  )
}

export { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem }
