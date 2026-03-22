# Enterprise UI / UX Standards (Mandatory)

All frontend implementations must meet enterprise-grade UI quality. These rules are NOT optional.

---

## 1. Overall UI Philosophy

- UI must feel like a mature SaaS product, not a scaffold.
- Prioritize:
  - clarity
  - hierarchy
  - actionability
  - consistency
- Avoid empty, oversized, or generic layouts.
- Desktop screens must use space efficiently (no large blank areas).

---

## 2. Dashboard UX Standards

### Structure (Required)
Every dashboard must include:

- Title + meaningful subtitle
- Primary action (if applicable)
- KPI summary section
- Action-oriented section (e.g., overdue, risks)
- Activity or timeline section (if applicable)
- Optional insights/recommendations

### KPI Cards
Each KPI card must include:
- Label
- Primary value
- Supporting context (1–2 lines max)
- Optional:
  - trend (↑ ↓)
  - status badge
  - drill-down hint

Do NOT create simple number-only cards without context.

---

## 3. Card System (Strict)

Do NOT use one generic card style.

### Required Variants

#### KPI Card
- compact
- high emphasis number
- minimal text

#### Content Card
- clear header
- optional actions (menu)
- structured body

#### Status Card
- rows of items
- status badges
- optional timestamps

#### Activity Card
- list-based
- chronological

#### Recommendation Card
- explanation + action

---

## 4. Information Density Rules

- Desktop must NOT look empty.
- Use grid layout effectively.
- Avoid:
  - oversized padding
  - large empty cards
- Show more data instead of bigger spacing.

---

## 5. Navigation Standards

### Sidebar
- Keep compact
- Avoid excessive spacing
- Support:
  - icon + label
  - optional short helper text (not for all items)
- Active item should NOT be oversized

### Behavior
- Desktop: fixed sidebar
- Mobile: drawer
- Support collapsed sidebar

---

## 6. Top Bar Standards

- Keep clean and prioritized
- Do NOT overload with icons
- Must include:
  - search (primary)
  - 1 main action (e.g., create)
- Secondary actions:
  - notifications
  - theme
  - profile

All icon buttons MUST have tooltips.

---

## 7. Tooltip Standards (Mandatory)

Use tooltips for:
- icon-only buttons
- technical fields
- status badges
- metrics needing explanation

### Rules
- 1–2 lines max
- explain purpose, not label
- show on hover + focus
- mobile → tap support

---

## 8. Form Standards

### Required
- Label (always visible)
- Required marker (*)
- Placeholder (optional)
- Tooltip (if needed)
- Inline validation

### Layout
- Desktop: 2-column where possible
- Mobile: single column
- Group fields:
  - Basic info
  - Relationships
  - Scheduling
  - Metadata

### Input Types
- Text → short fields
- Textarea → descriptions
- Select → enums
- Multi-select → tags
- Date / DateTime → pickers
- Toggle → boolean

---

## 9. Status & Priority UI

- Status → badge
- Priority → color indicator:
  - low → gray
  - medium → blue
  - high → orange
  - critical → red

---

## 10. Tables & Lists

Must include:
- search (if >10 items)
- filters
- sorting
- pagination

Row actions:
- view
- edit
- delete/archive

---

## 11. Empty / Loading / Error States

Every page must handle:

### Empty
"Nothing here yet" with action

### No results
"Try adjusting filters"

### Loading
- use skeletons (not only spinner)

### Error
- clear message
- retry option

---

## 12. Content Realism Rules

Do NOT show developer-style content like:
- "foundation ready"
- "modular backend"
- "ready for extension"

Instead show:
- actionable data
- realistic placeholders
- or hide section

---

## 13. Dashboard Content Rules

User dashboard must focus on:
- tasks
- goals
- routines
- events
- recommendations

Admin/system info (health, jobs, logs) should:
- be in Admin section
- NOT dominate user dashboard

---

## 14. Accessibility

- keyboard accessible
- proper labels
- aria support where needed
- good contrast
- clickable areas ≥ 40px

---

## 15. Theming

- Use tokens only (no hardcoded colors)
- Support:
  - light
  - dark
  - additional theme
- All components must adapt automatically

---

## 16. Responsiveness

Must support:
- mobile
- tablet
- laptop
- desktop
- wide screens

Rules:
- no horizontal scroll
- adaptive layouts
- stack intelligently on small screens

---

## 17. Consistency Rules

- Same naming across:
  - backend
  - API
  - frontend
- Reuse components
- Avoid duplicate patterns

---

## 18. AI UX Rules

- Label AI-generated content
- Show loading state
- Allow user edit before saving
- NEVER auto-save AI output

---

## 19. Strict Prohibitions

Codex MUST NOT:
- create forms without labels
- use placeholder as label
- hardcode styles
- create identical cards for everything
- show developer/internal text to users
- skip validation