import { ReactNode } from 'react'
import clsx from 'clsx'

interface PanelProps {
  title?: string
  children: ReactNode
  className?: string
  headerAction?: ReactNode
}

const Panel = ({ title, children, className, headerAction }: PanelProps) => {
  const isFlex = className?.includes('flex-col') || className?.includes('flex-1')

  return (
    <div className={clsx('panel', isFlex && 'is-flex', className)}>
      {title && (
        <div className="panel-header flex-shrink-0">
          <h3 className="panel-title">{title}</h3>
          {headerAction}
        </div>
      )}
      <div className={clsx('panel-content', isFlex && 'flex-1 min-h-0')}>
        {children}
      </div>
    </div>
  )
}

export default Panel