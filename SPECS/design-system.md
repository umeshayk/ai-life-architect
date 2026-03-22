# Design System — AI Life Architect

## Purpose
This document defines the visual, structural, and interaction system for the frontend.

It ensures:
- consistent UI across all features
- scalable component architecture
- theme support
- responsive behavior
- enterprise-grade UX

Codex MUST follow this document for all frontend work.

---

# 1. Design Principles

- Clarity over decoration
- Consistency over creativity
- Density with readability
- Action-oriented UI
- Minimal cognitive load
- Responsive-first design

---

# 2. Design Tokens

All styling MUST use tokens. No hardcoded values.

## 2.1 Colors (Semantic)

### Background
- `bg-primary`
- `bg-secondary`
- `bg-surface`
- `bg-muted`

### Text
- `text-primary`
- `text-secondary`
- `text-muted`
- `text-inverse`

### Borders
- `border-default`
- `border-muted`
- `border-strong`

### Status Colors
- `success`
- `warning`
- `danger`
- `info`

### Priority Colors
- `priority-low`
- `priority-medium`
- `priority-high`
- `priority-critical`

---

## 2.2 Spacing Scale

Use consistent spacing scale:

- xs → 4px
- sm → 8px
- md → 12px
- lg → 16px
- xl → 24px
- 2xl → 32px
- 3xl → 48px

---

## 2.3 Border Radius

- `radius-sm` → 6px
- `radius-md` → 10px
- `radius-lg` → 14px

---

## 2.4 Shadows

- `shadow-sm`
- `shadow-md`
- `shadow-lg`

---

## 2.5 Typography

### Headings
- h1 → page title
- h2 → section title
- h3 → card title

### Body
- base → normal text
- small → helper text
- xs → metadata

### Rules
- avoid too many font sizes
- maintain hierarchy

---

# 3. Layout System

## 3.1 Grid

- Use flexible grid (12-column recommended)
- Avoid fixed widths
- Support responsive breakpoints

## 3.2 Breakpoints

- mobile
- tablet
- laptop
- desktop
- wide

---

## 3.3 Page Layout

Each page must follow:

- header (title + actions)
- content sections
- optional sidebar

---

# 4. Component Library

## 4.1 Button

Variants:
- primary
- secondary
- ghost
- danger

States:
- default
- hover
- disabled
- loading

---

## 4.2 Input

Must include:
- label
- input
- helper text
- validation message

---

## 4.3 Select / Dropdown

- single select
- multi select
- searchable (if needed)

---

## 4.4 Card

Variants:
- KPI card
- content card
- status card
- activity card

---

## 4.5 Badge

Used for:
- status
- priority
- labels

---

## 4.6 Table

Features:
- sorting
- filtering
- pagination
- row actions

---

## 4.7 Modal / Dialog

- confirm actions
- edit forms
- detailed views

---

## 4.8 Drawer

- side panel editing
- quick view

---

## 4.9 Toast

- success
- error
- info

---

## 4.10 Loader

- skeleton loaders (preferred)
- spinner (secondary)

---

# 5. Dashboard Patterns

## KPI Section
- 3–5 cards
- compact layout

## Action Section
- overdue tasks
- alerts

## Activity Section
- recent updates

## Insight Section
- AI recommendations

---

# 6. Form Patterns

- group fields logically
- 2-column (desktop)
- 1-column (mobile)

Sections:
- basic info
- relationships
- scheduling
- metadata

---

# 7. Interaction Patterns

- hover feedback
- focus states
- loading states
- confirmation dialogs

---

# 8. Accessibility

- keyboard navigation
- aria labels
- proper contrast

---

# 9. Theming

Must support:
- light theme
- dark theme
- additional theme

Rules:
- no hardcoded colors
- all components adapt

---

# 10. Responsive Behavior

- mobile → stacked layout
- tablet → hybrid
- desktop → grid

---

# 11. Naming Conventions

- backend → snake_case
- frontend → consistent mapping
- avoid mixed naming

---

# 12. Performance

- lazy load heavy components
- avoid unnecessary re-renders
- optimize tables and lists

---

# 13. Anti-Patterns (Strictly Avoid)

- hardcoded styles
- inconsistent spacing
- duplicate components
- oversized empty layouts
- placeholder UI in production screens

---

# 14. Codex Rules

Codex MUST:
- use shared components
- follow tokens
- maintain consistency
- not invent new patterns per screen

If unsure:
- reuse existing component patterns