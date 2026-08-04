# Migration Progress

## Status

- Overall state: planning in progress
- Current phase: repository preparation and feasibility analysis
- Recommended rollout mode: staged hybrid migration

## Completed

- Added uv project metadata in `pyproject.toml`.
- Added `django-orm-firebase>=0.0.2` to managed dependencies.
- Generated `uv.lock` successfully.
- Documented the migration approach in the `plan/` folder.
- Updated the top-level setup instructions to use uv.
- Identified and corrected a PDF dependency compatibility issue exposed during uv validation.
- Verified the existing Django app still passes `uv run python vegitable/manage.py check`.

## Verified facts

- The current app depends on Django auth, sessions, admin-related contrib apps, and DRF auth settings.
- The current app uses foreign keys, aggregates, annotations, pagination, and query patterns that assume a relational backend.
- `django-orm-firebase` currently supports simple model persistence and equality filters only.
- `django-orm-firebase` does not provide Django model inheritance, migrations, relation support, or a `DATABASES` backend replacement.

## In scope next

- Introduce a Firebase configuration module and environment contract.
- Create Firestore-side document models or repository classes for one bounded slice.
- Migrate one low-risk workflow first, preferably ledger or mobile sales cache data.
- Keep auth, session, and relational reporting on SQL until replacements are designed.

## Blockers to full cutover

- Django `request.session` is configured to use the SQL session backend.
- `Shop.shop_owner` depends on `django.contrib.auth.models.User`.
- Reporting endpoints depend on `annotate`, `aggregate`, `F`, `Q`, and join-style access across related tables.
- Sequence counters in `Index` require atomic updates that must be redesigned for Firestore transactions.

## Update protocol

For each future implementation step:

1. Move one item from `In scope next` to `Completed`.
2. Add the exact files touched.
3. Record the verification command used.
4. Record any new blocker or design change before moving to the next slice.