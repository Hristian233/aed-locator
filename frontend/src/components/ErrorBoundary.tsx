import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(): State {
    return { hasError: true }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('UI error:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback ?? (
          <div className="flex min-h-[40vh] flex-col items-center justify-center gap-3 p-8 text-center">
            <h2 className="text-lg font-semibold text-slate-900">Something went wrong</h2>
            <p className="max-w-md text-sm text-slate-600">
              Please refresh the page. If the problem continues, try again later.
            </p>
            <button
              type="button"
              className="rounded-full bg-teal-600 px-5 py-2 text-sm font-medium text-white"
              onClick={() => window.location.reload()}
            >
              Reload
            </button>
          </div>
        )
      )
    }
    return this.props.children
  }
}
