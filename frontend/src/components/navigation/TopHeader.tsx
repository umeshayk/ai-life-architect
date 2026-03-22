import { Bell, BrainCircuit, Command, Menu, MoonStar, Plus, Search, UserCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';

import { useThemeStore } from 'store/themeStore';

type TopHeaderProps = {
  onMenuClick: () => void;
};

export function TopHeader({ onMenuClick }: TopHeaderProps) {
  const cycleTheme = useThemeStore((state) => state.cycleTheme);
  const theme = useThemeStore((state) => state.theme);

  return (
    <header className="top-header">
      <div className="top-header__left">
        <button className="icon-button top-header__menu" type="button" aria-label="Open navigation" onClick={onMenuClick}>
          <Menu size={18} />
        </button>
        <Link className="top-header__brand" to="/">
          <span className="top-header__logo">ALA</span>
          <div>
            <strong>AI Life Architect</strong>
            <small>Primary workspace</small>
          </div>
        </Link>
      </div>
      <div className="top-header__center">
        <label className="search-bar">
          <Search size={16} />
          <input aria-label="Global search" placeholder="Search goals, tasks, notes, and commands" />
          <kbd>Ctrl+K</kbd>
        </label>
      </div>
      <div className="top-header__right">
        <button className="icon-button" type="button" aria-label="Open command palette">
          <Command size={18} />
        </button>
        <button className="button button--secondary" type="button">
          <Plus size={16} />
          <span>Quick create</span>
        </button>
        <button className="icon-button" type="button" aria-label="Notifications">
          <Bell size={18} />
          <span className="icon-button__badge">3</span>
        </button>
        <button className="icon-button" type="button" aria-label="AI assistant">
          <BrainCircuit size={18} />
        </button>
        <button className="icon-button" type="button" aria-label={`Switch theme, current theme ${theme}`} onClick={cycleTheme}>
          <MoonStar size={18} />
        </button>
        <button className="icon-button" type="button" aria-label="Profile menu">
          <UserCircle2 size={20} />
        </button>
      </div>
    </header>
  );
}
