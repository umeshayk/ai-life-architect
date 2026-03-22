import { useState } from 'react';
import { Outlet } from 'react-router-dom';

import { Sidebar } from 'components/navigation/Sidebar';
import { TopHeader } from 'components/navigation/TopHeader';

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="app-shell">
      <TopHeader onMenuClick={() => setMobileOpen(true)} />
      <div className="app-shell__body">
        <Sidebar mobileOpen={mobileOpen} onClose={() => setMobileOpen(false)} />
        <div className="app-shell__main">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
