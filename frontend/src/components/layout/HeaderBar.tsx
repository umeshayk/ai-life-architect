import { Menu, Search } from "lucide-react";

import { ThemeSwitcher } from "./ThemeSwitcher";

interface HeaderBarProps {
  onOpenNavigation: () => void;
}

export function HeaderBar({ onOpenNavigation }: HeaderBarProps) {
  return (
    <header className="topbar">
      <button type="button" className="topbar__menu" onClick={onOpenNavigation} aria-label="Open navigation">
        <Menu size={18} />
      </button>

      <div className="topbar__search" role="search">
        <Search size={16} aria-hidden="true" />
        <span>Command-first navigation foundation</span>
      </div>

      <ThemeSwitcher />
    </header>
  );
}
