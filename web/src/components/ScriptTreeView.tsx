// ScriptTreeView - 脚本树形视图组件
import * as React from 'react'
import { ChevronRight, ChevronDown, File, Folder, FolderOpen } from 'lucide-react'
import { cn } from '../lib/utils'

export interface TreeNode {
  id: string
  name: string
  type: 'file' | 'folder'
  children?: TreeNode[]
  path?: string
}

interface ScriptTreeViewProps {
  data?: TreeNode[]
  nodes?: any[]
  onSelect?: (node: TreeNode) => void
  onEdit?: (name: string) => void
  onDelete?: (name: string) => void
  selectedId?: string
  className?: string
}

export const ScriptTreeView: React.FC<ScriptTreeViewProps> = ({
  data,
  nodes,
  onSelect,
  onEdit,
  onDelete,
  selectedId,
  className,
}) => {
  const [expandedIds, setExpandedIds] = React.useState<Set<string>>(new Set())
  
  // 支持 data 或 nodes 属性
  const treeData = data || nodes || []

  const toggleExpand = (id: string) => {
    const newExpanded = new Set(expandedIds)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedIds(newExpanded)
  }

  const renderNode = (node: TreeNode, level: number = 0) => {
    const isExpanded = expandedIds.has(node.id)
    const isSelected = selectedId === node.id
    const hasChildren = node.children && node.children.length > 0

    return (
      <div key={node.id}>
        <div
          className={cn(
            'flex items-center gap-2 px-2 py-1.5 rounded-md cursor-pointer hover:bg-accent',
            isSelected && 'bg-accent',
            className
          )}
          style={{ paddingLeft: `${level * 16 + 8}px` }}
          onClick={() => {
            if (node.type === 'folder') {
              toggleExpand(node.id)
            }
            onSelect?.(node)
          }}
        >
          {node.type === 'folder' ? (
            <>
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
              {isExpanded ? (
                <FolderOpen className="h-4 w-4 text-blue-500" />
              ) : (
                <Folder className="h-4 w-4 text-blue-500" />
              )}
            </>
          ) : (
            <>
              <span className="w-4" />
              <File className="h-4 w-4 text-gray-500" />
            </>
          )}
          <span className="text-sm">{node.name}</span>
        </div>
        {hasChildren && isExpanded && (
          <div>
            {node.children!.map((child) => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return <div className={className}>{treeData.map((node: any) => renderNode(node))}</div>
}
