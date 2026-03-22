import { StatusCard } from "../components/ui/StatusCard";

const phases = [
  "Monorepo-ready frontend and backend structure",
  "Shared API response envelope and health endpoints",
  "Token-driven theme system with premium theme variants",
  "Responsive enterprise app shell for mobile through wide desktop",
];

export function DashboardPage() {
  return (
    <div className="page-grid">
      <section className="page-header">
        <div>
          <p className="page-header__eyebrow">Phase 1</p>
          <h1>Foundation</h1>
          <p className="page-header__description">
            This baseline establishes the application shell, backend health API, configuration system, and the shared design-token foundation for the phases that follow.
          </p>
        </div>
      </section>

      <section className="kpi-grid" aria-label="Foundation checkpoints">
        {phases.map((phase) => (
          <StatusCard key={phase} title={phase} description="Delivered">
            <p>Ready for the next domain modules without reworking the core shell.</p>
          </StatusCard>
        ))}
      </section>
    </div>
  );
}
