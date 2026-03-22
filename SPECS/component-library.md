# Component Library — AI Life Architect

## Purpose
Defines reusable UI components. Codex MUST reuse these instead of creating new UI per screen.

---

# 1. Layout Components

## AppLayout
- sidebar
- header
- content area

## PageHeader
- title
- subtitle
- primary action
- secondary actions

---

# 2. Cards

## KPI Card
Props:
- label
- value
- subtext
- trend (optional)
- badge (optional)

## Content Card
- title
- actions (optional)
- body

## Status Card
- list of items
- status badge
- optional timestamp

## Activity Card
- list of events
- time
- description

## Recommendation Card
- title
- explanation
- action button

---

# 3. Forms

## FormSection
- section title
- grouped inputs

## FormField
- label
- input
- tooltip
- validation

---

# 4. Inputs

## TextInput
## TextArea
## Select
## MultiSelect
## DatePicker
## DateTimePicker
## Toggle

---

# 5. Data Components

## Table
- columns
- sorting
- filters
- pagination

## ListView
- compact list

---

# 6. Feedback

## Toast
## Modal
## Drawer
## SkeletonLoader

---

# 7. Navigation

## SidebarItem
## Breadcrumb

---

# 8. Rules

- NEVER create new UI if component exists
- ALWAYS reuse components
- Keep props consistent