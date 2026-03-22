import { ActivityCard } from 'components/layout/ActivityCard';
import { KpiCard } from 'components/layout/KpiCard';
import { PageContainer } from 'components/layout/PageContainer';
import { RecommendationCard } from 'components/layout/RecommendationCard';
import { Breadcrumbs } from 'components/navigation/Breadcrumbs';

const kpis = [
  { label: 'Active goals', value: '0', subtext: 'Create your first goal to turn strategy into tracked execution.' },
  { label: 'Due today', value: '0', subtext: 'No tasks or routines are currently scheduled for today.' },
  { label: 'Recommendations', value: '0', subtext: 'No active recommendations need review right now.' },
];

export function DashboardPage() {
  return (
    <PageContainer
      title="Executive dashboard"
      description="Track current priorities, next actions, and execution signals from a single workspace."
      breadcrumbs={<Breadcrumbs items={[{ label: 'Workspace', to: '/' }, { label: 'Dashboard' }]} />}
      actions={<button className="button button--primary page-cta-button">Review recommendations</button>}
    >
      <section className="kpi-grid">
        {kpis.map((kpi) => (
          <KpiCard key={kpi.label} label={kpi.label} value={kpi.value} subtext={kpi.subtext} badge="Ready to start" />
        ))}
      </section>
      <section className="content-grid">
        <section className="panel recommendation-card recommendation-card--hero">
          <div className="panel__header">
            <div>
              <h2>Today's focus</h2>
              <p className="panel__helper-text">Start by adding work that should surface in the daily dashboard.</p>
            </div>
            <span className="badge badge--neutral">No urgent items</span>
          </div>
          <div className="empty-panel-state">
            <h3>No tasks or routines due yet</h3>
            <p>Add your first task, routine, or event to populate today's focus and planning surfaces.</p>
          </div>
        </section>
        <section className="content-stack">
          <RecommendationCard
            title="Recommendations"
            helperText="Rule-based and AI-guided recommendations will appear here once work is created."
            badge="Up to date"
            emptyTitle="Nothing to review right now"
            emptyDescription="Recommendations will explain why an item needs attention and what action to take next."
          />
          <ActivityCard
            title="Upcoming schedule"
            helperText="Events, deadlines, and routine checkpoints appear here in chronological order."
            items={[
              {
                title: 'No upcoming events yet',
                description: 'Add a deadline or event to start seeing schedule context in the dashboard.',
              },
              {
                title: 'Need a planning starting point?',
                description: 'Create a goal first, then attach projects, tasks, and routines from quick create.',
              },
            ]}
          />
        </section>
      </section>
    </PageContainer>
  );
}
