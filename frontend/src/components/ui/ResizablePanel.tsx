/**
 * 可调整大小的面板组件
 * 支持鼠标拖动调整宽度和高度
 */

import { useState, useRef, useCallback, useEffect, ReactNode } from 'react'
import { Panel } from '@/components/ui'

interface ResizablePanelProps {
  title?: string
  children: ReactNode
  className?: string
  headerAction?: ReactNode
  // 初始宽度
  initialWidth?: number
  // 最小宽度
  minWidth?: number
  // 最大宽度
  maxWidth?: number
  // 初始高度
  initialHeight?: number
  // 最小高度
  minHeight?: number
  // 最大高度
  maxHeight?: number
  // 是否可调整宽度
  resizableWidth?: boolean
  // 是否可调整高度
  resizableHeight?: boolean
  // 尺寸变化回调
  onResize?: (width: number, height: number) => void
}

const ResizablePanel = ({
  title,
  children,
  className = '',
  headerAction,
  initialWidth,
  minWidth = 200,
  maxWidth = 600,
  initialHeight,
  minHeight = 100,
  maxHeight = 800,
  resizableWidth = false,
  resizableHeight = false,
  onResize,
}: ResizablePanelProps) => {
  const [width, setWidth] = useState<number | undefined>(initialWidth)
  const [height, setHeight] = useState<number | undefined>(initialHeight)
  const [isResizing, setIsResizing] = useState(false)
  const [resizeType, setResizeType] = useState<'width' | 'height' | 'both' | null>(null)
  const startPosRef = useRef({ x: 0, y: 0 })
  const startSizeRef = useRef({ width: 0, height: 0 })
  const panelRef = useRef<HTMLDivElement>(null)

  // 开始调整大小
  const handleMouseDown = useCallback(
    (e: React.MouseEvent, type: 'width' | 'height' | 'both') => {
      e.preventDefault()
      e.stopPropagation()
      setIsResizing(true)
      setResizeType(type)
      startPosRef.current = { x: e.clientX, y: e.clientY }
      startSizeRef.current = {
        width: panelRef.current?.offsetWidth || 0,
        height: panelRef.current?.offsetHeight || 0,
      }
    },
    []
  )

  // 调整大小
  useEffect(() => {
    if (!isResizing) return

    const handleMouseMove = (e: MouseEvent) => {
      const deltaX = e.clientX - startPosRef.current.x
      const deltaY = e.clientY - startPosRef.current.y

      if (resizeType === 'width' || resizeType === 'both') {
        const newWidth = Math.min(maxWidth, Math.max(minWidth, startSizeRef.current.width + deltaX))
        setWidth(newWidth)
      }

      if (resizeType === 'height' || resizeType === 'both') {
        const newHeight = Math.min(maxHeight, Math.max(minHeight, startSizeRef.current.height + deltaY))
        setHeight(newHeight)
      }
    }

    const handleMouseUp = () => {
      setIsResizing(false)
      setResizeType(null)
      if (onResize && width && height) {
        onResize(width, height)
      }
    }

    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isResizing, resizeType, minWidth, maxWidth, minHeight, maxHeight, onResize, width, height])

  const style: React.CSSProperties = {}
  if (width !== undefined) style.width = width
  if (height !== undefined) style.height = height

  return (
    <div
      ref={panelRef}
      className={`relative ${className}`}
      style={style}
    >
      <Panel title={title} className="h-full" headerAction={headerAction}>
        {children}
      </Panel>

      {/* 宽度调整手柄（右侧） */}
      {resizableWidth && (
        <div
          className={`absolute top-0 right-0 w-1 h-full cursor-ew-resize group ${
            isResizing && resizeType === 'width' ? 'bg-signal-blue' : 'hover:bg-signal-blue/50'
          }`}
          onMouseDown={(e) => handleMouseDown(e, 'width')}
        >
          <div className="absolute top-1/2 right-0 w-1 h-8 -translate-y-1/2 bg-gray-600 rounded opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      )}

      {/* 高度调整手柄（底部） */}
      {resizableHeight && (
        <div
          className={`absolute bottom-0 left-0 w-full h-1 cursor-ns-resize group ${
            isResizing && resizeType === 'height' ? 'bg-signal-blue' : 'hover:bg-signal-blue/50'
          }`}
          onMouseDown={(e) => handleMouseDown(e, 'height')}
        >
          <div className="absolute left-1/2 bottom-0 w-8 h-1 -translate-x-1/2 bg-gray-600 rounded opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      )}
    </div>
  )
}

export default ResizablePanel