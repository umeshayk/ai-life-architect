import { useState } from 'react';
import { Outlet } from 'react-router-dom';

import { Sidebar } from 'components/navigation/Sidebar';
import { TopHeader } from 'components/navigation/TopHeader';

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [desktopCollapsed, setDesktopCollapsed] = useState(false);

  const handleMenuClick = () => {
    if (window.matchMedia('(max-width: 1023px)').matches) {
      setMobileOpen(true);
      return;
    }

    setDesktopCollapsed((current) => !current);
  };

  return (
    <div className="app-shell">
      <TopHeader onMenuClick={handleMenuClick} />
      <div className={`app-shell__body ${desktopCollapsed ? 'app-shell__body--collapsed' : ''}`}>
        <Sidebar
          desktopCollapsed={desktopCollapsed}
          mobileOpen={mobileOpen}
          onClose={() => setMobileOpen(false)}
        />
        <div className="app-shell__main">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
