import type * as React from 'react';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';

import { AppLayout } from 'layouts/AppLayout';
import { SettingsPage } from 'pages/SettingsPage';
import { useThemeStore } from 'store/themeStore';

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter
        initialEntries={['/']}
        future={{ v7_startTransition: true, v7_relativeSplatPath: true }}
      >
        <Routes>
          <Route path="/" element={ui} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe('app shell foundation', () => {
  beforeEach(() => {
    useThemeStore.setState({ theme: 'light' });
  });

  it('renders sidebar navigation and global header controls', () => {
    renderWithProviders(<AppLayout />);

    expect(screen.getByLabelText('Primary navigation')).toBeInTheDocument();
    expect(screen.getByLabelText('Global search')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /notifications/i })).toBeInTheDocument();
  });

  it('supports mobile navigation trigger', () => {
    renderWithProviders(<AppLayout />);

    fireEvent.click(screen.getByRole('button', { name: /open navigation/i }));

    expect(screen.getByLabelText('Mobile navigation')).toBeInTheDocument();
  });

  it('switches theme from settings controls', () => {
    renderWithProviders(<SettingsPage />);

    fireEvent.click(screen.getByRole('button', { name: 'dark' }));

    expect(useThemeStore.getState().theme).toBe('dark');
  });
});
