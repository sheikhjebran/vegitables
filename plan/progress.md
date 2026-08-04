# Migration Progress

## Status

- Overall state: migration in progress
- Current phase: Firebase business-data slice migration
- Recommended rollout mode: staged hybrid migration toward Firebase-first business storage

## Completed

- Added uv project metadata in `pyproject.toml`.
- Added `django-orm-firebase>=0.0.2` to managed dependencies.
- Generated `uv.lock` successfully.
- Documented the migration approach in the `plan/` folder.
- Updated the top-level setup instructions to use uv.
- Identified and corrected a PDF dependency compatibility issue exposed during uv validation.
- Verified the existing Django app still passes `uv run python vegitable/manage.py check`.
- Added Phase 1 Firebase settings, shared initialization wiring, and a management command for connectivity checks.
- Re-verified `uv run python vegitable/manage.py check` after the Phase 1 Firebase wiring.
- Verified the `check_firebase` management command is registered via `uv run python vegitable/manage.py help check_firebase`.
- Added a feature-flagged `MobileSalesBill` repository with a Firestore-backed document model while preserving SQL as the default path.
- Re-verified `uv run python vegitable/manage.py check` after wiring the `MobileSalesBill` slice.
- Added repo-root `firebase.json` fallback support for Firebase project metadata and improved credential guidance in `check_firebase`.
- Verified that `check_firebase` fails with a clear backend-credential error when only repo-root `firebase.json` is present.
- Created the placeholder file `vegitable/serviceAccountKey.json`; real service-account JSON contents are still required.
- Verified that backend credentials now load, and the next blocker is that the Cloud Firestore API is disabled for project `prahar-d5a02`.
- Added a `backfill_mobile_sales_to_firebase` management command so the first Firestore slice can be populated immediately after the API blocker is cleared.
- Verified the `backfill_mobile_sales_to_firebase` command is registered and callable.
- Added a `compare_mobile_sales_sources` management command to verify SQL-vs-Firestore parity for the first migrated slice.
- Verified the `compare_mobile_sales_sources` command is registered and callable.
- Improved source-side error handling for backfill and parity commands when SQL data is unreachable or not present locally.
- Added a `smoke_test_mobile_sales_firebase` command for Firebase-only write/read/delete validation without requiring SQL source data.
- Verified the Firestore-backed `MobileSalesBill` repository path with a successful Firebase-only smoke test.
- Updated the plan to target full migration of business-domain data to Firebase while explicitly deferring Django-owned auth/session concerns until redesign.
- Started the `CustomerLedger` Firebase migration slice with a Firestore repository, feature flag, and Firebase-only smoke test.
- Verified the Firestore-backed `CustomerLedger` repository path with a successful Firebase-only smoke test.
- Started the `FarmerLedger` Firebase migration slice with a Firestore repository, feature flag, and Firebase-only smoke test.
- Verified the Firestore-backed `FarmerLedger` repository path with a successful Firebase-only smoke test.
- Started the `ArrivalEntry` plus embedded `ArrivalGoods` Firebase migration slice with a Firestore repository and Firebase-only smoke test.
- Verified the Firestore-backed `ArrivalEntry` plus embedded `ArrivalGoods` repository path with a successful Firebase-only smoke test.
- Switched arrival and inventory read-only paths to the Firestore arrival repository behind `USE_FIREBASE_ARRIVAL`.
- Switched mobile arrival-goods reads and mobile-sales customer lot lookups to the Firestore arrival repository behind `USE_FIREBASE_ARRIVAL`.
- Started a Firestore-native `SalesBillEntry` slice with embedded sales items that reference Firestore arrival goods directly.
- Verified the Firestore-native `SalesBillEntry` repository path with a successful stock decrement and restore smoke test.
- Switched live sales-bill listing and new sales-bill creation to the Firestore-native sales repository behind `USE_FIREBASE_SALES`.
- Implemented Firestore-native sales-bill edit/update with stock reconciliation and enabled live edit routing behind `USE_FIREBASE_SALES`.

## Verified facts

- The current app depends on Django auth, sessions, admin-related contrib apps, and DRF auth settings.
- The current app uses foreign keys, aggregates, annotations, pagination, and query patterns that assume a relational backend.
- `django-orm-firebase` currently supports simple model persistence and equality filters only.
- `django-orm-firebase` does not provide Django model inheritance, migrations, relation support, or a `DATABASES` backend replacement.
- The repo-root `firebase.json` provides client-side Firebase project config and can supply `projectId`, but it is not a Firebase Admin service-account credential.
- Firestore connectivity is now working for project `prahar-d5a02`, but local backfill still depends on whichever SQL source database contains the real `MobileSalesBill` rows.
- `CustomerLedger` is a viable next Firebase slice because its CRUD flow can run without SQL joins, and its search can be bridged temporarily with app-layer filtering.
- The migration plan is now explicitly Firebase-first for business-domain data, with Django auth/session/reporting remaining separate workstreams until redesigned.
- `FarmerLedger` can follow the same repository and app-layer search pattern as `CustomerLedger` with minimal additional relational coupling.
- `ArrivalEntry` requires a separate migration boundary because downstream sales and inventory still consume stock state; embedded goods rows are the first Firestore representation being validated.
- Arrival home, modify, duplicate-check, and inventory-style read paths can now use Firestore behind the feature flag without switching stock mutation logic yet.
- Mobile cache flows that fetch arrival-goods options and resolve stored lot references can now use Firestore behind the same arrival feature flag.
- The active sales redesign stores line items inside a Firestore sales document and mutates Firestore arrival stock without SQL foreign keys.
- The sales bill screen can now list Firestore-backed sales bills and create new fully paid Firestore sales bills when the arrival and sales flags are enabled.

## In scope next

- Continue migrating low-risk business workflows to Firebase, starting with ledger slices.
- Keep auth, session, and relational reporting on SQL until replacements are designed.
- Validate the `ArrivalEntry` Firebase slice end to end.
- Decide when and how to switch inventory and sales readers from SQL `ArrivalGoods` to Firestore arrival stock documents.
- Migrate stock mutation and sales consumption paths off SQL `ArrivalGoods`.
- Migrate sales-bill creation and stock decrement paths off SQL `ArrivalGoods`.
- Validate the Firestore-native sales bill repository with stock decrement and restore behavior.
- Decide how and when to cut live sales-bill creation over from SQL `SalesBillItem` to the Firestore-native sales repository.
- Decide how to implement Firestore-native sales bill editing and Firestore-native credit bill flows.
- Design and migrate Firestore-native credit bill flows for partially paid sales.
- Decide when to make Firebase the default enabled path for `MobileSalesBill` and `CustomerLedger` in the target environment.
- Decide when to make Firebase the default enabled path for `FarmerLedger` in the target environment.
- Decide whether the next implementation step is live inventory/read cutover or Firestore-side backfill for arrival history.

## Latest verification

- Passed: `uv run python vegitable/manage.py check`
- Passed: `uv run python vegitable/manage.py help check_firebase`
- Pending with real credentials: `uv run python vegitable/manage.py check_firebase`
- Passed: `uv run python vegitable/manage.py check` after the `MobileSalesBill` slice wiring
- Pending after `firebase.json` fallback wiring: `uv run python vegitable/manage.py check`
- Failed as expected without admin credentials: `uv run python vegitable/manage.py check_firebase`
- Failed with project-level API blocker: `uv run python vegitable/manage.py check_firebase` reports Firestore API disabled for `prahar-d5a02`
- Passed: `uv run python vegitable/manage.py backfill_mobile_sales_to_firebase --help`
- Passed: `uv run python vegitable/manage.py compare_mobile_sales_sources --help`
- Failed reading local SQLite source: `uv run python manage.py backfill_mobile_sales_to_firebase --dry-run` reported missing `shops_mobilesalesbill`
- Passed: `uv run python manage.py smoke_test_mobile_sales_firebase --help`
- Passed: `uv run python manage.py smoke_test_mobile_sales_firebase`
- Passed: `uv run python manage.py smoke_test_customer_ledger_firebase --help`
- Passed: `uv run python manage.py smoke_test_customer_ledger_firebase`
- Passed: `uv run python manage.py smoke_test_farmer_ledger_firebase --help`
- Passed: `uv run python manage.py smoke_test_farmer_ledger_firebase`
- Passed: `uv run python manage.py smoke_test_arrival_firebase --help`
- Passed: `uv run python manage.py smoke_test_arrival_firebase`
- Passed: `uv run python manage.py check` after the arrival/inventory read-only Firestore cutover
- Passed: `uv run python manage.py check` after the mobile arrival-goods Firestore cutover
- Passed: `uv run python manage.py smoke_test_sales_bill_firebase --help`
- Passed: `uv run python manage.py smoke_test_sales_bill_firebase`
- Passed: `uv run python manage.py check` after the live Firestore sales create/list cutover
- Passed: `uv run python manage.py check` after the live Firestore sales edit/update cutover
- Passed: `uv run python manage.py smoke_test_sales_bill_firebase` with create/update/delete stock reconciliation checks

## Current slice

- Slice: live sales-bill create/list/edit Firebase cutover
- Strategy: Firestore-native sales repository behind `USE_FIREBASE_SALES`, with Firestore-backed new-bill creation, listing, and editing, while credit flows remain partial
- Files touched:
	- `vegitable/vegitable/settings.py`
	- `vegitable/shops/firebase_models/sales_bill.py`
	- `vegitable/shops/repositories/sales_bill_repository.py`
	- `vegitable/shops/repositories/arrival_repository.py`
	- `vegitable/shops/management/commands/smoke_test_sales_bill_firebase.py`
	- `vegitable/shops/shop_views/sales_view.py`
	- `vegitable/template/Entry/Sales/modify_sales_bill_entry.html`
	- `vegitable/template/Entry/Sales/sales_bill_entry.html`
	- `plan/04-migration-runbook.md`
	- `plan/05-data-mapping.md`
	- `plan/progress.md`
	- `vegitable/.env.example`
	- `README.md`

## Proven Firebase slices

- `MobileSalesBill`: write/read/delete verified through Firestore.
- `CustomerLedger`: write/read/search/update/delete verified through Firestore.
- `FarmerLedger`: write/read/search/update/delete verified through Firestore.
- `ArrivalEntry` plus embedded `ArrivalGoods`: write/read/duplicate-check/goods-list/update/delete verified through Firestore.
- `SalesBillEntry` plus embedded Firestore items: write/read/stock-decrement/stock-restore/delete verified through Firestore.
- `SalesBillEntry` live list/create flow: routed to Firestore behind `USE_FIREBASE_SALES` for new fully paid bills.

## Blockers to full cutover

- Django `request.session` is configured to use the SQL session backend.
- `Shop.shop_owner` depends on `django.contrib.auth.models.User`.
- Reporting endpoints depend on `annotate`, `aggregate`, `F`, `Q`, and join-style access across related tables.
- Sequence counters in `Index` require atomic updates that must be redesigned for Firestore transactions.
- Backfill and parity checks still depend on a reachable SQL source if historical data must be copied.

## Update protocol

For each future implementation step:

1. Move one item from `In scope next` to `Completed`.
2. Add the exact files touched.
3. Record the verification command used.
4. Record any new blocker or design change before moving to the next slice.