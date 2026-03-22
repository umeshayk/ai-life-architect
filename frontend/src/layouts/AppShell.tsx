import { useState } from "react";
import { Outlet } from "react-router-dom";

import { HeaderBar } from "../components/layout/HeaderBar";
import { SidebarNav } from "../components/layout/SidebarNav";

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="app-shell">
      <SidebarNav mobileOpen={mobileOpen} onNavigate={() => setMobileOpen(false)} />
      {mobileOpen ? (
        <button className="app-shell__scrim" onClick={() => setMobileOpen(false)} aria-label="Close navigation" />
      ) : null}

      <div className="app-shell__content">
        <HeaderBar onOpenNavigation={() => setMobileOpen(true)} />
        <main className="page-shell">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
