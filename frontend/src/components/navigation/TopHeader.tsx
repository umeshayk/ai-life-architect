import { Bell, BrainCircuit, Command, Ellipsis, Menu, MoonStar, Plus, Search, UserCircle2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { Tooltip } from 'components/feedback/Tooltip';
import { useThemeStore } from 'store/themeStore';

type TopHeaderProps = {
  onMenuClick: () => void;
};

export function TopHeader({ onMenuClick }: TopHeaderProps) {
  const cycleTheme = useThemeStore((state) => state.cycleTheme);
  const theme = useThemeStore((state) => state.theme);
  const isMobile = window.matchMedia('(max-width: 767px)').matches;
  const menuTooltip = isMobile ? 'Open navigation' : 'Collapse sidebar';
  const [mobileSearchOpen, setMobileSearchOpen] = useState(false);
  const [mobileActionsOpen, setMobileActionsOpen] = useState(false);

  useEffect(() => {
    if (!isMobile) {
      setMobileSearchOpen(false);
      setMobileActionsOpen(false);
    }
  }, [isMobile]);

  return (
    <div className="top-header-shell">
      <header className="top-header">
        <div className="top-header__left">
          <Tooltip content={menuTooltip} disabled={isMobile}>
            <button className="icon-button top-header__menu" type="button" aria-label="Open navigation" onClick={onMenuClick}>
              <Menu size={18} />
            </button>
          </Tooltip>
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
          <div className="top-header__desktop-actions">
            <Tooltip content="Open command palette">
              <button className="icon-button" type="button" aria-label="Open command palette">
                <Command size={18} />
              </button>
            </Tooltip>
            <Tooltip content="Create a task, goal, note, or project">
              <button className="button button--secondary" type="button">
                <Plus size={16} />
                <span>Quick create</span>
              </button>
            </Tooltip>
            <Tooltip content="View notifications">
              <button className="icon-button" type="button" aria-label="Notifications">
                <Bell size={18} />
                <span className="icon-button__badge">3</span>
              </button>
            </Tooltip>
            <Tooltip content="Open AI assistant">
              <button className="icon-button" type="button" aria-label="AI assistant">
                <BrainCircuit size={18} />
              </button>
            </Tooltip>
            <Tooltip content={`Switch theme from ${theme}`}>
              <button className="icon-button" type="button" aria-label={`Switch theme, current theme ${theme}`} onClick={cycleTheme}>
                <MoonStar size={18} />
              </button>
            </Tooltip>
            <Tooltip content="Open profile menu">
              <button className="icon-button" type="button" aria-label="Profile menu">
                <UserCircle2 size={20} />
              </button>
            </Tooltip>
          </div>
          <div className="top-header__mobile-actions">
            <button
              className="icon-button"
              type="button"
              aria-label="Toggle search"
              aria-expanded={mobileSearchOpen}
              onClick={() => setMobileSearchOpen((current) => !current)}
            >
              <Search size={18} />
            </button>
            <button className="icon-button" type="button" aria-label="Notifications">
              <Bell size={18} />
              <span className="icon-button__badge">3</span>
            </button>
            <button className="icon-button" type="button" aria-label="Profile menu">
              <UserCircle2 size={20} />
            </button>
            <button
              className="icon-button"
              type="button"
              aria-label="More actions"
              aria-expanded={mobileActionsOpen}
              onClick={() => setMobileActionsOpen((current) => !current)}
            >
              <Ellipsis size={18} />
            </button>
          </div>
        </div>
      </header>
      <div className={`mobile-search-panel ${mobileSearchOpen ? 'mobile-search-panel--open' : ''}`}>
        <label className="search-bar mobile-search-panel__bar">
          <Search size={16} />
          <input aria-label="Global search" placeholder="Search goals, tasks, notes, and commands" />
          <kbd>Ctrl+K</kbd>
        </label>
      </div>
      <div className={`mobile-actions-sheet ${mobileActionsOpen ? 'mobile-actions-sheet--open' : ''}`}>
        <button className="mobile-actions-sheet__item" type="button">
          <Command size={18} />
          <span>Command palette</span>
        </button>
        <button className="mobile-actions-sheet__item" type="button">
          <Plus size={18} />
          <span>Quick create</span>
        </button>
        <button className="mobile-actions-sheet__item" type="button">
          <BrainCircuit size={18} />
          <span>AI assistant</span>
        </button>
        <button className="mobile-actions-sheet__item" type="button" onClick={cycleTheme}>
          <MoonStar size={18} />
          <span>Switch theme</span>
        </button>
      </div>
    </div>
  );
}
