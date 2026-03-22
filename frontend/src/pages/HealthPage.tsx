import { StatusCard } from "../components/ui/StatusCard";
import { QueryState } from "../components/ui/QueryState";
import { useHealthStatus, useReadinessStatus } from "../hooks/useHealth";

export function HealthPage() {
  const healthQuery = useHealthStatus();
  const readinessQuery = useReadinessStatus();

  return (
    <div className="page-grid">
      <section className="page-header">
        <div>
          <p className="page-header__eyebrow">Operations</p>
          <h1>Foundation Health</h1>
          <p className="page-header__description">
            Health and readiness states use the standard API contract and expose the Phase 1 runtime dependencies we need before deeper modules are added.
          </p>
        </div>
      </section>

      <section className="two-column-grid">
        <StatusCard title="API Health" description="Loading, empty, and error states included">
          {healthQuery.isLoading ? <QueryState title="Loading" body="Fetching backend health status." /> : null}
          {healthQuery.isError ? <QueryState title="Unavailable" body="The backend health endpoint could not be reached." tone="error" /> : null}
          {healthQuery.data ? (
            <dl className="definition-list">
              <div>
                <dt>Status</dt>
                <dd>{healthQuery.data.status}</dd>
              </div>
              <div>
                <dt>Environment</dt>
                <dd>{healthQuery.data.environment}</dd>
              </div>
              <div>
                <dt>Ports</dt>
                <dd>
                  API {healthQuery.data.ports?.backend} / UI {healthQuery.data.ports?.frontend}
                </dd>
              </div>
            </dl>
          ) : null}
          {!healthQuery.isLoading && !healthQuery.isError && !healthQuery.data ? (
            <QueryState title="No data" body="No health information is available yet." />
          ) : null}
        </StatusCard>

        <StatusCard title="Readiness" description="Dependency configuration visibility">
          {readinessQuery.isLoading ? <QueryState title="Loading" body="Checking configured dependencies." /> : null}
          {readinessQuery.isError ? <QueryState title="Unavailable" body="The readiness endpoint could not be reached." tone="error" /> : null}
          {readinessQuery.data ? (
            <div className="dependency-list">
              {Object.entries(readinessQuery.data.dependencies).map(([name, values]) => (
                <div className="dependency-list__item" key={name}>
                  <strong>{name}</strong>
                  <p>{values.status}</p>
                </div>
              ))}
            </div>
          ) : null}
          {!readinessQuery.isLoading && !readinessQuery.isError && !readinessQuery.data ? (
            <QueryState title="No data" body="No readiness information is available yet." />
          ) : null}
        </StatusCard>
      </section>
    </div>
  );
}
