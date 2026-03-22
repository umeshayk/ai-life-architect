import { Component, type ErrorInfo, type ReactNode } from 'react';

import { EmptyState } from './EmptyState';

type Props = {
  children: ReactNode;
};

type State = {
  hasError: boolean;
};

export class AppErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Application error boundary captured an error.', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <EmptyState
          title="Workspace unavailable"
          description="The application shell hit an unexpected error. Refresh the page or review the browser console for details."
          actionLabel="Reload"
          onAction={() => window.location.reload()}
        />
      );
    }

    return this.props.children;
  }
}
