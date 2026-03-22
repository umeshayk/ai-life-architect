import { createBrowserRouter } from 'react-router-dom';

import { AppLayout } from 'layouts/AppLayout';
import { AdminPage } from 'pages/AdminPage';
import { DashboardPage } from 'pages/DashboardPage';
import { SettingsPage } from 'pages/SettingsPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'admin', element: <AdminPage /> },
      { path: 'settings', element: <SettingsPage /> },
    ],
  },
]);
