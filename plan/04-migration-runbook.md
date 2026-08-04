# Step-by-Step Migration Runbook

## Phase 0: freeze the baseline

1. Commit the uv conversion and planning docs.
2. Run Django validation commands against the current SQL-backed app.
3. Export a production database backup and a local SQLite snapshot.
4. Record representative user flows for arrival, sales, patti, ledgers, credit, and reports.

## Phase 1: introduce Firebase infrastructure

1. Add Firebase environment variables:
   - `FIREBASE_CREDENTIAL_PATH`
   - `FIREBASE_PROJECT_ID`
   - optional `FIREBASE_OPTIONS_JSON`
   - `FIREBASE_AUTO_INIT`
2. Add a project module such as `vegitable/vegitable/firebase.py` to centralize initialization.
3. Register `django_firebase_orm.apps.DjangoFirebaseOrmConfig` only when the environment enables Firebase startup.
4. Add a startup health check command that verifies Firestore connectivity.

## Phase 2: create an application data boundary

1. Create a new package such as `vegitable/shops/firebase_models/` or `vegitable/shops/repositories/`.
2. Define Firestore document models outside the current Django models file.
3. Add mapping helpers between Django relational objects and Firestore document payloads.
4. Add a feature flag per domain slice, for example `USE_FIREBASE_MOBILE_SALES`.

## Phase 3: migrate a low-risk slice first

1. Start with `MobileSalesBill`.
2. Implement create, read, update, and delete operations in Firebase.
3. Redirect only the mobile-sales code path to the new repository when the feature flag is enabled.
4. Validate functional parity with the SQL version.
5. Backfill existing SQL rows into Firestore and compare record counts.

## Phase 4: migrate ledger CRUD slices

1. Move `CustomerLedger` and `FarmerLedger` next.
2. Replace `icontains` assumptions with Firestore-compatible search strategy.
3. Decide whether search will use normalized prefix fields, exact-match indexes, or external search.
4. Keep a rollback flag for each ledger slice.

## Phase 5: redesign transactional inventory flows

1. Redesign `Index` counters as Firestore transaction-backed counters.
2. Redesign `ArrivalEntry` and `ArrivalGoods` writes to avoid partial multi-document failure.
3. Use Firestore transactions or batched writes for stock decrements.
4. Add idempotency keys for form submissions that currently rely on session tokens.

## Phase 6: redesign sales and credit flows

1. Model `SalesBillEntry` and `SalesBillItem` either as parent document plus embedded line items or as parent-child collections.
2. Redesign credit-bill derivation so balance data is either stored denormalized or recomputed safely.
3. Replace aggregate report queries with precomputed fields or Firestore-specific read models.
4. Validate monetary calculations with snapshot tests before cutover.

## Phase 7: reporting strategy

1. Identify every report that currently depends on joins or aggregation.
2. Choose one of these approaches per report:
   - Keep report data in SQL during transition.
   - Maintain denormalized Firestore reporting documents.
   - Export Firestore data into a reporting store.
3. Cut reports last, after transactional domains are stable.

## Phase 8: auth and session decision

1. Keep Django auth and SQL sessions unchanged unless there is a strong reason to migrate them.
2. If Firebase Authentication must be adopted, design it as a separate auth migration project.
3. Do not combine business-data migration with auth migration in the same rollout.

## Phase 9: cutover and rollback

1. Enable Firebase slice flags in staging only.
2. Run side-by-side comparison for writes and reads.
3. Promote one slice at a time to production.
4. Keep SQL rollback paths until parity checks pass for a full business cycle.
5. Remove legacy SQL code only after production stability is confirmed.