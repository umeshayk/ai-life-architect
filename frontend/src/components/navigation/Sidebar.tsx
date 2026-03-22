import { LayoutDashboard, Settings, ShieldCheck } from 'lucide-react';
import { NavLink } from 'react-router-dom';

import { Tooltip } from 'components/feedback/Tooltip';
import type { NavigationItem } from 'types/navigation';

const navigationItems: NavigationItem[] = [
  {
    label: 'Dashboard',
    to: '/',
    icon: LayoutDashboard,
    description: 'Overview, KPIs, and recommendations',
  },
  {
    label: 'Admin',
    to: '/admin',
    icon: ShieldCheck,
    description: 'System controls, jobs, and audit visibility',
  },
  {
    label: 'Settings',
    to: '/settings',
    icon: Settings,
    description: 'Preferences, themes, and workspace behavior',
  },
];

type SidebarProps = {
  desktopCollapsed: boolean;
  mobileOpen: boolean;
  onClose: () => void;
};

export function Sidebar({ desktopCollapsed, mobileOpen, onClose }: SidebarProps) {
  return (
    <>
      <aside
        className={`sidebar sidebar--desktop ${desktopCollapsed ? 'sidebar--collapsed' : ''}`}
        aria-label="Primary navigation"
      >
        <SidebarContent collapsed={desktopCollapsed} />
      </aside>
      <div className={`sidebar-drawer ${mobileOpen ? 'sidebar-drawer--open' : ''}`} aria-hidden={!mobileOpen}>
        <button className="sidebar-drawer__backdrop" type="button" aria-label="Close navigation" onClick={onClose} />
        <aside className="sidebar sidebar--mobile" aria-label="Mobile navigation">
          <SidebarContent onNavigate={onClose} />
        </aside>
      </div>
    </>
  );
}

function SidebarContent({
  collapsed = false,
  onNavigate,
}: {
  collapsed?: boolean;
  onNavigate?: () => void;
}) {
  return (
    <div className="sidebar__content">
      <div className="sidebar__brand">
        <span className={`sidebar__eyebrow ${collapsed ? 'sidebar__eyebrow--hidden' : ''}`}>
          Personal intelligence OS
        </span>
        <strong className={collapsed ? 'sidebar__brand-title--hidden' : ''}>AI Life Architect</strong>
      </div>
      <nav className="sidebar__nav">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <Tooltip key={item.to} content={item.label} side="right" disabled={!collapsed}>
              <NavLink
                to={item.to}
                className={({ isActive }) => `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
                onClick={onNavigate}
              >
                <Icon size={18} />
                <span className={collapsed ? 'sidebar__link-content--hidden' : ''}>
                  <strong>{item.label}</strong>
                  <small>{item.description}</small>
                </span>
              </NavLink>
            </Tooltip>
          );
        })}
      </nav>
    </div>
  );
}
