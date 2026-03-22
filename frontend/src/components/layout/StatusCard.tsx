import { useQuery } from '@tanstack/react-query';

import { Skeleton } from 'components/feedback/Skeleton';
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
          <h2>Platform health</h2>
        </div>
        <Skeleton height="lg" />
      </section>
    );
  }

  if (isError || !data) {
    return (
      <section className="panel">
        <div className="panel__header">
          <h2>Platform health</h2>
        </div>
        <p className="status-text status-text--warning">
          Health data is temporarily unavailable. Core navigation remains available.
        </p>
      </section>
    );
  }

  return (
    <section className="panel">
      <div className="panel__header">
        <h2>Platform health</h2>
        <span className={`badge badge--${statusToneMap[data.data.status]}`}>{data.data.status}</span>
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
            <span className={`badge badge--${statusToneMap[dependency.status]}`}>{dependency.status}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
