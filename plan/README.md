# Firebase Migration Plan

This folder tracks the planned migration of the Vegitables backend from a relational Django data layer to Firebase using `django-orm-firebase`.

The plan is split into focused documents so execution can happen incrementally without losing the current production path.

Files:

- `progress.md`: current execution status and completed work.
- `01-current-state.md`: baseline assessment of the existing backend.
- `02-uv-conversion.md`: uv adoption and dependency-management checklist.
- `03-firebase-compatibility.md`: gap analysis between this repo and `django-orm-firebase`.
- `04-migration-runbook.md`: step-by-step execution plan.
- `05-data-mapping.md`: model-by-model target mapping and query rewrite notes.

Execution rule: do not switch the production database engine directly from SQL to Firebase. This package is an ORM-like Firestore wrapper, not a Django `DATABASES` backend.