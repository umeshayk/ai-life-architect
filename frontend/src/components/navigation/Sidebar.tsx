import { LayoutDashboard, Settings, ShieldCheck } from 'lucide-react';
import { NavLink } from 'react-router-dom';

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
  mobileOpen: boolean;
  onClose: () => void;
};

export function Sidebar({ mobileOpen, onClose }: SidebarProps) {
  return (
    <>
      <aside className="sidebar sidebar--desktop" aria-label="Primary navigation">
        <SidebarContent />
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

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="sidebar__content">
      <div className="sidebar__brand">
        <span className="sidebar__eyebrow">Personal intelligence OS</span>
        <strong>AI Life Architect</strong>
      </div>
      <nav className="sidebar__nav">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `sidebar__link ${isActive ? 'sidebar__link--active' : ''}`}
              onClick={onNavigate}
            >
              <Icon size={18} />
              <span>
                <strong>{item.label}</strong>
                <small>{item.description}</small>
              </span>
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}
