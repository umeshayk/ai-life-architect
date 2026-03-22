# Frontend Architecture

## Layout System

The frontend foundation is built around a single shared `AppLayout` that enforces the AGENTS.md shell requirements:

- sticky `TopHeader`
- responsive `Sidebar`
- shared page container and breadcrumb pattern
- route content region for domain modules

No page bypasses this shell.

## UI Foundation

- semantic CSS tokens in `src/styles/foundations/global.css`
- themes applied at the root token layer
- light, dark, and graphite theme modes
- shared feedback primitives: empty state, skeleton, error boundary

## State and Data

- TanStack Query handles server state
- Zustand handles UI-only theme state
- React Router owns route composition

## Route Baseline

- `/`: executive dashboard shell
- `/admin`: admin foundation route
- `/settings`: settings route with theme controls

This provides a durable base for later feature modules without revisiting core shell decisions.
