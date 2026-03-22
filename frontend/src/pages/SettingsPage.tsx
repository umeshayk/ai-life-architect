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
            <h2>Theme mode</h2>
            <p className="panel__helper-text">Apply workspace-safe display themes without changing page-level layouts.</p>
          </div>
        </div>
        <div className="segmented-control" role="group" aria-label="Theme mode">
          {themeOptions.map((option) => (
            <button
              key={option}
              type="button"
              className={`segmented-control__item ${theme === option ? 'segmented-control__item--active' : ''}`}
              onClick={() => setTheme(option)}
            >
              {option}
            </button>
          ))}
        </div>
      </section>
    </PageContainer>
  );
}
