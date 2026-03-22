import { HeartPulse, LayoutDashboard } from "lucide-react";
import { NavLink } from "react-router-dom";

const navigation = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/foundation/health", label: "Foundation Health", icon: HeartPulse },
];

interface SidebarNavProps {
  mobileOpen: boolean;
  onNavigate: () => void;
}

export function SidebarNav({ mobileOpen, onNavigate }: SidebarNavProps) {
  return (
    <aside className={`sidebar ${mobileOpen ? "sidebar--open" : ""}`} aria-label="Primary navigation">
      <div className="sidebar__brand">
        <span className="sidebar__eyebrow">Enterprise OS</span>
        <strong>AI Life Architect</strong>
      </div>

      <nav className="sidebar__nav" aria-label="Primary navigation links">
        {navigation.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `sidebar__link ${isActive ? "sidebar__link--active" : ""}`}
            onClick={onNavigate}
          >
            <Icon size={18} aria-hidden="true" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
