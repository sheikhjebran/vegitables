# Firebase Compatibility Analysis

## Package reality

`django-orm-firebase` is currently a Firestore wrapper with a Django-friendly initialization path. It is not a Django database backend and not a drop-in replacement for `django.db.models.Model`.

## Supported by the package today

- Firebase initialization from a service account or Django settings.
- Simple model classes inheriting from the package `Model`.
- Basic CRUD operations.
- `get`, `all`, and simple equality-based filtering.
- Manager and queryset wrappers for basic update and delete helpers.

## Not supported by the package today

- Django migrations.
- Django `ForeignKey` relations.
- Join-style querying.
- `annotate`, `aggregate`, `F`, `Q`, or relational traversals.
- Django auth model integration.
- Django admin integration as a true ORM backend.

## What this means for this repo

- Do not attempt to point `DATABASES['default']` at Firebase.
- Do not rewrite `shops/models.py` in place as a first step.
- Do not migrate auth, sessions, or admin until there is a separate design for them.
- Do migrate bounded business data slices to Firestore through explicit repository or adapter layers.

## Recommended architecture

- Keep Django as the web framework.
- Keep SQL for `auth`, `sessions`, and any Django-owned app tables.
- Add a Firebase data access layer for selected business entities.
- Convert views one slice at a time from direct ORM access to service-layer calls.

## First candidate slices

1. `MobileSalesBill`: simple shape and low relational complexity.
2. `CustomerLedger` and `FarmerLedger`: moderate complexity, mostly CRUD plus search.
3. `ArrivalEntry` and `ArrivalGoods`: only after transaction and stock-update strategy is defined.
4. Sales, credit, patti, and reporting: last, because they depend most heavily on relational queries.