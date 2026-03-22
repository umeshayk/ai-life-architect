import { useQuery } from '@tanstack/react-query';

import { Skeleton } from 'components/feedback/Skeleton';
import { Tooltip } from 'components/feedback/Tooltip';
import { fetchHealthDetails } from 'services/health';

const statusToneMap = {
  healthy: 'success',
  degraded: 'warning',
  unavailable: 'error',
} as const;

export function StatusCard() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['platform-health'],
    queryFn: fetchHealthDetails,
  });

  if (isLoading) {
    return (
      <section className="panel">
        <div className="panel__header">
          <div>
            <h2>Platform health</h2>
            <p className="panel__helper-text">Operational status for the API, database, and background worker dependencies.</p>
          </div>
        </div>
        <Skeleton height="lg" />
      </section>
    );
  }

  if (isError || !data) {
    return (
      <section className="panel">
        <div className="panel__header">
          <div>
            <h2>Platform health</h2>
            <p className="panel__helper-text">Operational status for the API, database, and background worker dependencies.</p>
          </div>
        </div>
        <p className="status-text status-text--warning">
          Health data is temporarily unavailable. Core navigation remains available.
        </p>
      </section>
    );
  }

  return (
    <section className="panel status-card">
      <div className="panel__header">
        <div>
          <h2>Platform health</h2>
          <p className="panel__helper-text">Operational status for the API, database, and background worker dependencies.</p>
        </div>
        <Tooltip content="Summarizes whether required services are ready to support core product workflows.">
          <span className={`badge badge--${statusToneMap[data.data.status]}`}>{data.data.status}</span>
        </Tooltip>
      </div>
      <dl className="health-grid">
        <div>
          <dt>Service</dt>
          <dd>{data.data.service}</dd>
        </div>
        <div>
          <dt>Environment</dt>
          <dd>{data.data.environment}</dd>
        </div>
        <div>
          <dt>Version</dt>
          <dd>{data.data.version}</dd>
        </div>
      </dl>
      <ul className="dependency-list">
        {data.data.dependencies.map((dependency) => (
          <li key={dependency.name}>
            <span>{dependency.name}</span>
            <Tooltip
              content={
                dependency.required
                  ? `${dependency.name} is required for core workflows and is currently ${dependency.status}.`
                  : `${dependency.name} is optional right now and is currently ${dependency.status}.`
              }
            >
              <span className={`badge badge--${statusToneMap[dependency.status]}`}>{dependency.status}</span>
            </Tooltip>
          </li>
        ))}
      </ul>
    </section>
  );
}
