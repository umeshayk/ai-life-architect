import { ContentCard } from 'components/layout/ContentCard';
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
      <ContentCard
        title="Platform health"
        helperText="Operational status for the API, database, and background worker dependencies."
        className="status-card"
      >
        <Skeleton height="lg" />
      </ContentCard>
    );
  }

  if (isError || !data) {
    return (
      <ContentCard
        title="Platform health"
        helperText="Operational status for the API, database, and background worker dependencies."
        className="status-card"
      >
        <p className="status-text status-text--warning">
          Health data is temporarily unavailable. Core navigation remains available.
        </p>
      </ContentCard>
    );
  }

  return (
    <ContentCard
      title="Platform health"
      helperText="Operational status for the API, database, and background worker dependencies."
      className="status-card"
      actions={
        <Tooltip content="Summarizes whether required services are ready to support core product workflows.">
          <span className={`badge badge--${statusToneMap[data.data.status]}`}>{data.data.status}</span>
        </Tooltip>
      }
    >
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
    </ContentCard>
  );
}
