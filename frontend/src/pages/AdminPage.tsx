import { PageContainer } from 'components/layout/PageContainer';
import { StatusCard } from 'components/layout/StatusCard';
import { Breadcrumbs } from 'components/navigation/Breadcrumbs';

export function AdminPage() {
  return (
    <PageContainer
      title="Admin console"
      description="Operational visibility for jobs, integrations, and audit-oriented platform controls."
      breadcrumbs={<Breadcrumbs items={[{ label: 'Workspace', to: '/' }, { label: 'Admin' }]} />}
    >
      <section className="content-grid content-grid--admin">
        <StatusCard />
        <section className="panel content-card">
          <div className="panel__header">
            <div>
              <h2>Operational checks</h2>
              <p className="panel__helper-text">Use these checks before enabling more modules in a local or shared environment.</p>
            </div>
          </div>
          <ul className="activity-list">
            <li className="activity-list__item">
              <strong>Verify API readiness</strong>
              <span>Use the readiness endpoint before connecting new workers, jobs, or external tooling.</span>
            </li>
            <li className="activity-list__item">
              <strong>Confirm dependency health</strong>
              <span>Database and worker status are surfaced here so issues are isolated before users see failures.</span>
            </li>
            <li className="activity-list__item">
              <strong>Review environment configuration</strong>
              <span>Keep local ports, database credentials, and the configured Ollama model aligned with the documented setup.</span>
            </li>
          </ul>
        </section>
      </section>
    </PageContainer>
  );
}
