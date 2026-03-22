import { env } from 'lib/env';

export type HealthDependency = {
  name: string;
  status: 'healthy' | 'degraded' | 'unavailable';
  required: boolean;
  details: Record<string, string>;
};

export type HealthResponse = {
  success: boolean;
  data: {
    status: 'healthy' | 'degraded' | 'unavailable';
    service: string;
    environment: string;
    version: string;
    dependencies: HealthDependency[];
  };
  error: null;
  meta: Record<string, unknown>;
};

export async function fetchHealthDetails(): Promise<HealthResponse> {
  const response = await fetch(`${env.apiBaseUrl}/health/details`);
  if (!response.ok) {
    throw new Error('Failed to load platform health details.');
  }
  return (await response.json()) as HealthResponse;
}
