# Domain Model — AI Life Architect

## Purpose
This document defines the authoritative high-level domain model for AI Life Architect.

Use this file as the schema and relationship reference for all implementation work across backend, database, API, workers, AI features, and frontend forms/pages.

## Modeling Principles
- Use UUIDs for primary keys unless there is a strong technical reason not to.
- Use ISO 8601 timestamps.
- Every user-owned record must support ownership and workspace scoping.
- Prefer normalized core tables plus JSONB metadata only where flexibility is genuinely needed.
- Use soft-delete where historical traceability matters.
- Support auditability for important changes.
- Keep field names consistent across backend, database, and frontend.
- Avoid storing derived values when they can be computed cheaply, unless needed for performance or analytics.

## Common Base Fields
These fields should exist on most business entities unless explicitly excluded.

- `id`
- `workspace_id`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `deleted_at` (nullable, for soft delete where applicable)
- `is_archived` (boolean, default false, where useful)
- `metadata` (jsonb, optional, only for extensibility)

---

# 1. Identity, Access, and Governance

## 1.1 User
Represents a platform user.

### Fields
- `id`
- `email` (unique)
- `username` (nullable, unique if used)
- `full_name`
- `password_hash`
- `is_active`
- `is_superuser`
- `last_login_at` (nullable)
- `timezone` (default user preference or system default)
- `locale` (nullable)
- `avatar_url` (nullable)
- `created_at`
- `updated_at`

### Notes
- A user can belong to one or more workspaces.
- A user can hold multiple roles.
- Password hash must never be exposed through API responses.

## 1.2 Role
Represents a named access role.

### Fields
- `id`
- `name` (unique)
- `code` (unique)
- `description` (nullable)
- `is_system_role`
- `created_at`
- `updated_at`

## 1.3 Permission
Represents a granular permission.

### Fields
- `id`
- `name`
- `code` (unique)
- `description` (nullable)
- `module` (nullable)
- `created_at`
- `updated_at`

## 1.4 UserRole
Maps users to roles, optionally scoped to workspace.

### Fields
- `id`
- `user_id`
- `role_id`
- `workspace_id` (nullable if global)
- `created_at`

## 1.5 RolePermission
Maps roles to permissions.

### Fields
- `id`
- `role_id`
- `permission_id`
- `created_at`

## 1.6 AuthSession
Represents refresh token/session lifecycle.

### Fields
- `id`
- `user_id`
- `refresh_token_hash`
- `device_info` (nullable)
- `ip_address` (nullable)
- `user_agent` (nullable)
- `expires_at`
- `revoked_at` (nullable)
- `created_at`
- `updated_at`

## 1.7 AuditLog
Tracks important security and business actions.

### Fields
- `id`
- `workspace_id` (nullable)
- `actor_user_id` (nullable)
- `action`
- `entity_type`
- `entity_id` (nullable)
- `status` (e.g. success, failure)
- `details` (jsonb, nullable)
- `ip_address` (nullable)
- `user_agent` (nullable)
- `created_at`

---

# 2. Workspace and Organizational Structure

## 2.1 Workspace
Top-level container for user data.

### Fields
- `id`
- `name`
- `slug` (unique)
- `description` (nullable)
- `owner_user_id`
- `visibility` (private, shared, team)
- `status` (active, archived)
- `settings` (jsonb, nullable)
- `created_at`
- `updated_at`

### Relationships
- Workspace has many life areas.
- Workspace has many goals, projects, tasks, notes, journals, routines, events, tags, documents, recommendations, notifications, and analytics events.

## 2.2 WorkspaceMember
Maps users to workspaces.

### Fields
- `id`
- `workspace_id`
- `user_id`
- `membership_type` (owner, admin, editor, viewer)
- `joined_at`
- `is_active`

---

# 3. Core Planning and Knowledge Domain

## 3.1 LifeArea
Represents a major life dimension such as Health, Career, Family, Finance.

### Fields
- `id`
- `workspace_id`
- `name`
- `slug`
- `description` (nullable)
- `color_token` (nullable)
- `icon_name` (nullable)
- `sort_order` (nullable)
- `status` (active, archived)
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `deleted_at` (nullable)

### Relationships
- LifeArea belongs to Workspace.
- LifeArea has many Goals.
- LifeArea can be linked to Notes, Journals, Routines, Events, and Recommendations.

## 3.2 Goal
Represents a medium- or long-term outcome.

### Fields
- `id`
- `workspace_id`
- `life_area_id` (nullable)
- `title`
- `description` (nullable)
- `status` (draft, active, paused, completed, cancelled, archived)
- `priority` (low, medium, high, critical)
- `target_date` (nullable)
- `start_date` (nullable)
- `completed_at` (nullable)
- `progress_percent` (nullable, derived or cached)
- `owner_user_id` (nullable)
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `deleted_at` (nullable)

### Relationships
- Goal belongs to Workspace.
- Goal may belong to LifeArea.
- Goal has many Projects.
- Goal may have many Notes, Journals, Tags, Relationships, Recommendations.

## 3.3 Milestone
Represents an intermediate checkpoint under a goal or project.

### Fields
- `id`
- `workspace_id`
- `goal_id` (nullable)
- `project_id` (nullable)
- `title`
- `description` (nullable)
- `status` (planned, active, completed, skipped)
- `due_date` (nullable)
- `completed_at` (nullable)
- `sort_order` (nullable)
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

### Relationships
- Milestone belongs to either Goal or Project.
- Milestone can have many Tasks.

## 3.4 Project
Represents a structured effort that supports a goal or stands independently.

### Fields
- `id`
- `workspace_id`
- `goal_id` (nullable)
- `life_area_id` (nullable)
- `title`
- `description` (nullable)
- `status` (draft, active, on_hold, completed, cancelled, archived)
- `priority` (low, medium, high, critical)
- `start_date` (nullable)
- `due_date` (nullable)
- `completed_at` (nullable)
- `owner_user_id` (nullable)
- `health_status` (on_track, at_risk, off_track, unknown)
- `progress_percent` (nullable)
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `deleted_at` (nullable)

### Relationships
- Project belongs to Workspace.
- Project may belong to Goal.
- Project may belong to LifeArea.
- Project has many Tasks, Milestones, Notes, Events, Tags, Documents.

## 3.5 Task
Represents a concrete actionable item.

### Fields
- `id`
- `workspace_id`
- `project_id` (nullable)
- `goal_id` (nullable)
- `milestone_id` (nullable)
- `parent_task_id` (nullable, for subtask support)
- `title`
- `description` (nullable)
- `status` (todo, in_progress, blocked, completed, cancelled, archived)
- `priority` (low, medium, high, critical)
- `due_date` (nullable)
- `start_date` (nullable)
- `completed_at` (nullable)
- `estimated_minutes` (nullable)
- `actual_minutes` (nullable)
- `assigned_user_id` (nullable)
- `blocked_reason` (nullable)
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `deleted_at` (nullable)

### Relationships
- Task belongs to Workspace.
- Task may belong to Project, Goal, or Milestone.
- Task may have parent Task.
- Task can link to Notes, Events, Tags, Documents, Recommendations.

## 3.6 Note
Represents a general-purpose note.

### Fields
- `id`
- `workspace_id`
- `title`
- `content`
- `content_format` (plain_text, markdown, rich_text)
- `status` (active, archived)
- `source_type` (manual, imported, ai_generated, derived)
- `owner_user_id` (nullable)
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `deleted_at` (nullable)

### Relationships
- Note belongs to Workspace.
- Note can be linked to Goals, Projects, Tasks, Journals, LifeAreas, Events, Documents.
- Note can have many Tags.

## 3.7 JournalEntry
Represents a dated personal or reflective entry.

### Fields
- `id`
- `workspace_id`
- `title` (nullable)
- `entry_date`
- `content`
- `content_format` (plain_text, markdown, rich_text)
- `privacy_level` (private, workspace_visible, restricted)
- `mood_label` (nullable, user-provided or inferred proxy)
- `energy_label` (nullable)
- `is_ai_processing_enabled`
- `owner_user_id`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `deleted_at` (nullable)

### Relationships
- JournalEntry belongs to Workspace.
- JournalEntry may be linked to LifeAreas, Goals, Projects, Tags, Documents.
- JournalEntry can produce JournalInsights.

## 3.8 Routine
Represents a recurring habit or repeated practice.

### Fields
- `id`
- `workspace_id`
- `life_area_id` (nullable)
- `goal_id` (nullable)
- `title`
- `description` (nullable)
- `status` (active, paused, archived, completed)
- `frequency_type` (daily, weekly, monthly, custom)
- `frequency_config` (jsonb)
- `start_date`
- `end_date` (nullable)
- `target_count` (nullable)
- `owner_user_id` (nullable)
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `deleted_at` (nullable)

### Relationships
- Routine belongs to Workspace.
- Routine may belong to LifeArea or Goal.
- Routine has many RoutineLogs.
- Routine can have Tags and Recommendations.

## 3.9 RoutineLog
Represents execution history for a routine.

### Fields
- `id`
- `workspace_id`
- `routine_id`
- `log_date`
- `status` (done, skipped, missed, partial)
- `value_numeric` (nullable)
- `value_text` (nullable)
- `notes` (nullable)
- `created_by`
- `created_at`
- `updated_at`

## 3.10 Event
Represents a scheduled item.

### Fields
- `id`
- `workspace_id`
- `title`
- `description` (nullable)
- `start_at`
- `end_at` (nullable)
- `timezone` (nullable)
- `location` (nullable)
- `status` (scheduled, completed, cancelled)
- `event_type` (personal, routine, deadline, meeting, reminder, system)
- `goal_id` (nullable)
- `project_id` (nullable)
- `task_id` (nullable)
- `life_area_id` (nullable)
- `owner_user_id` (nullable)
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `deleted_at` (nullable)

## 3.11 Tag
Represents a reusable label.

### Fields
- `id`
- `workspace_id`
- `name`
- `slug`
- `color_token` (nullable)
- `description` (nullable)
- `created_by`
- `created_at`
- `updated_at`

## 3.12 EntityTag
Polymorphic mapping of tags to entities.

### Fields
- `id`
- `workspace_id`
- `tag_id`
- `entity_type`
- `entity_id`
- `created_at`

---

# 4. Cross-Linking and Relationship Graph

## 4.1 EntityLink
Explicit cross-link between two domain entities.

### Fields
- `id`
- `workspace_id`
- `source_entity_type`
- `source_entity_id`
- `target_entity_type`
- `target_entity_id`
- `link_type` (references, supports, blocks, relates_to, derived_from, mentions, attached_to)
- `direction` (forward, bidirectional)
- `notes` (nullable)
- `created_by`
- `created_at`
- `updated_at`

## 4.2 RelationshipSuggestion
Inferred or AI/rule-suggested link awaiting review.

### Fields
- `id`
- `workspace_id`
- `source_entity_type`
- `source_entity_id`
- `target_entity_type`
- `target_entity_id`
- `suggestion_type`
- `confidence_score`
- `source_method` (rule, ai, ingestion, semantic_similarity)
- `justification` (nullable)
- `status` (pending, accepted, rejected, expired)
- `reviewed_by` (nullable)
- `reviewed_at` (nullable)
- `created_at`
- `updated_at`

---

# 5. Documents, Ingestion, and Retrieval

## 5.1 Document
Represents an uploaded or imported file.

### Fields
- `id`
- `workspace_id`
- `title`
- `original_filename`
- `storage_path`
- `mime_type`
- `file_size_bytes`
- `checksum`
- `source_type` (upload, import, generated, external_sync)
- `status` (uploaded, queued, processing, completed, failed, archived)
- `owner_user_id`
- `uploaded_by`
- `uploaded_at`
- `processed_at` (nullable)
- `processing_error` (nullable)
- `created_at`
- `updated_at`
- `deleted_at` (nullable)

## 5.2 DocumentVersion
Optional version tracking for documents.

### Fields
- `id`
- `workspace_id`
- `document_id`
- `version_number`
- `storage_path`
- `checksum`
- `status`
- `created_by`
- `created_at`

## 5.3 DocumentChunk
Represents extracted chunked content for retrieval.

### Fields
- `id`
- `workspace_id`
- `document_id`
- `document_version_id` (nullable)
- `chunk_index`
- `content`
- `token_count` (nullable)
- `page_number` (nullable)
- `section_label` (nullable)
- `embedding_vector` (nullable, pgvector)
- `keyword_tsv` (nullable, tsvector or equivalent)
- `source_attribution` (jsonb, nullable)
- `created_at`
- `updated_at`

## 5.4 IngestionJob
Tracks processing lifecycle.

### Fields
- `id`
- `workspace_id`
- `document_id` (nullable)
- `job_type` (extract, chunk, embed, retry)
- `status` (queued, running, completed, failed, retry_scheduled, cancelled)
- `attempt_count`
- `error_message` (nullable)
- `started_at` (nullable)
- `finished_at` (nullable)
- `created_at`
- `updated_at`

## 5.5 SearchQueryLog
Tracks search activity for debugging and analytics.

### Fields
- `id`
- `workspace_id`
- `user_id`
- `query_text`
- `search_mode` (keyword, semantic, hybrid)
- `filters` (jsonb, nullable)
- `result_count`
- `latency_ms` (nullable)
- `created_at`

---

# 6. AI Orchestration and Planning

## 6.1 PromptTemplate
Versioned prompt template for AI tasks.

### Fields
- `id`
- `workspace_id` (nullable if global/system)
- `name`
- `task_type`
- `version`
- `template_text`
- `is_active`
- `is_system_template`
- `created_by` (nullable)
- `created_at`
- `updated_at`

## 6.2 AIRequestLog
Tracks AI calls.

### Fields
- `id`
- `workspace_id`
- `user_id` (nullable)
- `task_type`
- `provider_name`
- `model_name`
- `prompt_template_id` (nullable)
- `status` (queued, completed, failed, blocked)
- `input_summary` (nullable)
- `output_summary` (nullable)
- `latency_ms` (nullable)
- `token_input_estimate` (nullable)
- `token_output_estimate` (nullable)
- `error_message` (nullable)
- `created_at`

## 6.3 Plan
Represents a user-requested planning artifact.

### Fields
- `id`
- `workspace_id`
- `source_type` (freeform, goal_based, template_based)
- `input_text` (nullable)
- `goal_id` (nullable)
- `life_area_id` (nullable)
- `template_id` (nullable)
- `status` (draft, generated, reviewed, accepted, rejected, archived)
- `generated_by_method` (template, ai, hybrid)
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

## 6.4 PlanItem
Structured output node within a plan.

### Fields
- `id`
- `workspace_id`
- `plan_id`
- `item_type` (milestone, project, task, routine)
- `parent_item_id` (nullable)
- `title`
- `description` (nullable)
- `status` (draft, accepted, rejected)
- `proposed_start_date` (nullable)
- `proposed_due_date` (nullable)
- `priority` (nullable)
- `sort_order` (nullable)
- `mapped_entity_type` (nullable)
- `mapped_entity_id` (nullable)
- `created_at`
- `updated_at`

---

# 7. Recommendations, Insights, and Intelligence

## 7.1 Recommendation
Represents a system-generated suggestion.

### Fields
- `id`
- `workspace_id`
- `user_id` (nullable)
- `recommendation_type` (overdue_task, inactive_goal, routine_dropoff, neglected_area, project_risk, ai_insight)
- `title`
- `description`
- `severity` (low, medium, high, critical)
- `confidence_score` (nullable)
- `generation_method` (rule, ai, hybrid)
- `status` (new, active, dismissed, accepted, expired, archived)
- `explanation` (nullable)
- `source_payload` (jsonb, nullable)
- `related_entity_type` (nullable)
- `related_entity_id` (nullable)
- `generated_at`
- `acted_at` (nullable)
- `created_at`
- `updated_at`

## 7.2 JournalInsight
Represents insight derived from journals.

### Fields
- `id`
- `workspace_id`
- `journal_entry_id` (nullable)
- `insight_scope` (entry, weekly, monthly)
- `insight_type` (theme, blocker, win, sentiment_proxy, summary)
- `title` (nullable)
- `content`
- `confidence_score` (nullable)
- `source_method` (rule, ai, hybrid)
- `period_start` (nullable)
- `period_end` (nullable)
- `created_at`
- `updated_at`

## 7.3 DashboardSnapshot
Optional cached dashboard aggregation.

### Fields
- `id`
- `workspace_id`
- `user_id`
- `snapshot_date`
- `payload` (jsonb)
- `created_at`

---

# 8. Notifications and Reminders

## 8.1 Notification
Represents an in-app notification.

### Fields
- `id`
- `workspace_id`
- `user_id`
- `type` (reminder, recommendation, system, admin, ingestion_failure)
- `title`
- `message`
- `status` (unread, read, archived)
- `related_entity_type` (nullable)
- `related_entity_id` (nullable)
- `action_url` (nullable)
- `created_at`
- `read_at` (nullable)
- `archived_at` (nullable)

## 8.2 NotificationPreference
User preferences for notification behavior.

### Fields
- `id`
- `workspace_id`
- `user_id`
- `category`
- `is_enabled`
- `delivery_in_app`
- `delivery_email` (nullable for future support)
- `quiet_hours_config` (jsonb, nullable)
- `created_at`
- `updated_at`

## 8.3 Reminder
Represents a generated reminder item.

### Fields
- `id`
- `workspace_id`
- `user_id`
- `source_entity_type`
- `source_entity_id`
- `title`
- `due_at`
- `status` (pending, sent, dismissed, completed, expired)
- `created_at`
- `updated_at`

---

# 9. Background Jobs and Operations

## 9.1 BackgroundJob
Represents async work unit.

### Fields
- `id`
- `workspace_id` (nullable)
- `job_type`
- `status` (queued, running, completed, failed, retry_scheduled, cancelled)
- `priority` (nullable)
- `payload` (jsonb, nullable)
- `result_payload` (jsonb, nullable)
- `attempt_count`
- `max_attempts`
- `error_message` (nullable)
- `scheduled_at` (nullable)
- `started_at` (nullable)
- `finished_at` (nullable)
- `created_at`
- `updated_at`

---

# 10. Import / Export

## 10.1 ImportJob
Tracks structured import lifecycle.

### Fields
- `id`
- `workspace_id`
- `user_id`
- `source_filename`
- `source_type`
- `status` (uploaded, validating, preview_ready, importing, completed, failed)
- `validation_summary` (jsonb, nullable)
- `error_message` (nullable)
- `created_at`
- `updated_at`

## 10.2 ExportJob
Tracks export generation.

### Fields
- `id`
- `workspace_id`
- `user_id`
- `export_type` (json, markdown_zip, custom_bundle)
- `scope_type`
- `scope_id` (nullable)
- `status` (queued, generating, completed, failed, expired)
- `storage_path` (nullable)
- `expires_at` (nullable)
- `error_message` (nullable)
- `created_at`
- `updated_at`

---

# 11. Analytics

## 11.1 AnalyticsEvent
Represents privacy-aware event tracking.

### Fields
- `id`
- `workspace_id`
- `user_id` (nullable)
- `event_name`
- `event_category`
- `entity_type` (nullable)
- `entity_id` (nullable)
- `session_id` (nullable)
- `properties` (jsonb, nullable)
- `occurred_at`

## 11.2 ProductivityMetricSnapshot
Optional aggregated metrics by period.

### Fields
- `id`
- `workspace_id`
- `user_id`
- `period_type` (daily, weekly, monthly)
- `period_start`
- `period_end`
- `metrics_payload` (jsonb)
- `created_at`

---

# 12. Main Relationships Summary

## Workspace-Centric Ownership
- Workspace has many LifeAreas
- Workspace has many Goals
- Workspace has many Projects
- Workspace has many Tasks
- Workspace has many Notes
- Workspace has many JournalEntries
- Workspace has many Routines
- Workspace has many Events
- Workspace has many Tags
- Workspace has many Documents
- Workspace has many Recommendations
- Workspace has many Notifications
- Workspace has many AnalyticsEvents

## Planning Hierarchy
- LifeArea has many Goals
- Goal has many Projects
- Goal has many Milestones
- Project has many Tasks
- Project has many Milestones
- Milestone has many Tasks
- Task may have many child Tasks

## Knowledge and Linking
- Tags can attach to many entities through EntityTag
- EntityLink connects any entity to any other entity
- RelationshipSuggestion proposes cross-entity connections

## Routine and Event Tracking
- Routine has many RoutineLogs
- Event may link to Goal, Project, Task, or LifeArea

## Documents and Retrieval
- Document has many DocumentChunks
- Document has many IngestionJobs
- DocumentChunk may store embedding vector and keyword search representation

## AI and Insight
- PromptTemplate supports AI tasks
- AIRequestLog records provider interactions
- Plan has many PlanItems
- Recommendation may point to a related entity
- JournalInsight may point to a JournalEntry or a period summary

---

# 13. Enumerations Guidance

Use enums or constrained string values for these groups:
- status fields
- priority fields
- visibility fields
- recommendation types
- notification status/type
- job status/type
- content format
- frequency type
- relationship types
- source methods

Keep enum names stable and shared across backend schemas and frontend types.

---

# 14. Frontend Form Field Guidance

## Workspace Form
- name
- slug
- description
- visibility

## LifeArea Form
- name
- description
- icon
- color
- sort_order
- status

## Goal Form
- title
- description
- life_area
- status
- priority
- start_date
- target_date
- owner

## Project Form
- title
- description
- goal
- life_area
- status
- priority
- start_date
- due_date
- owner
- health_status

## Task Form
- title
- description
- project
- goal
- milestone
- parent_task
- status
- priority
- start_date
- due_date
- assigned_user
- estimated_minutes
- blocked_reason

## Note Form
- title
- content
- content_format
- tags
- linked_entities

## Journal Form
- title
- entry_date
- content
- content_format
- privacy_level
- mood_label
- energy_label
- tags
- linked_life_area / linked_goal

## Routine Form
- title
- description
- life_area
- goal
- frequency_type
- frequency_config
- start_date
- end_date
- target_count
- status

## Event Form
- title
- description
- start_at
- end_at
- timezone
- location
- event_type
- related_goal
- related_project
- related_task
- related_life_area

## Tag Form
- name
- description
- color

## Document Upload Form
- file
- title
- source_type
- optional linked entity
- tags

---

# 15. API Design Guidance

For each major entity, support:
- create
- update
- get detail
- list
- delete or archive
- filter
- sort
- pagination

List endpoints should support, where relevant:
- `q`
- `status`
- `priority`
- `life_area_id`
- `goal_id`
- `project_id`
- `tag_id`
- `owner_user_id`
- `assigned_user_id`
- `date_from`
- `date_to`
- `page`
- `page_size`
- `sort_by`
- `sort_order`

---

# 16. Database Constraints Guidance

## Must Have
- foreign keys for real typed relations
- unique constraint on workspace slug
- unique constraint on tag name per workspace if desired
- unique constraint on role code and permission code
- indexes on all foreign keys
- indexes on status + workspace combinations for core tables
- indexes on due_date for tasks/events/reminders
- full-text/search indexes where applicable
- vector index for embeddings when retrieval is enabled

## Important Business Rules
- A task should belong to the same workspace as its parent project/goal/milestone.
- A project’s goal and life area must belong to the same workspace.
- A journal marked private should be excluded from AI processing when disabled.
- A recommendation should not duplicate an already active equivalent recommendation for the same entity and reason unless intentionally refreshed.
- Relationship suggestions must not auto-create explicit links without review unless rules explicitly allow it.

---

# 17. Suggested Phase Mapping

## Foundation / Auth
- User
- Role
- Permission
- UserRole
- RolePermission
- AuthSession
- AuditLog
- Workspace
- WorkspaceMember

## Core Domain
- LifeArea
- Goal
- Milestone
- Project
- Task
- Note
- JournalEntry
- Routine
- RoutineLog
- Event
- Tag
- EntityTag
- EntityLink

## Documents / Search / AI
- Document
- DocumentVersion
- DocumentChunk
- IngestionJob
- PromptTemplate
- AIRequestLog
- SearchQueryLog
- RelationshipSuggestion
- Plan
- PlanItem

## Insights / Admin / Ops
- Recommendation
- JournalInsight
- Notification
- NotificationPreference
- Reminder
- BackgroundJob
- ImportJob
- ExportJob
- AnalyticsEvent
- ProductivityMetricSnapshot
- DashboardSnapshot

---

# 18. Final Rule for Codex
Codex must use this file as the authoritative reference for:
- database schema direction
- SQLAlchemy or ORM model design
- migration planning
- backend DTO/schema fields
- frontend form fields
- filters and list APIs
- relationship mapping
- AI, retrieval, recommendation, analytics, and admin module integration

If implementation details are missing, Codex may extend the design carefully, but it must not contradict this document.