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
- token values aligned to `SPECS/design-tokens.json` and mapped into theme-aware semantic aliases
- themes applied at the root token layer
- light, dark, graphite, and ocean theme modes
- shared feedback primitives: empty state, skeleton, error boundary
- shared tooltip primitive for icon actions, badges, and technical affordances
- shared layout cards for KPI, content, activity, and recommendation surfaces

## State and Data

- TanStack Query handles server state
- Zustand handles UI-only theme state
- React Router owns route composition

## Route Baseline

- `/`: executive dashboard shell with user-facing empty, KPI, and recommendation states
- `/admin`: admin route for health and operational visibility
- `/settings`: settings route with theme controls

This provides a durable base for later feature modules without revisiting core shell decisions.
