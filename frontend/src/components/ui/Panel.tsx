import { ReactNode } from 'react'
import clsx from 'clsx'

interface PanelProps {
  title?: string
  children: ReactNode
  className?: string
  headerAction?: ReactNode
}

const Panel = ({ title, children, className, headerAction }: PanelProps) => {
  const isFlex = className?.includes('is-flex')

  return (
    <div className={clsx('panel', isFlex && 'is-flex', className)}>
      {title && (
        <div className="panel-header flex-shrink-0">
          <h3 className="panel-title">{title}</h3>
          {headerAction}
        </div>
      )}
      <div className={clsx('panel-content', isFlex && 'is-flex-content')}>
        {children}
      </div>
    </div>
  )
}

export default Panel