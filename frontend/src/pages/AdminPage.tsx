import { ActivityCard } from 'components/layout/ActivityCard';
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
        <ActivityCard
          title="Operational checks"
          helperText="Use these checks before enabling more modules in a local or shared environment."
          items={[
            {
              title: 'Verify API readiness',
              description: 'Use the readiness endpoint before connecting new workers, jobs, or external tooling.',
            },
            {
              title: 'Confirm dependency health',
              description: 'Database and worker status are surfaced here so issues are isolated before users see failures.',
            },
            {
              title: 'Review environment configuration',
              description: 'Keep local ports, database credentials, and the configured Ollama model aligned with the documented setup.',
            },
          ]}
        />
      </section>
    </PageContainer>
  );
}
