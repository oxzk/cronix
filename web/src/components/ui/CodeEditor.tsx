import { useRef, useEffect } from 'react'
import Editor from '@monaco-editor/react'
import { ScriptType } from '../../api/types'

interface CodeEditorProps {
  value: string
  onChange: (value: string | undefined) => void
  language: string
  height?: string
  readOnly?: boolean
}

export function CodeEditor({ value, onChange, language, height = '300px', readOnly = false }: CodeEditorProps) {
  const editorRef = useRef<any>(null)

  const handleEditorDidMount = (editor: any) => {
    editorRef.current = editor
  }

  const getLanguageFromScriptType = (type: ScriptType): string => {
    switch (type) {
      case ScriptType.PYTHON:
        return 'python'
      case ScriptType.NODE:
        return 'javascript'
      case ScriptType.SHELL:
        return 'shell'
      default:
        return 'python'
    }
  }

  return (
    <div className="border border-input rounded-md overflow-hidden">
      <Editor
        height={height}
        defaultLanguage={language}
        language={language}
        value={value}
        onChange={onChange}
        onMount={handleEditorDidMount}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          readOnly: readOnly,
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 4,
          wordWrap: 'on',
          formatOnPaste: true,
          formatOnType: true,
          overflow: 'hidden',
        }}
      />
    </div>
  )
}
