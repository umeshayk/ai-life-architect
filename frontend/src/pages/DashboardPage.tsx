import { PageContainer } from 'components/layout/PageContainer';
import { StatusCard } from 'components/layout/StatusCard';
import { Breadcrumbs } from 'components/navigation/Breadcrumbs';

const kpis = [
  { label: 'Active goals', value: '14', detail: 'Across work, health, finance, and relationships' },
  { label: 'Open projects', value: '7', detail: '3 need stakeholder review this week' },
  { label: 'Focus tasks', value: '22', detail: '6 overdue and surfaced for triage today' },
];

export function DashboardPage() {
  return (
    <PageContainer
      title="Executive dashboard"
      description="Track execution health, active priorities, and platform readiness from a single operational workspace."
      breadcrumbs={<Breadcrumbs items={[{ label: 'Workspace', to: '/' }, { label: 'Dashboard' }]} />}
      actions={<button className="button button--primary page-cta-button">Review recommendations</button>}
    >
      <section className="kpi-grid">
        {kpis.map((kpi) => (
          <article className="panel" key={kpi.label}>
            <p className="panel__label">{kpi.label}</p>
            <strong className="panel__metric">{kpi.value}</strong>
            <p className="panel__description">{kpi.detail}</p>
          </article>
        ))}
      </section>
      <section className="content-grid">
        <StatusCard />
        <section className="panel">
          <div className="panel__header">
            <h2>Foundation status</h2>
          </div>
          <ul className="list">
            <li>Modular FastAPI backend with structured error and health contracts</li>
            <li>Responsive React shell with themed navigation, breadcrumbs, and status surfaces</li>
            <li>Docker, local setup docs, migrations, and verification commands ready for extension</li>
          </ul>
        </section>
      </section>
    </PageContainer>
  );
}
