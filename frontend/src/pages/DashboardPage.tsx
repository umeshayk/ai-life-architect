import { PageContainer } from 'components/layout/PageContainer';
import { Breadcrumbs } from 'components/navigation/Breadcrumbs';

const kpis = [
  { label: 'Active goals', value: '0', detail: 'Create your first goal to turn strategy into tracked execution.' },
  { label: 'Due today', value: '0', detail: 'No tasks or routines are currently scheduled for today.' },
  { label: 'Recommendations', value: '0', detail: 'No active recommendations need review right now.' },
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
          <article className="panel kpi-card" key={kpi.label}>
            <div className="kpi-card__header">
              <p className="panel__label">{kpi.label}</p>
              <span className="badge badge--neutral">Ready to start</span>
            </div>
            <strong className="panel__metric">{kpi.value}</strong>
            <p className="panel__description">{kpi.detail}</p>
          </article>
        ))}
      </section>
      <section className="content-grid">
        <section className="panel recommendation-card">
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
          <section className="panel status-card">
            <div className="panel__header">
              <div>
                <h2>Recommendations</h2>
                <p className="panel__helper-text">Rule-based and AI-guided recommendations will appear here once work is created.</p>
              </div>
              <span className="badge badge--neutral">Up to date</span>
            </div>
            <div className="empty-panel-state empty-panel-state--compact">
              <h3>Nothing to review right now</h3>
              <p>Recommendations will explain why an item needs attention and what action to take next.</p>
            </div>
          </section>
          <section className="panel activity-card">
            <div className="panel__header">
              <div>
                <h2>Upcoming schedule</h2>
                <p className="panel__helper-text">Events, deadlines, and routine checkpoints appear here in chronological order.</p>
              </div>
            </div>
            <ul className="activity-list">
              <li className="activity-list__item">
                <strong>No upcoming events yet</strong>
                <span>Add a deadline or event to start seeing schedule context in the dashboard.</span>
              </li>
              <li className="activity-list__item">
                <strong>Need a planning starting point?</strong>
                <span>Create a goal first, then attach projects, tasks, and routines from quick create.</span>
              </li>
            </ul>
          </section>
        </section>
      </section>
    </PageContainer>
  );
}
