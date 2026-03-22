import { CircleHelp } from 'lucide-react';

import { Tooltip } from 'components/feedback/Tooltip';
import { PageContainer } from 'components/layout/PageContainer';
import { Breadcrumbs } from 'components/navigation/Breadcrumbs';
import { useThemeStore, type ThemeMode } from 'store/themeStore';

const themeOptions: ThemeMode[] = ['light', 'dark', 'graphite', 'ocean'];

export function SettingsPage() {
  const theme = useThemeStore((state) => state.theme);
  const setTheme = useThemeStore((state) => state.setTheme);

  return (
    <PageContainer
      title="Settings"
      description="Control global workspace presentation and core application preferences."
      breadcrumbs={<Breadcrumbs items={[{ label: 'Workspace', to: '/' }, { label: 'Settings' }]} />}
    >
      <section className="panel">
        <div className="panel__header">
          <div>
            <div className="field-heading">
              <h2>Theme mode</h2>
              <Tooltip content="Changes the visual theme for the current workspace shell without changing data or layout structure.">
                <button className="icon-button icon-button--sm" type="button" aria-label="Theme mode help">
                  <CircleHelp size={14} />
                </button>
              </Tooltip>
            </div>
            <p className="panel__helper-text">Apply workspace-safe display themes without changing page-level layouts.</p>
          </div>
        </div>
        <div className="segmented-control" role="group" aria-label="Theme mode">
          {themeOptions.map((option) => (
            <Tooltip
              key={option}
              content={`Switch to the ${option} theme for workspace navigation, surfaces, and controls.`}
            >
              <button
                type="button"
                className={`segmented-control__item ${theme === option ? 'segmented-control__item--active' : ''}`}
                onClick={() => setTheme(option)}
              >
                {option}
              </button>
            </Tooltip>
          ))}
        </div>
      </section>
    </PageContainer>
  );
}
