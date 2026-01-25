import { useState } from 'react'
import { ChevronRight, ChevronDown, File, FileJson, Terminal, Folder, Edit, Trash2 } from 'lucide-react'
import { Button } from './button'
import { Tooltip } from './tooltip'
import { ScriptType, type ScriptTreeNode } from '../../api/types'

interface ScriptTreeViewProps {
  nodes: ScriptTreeNode[]
  onEdit: (name: string) => void
  onDelete: (name: string) => void
}

export function ScriptTreeView({ nodes, onEdit, onDelete }: ScriptTreeViewProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())

  const toggleNode = (path: string) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
    }
    setExpandedNodes(newExpanded)
  }

  const getScriptTypeIcon = (type: ScriptType) => {
    switch (type) {
      case ScriptType.PYTHON:
        return <Terminal className="h-5 w-5 text-blue-500" />
      case ScriptType.NODE:
        return <FileJson className="h-5 w-5 text-green-500" />
      case ScriptType.SHELL:
        return <Terminal className="h-5 w-5 text-yellow-500" />
      default:
        return <File className="h-5 w-5 text-muted-foreground" />
    }
  }

  const renderNode = (node: ScriptTreeNode, level: number = 0) => {
    const isExpanded = expandedNodes.has(node.path)
    const hasChildren = node.children && node.children.length > 0
    const paddingLeft = level * 16

    return (
      <div key={node.path} className="select-none">
        <div
          className="flex items-center gap-2 py-1.5 px-2 hover:bg-muted/50 rounded-md cursor-pointer group transition-colors"
          style={{ paddingLeft: `${paddingLeft + 8}px` }}
          onClick={() => hasChildren && toggleNode(node.path)}
        >
          {hasChildren ? (
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5 p-0 shrink-0"
              onClick={(e) => {
                e.stopPropagation()
                toggleNode(node.path)
              }}
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4 text-muted-foreground" />
              ) : (
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
              )}
            </Button>
          ) : (
            <div className="w-5 shrink-0" />
          )}

          {node.type === 'directory' ? (
            <Folder className="h-6 w-6 text-orange-500" />
          ) : node.script_type ? (
            getScriptTypeIcon(node.script_type)
          ) : (
            <File className="h-5 w-5 text-muted-foreground" />
          )}

          <span className="flex-1 text-sm font-mono truncate">{node.name}</span>

          {node.type === 'file' && (
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
              <Tooltip content="编辑脚本">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7"
                  onClick={(e) => {
                    e.stopPropagation()
                    onEdit(node.path)
                  }}
                >
                  <Edit className="h-3.5 w-3.5" />
                </Button>
              </Tooltip>
              <Tooltip content="删除脚本">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-7 w-7 hover:text-destructive"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDelete(node.path)
                  }}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </Tooltip>
            </div>
          )}
        </div>

        {hasChildren && isExpanded && (
          <div>
            {node.children!.map((child) => renderNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  if (nodes.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">没有脚本</p>
      </div>
    )
  }

  return (
    <div className="py-2">
      {nodes.map((node) => renderNode(node))}
    </div>
  )
}
