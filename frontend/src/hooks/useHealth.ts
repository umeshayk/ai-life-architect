import { useQuery } from "@tanstack/react-query";

import { fetchApi } from "../services/api";
import { HealthStatus, ReadinessStatus } from "../types/api";

export function useHealthStatus() {
  return useQuery({
    queryKey: ["health-status"],
    queryFn: () => fetchApi<HealthStatus>("/health"),
  });
}

export function useReadinessStatus() {
  return useQuery({
    queryKey: ["readiness-status"],
    queryFn: () => fetchApi<ReadinessStatus>("/health/readiness"),
  });
}
