import { ReactNode } from 'react'
import clsx from 'clsx'

interface PanelProps {
  title?: string
  children: ReactNode
  className?: string
  headerAction?: ReactNode
}

const Panel = ({ title, children, className, headerAction }: PanelProps) => {
  return (
    <div className={clsx('panel', className)}>
      {title && (
        <div className="panel-header">
          <h3 className="panel-title">{title}</h3>
          {headerAction}
        </div>
      )}
      <div className={clsx('panel-content', className?.includes('flex-col') && 'flex-1 min-h-0')}>
        {children}
      </div>
    </div>
  )
}

export default Panel