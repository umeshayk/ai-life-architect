import { RouterProvider } from 'react-router-dom';

import { AppErrorBoundary } from 'components/feedback/AppErrorBoundary';
import { ThemeProvider } from 'app/ThemeProvider';
import { router } from 'routes/router';

export function App() {
  return (
    <ThemeProvider>
      <AppErrorBoundary>
        <RouterProvider router={router} />
      </AppErrorBoundary>
    </ThemeProvider>
  );
}
