import { ActivityCard } from 'components/layout/ActivityCard';
import { ContentCard } from 'components/layout/ContentCard';
import { KpiCard } from 'components/layout/KpiCard';
import { PageContainer } from 'components/layout/PageContainer';
import { RecommendationCard } from 'components/layout/RecommendationCard';
import { Breadcrumbs } from 'components/navigation/Breadcrumbs';
import { Tooltip } from 'components/feedback/Tooltip';

const kpis = [
  {
    label: 'Active goals',
    value: '0',
    subtext: 'Create your first goal to turn strategy into tracked execution.',
    tooltip: 'Tracks goals that are active and should be progressing in this workspace.',
  },
  {
    label: 'Due today',
    value: '0',
    subtext: 'No tasks or routines are currently scheduled for today.',
    tooltip: 'Counts tasks, routines, and near-term work items that need attention today.',
  },
  {
    label: 'Recommendations',
    value: '0',
    subtext: 'No active recommendations need review right now.',
    tooltip: 'Shows recommendations generated from rules or future AI insight flows.',
  },
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
          <KpiCard
            key={kpi.label}
            label={kpi.label}
            value={kpi.value}
            subtext={kpi.subtext}
            badge="Ready to start"
            tooltip={kpi.tooltip}
            badgeTooltip={`${kpi.label} will populate once the workspace has live data.`}
          />
        ))}
      </section>
      <section className="content-grid">
        <ContentCard
          title="Today's focus"
          helperText="Start by adding work that should surface in the daily dashboard."
          className="recommendation-card recommendation-card--hero"
          actions={
            <Tooltip content="No overdue tasks, missed routines, or urgent alerts are currently surfaced.">
              <span className="badge badge--neutral">No urgent items</span>
            </Tooltip>
          }
        >
          <div className="empty-panel-state">
            <h3>No tasks or routines due yet</h3>
            <p>Add your first task, routine, or event to populate today's focus and planning surfaces.</p>
          </div>
        </ContentCard>
        <section className="content-stack">
          <RecommendationCard
            title="Recommendations"
            helperText="Rule-based and AI-guided recommendations will appear here once work is created."
            badge="Up to date"
            badgeTooltip="There are no current recommendations requiring review or action."
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
