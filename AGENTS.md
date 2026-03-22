# AI Life Architect — AGENTS.md

## 0. Purpose

This document defines how AI Life Architect MUST be built.
All agents, Codex runs, developers, and automation flows must follow this file as execution law, not optional guidance.

This product is not an MVP. It must be built as an enterprise-grade personal intelligence operating system with production-quality UX, maintainable architecture, strong observability, secure defaults, and scalable foundations.

---

## 1. Mission

Build **AI Life Architect** as an **enterprise-grade application**, not an MVP.

This system is a **personal intelligence operating system** that helps users organize, retrieve, plan, execute, and improve across all major life domains using structured data, AI assistance, semantic retrieval, relationship mapping, and intelligent recommendations.

The final product must feel like a **mature enterprise/internal SaaS platform** with:
- strong architecture
- modular code organization
- high maintainability
- production-quality UX
- security and auditability
- background processing
- observability
- clear documentation

---

## 2. Product Scope

The platform should support these major domains:

- Authentication and RBAC
- User and admin management
- Workspaces
- Life areas
- Goals
- Projects
- Tasks
- Notes
- Journals
- Documents and uploads
- Document ingestion pipeline
- Routines
- Events
- Tags
- Relationships / graph
- Semantic search and retrieval
- AI orchestration
- Planning engine
- Recommendation engine
- Dashboard
- Notifications and reminders
- Admin console
- Analytics
- Import / export

---

## 3. Locked Technology Standards

### Frontend
- React
- TypeScript
- Vite
- React Router
- TanStack Query for server state
- Zustand for UI state only
- React Hook Form + Zod for forms and validation
- TanStack Table for tables/data grids
- Recharts for charts
- Lucide Icons
- Strict typing
- Reusable design system
- Token-driven styling system
- Theme-aware component architecture
- Responsive enterprise UX across mobile, tablet, laptop, desktop, and ultrawide
- Accessibility-first UI patterns
- CSS variables for semantic tokens
- Tailwind CSS or equivalent token-driven utility layer only if wired to design tokens
- No hardcoded one-off page styling as the primary UI strategy

### Backend
- Python
- FastAPI
- SQLAlchemy 2.x
- Alembic
- Pydantic
- PostgreSQL
- pgvector
- Redis
- Celery or RQ for background processing

### AI
- Ollama as default local AI provider
- All AI calls must go through a provider abstraction layer
- Future providers such as OpenAI / Anthropic must be easy to add

### Infrastructure
- Docker Compose for local development
- `.env`-driven configuration
- Clean setup for future cloud deployment
- Multi-tenant readiness in architecture, even if not fully implemented now

🚫 No deviation from the locked stack without explicit approval.

---

## 3A. External Specification Files (Mandatory)

Codex and all implementers MUST read and follow these files in addition to this AGENTS.md:

- `SPECS/domain-model.md` → authoritative schema, entities, relationships, and form field direction
- `SPECS/ui-ux-standards.md` → authoritative UI/UX interaction rules
- `SPECS/design-system.md` → authoritative design system and token usage rules
- `SPECS/component-library.md` → authoritative reusable component definitions
- `SPECS/dashboard-patterns.md` → authoritative dashboard composition rules
- `SPECS/design-tokens.json` → authoritative token source for implementation values

### Precedence Rules

If there is conflict:

1. `SPECS/domain-model.md` overrides schema and entity assumptions
2. `SPECS/design-tokens.json` overrides raw visual values
3. `SPECS/design-system.md`, `SPECS/ui-ux-standards.md`, `SPECS/component-library.md`, and `SPECS/dashboard-patterns.md` override page-level UI decisions
4. `AGENTS.md` governs architecture, workflow, quality bar, and Definition of Done

No implementation may ignore these files once they exist.

---

## 4. Non-Negotiable Rules

1. This is **not** an MVP, prototype, or mock-only app.
2. Do not hardcode AI responses.
3. Do not build disconnected frontend mock screens and call them complete.
4. Do not place business logic in API route handlers.
5. Do not create giant monolithic files.
6. Do not skip migrations.
7. Do not skip validation.
8. Do not skip loading, empty, and error states in the UI.
9. Do not hardcode widths, heights, spacing, font sizes, breakpoints, or colors directly into feature pages unless they come from shared design tokens.
10. Do not ship desktop-only layouts.
11. Do not build dark mode as a later afterthought; theme support must be built into the design system from the start.
12. Do not remove working features unless replacing them with a better structured implementation.
13. Keep the app runnable after every major change.
14. Update docs whenever architecture or module behavior changes.
15. Add tests for critical flows.
16. Use seed/dev data only where clearly labeled.
17. Maintain naming consistency across DB, backend, and frontend.
18. Prefer modular domain-oriented architecture over quick shortcuts.
19. Do not duplicate server state into a global UI store.
20. Do not mark a phase complete if screenshots, responsive validation, or build checks are missing.
21. Do not use inline styles for layout except where dynamic runtime behavior truly requires them.
22. Do not skip commit/push after a completed phase.
23. Do not rely on frontend-only permission hiding for security.
24. Do not invent schema fields or relationships that contradict `SPECS/domain-model.md`.
25. Do not introduce new visual tokens ad hoc; add them to the shared token system first.

---

## 5. Architecture Principles

### Backend Principles
- Thin controllers/routes
- Business logic in services
- Pydantic schemas for all request/response models
- SQLAlchemy models with proper relationships and indexing
- Alembic migrations for schema changes
- Common error response structure
- Dependency injection for database, current user, permissions
- Structured logging
- Correlation IDs for requests
- Audit logs for important actions
- Background jobs for heavy or async processing

### Frontend Principles
- Feature-based module organization
- Server state handled via TanStack Query
- Shared reusable UI primitives
- Protected routes
- Permission-aware navigation
- Clear page header / breadcrumb / action bar pattern
- Consistent table / form / card / drawer / modal / tab / badge behavior
- Strong empty states, skeleton loaders, and error states
- Responsive-first enterprise UX that works intentionally across phone, tablet, laptop, desktop, and ultrawide
- Layouts must adapt by composition, not by hiding broken sections
- Use semantic design tokens for color, typography, radius, shadow, spacing, border, z-index, and motion
- Themes must be implemented at the token layer, not via duplicated component code
- Support light theme, dark theme, and at least one additional premium theme pack such as graphite / ocean / emerald
- Respect reduced-motion and accessibility preferences
- Mobile and tablet must preserve core actions without forcing desktop behaviors

### AI Principles
- All AI operations go through a central AI orchestration layer
- Prompt templates must be centralized, not scattered
- Provider abstraction required
- AI actions must be traceable by model, task type, latency, status
- Use AI to enhance structured workflows, not bypass architecture
- AI must never block core workflows when the model/provider is unavailable

---

## 5A. Frontend Design System, Responsiveness, and Theme Standards

## 5A.1 Global Layout System (Mandatory)
## 5A.2 Color System (Mandatory)

All UI must use predefined color tokens. No hardcoded colors allowed.

### Primary Palette

Primary:
- #2563EB (default)
- #1D4ED8 (hover)
- #1E40AF (active)

Neutral:
- #F9FAFB (bg)
- #F3F4F6
- #E5E7EB
- #D1D5DB
- #6B7280
- #374151
- #111827 (text)

### Semantic Colors

- Success: #16A34A
- Warning: #F59E0B
- Error: #DC2626
- Info: #0EA5E9

### Dark Theme

- Background: #121212
- Surface: #1E1E1E
- Border: #30363D
- Text: #E5E7EB

### Rules

- No random hex usage
- Follow semantic mapping
- Use tokens only

## 5A.3 Typography System (Mandatory)

### Font

Primary: Inter  
Fallback: system-ui, Segoe UI, Roboto  

Monospace: JetBrains Mono  

### Scale

- H1: 32px
- H2: 24px
- H3: 20px
- Body: 16px
- Small: 14px
- Caption: 12px

### Weights

- Regular: 400
- Medium: 500
- Semibold: 600
- Bold: 700

### Rules

- Use Inter everywhere
- No multiple fonts
- Maintain readability

## 🤖 Codex Color & Typography Enforcement

Codex MUST:

- Use only defined color tokens
- Use Inter font
- Apply semantic colors correctly
- Support light/dark themes

Reject implementation if:
- random colors used
- inconsistent fonts


This section defines the canonical layout system for the entire application.
All frontend implementations MUST follow this system.

### Mandatory Specs
Codex MUST follow:
- `SPECS/design-system.md`
- `SPECS/ui-ux-standards.md`
- `SPECS/component-library.md`
- `SPECS/dashboard-patterns.md`
- `SPECS/design-tokens.json`

Rules:
- Always reuse components from `component-library.md`
- Always follow `dashboard-patterns.md` for dashboards
- Always use shared design tokens
- No hardcoded visual styling in feature pages

### Token Source of Truth
All visual values must come from shared tokens.

Authoritative source:
- `SPECS/design-tokens.json`

Rules:
- No hardcoded colors
- No random spacing values
- No arbitrary font sizes
- No per-page visual styling overrides without shared token support

If AGENTS.md examples conflict with the token file:
→ the token file wins

### Typography System
Typography must be controlled through the shared design system.

Authoritative sources:
- `SPECS/design-system.md`
- `SPECS/design-tokens.json`

Rules:
- single primary UI font family
- consistent heading/body scale
- no page-specific typography inventions
- readable hierarchy across devices

### Canonical Breakpoints
Use this breakpoint set everywhere:

- mobile: 320px–639px
- tablet: 640px–1023px
- desktop: 1024px–1439px
- wide desktop: 1440px–1919px
- ultrawide: 1920px+

### Global App Layout Architecture

Every authenticated page must be rendered inside a shared `AppLayout`.

Structure:

AppLayout  
├── TopHeader (sticky)  
├── Sidebar (responsive navigation)  
├── MainContent  
│   ├── PageHeader  
│   ├── PageBody  
│   └── FooterActions (optional)  
└── RightPanel (optional contextual panel)

Rules:
- Do not create independent layouts per page
- Do not bypass AppLayout
- Layout must be compositional and reusable
- No hardcoded layout wrappers inside feature pages

### Layout Composition Rules
- Use CSS Grid for macro layout
- Use Flexbox for internal alignment
- Prefer `minmax()`, `clamp()`, and fluid/container-aware layouts
- Avoid fixed pixel widths for core layout
- Avoid absolute positioning for primary structure

### Page Layout Templates
All pages should follow one of the approved layout families:

- dashboard layout: KPI row + insights grid + activity panel
- list layout: filters toolbar + table/list + optional detail panel
- detail layout: header + metadata + tabbed content + side info panel
- builder layout: navigation + work area + validation/insights
- form layout: title/actions + sectioned form + sticky action bar
- settings/admin layout: section nav + configuration panel

Do not invent new layout families unless AGENTS.md is updated.

### UI Composition Rules
- Prefer flat grouped sections over excessive card nesting
- Use cards for logical grouping, not decoration
- Maintain consistent spacing from the shared token scale
- Align content to a shared content grid
- Large desktop layouts must not look sparse

### Required Device Support
Support these viewport categories from the start:
- mobile small (320px+)
- mobile standard (375px+)
- large mobile / small phablet (414px+)
- tablet portrait (768px+)
- tablet landscape / small laptop (1024px+)
- desktop (1280px+)
- wide desktop (1440px+)
- ultrawide (1600px+)

### Responsive layout rules
- No page should depend on a single fixed-width layout
- No critical action may disappear without an accessible alternative
- Tables must have responsive strategies:
  - column priority
  - horizontal scroll wrapper when necessary
  - compact row density mode
  - card/list fallback for mobile where justified
- Sidebars must support:
  - expanded desktop state
  - collapsible tablet state
  - drawer state on mobile
- Detail panels, drawers, and modals must be usable on small screens
- Sticky headers/filters/action bars must not block content on mobile
- Forms must support single-column mobile layout and multi-column desktop layout
- Charts and graph views must degrade gracefully on smaller screens
- Empty states, loaders, and error states must also be responsive

### Theme system rules
- Build a centralized theme system using semantic tokens
- Required theme modes:
  - light
  - dark
  - at least one additional premium theme
- Components must inherit tokens rather than define raw colors locally
- Theme switching must not require per-page rewrites
- Preserve readability and contrast across all supported themes

### Modern Styling Rules
- Use a mature visual language: clean spacing, layered surfaces, subtle borders, restrained shadows, modern typography
- Prefer contemporary interaction patterns: compact filters, drawer-first edits where appropriate, skeleton loading, command-first access where suitable
- Avoid outdated UI patterns: giant padding everywhere, generic bootstrap-like feel, mismatched control heights, loud unstructured colors
- Motion must be subtle and purposeful

### Design token expectations
At minimum define shared tokens for:
- color
- typography
- spacing
- radius
- shadow
- border
- motion
- layer/elevation
- layout widths
- z-index
- control heights
- data-viz palette
- focus ring

### Accessibility and polish
- Keyboard accessibility is required for primary interactions
- Visible focus states are mandatory in every theme
- Contrast must remain readable in all themes
- Use semantic HTML and aria support for dialogs, navigation, forms, and interactive controls
- Respect reduced-motion preferences

### Header Standards
The top header must remain consistent across pages.

Left section:
- app logo or product name
- current workspace/context selector where relevant

Center section:
- global search bar
- command palette entry point

Right section:
- command palette trigger
- quick create
- notifications
- AI assistant entry
- theme toggle
- user profile menu

Header rules:
- sticky
- consistent height
- no page-specific structure changes
- responsive on all supported breakpoints
- icon-only buttons must have tooltips and accessible labels

### Frontend Review Checklist
For every frontend phase, verify and document:
- mobile layout works
- tablet layout works
- desktop layout works
- wide desktop layout works
- light theme works
- dark theme works
- no broken overflow or clipped content
- no inconsistent spacing or alignment
- no page-specific hardcoded layout hacks

---

## 5B. Definition of Done (Mandatory for Every Phase)

A phase or sub-phase is complete only if all relevant items below are satisfied:

- Backend API implemented and tested where applicable
- Frontend UI implemented and connected to real backend flows where applicable
- Database migrations created and applied where schema changed
- Request/response contract verified
- Validation implemented
- Loading, empty, success, and error states implemented
- Logging and error handling added
- Responsive behavior verified on mobile, tablet, desktop, and wide desktop where UI changed
- Themes verified in at least light and dark, and checked against premium themes where impacted
- Accessibility basics verified: keyboard, focus, contrast, labels
- Unit tests added/updated
- Integration or end-to-end behavior verified for critical paths
- Build passes
- Docs updated
- Screenshots captured for relevant UI work
- Changes committed and pushed

If any required item is missing, the phase is not complete.

---

## 5C. API Contract Standards

All APIs must follow a consistent contract.

### Standard success response
```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {}
}
```

### Standard paginated response
```json
{
  "success": true,
  "data": [],
  "error": null,
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 100
  }
}
```

### Standard error response
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": {}
  },
  "meta": {}
}
```

### Contract rules
- Dates/times must use ISO 8601
- IDs should use UUID strings unless there is a compelling reason otherwise
- Enums must use UPPER_SNAKE_CASE
- Sorting, filtering, and pagination must be consistent across list endpoints
- Never return unstructured ad hoc response shapes for similar resources

---

## 5D. State Management Rules

- TanStack Query handles server state only
- Zustand handles UI state only
- React Hook Form manages form state
- Do not copy server data into Zustand except for narrow, justified UI coordination cases
- Do not mix persistent API entities with ephemeral UI flags in the same store

---

## 5E. File Upload and Processing Standards

- Validate allowed file types and size limits on both frontend and backend
- File lifecycle must support:
  - uploading
  - processing
  - ready
  - failed
- Long-running document operations must use background jobs
- Retry mechanism must exist for recoverable processing failures
- Error UI must explain the failure state clearly
- Storage implementation must remain abstracted so local and future cloud storage can be swapped cleanly

---

## 5F. AI Fallback and Reliability Rules

- AI must not block core workflows
- AI requests must support timeout handling
- Retries should be limited and controlled
- The UI must show graceful fallback states when AI is unavailable
- AI responses should be cached where useful and safe
- AI logs must capture task type, provider, model, latency, status, and key metadata
- Deterministic logic must remain primary when it is sufficient

---

## 5G. Seed, Demo, and Test Data Rules

- Seed scripts must exist for local development
- Seed data must be clearly separated from test fixtures and production data assumptions
- Demo/sample users and realistic sample content should exist where helpful for UI and QA
- Never blur development sample data with actual business logic correctness

---

## 5H. Performance and CI Rules

### Performance rules
- Lazy load major routes
- Virtualize large lists/tables where needed
- Use pagination for large result sets
- Avoid unnecessary rerenders in dashboards and dense list screens
- Keep bundle growth controlled
- Avoid layout shifts across responsive breakpoints

### CI / quality gates
Every meaningful phase should pass:
- type check
- lint
- unit tests
- build
- backend integration checks where relevant
- migration verification where relevant

---

## 6. Expected Repository Structure

### Backend
```text
backend/
  app/
    api/
      v1/
    core/
    db/
    models/
    schemas/
    services/
    modules/
      auth/
      users/
      workspaces/
      life_areas/
      goals/
      projects/
      tasks/
      notes/
      journals/
      documents/
      routines/
      events/
      tags/
      relationships/
      search/
      ai/
      planning/
      recommendations/
      notifications/
      admin/
      analytics/
      audit/
    workers/
    utils/
    tests/
```

### Frontend
```text
frontend/
  src/
    app/
    components/
    features/
      auth/
      dashboard/
      goals/
      projects/
      tasks/
      notes/
      journals/
      documents/
      search/
      planner/
      recommendations/
      routines/
      graph/
      notifications/
      admin/
      analytics/
      settings/
    hooks/
    layouts/
    lib/
    pages/
    services/
    store/
    styles/
      tokens/
      themes/
      foundations/
    types/
```

---

## 7. Data Modeling Standards

Use normalized relational design with foreign keys, timestamps, and indexes.

Expected key tables include:
- users
- roles
- permissions
- user_roles
- role_permissions
- audit_logs
- workspaces
- life_areas
- goals
- projects
- tasks
- task_dependencies
- notes
- journals
- routines
- routine_logs
- events
- tags
- entity_tags
- documents
- document_versions
- document_chunks
- ingestion_jobs
- relationships
- relationship_suggestions
- ai_request_logs
- plans
- plan_generations
- recommendations
- notifications
- analytics_events

Use:
- `created_at`
- `updated_at`
- `created_by`
- `updated_by`
- soft delete where appropriate
- `metadata` JSONB where extensibility is useful

---

## 8. Enterprise Features to Implement

### 8.1 Foundation
- Monorepo or clean multi-app structure
- Docker Compose
- Env examples
- README
- Architecture docs
- Health checks
- Frontend app shell

### 8.2 Auth and RBAC
- Login
- Refresh token flow
- Logout
- Current user endpoint
- User admin management
- Role and permission mapping
- Password hashing
- Auth audit logging

### 8.3 Core Domain
- CRUD + list/detail + filtering + sorting + pagination
- Workspaces
- Life areas
- Goals
- Projects
- Tasks
- Notes
- Journals
- Routines
- Events
- Tags
- Cross-linking between entities

### 8.4 Documents and Ingestion
- File upload
- Metadata
- Processing status
- Background extraction/chunking
- Retry processing
- Source attribution

### 8.5 Search and Retrieval
- pgvector support
- Embedding abstraction
- Semantic search
- Keyword search
- Hybrid retrieval
- Filters
- Related content

### 8.6 AI Orchestration
- Provider abstraction
- Ollama implementation
- Task-based routing
- Prompt template management
- AI request logs
- Failure handling
- Safety hooks

### 8.7 Relationship / Graph Engine
- Explicit relationships
- Suggested/inferred relationships
- Confidence score
- Source of relationship
- Graph browsing APIs and UI

### 8.8 Planning Engine
- Convert goals/freeform ideas into milestones, projects, tasks, routines
- Planning templates
- Human approval/edit flow
- Save accepted output into structured entities

### 8.9 Dashboard
- Today focus
- Overdue tasks
- Active goals
- Routines due
- Recent notes and journals
- Upcoming events
- Recommendations
- AI insight widgets

### 8.10 Recommendation Engine
- Hybrid rule-based + AI
- Overdue detection
- Inactive goal detection
- Routine drop-off
- Neglected area detection
- Project risk warnings
- Explainability and lifecycle states

### 8.11 Journal Intelligence
- Theme extraction
- Mood/sentiment proxy
- Recurring blockers
- Wins
- Weekly/monthly synthesis
- Privacy-aware controls

### 8.12 Background Jobs
- Ingestion jobs
- Embedding jobs
- AI summary jobs
- Recommendation refresh jobs
- Reminder generation
- Retry and monitoring support

### 8.13 Notifications
- In-app notifications
- Reminder center
- Preferences
- Read/unread/archive states

### 8.14 Admin Console
- System overview
- Users
- Jobs
- AI usage
- Audit logs
- Ingestion failures
- High-level analytics

### 8.15 Security Hardening
- Rate limiting
- Secure uploads
- Ownership checks
- Permission enforcement
- Safe rendering paths
- Secure defaults

### 8.16 Import / Export
- JSON export
- Markdown/zip export where useful
- Structured import flows
- Validation preview

### 8.17 Analytics
- Internal usage analytics
- User productivity analytics
- Privacy-aware event collection

### 8.18 UI Polish
- Design system
- Token-based theming system
- Multi-theme support
- Consistent enterprise layout
- Quality forms, tables, drawers, dialogs, cards, badges, loaders, toasts
- Responsive behavior across all supported device classes
- Accessible focus, keyboard, and contrast handling

### 8.19 Testing
- Backend tests
- Frontend tests
- E2E tests for critical flows

### 8.20 Documentation
- README
- AGENTS
- Architecture docs
- Security docs
- Testing docs
- Deployment docs
- Module docs
- Roadmap docs

---

## 9. Development Workflow

For every meaningful feature or module:

1. Update/define schema and models
2. Create or update migration
3. Implement service logic
4. Expose API endpoints
5. Connect frontend pages and components
6. Add loading / empty / error states
7. Add tests for critical behavior
8. Update docs
9. Verify the app still runs
10. Ensure permissions/audit implications are handled where relevant
11. Validate responsive behavior and theme behavior where UI changed
12. Capture screenshots for major UI work
13. Commit and push after the phase is complete

---

## 10. Quality Bar

A change is not complete unless it includes, where relevant:
- backend implementation
- frontend integration
- migration
- validation
- error handling
- docs update
- test coverage for critical paths
- responsive validation
- theme validation
- build success

---

## 11. UX Expectations

The UI must be:
- professional
- clean
- business-like
- modern and premium, not dated
- not cartoonish
- not over-spaced
- information-dense without feeling cluttered
- consistent in typography and layout
- effective for daily use
- visually coherent across light, dark, and alternate themes
- usable across mobile, tablet, laptop, desktop, and ultrawide screens

Must include:
- sidebar navigation with responsive collapse/drawer behavior
- header
- breadcrumbs where appropriate
- page titles
- action bars
- clear list/detail workflows
- great empty states
- skeleton loaders
- polished dialogs and forms

### 11.1 Frontend Layout Instruction (Mandatory)

The generated frontend layout must follow these rules exactly:

#### A. Global App Shell
- use a stable application shell with:
  - left navigation rail / sidebar on desktop
  - compact collapsible sidebar on laptop
  - bottom navigation or drawer-triggered navigation on mobile where appropriate
  - sticky top header for global actions, search, notifications, and profile
- do not allow each page to invent its own layout pattern
- keep navigation, spacing, sizing, and page structure consistent across modules



#### A1. Header Content Definition (Mandatory)

The Top Header (TopNav) must be consistent across all pages.

##### Left Section (Identity + Navigation Context)
Must include:
- App logo or product name (click navigates to dashboard)
- Current workspace or context selector if multi-workspace is enabled

Optional:
- Breadcrumb if not shown in the page header

##### Center Section (Primary Interaction)
Must include:
- Global search bar

Behavior:
- supports entity search
- supports command palette trigger (Ctrl+K)
- supports quick navigation
- expandable on desktop
- full-width or overlay behavior on mobile

##### Right Section (Actions + User Controls)
Must include:
- Command palette trigger
- Quick create button
- Notifications icon with unread badge
- AI assistant entry
- Theme toggle
- User profile menu

Quick create must support:
- task
- goal
- note
- project

User profile menu should include:
- profile
- settings
- logout

##### Mobile Behavior
On mobile, collapse header into:
- left: hamburger + logo
- right: search, notifications, profile

Optional:
- move create action into FAB or overflow menu if space is limited

##### Header Behavior Rules
- Header must be sticky
- Header height must remain consistent across pages
- Header must not wrap into multiple rows unless explicitly designed for a small breakpoint
- Header must remain usable on mobile, tablet, desktop, and wide desktop

##### Anti-Patterns
Do not:
- overload the header with page-specific actions
- change header structure per page
- hide critical actions several levels deep
- duplicate page action bar responsibilities inside the top header

##### Styling Rules
- Background:
  - light theme: surface or white
  - dark theme: dark surface token
- Border:
  - subtle bottom border only
- Standard height:
  - 56px to 64px
- Spacing:
  - token-driven only

##### Codex Header Rules
Codex MUST:
- implement header as reusable TopHeader component
- keep header structure consistent across pages
- ensure responsive behavior
- integrate header with command palette, notifications, assistant, theme toggle, and user menu
- avoid page-specific header variants unless explicitly approved in AGENTS.md

#### B. Responsive Breakpoints
Design and test for all of these viewport groups:
- mobile: 320px to 639px
- tablet: 640px to 1023px
- desktop: 1024px to 1439px
- wide desktop: 1440px to 1919px
- ultrawide: 1920px and above

Rules:
- no horizontal scrolling for normal page content
- no fixed pixel widths for main containers, cards, forms, tables, modals, or charts unless absolutely required
- prefer CSS grid, flex, minmax(), clamp(), and container-aware layouts
- content must reflow cleanly instead of shrinking into unusable blocks

#### C. Page Composition Pattern
Every major page should follow this order unless there is a strong reason not to:
1. page container
2. page header row
3. breadcrumb / context row
4. primary action bar
5. summary / KPI strip if relevant
6. filter/search/sort controls
7. main content region
8. secondary detail panel / drawer / inspector if relevant

Do not place large decorative hero sections above working content in authenticated screens.

#### D. Standard Layout Types
Use only a small number of approved layout patterns:
- dashboard layout: KPI row + insights grid + activity panel
- list layout: filters toolbar + table/list + optional right detail panel
- detail layout: header + metadata + tabbed content + side info panel
- workspace layout: split pane or 3-column knowledge layout where useful
- settings/admin layout: left section nav + right configuration panel
- form layout: narrow readable form column with grouped sections, not full-width stretched inputs

#### E. Navigation Layout Rules
- sidebar width should be token-driven and collapsible
- support icon + label in expanded state and icon-only in collapsed state
- on tablet, prefer collapsible overlay drawer if persistent sidebar harms content width
- on mobile, navigation must not consume permanent vertical space unnecessarily
- highlight active route clearly and consistently
- group navigation by domain, not random ordering

#### F. Spacing and Alignment Rules
- use a spacing scale and design tokens; do not hardcode arbitrary spacing repeatedly
- align page titles, filters, cards, tables, and form sections to a consistent content grid
- reduce excessive empty space above fold
- use denser enterprise spacing for data-heavy screens
- use larger breathing room only for onboarding, landing, or marketing-like panels

#### G. Card, Panel, and Surface Rules
- avoid excessive card nesting
- do not place every small item inside a separate card if a flat grouped section works better
- use cards for logical grouping, not as decoration
- each surface must have clear hierarchy through elevation, border, background, spacing, and typography
- on dense screens, prefer flat sections with separators over too many floating cards

#### H. Table and Data Grid Rules
- tables must be usable on laptop widths and degrade gracefully on tablet/mobile
- support sticky headers where useful
- support column prioritization so low-value columns collapse first on smaller screens
- on small screens, convert wide tables into stacked row cards or expandable rows when needed
- action buttons in tables must be compact and consistent

#### I. Form Layout Rules
- forms should use 1-column layout on mobile, 2-column only when space truly supports it
- related fields must be grouped into sections with section titles and helper text
- labels must always remain visible; do not rely on placeholder-only inputs
- validation states must not break layout
- long forms should support sticky section navigation or segmented tabs when appropriate

#### J. Drawer / Modal / Side Panel Rules
- use drawers for contextual edit/view flows
- use modals for confirmations or short focused tasks
- use full-screen dialogs on small devices when standard modal size becomes cramped
- right-side inspectors should collapse into drawer or stacked section on smaller screens

#### K. Dashboard Layout Rules
- top row should show the most important KPIs, not too many equal-priority widgets
- chart areas must have minimum heights and must not be squeezed into tiny cards
- supporting widgets should align to a clean grid with consistent row rhythm
- do not create a patchwork layout with random card heights unless intentional

#### L. Theme and Styling Rules
- implement theme through semantic design tokens, not per-component hardcoded colors
- support at minimum: light, dark, and one additional premium theme
- all layouts must remain readable in every theme
- use modern enterprise styling: subtle borders, controlled shadows, layered surfaces, good contrast, and restrained accent usage
- avoid outdated gradients, overly rounded toy-like cards, or flashy neon visuals unless theme-specific and intentional

#### M. Typography Rules
- use a clear type scale for page title, section title, body, helper, caption, and numeric emphasis
- avoid oversized headings that push content below the fold
- keep line lengths readable
- maintain consistent heading rhythm across screens

#### N. Component Responsiveness Rules
All shared components must be responsive by default:
- page headers
- action bars
- search bars
- filter chips
- tabs
- cards
- tables
- dialogs
- charts
- side panels
- breadcrumbs
- toasts

#### O. Accessibility and Usability Rules
- keyboard navigation must work across sidebar, tables, dialogs, forms, and command areas
- visible focus states are mandatory in every theme
- touch targets must be appropriate on mobile/tablet
- contrast must meet accessible standards
- support reduced motion preferences

#### P. Frontend Review Checklist for Every Phase
For every frontend phase, verify and document:
- mobile layout works
- tablet layout works
- desktop layout works
- wide desktop layout works
- light theme works
- dark theme works
- no broken overflow or clipped content
- no inconsistent spacing or alignment
- no page-specific hardcoded layout hacks

#### Q. Codex Instruction for Layout Work
When implementing any frontend phase, Codex must:
- follow the approved layout patterns in this AGENTS.md
- refactor pages that violate the shared layout system
- prefer shared layout primitives over one-off page wrappers
- avoid hardcoded widths, heights, spacing, and colors unless defined through tokens
- test every changed screen against multiple breakpoints and themes before marking the phase complete
- keep layout modern, responsive, enterprise-grade, and visually consistent across the whole product

---

## 12. Observability and Audit

Must support:
- request logging
- structured error logging
- request correlation IDs
- audit logs for important entity changes and auth/admin actions
- job status tracking
- AI request visibility
- admin operational monitoring

---

## 13. Anti-Patterns to Avoid

Strictly avoid:
- mock-only implementations
- hardcoded AI outputs
- giant files
- direct DB logic scattered in routes
- copy-paste duplication
- silent failures
- feature pages with no real backend connection
- skipping permissions because UI hides buttons
- weak typing and inconsistent DTO/schema definitions
- duplicated API contracts across modules
- global-store misuse for server state

---

## 14. Codex Execution Guidance

When working on this repository:
- read this AGENTS.md first
- preserve good existing code
- refactor weak structure gradually
- implement features in coherent phases
- keep the project runnable
- prefer quality over rushed scaffolding
- do not stop at UI-only or API-only completion
- validate UI on at least mobile, tablet, and desktop breakpoints for frontend-facing changes
- implement styling through shared tokens/components before page-level overrides
- ensure new UI works in all supported themes
- leave the codebase cleaner after each phase
- commit and push after each completed phase or sub-phase

### Standard Codex instruction pattern
Use this structure when prompting Codex:

```text
Read AGENTS.md and implement Phase X.

Follow strictly:
- locked stack
- frontend layout system
- design tokens
- API contract
- Definition of Done

Validate:
- mobile, tablet, desktop, wide desktop
- light and dark themes
- loading, empty, and error states

Do not:
- hardcode styles
- use mock data when real backend exists
- skip tests, docs, or commit

Commit and push after completion.
```

---

## 15. End Goal

Deliver a scalable, intelligent, enterprise-grade AI Life Architect platform that unifies:
- knowledge
- planning
- execution
- reflection
- retrieval
- recommendations
- AI assistance

The system should be strong enough to evolve into a full personal intelligence platform for serious long-term usage.

---

## Phase 16–25 Roadmap

### Phase 16 — Core Entity System (Goals, Tasks, Projects, Notes)
Goal: establish the fundamental data model and relationships.

Requirements:
- implement CRUD for:
  - goals
  - tasks
  - projects
  - notes
- support relationships:
  - tasks linked to goals
  - tasks linked to projects
  - notes linked to entities
- ensure consistent data schema across modules
- add validation and error handling

Quality bar:
- no duplicate entity logic
- clean service layer
- consistent naming

---

### Phase 17 — List/Detail UI System
Goal: standardize how entities are viewed and edited.

Requirements:
- implement list + detail layout pattern:
  - table/list view
  - context panel (detail view)
- support:
  - sorting
  - filtering
  - pagination
- maintain consistent UI across all entity pages
- ensure responsive behavior for:
  - mobile stacked view
  - tablet split behavior where appropriate
  - desktop multi-panel layout
- use shared layout primitives and token-based spacing/typography
- avoid hardcoded one-off page CSS

Quality bar:
- reusable layout components
- consistent UX
- usable on all supported device classes

---

### Phase 18 — Execution Queue (Task Focus Layer)
Goal: create a focused execution surface for tasks.

Requirements:
- build execution queue:
  - prioritized tasks
  - quick actions (open, complete, defer)
- support filtering:
  - overdue
  - due today
  - active
- integrate with tasks and goals

Quality bar:
- action-first UI
- fast interaction

---

### Phase 19 — Planner Engine (AI Planning Foundation)
Goal: convert user input into structured plans.

Requirements:
- accept:
  - freeform input
  - templates
- generate:
  - goal
  - tasks
  - milestones
  - projects
- support structured output (JSON)
- integrate with AI layer

Quality bar:
- structured, not free text
- predictable output format

---

### Phase 20 — Planner Review & Approval UI
Goal: allow users to review and edit AI-generated plans.

Requirements:
- build review interface:
  - goal summary
  - tasks list
  - milestones
  - projects
- support inline editing
- support selective import:
  - goal
  - tasks
  - milestones
- provide:
  - Save Review
  - Approve & Import

Quality bar:
- not form-heavy
- structured UI
- clear hierarchy

---

### Phase 21 — Command Palette
Goal: enable fast navigation and actions.

Requirements:
- implement command palette (Ctrl+K)
- support:
  - navigation
  - quick actions
  - entity search
- keyboard navigation:
  - arrow keys
  - enter
  - escape

Quality bar:
- fast
- no lag
- consistent behavior

---

### Phase 22 — Deep Command Actions
Goal: extend command palette to execute real actions.

Requirements:
- support:
  - open entity
  - create entity
  - filter views
  - run actions (complete task, etc.)
- integrate with real data
- no mock responses

Quality bar:
- command = action
- not just navigation

---

### Phase 23 — Context-Aware AI Suggestions
Goal: provide smart suggestions based on real data.

Requirements:
- use:
  - overdue tasks
  - active goals
  - recent activity
- generate suggestions like:
  - focus on high priority tasks
  - review overdue work
- integrate into:
  - dashboard
  - command palette

Quality bar:
- grounded in data
- not generic AI output

---

### Phase 24 — Unified Search (Hybrid Retrieval)
Goal: search across all entities and documents.

Requirements:
- support search across:
  - tasks
  - goals
  - projects
  - notes
  - journals
- implement:
  - keyword search
  - semantic search (pgvector)
  - hybrid retrieval
- provide filters:
  - type
  - date
  - source

Quality bar:
- fast
- relevant results
- structured output

---

### Phase 25 — AI Create (Natural Language → Structured Data)
Goal: allow users to create entities via natural language.

Requirements:
- detect intent:
  - create goal
  - create task
  - create note
- generate structured output:
  - title
  - description
  - tasks (if goal)
- integrate with:
  - command palette
  - planner
- support review-before-create

Quality bar:
- structured output
- no raw text
- clean UX flow

---

## Phase 26–40 Roadmap

### Phase 26 — Command Memory and Personalized Ranking
Goal: make the command palette smarter based on user behavior and recency.

Requirements:
- Track recently opened entities
- Track recently created entities
- Track frequently used commands
- Track recently executed AI create actions
- Support lightweight persistence for command memory
- Show useful empty-query sections:
  - Recent Items
  - Frequent Actions
  - Suggested Next Actions
- Improve ranking by:
  - recency
  - frequency
  - current workspace relevance
  - current page/context relevance
- Keep deterministic ranking stable and explainable
- Preserve keyboard-first behavior

Quality bar:
- no fake memory
- no noisy personalization
- no degraded search performance

---

### Phase 27 — Smart Recommendations Engine
Goal: create a hybrid rule-based + AI recommendation system.

Requirements:
- Deterministic recommendation rules for:
  - overdue tasks
  - high-priority unfinished tasks
  - inactive goals
  - stale projects
  - neglected life areas
  - routine drop-off
  - work overload
- AI enhancement layer to:
  - explain recommendations
  - improve wording
  - group related suggestions
- Recommendation model should support:
  - type
  - title
  - subtitle/reason
  - priority
  - confidence
  - source
  - lifecycle state
- Actions:
  - accept
  - snooze
  - dismiss
  - convert to task/plan
- Surface recommendations in:
  - dashboard
  - command palette
  - recommendations inbox/page

Quality bar:
- recommendations must be actionable
- avoid duplicates and noise
- deterministic signals remain primary when strong

---

### Phase 28 — Weekly AI Review
Goal: synthesize the user’s week into grounded, useful review output.

Requirements:
- Aggregate weekly signals from:
  - completed tasks
  - overdue tasks
  - active goals
  - recent notes
  - recent journals
  - routines performed/missed
  - activity timeline
- Generate structured weekly review sections:
  - wins
  - misses
  - unfinished priorities
  - recurring blockers
  - goal momentum
  - next-week focus
- Make review available from:
  - command palette
  - dedicated weekly review UI
  - dashboard entry point where useful
- Support follow-up actions:
  - create tasks
  - open affected goals
  - create note/journal from review
- Keep privacy-aware handling for journal content

Quality bar:
- concise
- action-oriented
- grounded in real user data

---

### Phase 29 — Progress Intelligence
Goal: create real progress signals across goals, projects, tasks, and routines.

Requirements:
- Compute metrics such as:
  - goal velocity
  - task completion rate
  - overdue trend
  - consistency trend
  - stagnation signals
  - momentum score where justified
- Expose insights on:
  - dashboard
  - goal detail
  - project detail
  - command palette suggestions where useful
- AI may enhance explanation of computed metrics
- Support drill-down to underlying items
- Add tests for calculations

Quality bar:
- no vanity metrics
- insights must connect to action
- formulas should be understandable

---

### Phase 30 — Cross-Entity Linking
Goal: connect related entities manually and through AI/rule-assisted suggestions.

Requirements:
- Support links between:
  - goals and tasks
  - goals and projects
  - notes and projects
  - notes and goals
  - journals and life areas
  - journals and goals
  - routines and goals
- Support inferred links using:
  - shared keywords
  - semantic similarity
  - recent activity
  - tags
- Relationship record should support:
  - source entity
  - target entity
  - relationship type
  - confidence
  - source of link
- Surface related items in detail pages
- Let users accept/reject inferred links
- Improve search and palette behavior using links

Quality bar:
- no noisy auto-link spam
- inferred links must be reviewable
- manual control preserved

---

### Phase 31 — Knowledge Graph Engine
Goal: create a useful graph layer for related entities.

Requirements:
- Support graph across:
  - goals
  - projects
  - tasks
  - notes
  - journals
  - routines
  - life areas
- Relationship types may include:
  - supports
  - blocks
  - related_to
  - references
  - derived_from
  - linked_to_goal
- APIs for:
  - neighbors
  - focused subgraph
  - suggested expansions
- Graph explorer UI:
  - focus node
  - relationship filters
  - click-to-open entity
- Integrate graph awareness into detail pages and search
- Support manual link creation

Quality bar:
- graph must be useful, not decorative
- keep UI focused and readable

---

### Phase 32 — Semantic Search with pgvector
Goal: make the system searchable by meaning, not just keywords.

Requirements:
- Use pgvector for semantic retrieval
- Index embeddings for:
  - document chunks
  - notes
  - journals
  - selected goals/projects/tasks where useful
- Support:
  - semantic search
  - keyword search
  - hybrid ranking
- Filters:
  - entity type
  - workspace
  - date range
  - goal/project/life area
  - tags
- Results should show:
  - title
  - snippet
  - entity type
  - relevance context
- Integrate with:
  - search page
  - command palette
  - related content suggestions

Quality bar:
- scoped and fast
- no irrelevant noisy matches
- deterministic filters remain first-class

---

### Phase 33 — Memory Synthesis
Goal: synthesize patterns across accumulated user data.

Requirements:
- Build synthesis across:
  - notes
  - journals
  - goals
  - completed tasks
  - routines
- Generate structured insights:
  - recurring themes
  - repeated blockers
  - repeated wins
  - long-term priorities
  - unresolved topics
- Surface synthesis in:
  - dashboard insights
  - weekly review
  - command palette
  - dedicated insights/memory page if useful
- Link synthesized insights back to source entities
- Keep synthesized content distinct from raw user content

Quality bar:
- evidence-linked
- not generic
- clearly useful

---

### Phase 34 — Habit and Routine Tracking
Goal: make routines measurable and operational.

Requirements:
- Extend routines with:
  - recurrence pattern
  - completion logs
  - missed logs
  - streaks
  - consistency metrics
- Add routine log model/service
- UI for:
  - marking routine complete
  - viewing streaks
  - viewing recent routine history
- Integrate routine data into:
  - dashboard
  - weekly review
  - AI suggestions
  - progress intelligence
- Allow AI to suggest routine improvements

Quality bar:
- practical, not gamified
- integrated with planning system

---

### Phase 35 — Workflow Automation
Goal: support safe event-driven automations.

Requirements:
- Support automations like:
  - when task completed -> update linked goal progress
  - when goal created -> suggest tasks
  - when item overdue -> create notification
  - when routine repeatedly missed -> create recommendation
- Automation model:
  - trigger
  - conditions
  - actions
  - enabled/disabled state
- Add execution logs and audit visibility
- UI for viewing configured automations
- Start with a controlled set of safe triggers/actions

Quality bar:
- no automation loops
- no silent side effects
- logs must explain execution

---

### Phase 36 — Notification Engine
Goal: create a reliable in-app notification system.

Requirements:
- Notification model should support:
  - type
  - title
  - body
  - severity
  - source entity
  - read/unread
  - archived
- Generate notifications for:
  - overdue tasks
  - due today tasks
  - automation events
  - AI suggestions requiring attention
  - routine misses
- Notification center UI:
  - unread count
  - mark read/unread
  - archive
  - navigate to source item
- Integrate notifications with:
  - header
  - command palette
- Prepare preference hooks for future expansion

Quality bar:
- avoid notification spam
- every notification should be actionable

---

### Phase 37 — Analytics Dashboard
Goal: provide meaningful user productivity and product usage analytics.

Requirements:
- Track and show:
  - tasks completed over time
  - overdue trends
  - goal progress trends
  - routine consistency
  - AI feature usage
  - command palette usage
- Build backend aggregation services/endpoints
- Build analytics UI with:
  - summary cards
  - tables
  - charts where useful
- Distinguish:
  - user productivity analytics
  - product usage analytics

Quality bar:
- no vanity metrics
- analytics should lead to action
- clean, business-like visual design

---

### Phase 38 — Admin Console
Goal: provide operational visibility for enterprise usage.

Requirements:
- Admin pages for:
  - users
  - roles/permissions
  - jobs
  - notifications
  - AI usage
  - audit logs
  - ingestion failures
  - system overview
- Add admin aggregation endpoints
- Enforce strict permission checks
- Add searchable/sortable tables
- Expose useful operational data safely

Quality bar:
- admin must feel clean and serious
- no permission leakage
- operational visibility must be actionable

---

### Phase 39 — Security Hardening
Goal: perform a systematic security pass across the platform.

Requirements:
- Review/enforce RBAC across backend routes
- Add/verify:
  - ownership checks
  - secure defaults
  - validation hardening
  - file upload safety
  - rate limiting for auth and AI-heavy endpoints
  - safe rendering paths
- Normalize API error responses
- Add security-focused tests for:
  - unauthorized access
  - forbidden actions
  - invalid payloads
- Improve audit logging for security-sensitive actions
- Update security documentation/checklist

Quality bar:
- backend enforcement first
- no UI-only protection
- systematic, not ad hoc

---

### Phase 40 — Import / Export
Goal: provide structured data portability.

Requirements:
- Export support for:
  - goals
  - tasks
  - notes
  - journals
  - routines
  - projects
  - relationship metadata where appropriate
- Export formats:
  - JSON bundle
  - markdown/zip where useful
- Import support for:
  - structured JSON
  - CSV where practical
- Add validation preview before import
- Preserve links where possible
- Use background jobs for large operations

Quality bar:
- portability must be real
- import errors must be understandable
- do not corrupt existing data

---

## Phase 41–60 Roadmap

### Phase 41 — AI Command Layer
Goal: make the application command-driven through natural language.

Requirements:
- Accept natural language commands such as:
  - plan my week
  - show overdue tasks
  - summarize my goals
  - review my journals
- Parse commands into structured intents:
  - navigate
  - filter
  - create
  - summarize
  - review
  - prioritize
- Integrate with command palette
- Map commands to real actions, not chat-only responses
- Return structured outputs with:
  - intent
  - target entity/module
  - action
  - payload
  - confidence
- Preserve deterministic routing when intent is obvious
- Use AI only when command classification is ambiguous or broad

Quality bar:
- commands must execute real actions
- deterministic commands should feel instant
- no generic conversational fluff

---

### Phase 42 — AI Context Memory
Goal: give AI flows awareness of user context and recent behavior.

Requirements:
- Build a context memory layer using:
  - recent entities
  - recent commands
  - recent AI actions
  - current workspace
  - active goals
  - overdue tasks
  - recent reviews/summaries
- Context should support:
  - better recommendations
  - better planning
  - smarter command interpretation
  - more relevant summaries
- Add a context builder service that assembles structured context bundles
- Keep context scoped and privacy-safe
- Use context in:
  - command palette AI results
  - planning flows
  - assistant responses
  - review flows

Quality bar:
- context must improve relevance
- no creepy or over-personalized behavior
- context must remain explainable

---

### Phase 43 — AI Assistant Panel
Goal: add a persistent AI assistant workspace inside the app.

Requirements:
- Add an assistant panel or assistant surface
- Allow natural language questions and actions such as:
  - what should I do today
  - summarize my week
  - help me plan this goal
  - what is blocking progress
- Assistant should return:
  - answers
  - suggested actions
  - links into app modules
  - structured lists where appropriate
- Integrate with:
  - tasks
  - goals
  - journals
  - notes
  - recommendations
- Preserve actionability:
  - open item
  - create follow-up
  - apply filter
  - start plan
- Keep assistant UX compact and production-grade

Quality bar:
- assistant must connect to real data
- responses should be structured and actionable
- avoid generic chatbot feel

---

### Phase 44 — AI Auto-Prioritization
Goal: automatically rank work by urgency and strategic importance.

Requirements:
- Build prioritization engine using:
  - due dates
  - priority values
  - goal linkage
  - inactivity
  - user behavior signals
  - recommendation signals
- Output ranked execution queue
- Expose prioritization reasons such as:
  - overdue
  - high importance
  - blocked goal
  - repeated neglect
- Integrate with:
  - execution queue
  - dashboard
  - command palette
  - assistant
- Allow user override while preserving system ranking visibility

Quality bar:
- rankings must be explainable
- no arbitrary or opaque scoring
- system must remain stable and predictable

---

### Phase 45 — Smart Notifications
Goal: upgrade notifications into prioritized, contextual alerts.

Requirements:
- Replace basic alerts with smart notifications
- Notifications should support:
  - urgency
  - context
  - related entity
  - next recommended action
- Examples:
  - this goal has stalled
  - these 2 tasks need attention today
  - you missed your routine 3 times this week
- Group related notifications
- Suppress low-value noise
- Integrate with:
  - header notification center
  - dashboard
  - command palette
  - assistant

Quality bar:
- notifications must be helpful, not spammy
- every notification should imply a clear next action

---

### Phase 46 — Event-Driven Auto Workflows
Goal: automate system actions from real user/system events.

Requirements:
- Support events such as:
  - task completed
  - task overdue
  - goal created
  - goal stalled
  - routine missed
  - review completed
- Support actions such as:
  - update linked progress
  - create recommendation
  - create notification
  - suggest follow-up tasks
  - trigger assistant insight
- Build workflow runner with:
  - trigger
  - conditions
  - actions
  - logs
- Ensure idempotency and loop prevention

Quality bar:
- automations must be safe
- logs must explain what happened
- no silent confusing side effects

---

### Phase 47 — AI Habit Engine
Goal: build intelligence around routines and repeated behaviors.

Requirements:
- Detect behavior patterns from:
  - routine completion logs
  - missed routines
  - task repetition
  - journal patterns
- Generate insights such as:
  - most consistent routines
  - routines likely to fail
  - time windows with best completion
- Suggest habit improvements
- Integrate with:
  - routines
  - weekly review
  - dashboard
  - assistant

Quality bar:
- useful, practical, not gimmicky
- recommendations must be grounded in logs/patterns

---

### Phase 48 — AI Daily Planning
Goal: generate a practical daily plan from real data.

Requirements:
- Support prompts like:
  - plan my day
  - what should I focus on today
- Build day plan from:
  - overdue items
  - due today items
  - active goals
  - routines
  - existing calendar/events if available later
- Produce structured output:
  - must-do
  - should-do
  - optional
  - avoid today
- Allow importing plan into tasks or planner
- Integrate with:
  - dashboard
  - assistant
  - command palette

Quality bar:
- plans must be realistic
- no generic motivational output
- must reflect actual workload

---

### Phase 49 — AI Weekly Strategy
Goal: extend weekly review into forward-looking weekly strategy.

Requirements:
- Build from:
  - weekly review data
  - incomplete priorities
  - goal momentum
  - routine consistency
  - stalled projects
- Produce structured strategy output:
  - keep doing
  - fix this
  - stop doing
  - next week focus
- Allow conversion into:
  - tasks
  - goals
  - plans
  - notes
- Integrate with assistant and planner

Quality bar:
- strategy must be specific
- must connect to actual data and outcomes

---

### Phase 50 — AI Decision Engine
Goal: help user decide what to continue, stop, delay, or prioritize.

Requirements:
- Build decision support using:
  - progress signals
  - task load
  - routine completion
  - stalled goals
  - time/effort patterns
- Generate recommendations like:
  - pause this goal
  - focus on this project
  - stop maintaining this routine
  - convert this note into action
- Expose reasoning clearly
- Allow actions directly from decision cards/panel

Quality bar:
- decisions must be explainable
- avoid over-automation at this phase
- user remains in control

---

### Phase 51 — Multi-Agent Architecture
Goal: split AI work into specialized agents.

Requirements:
- Introduce specialized agents such as:
  - planner agent
  - review agent
  - recommendation agent
  - retrieval agent
  - prioritization agent
- Add orchestration layer to route tasks to the correct agent
- Share common context memory safely
- Standardize input/output contracts for agents
- Preserve observability and logs

Quality bar:
- agents must have clear responsibility boundaries
- no duplicated logic across agents
- orchestration must remain debuggable

---

### Phase 52 — Knowledge Intelligence
Goal: make the knowledge system actively useful.

Requirements:
- Connect:
  - notes
  - journals
  - tasks
  - goals
  - projects
- Detect:
  - repeated ideas
  - unresolved notes
  - notes that should become tasks
  - journals linked to goals
- Suggest:
  - create task from note
  - link journal to goal
  - merge duplicate note topics
- Integrate with:
  - search
  - assistant
  - recommendations
  - knowledge views

Quality bar:
- insight quality over quantity
- avoid noisy suggestions

---

### Phase 53 — Predictive Planning
Goal: forecast likely slippage and execution risk.

Requirements:
- Predict:
  - likely overdue tasks
  - likely stalled goals
  - overloaded weeks
  - weak routine adherence
- Use:
  - historical completion patterns
  - workload density
  - prioritization behavior
  - routine consistency
- Surface prediction as:
  - risk indicator
  - early warning
  - actionable suggestion
- Integrate with dashboard and assistant

Quality bar:
- predictions must be conservative and explainable
- no fake certainty

---

### Phase 54 — AI Work Graph
Goal: create an intelligent graph of work relationships and execution paths.

Requirements:
- Build graph over:
  - goals
  - tasks
  - projects
  - routines
  - notes
  - journals
- Support:
  - dependency mapping
  - blocker chains
  - linked work clusters
  - execution path visualization
- Add AI suggestions for:
  - missing links
  - hidden dependencies
  - work clusters that should be grouped
- Integrate with graph explorer and detail pages

Quality bar:
- graph must support decisions, not just visualization
- remain readable and useful

---

### Phase 55 — AI Coaching
Goal: provide coaching-style guidance from actual work patterns.

Requirements:
- Generate coaching insights such as:
  - you start too many things at once
  - this goal is under-defined
  - your routines are strongest on certain days
  - you complete small tasks but avoid strategic work
- Connect coaching to:
  - routines
  - tasks
  - goals
  - weekly reviews
  - decision engine
- Keep coaching practical and non-judgmental
- Allow dismiss/snooze/accept actions

Quality bar:
- must feel supportive and grounded
- avoid generic life advice

---

### Phase 56 — Multi-User / Team Mode
Goal: support shared workspaces and collaborative usage.

Requirements:
- Add:
  - team workspaces
  - shared goals
  - shared projects
  - assignments
  - permissions
- Preserve personal and team boundaries
- Add role-aware views
- Update assistant and search to respect workspace permissions

Quality bar:
- permission handling must be strict
- collaboration must not break personal workflows

---

### Phase 57 — Collaboration AI
Goal: extend AI features into shared/team workflows.

Requirements:
- Support team-aware suggestions such as:
  - coordination blockers
  - unowned work
  - duplicated effort
  - missing follow-up
- Summarize team progress
- Recommend next-team actions
- Integrate with:
  - shared workspaces
  - notifications
  - assistant
  - planning/review flows

Quality bar:
- respect permissions
- avoid exposing private context in shared flows

---

### Phase 58 — External Integrations and API Layer
Goal: connect the system with external sources and actions.

Requirements:
- Add API/integration layer for:
  - calendar
  - email
  - messaging/chat tools
  - file stores
- Allow external signals to appear as:
  - tasks
  - reminders
  - context
  - search results
- Keep integrations modular and permission-safe
- Add import/export mappings where useful

Quality bar:
- integrations must be optional and isolated
- external data should not pollute core UX

---

### Phase 59 — AI Templates / Agent Marketplace
Goal: make AI behaviors reusable and configurable.

Requirements:
- Support reusable templates for:
  - planning
  - weekly review
  - daily planning
  - habit coaching
  - project kickoff
- Allow user/admin to choose templates
- Support future agent presets or marketplace-style extensibility
- Keep template metadata structured and versioned

Quality bar:
- templates must be practical
- avoid template sprawl
- keep consistent execution contracts

---

### Phase 60 — Autonomous Mode
Goal: allow safe, approved AI-driven execution of routine actions.

Requirements:
- Support opt-in autonomous flows such as:
  - reorganize daily plan
  - reschedule low-priority work
  - generate weekly review draft
  - create follow-up tasks from accepted rules
- Require approval boundaries and audit logs
- Allow users to inspect what the system will do before execution
- Add safety controls:
  - disable
  - revert where possible
  - audit trail
  - scope limits

Quality bar:
- no uncontrolled automation
- user must remain in control
- actions must be observable and reversible where practical

---

## Phase 61–80 Roadmap

### Phase 61 — Plugin Architecture
Goal: make the system extensible via plugins.

Requirements:
- define plugin interface
- allow modules to register:
  - commands
  - UI components
  - workflows
- support dynamic loading
- isolate plugin logic from core system

Quality:
- no plugin can break core app
- strict interface contracts

---

### Phase 62 — Custom AI Agents (User-defined)
Goal: allow users to define their own AI agents.

Requirements:
- users define:
  - goal
  - behavior
  - triggers
- agents can:
  - suggest
  - create tasks
  - summarize data
- integrate with command palette

Quality:
- structured configs
- no unsafe execution

---

### Phase 63 — Data Layer Unification
Goal: unify all entity data into a single semantic layer.

Requirements:
- unify:
  - tasks
  - goals
  - notes
  - journals
- build central query layer
- standardize schema

Quality:
- no duplicated data access logic
- consistent queries everywhere

---

### Phase 64 — AI Explainability Layer
Goal: show why AI made decisions.

Requirements:
- expose:
  - reasoning
  - inputs
  - confidence
- integrate into:
  - recommendations
  - prioritization
  - assistant

Quality:
- transparent
- simple explanation

---

### Phase 65 — AI Audit Trail
Goal: track all AI decisions and actions.

Requirements:
- log:
  - AI input
  - output
  - actions triggered
- allow inspection

Quality:
- traceable
- debuggable

---

### Phase 66 — Offline Mode / Sync
Goal: allow partial offline usage.

Requirements:
- local cache
- sync mechanism
- conflict resolution

Quality:
- no data loss
- predictable behavior

---

### Phase 67 — Performance Optimization
Goal: scale frontend + backend performance.

Requirements:
- optimize:
  - queries
  - rendering
  - caching
- add lazy loading
- reduce bundle size
- optimize theme switching and token resolution so styling remains fast
- avoid layout shift across responsive breakpoints
- measure page performance on mobile and desktop profiles

Quality:
- fast interaction
- no lag
- responsive UI should remain smooth across device classes

---

### Phase 68 — AI Latency Optimization
Goal: reduce AI response time.

Requirements:
- caching
- streaming responses
- partial responses

Quality:
- fast perceived performance

---

### Phase 69 — Multi-Device Sync
Goal: seamless usage across devices.

Requirements:
- real-time sync
- state persistence
- session continuity
- preserve user UI preferences across devices where appropriate:
  - theme
  - density
  - navigation state
  - recent workspace context

Quality:
- no mismatch between devices
- preferences should feel consistent and intentional

---

### Phase 70 — Cross-App Intelligence
Goal: connect external tools.

Requirements:
- connect:
  - calendar
  - email
  - notes apps
- ingest external signals into system

Quality:
- secure integrations
- clean mapping

---

### Phase 71 — AI Workspace Personalization
Goal: personalize workspace layout and behavior.

Requirements:
- adaptive layout
- smart defaults
- preferred modules
- theme-aware personalization that respects user-selected themes and does not override them unexpectedly
- support workspace-level theme defaults with user override capability

Quality:
- predictable, not chaotic
- personalization must not break consistency

---

### Phase 72 — Predictive UI
Goal: UI adapts based on user behavior.

Requirements:
- highlight likely actions
- reorder sections
- suggest next steps
- preserve responsive layout integrity while adapting UI
- do not create unpredictable control movement that harms usability on smaller screens

Quality:
- helpful, not intrusive
- adaptive behavior must remain stable and readable

---

### Phase 73 — Scenario Simulation
Goal: simulate outcomes.

Requirements:
- test:
  - plan changes
  - task changes
- show impact

Quality:
- grounded in real data

---

### Phase 74 — Goal Forecasting
Goal: predict goal success probability.

Requirements:
- use:
  - past performance
  - workload
- show:
  - success likelihood
  - risk

Quality:
- realistic predictions

---

### Phase 75 — Time Intelligence Engine
Goal: optimize time usage.

Requirements:
- analyze:
  - work patterns
  - routines
- suggest:
  - time blocks
  - improvements

Quality:
- actionable insights

---

### Phase 76 — Collaboration Intelligence
Goal: improve team coordination.

Requirements:
- detect:
  - delays
  - bottlenecks
- suggest fixes

Quality:
- team-aware insights

---

### Phase 77 — AI Governance Layer
Goal: control AI behavior.

Requirements:
- policies:
  - allowed actions
  - limits
- admin control

Quality:
- safe AI usage

---

### Phase 78 — Data Privacy Controls
Goal: protect user data.

Requirements:
- data access control
- AI usage boundaries
- audit controls

Quality:
- compliance-ready

---

### Phase 79 — Enterprise Deployment Mode
Goal: support enterprise customers.

Requirements:
- multi-tenant architecture
- configuration layers
- scaling support

Quality:
- stable and secure

---

### Phase 80 — AI Operating System Mode
Goal: unify all features into one system.

Requirements:
- command-first UX
- assistant-driven workflows
- system-wide intelligence

Quality:
- cohesive experience
- not feature-fragmented

---

## Phase 81–85 Roadmap (Testing, Quality, and Release Confidence)

### Phase 81 — Testing Foundation
Goal: establish a production-grade testing architecture across frontend, backend, database, AI flows, and end-to-end usage.

Requirements:
- Create a complete testing strategy covering:
  - frontend unit/component tests
  - frontend integration tests
  - backend unit tests
  - backend service/API integration tests
  - database integration tests
  - end-to-end browser tests
  - AI workflow tests
  - responsive UI tests
  - regression smoke tests
- Use:
  - Vitest + React Testing Library for frontend
  - pytest for backend
  - Playwright for end-to-end flows
- Add fixtures, factories, seed data helpers, and reusable test utilities
- Add scripts/commands for running:
  - frontend tests
  - backend tests
  - e2e tests
  - all tests
- Document the testing architecture and how to run it

Quality bar:
- no mock-only coverage without real behavior value
- clear separation of unit, integration, and e2e tests
- testing setup must scale with future phases

---

### Phase 82 — Backend and Database Coverage
Goal: validate backend behavior, service logic, and database integrity.

Requirements:
- Add backend coverage for:
  - auth flows
  - role/permission checks
  - CRUD flows for core entities
  - planner endpoints
  - AI create endpoints
  - unified search endpoints
  - recommendation and prioritization logic
  - notifications/workflows where implemented
- Add database integration tests for:
  - migrations
  - relationships
  - goal-task linkage
  - create/update/delete consistency
  - entity constraints
- Add error-path tests:
  - invalid payloads
  - missing entities
  - forbidden access
  - malformed requests

Quality bar:
- service logic must be tested, not just routes
- DB tests must catch real relationship issues
- authorization must be tested at backend level

---

### Phase 83 — Frontend and Interaction Coverage
Goal: validate critical frontend workflows and reusable UI behavior.

Requirements:
- Add frontend coverage for:
  - app shell
  - sidebar/header navigation
  - command palette
  - dashboard
  - unified search
  - planner review/import
  - list/detail pages
  - modals/drawers/tabs/cards/chips/buttons
- Test:
  - render behavior
  - interaction behavior
  - keyboard behavior
  - action triggers
  - state changes
- Add helpers for rendering with providers/router/query/state

Quality bar:
- no brittle UI assertions
- test what users do, not implementation noise
- command palette and planner interactions are especially important

---

### Phase 84 — End-to-End and Responsive Validation
Goal: validate full user journeys from browser UI through backend and database.

Requirements:
- Use Playwright to test:
  - login
  - dashboard load
  - command palette navigation
  - AI create flow
  - planner review and import
  - unified search
  - task actions
  - key entity flows
- Add responsive viewport checks for:
  - desktop
  - tablet
  - mobile
- Add theme validation checks for:
  - light
  - dark
  - at least one alternate premium theme
- Validate:
  - no major overflow
  - key actions visible
  - drawer/sidebar behavior works
  - command palette usable across sizes
  - no unreadable contrast regressions in any supported theme
- Seed reliable test data for end-to-end scenarios

Quality bar:
- e2e tests must reflect real product flows
- viewport coverage must catch layout regressions
- theme coverage must catch visual regressions
- tests should be maintainable and stable

---

### Phase 85 — Regression, Smoke, and Release Confidence
Goal: create a fast confidence layer for future development and releases.

Requirements:
- Add smoke suite for:
  - app load
  - login
  - dashboard
  - command palette
  - search
  - planner
  - key entity pages
- Add regression suite for:
  - create goal
  - create task
  - AI create flow
  - planner import
  - search result open
  - task action flows
  - navigation flows
- Add:
  - fast smoke mode
  - full regression mode
  - CI-friendly commands
- Document:
  - what is covered
  - what is not yet covered
  - how to run quick vs full suites

Quality bar:
- regression suite should catch major breakage quickly
- smoke suite should be fast enough for regular use
- test coverage must support future phases without constant rework
