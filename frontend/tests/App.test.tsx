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
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: query === '(max-width: 1023px)',
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });
  });

  it('renders sidebar navigation and global header controls', () => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    renderWithProviders(<AppLayout />);

    expect(screen.getByLabelText('Primary navigation')).toBeInTheDocument();
    expect(screen.getAllByLabelText('Global search').length).toBeGreaterThan(0);
    expect(screen.getAllByRole('button', { name: /notifications/i }).length).toBeGreaterThan(0);
  });

  it('supports mobile navigation trigger', () => {
    renderWithProviders(<AppLayout />);

    fireEvent.click(screen.getByRole('button', { name: /open navigation/i }));

    expect(screen.getByLabelText('Mobile navigation')).toBeInTheDocument();
  });

  it('uses compact mobile header actions and reveals search on demand', () => {
    renderWithProviders(<AppLayout />);

    expect(screen.getByRole('button', { name: /toggle search/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /more actions/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /toggle search/i }));

    expect(document.querySelector('.mobile-search-panel--open')).toBeInTheDocument();
  });

  it('collapses desktop sidebar when the header menu button is used on wide screens', () => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    renderWithProviders(<AppLayout />);

    fireEvent.click(screen.getByRole('button', { name: /open navigation/i }));

    expect(document.querySelector('.app-shell__body--collapsed')).toBeInTheDocument();
  });

  it('switches theme from settings controls', () => {
    renderWithProviders(<SettingsPage />);

    fireEvent.click(screen.getByRole('button', { name: 'dark' }));

    expect(useThemeStore.getState().theme).toBe('dark');
  });

  it('shows a tooltip for header icon actions', () => {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    renderWithProviders(<AppLayout />);

    fireEvent.mouseEnter(screen.getAllByRole('button', { name: /notifications/i })[0]);

    expect(screen.getByRole('tooltip', { name: /view notifications/i })).toBeInTheDocument();
  });
});
