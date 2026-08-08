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

### Current execution note

- `CustomerLedger` is now the active next migration slice.
- Initial Firebase implementation may use app-layer substring filtering over shop-scoped Firestore results until a more scalable search design is introduced.
- `FarmerLedger` should follow only after `CustomerLedger` CRUD and search behavior are validated.

## Phase 5: redesign transactional inventory flows

1. Redesign `Index` counters as Firestore transaction-backed counters.
2. Redesign `ArrivalEntry` and `ArrivalGoods` writes to avoid partial multi-document failure.
3. Use Firestore transactions or batched writes for stock decrements.
4. Add idempotency keys for form submissions that currently rely on session tokens.

### Current execution note

- `ArrivalEntry` plus `ArrivalGoods` is the active inventory migration slice.
- The first Firebase boundary uses one arrival document with embedded goods rows.
- Live view cutover is deferred until dependent sales and inventory flows can read the new stock representation safely.

## Phase 6: redesign sales and credit flows

1. Model `SalesBillEntry` and `SalesBillItem` either as parent document plus embedded line items or as parent-child collections.
2. Redesign credit-bill derivation so balance data is either stored denormalized or recomputed safely.
3. Replace aggregate report queries with precomputed fields or Firestore-specific read models.
4. Validate monetary calculations with snapshot tests before cutover.

### Current execution note

- The active sales migration boundary is a Firestore-native sales bill document with embedded line items.
- Firestore sales items reference Firestore arrival goods local IDs rather than SQL foreign keys.
- Stock decrement and restore behavior is being validated at the repository level before live view cutover.

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

## Source-Environment Execution

This is the concrete run order for the environment that still has the real SQL source data and working Firebase credentials.

### Preconditions

1. Run commands from `vegitable/`, the folder that contains `manage.py`.
2. Ensure the environment can reach both:
   - the source SQL database
   - the target Firebase project
3. Ensure the following base environment variables are set:
   - `FIREBASE_ENABLED=True`
   - `FIREBASE_CREDENTIAL_PATH=...`
   - `FIREBASE_PROJECT_ID=...`
4. Enable the Firebase feature flag for the slice you are backfilling before running that slice's command.
5. Keep `USE_CLOUD_DB=True` only if this environment can reach the production MySQL host. Otherwise point the app at a local restored source database.

### Baseline Validation

Run these first:

```powershell
Set-Location "C:\Users\sheik\Documents\GitHub\vegitables\vegitable"
uv run python manage.py check
uv run python manage.py check_firebase
```

If either fails, stop before starting any backfill.

### Step 1: Backfill Shop Metadata First

The runtime app now depends on Firebase shop metadata for shop context and prefix counters. Backfill this before enabling `USE_FIREBASE_SHOP_METADATA` in a live environment.

Dry run:

```powershell
$env:FIREBASE_ENABLED='True'
$env:USE_FIREBASE_SHOP_METADATA='True'
uv run python manage.py backfill_shop_metadata_to_firebase --dry-run
```

Write:

```powershell
$env:FIREBASE_ENABLED='True'
$env:USE_FIREBASE_SHOP_METADATA='True'
uv run python manage.py backfill_shop_metadata_to_firebase
```

Validate repository behavior:

```powershell
$env:FIREBASE_ENABLED='True'
$env:USE_FIREBASE_SHOP_METADATA='True'
uv run python manage.py smoke_test_shop_metadata_firebase
```

### Step 2: Backfill Domain Slices With Existing SQL Tooling

Recommended order:

1. `ArrivalEntry` plus `ArrivalGoods`
2. `SalesBillEntry` plus `SalesBillItem`
3. `CreditBillEntry` plus `CreditBillHistory`
4. `PattiEntry`
5. `ExpenditureEntry`
6. `CustomerLedger`
7. `FarmerLedger`
8. `MobileSalesBill`

For each slice, run dry-run, write, then compare.

#### Arrival

```powershell
$env:FIREBASE_ENABLED='True'
$env:USE_FIREBASE_ARRIVAL='True'
uv run python manage.py backfill_arrival_to_firebase --dry-run
uv run python manage.py backfill_arrival_to_firebase
uv run python manage.py compare_arrival_sources --show-mismatches 20
```

#### Patti

```powershell
$env:FIREBASE_ENABLED='True'
$env:USE_FIREBASE_PATTI='True'
uv run python manage.py backfill_patti_to_firebase --dry-run
uv run python manage.py backfill_patti_to_firebase
uv run python manage.py compare_patti_sources --show-mismatches 20
```

#### Sales

```powershell
$env:FIREBASE_ENABLED='True'
$env:USE_FIREBASE_ARRIVAL='True'
$env:USE_FIREBASE_SALES='True'
uv run python manage.py backfill_sales_to_firebase --dry-run
uv run python manage.py backfill_sales_to_firebase
uv run python manage.py compare_sales_sources --show-mismatches 20
```

#### Credit

Note: this depends on Firestore sales already being backfilled, because each Firestore credit document must point at the corresponding Firestore sales record.

```powershell
$env:FIREBASE_ENABLED='True'
$env:USE_FIREBASE_ARRIVAL='True'
$env:USE_FIREBASE_SALES='True'
$env:USE_FIREBASE_CREDIT='True'
uv run python manage.py backfill_credit_to_firebase --dry-run
uv run python manage.py backfill_credit_to_firebase
uv run python manage.py compare_credit_sources --show-mismatches 20
```

#### Expenditure

```powershell
$env:FIREBASE_ENABLED='True'
$env:USE_FIREBASE_EXPENDITURE='True'
uv run python manage.py backfill_expenditure_to_firebase --dry-run
uv run python manage.py backfill_expenditure_to_firebase
uv run python manage.py compare_expenditure_sources --show-mismatches 20
```

#### Customer Ledger

```powershell
$env:FIREBASE_ENABLED='True'
$env:USE_FIREBASE_CUSTOMER_LEDGER='True'
uv run python manage.py backfill_customer_ledger_to_firebase --dry-run
uv run python manage.py backfill_customer_ledger_to_firebase
uv run python manage.py compare_customer_ledger_sources --show-mismatches 20
```

#### Farmer Ledger

```powershell
$env:FIREBASE_ENABLED='True'
$env:USE_FIREBASE_FARMER_LEDGER='True'
uv run python manage.py backfill_farmer_ledger_to_firebase --dry-run
uv run python manage.py backfill_farmer_ledger_to_firebase
uv run python manage.py compare_farmer_ledger_sources --show-mismatches 20
```

#### Mobile Sales

```powershell
$env:FIREBASE_ENABLED='True'
$env:USE_FIREBASE_MOBILE_SALES='True'
uv run python manage.py backfill_mobile_sales_to_firebase --dry-run
uv run python manage.py backfill_mobile_sales_to_firebase
uv run python manage.py compare_mobile_sales_sources --show-mismatches 20
```

### Step 3: Validate Live Firebase Runtime Paths

After backfills complete, run the Firebase smoke suite with the runtime flags you intend to enable.

```powershell
$env:FIREBASE_ENABLED='True'
$env:USE_FIREBASE_SHOP_METADATA='True'
$env:USE_FIREBASE_MOBILE_SALES='True'
$env:USE_FIREBASE_CUSTOMER_LEDGER='True'
$env:USE_FIREBASE_FARMER_LEDGER='True'
$env:USE_FIREBASE_ARRIVAL='True'
$env:USE_FIREBASE_SALES='True'
$env:USE_FIREBASE_CREDIT='True'
$env:USE_FIREBASE_PATTI='True'
$env:USE_FIREBASE_EXPENDITURE='True'

uv run python manage.py smoke_test_shop_metadata_firebase
uv run python manage.py smoke_test_mobile_sales_firebase
uv run python manage.py smoke_test_customer_ledger_firebase
uv run python manage.py smoke_test_farmer_ledger_firebase
uv run python manage.py smoke_test_arrival_firebase
uv run python manage.py smoke_test_sales_bill_firebase
uv run python manage.py smoke_test_credit_bill_firebase
uv run python manage.py smoke_test_patti_firebase
uv run python manage.py smoke_test_expenditure_firebase
uv run python manage.py smoke_test_shilk_patti_firebase
uv run python manage.py smoke_test_report_firebase
uv run python manage.py smoke_test_report_http_firebase
uv run python manage.py smoke_test_report_pdf_firebase
```

### Step 4: Enable Runtime Flags in Staging

Enable these together for the current migrated runtime:

```text
FIREBASE_ENABLED=True
USE_FIREBASE_SHOP_METADATA=True
USE_FIREBASE_MOBILE_SALES=True
USE_FIREBASE_CUSTOMER_LEDGER=True
USE_FIREBASE_FARMER_LEDGER=True
USE_FIREBASE_ARRIVAL=True
USE_FIREBASE_SALES=True
USE_FIREBASE_CREDIT=True
USE_FIREBASE_PATTI=True
USE_FIREBASE_EXPENDITURE=True
```

Then rerun:

```powershell
uv run python manage.py check
uv run python manage.py smoke_test_report_http_firebase
uv run python manage.py smoke_test_report_pdf_firebase
```

### Current Gaps Before Declaring Full Migration Complete

These are still open and should be treated as blockers for a final "MySQL fully retired" statement:

1. The historical backfill/parity commands must still be executed in the real source-data environment.
2. Runtime code is now pointed at Firebase for migrated paths, but production completion still depends on successful source-environment backfill, compare, and staging validation runs.

### Rollback Rule

If any compare command reports mismatches or any runtime smoke fails in the source environment:

1. Do not enable or widen the corresponding Firebase runtime flag.
2. Fix the slice-specific mismatch first.
3. Re-run dry-run, backfill, compare, and smoke validation for that slice before continuing.