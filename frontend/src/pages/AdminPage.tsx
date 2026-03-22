import { EmptyState } from 'components/feedback/EmptyState';
import { PageContainer } from 'components/layout/PageContainer';
import { Breadcrumbs } from 'components/navigation/Breadcrumbs';

export function AdminPage() {
  return (
    <PageContainer
      title="Admin console"
      description="Operational visibility for jobs, integrations, and audit-oriented platform controls."
      breadcrumbs={<Breadcrumbs items={[{ label: 'Workspace', to: '/' }, { label: 'Admin' }]} />}
    >
      <EmptyState
        title="Admin foundations are ready"
        description="Section 8.1 establishes the shell, routing, and health visibility that later admin modules will extend without replacing layout infrastructure."
      />
    </PageContainer>
  );
}
