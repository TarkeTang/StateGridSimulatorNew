import { ReactNode, Component, ErrorInfo } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <h2 className="text-xl text-signal-red mb-2">出现错误</h2>
            <p className="text-gray-400">请刷新页面重试</p>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary