export const env = {
  appName: import.meta.env.VITE_APP_NAME ?? 'AI Life Architect',
  appEnv: import.meta.env.VITE_APP_ENV ?? 'development',
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8004/api/v1',
};
