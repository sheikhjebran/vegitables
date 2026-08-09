# Source Environment Checklist

Use this checklist only in the environment that has:

- real SQL source data
- working Firebase credentials
- network access to both SQL and Firestore

Run from `vegitable/` where `manage.py` exists.

## 1. Base Environment

Set the base Firebase variables first.

```powershell
Set-Location "C:\Users\sheik\Documents\GitHub\vegitables\vegitable"

$env:FIREBASE_ENABLED='True'
$env:FIREBASE_CREDENTIAL_PATH='C:\path\to\serviceAccountKey.json'
$env:FIREBASE_PROJECT_ID='your-firebase-project-id'
```

If this environment reads production MySQL directly, also ensure the SQL env vars are correct.

## 2. Baseline Validation

```powershell
uv run python manage.py check
uv run python manage.py check_firebase
```

Stop if either command fails.

## 3. Shop Metadata First

```powershell
$env:USE_FIREBASE_SHOP_METADATA='True'

uv run python manage.py backfill_shop_metadata_to_firebase --dry-run
uv run python manage.py backfill_shop_metadata_to_firebase
uv run python manage.py smoke_test_shop_metadata_firebase
```

## 4. Arrival

```powershell
$env:USE_FIREBASE_ARRIVAL='True'

uv run python manage.py backfill_arrival_to_firebase --dry-run
uv run python manage.py backfill_arrival_to_firebase
uv run python manage.py compare_arrival_sources --show-mismatches 20
uv run python manage.py smoke_test_arrival_firebase
```

## 5. Sales

Sales depends on arrival already being in Firestore.

```powershell
$env:USE_FIREBASE_SALES='True'

uv run python manage.py backfill_sales_to_firebase --dry-run
uv run python manage.py backfill_sales_to_firebase
uv run python manage.py compare_sales_sources --show-mismatches 20
uv run python manage.py smoke_test_sales_bill_firebase
```

## 6. Credit

Credit depends on Firestore sales already being backfilled.

```powershell
$env:USE_FIREBASE_CREDIT='True'

uv run python manage.py backfill_credit_to_firebase --dry-run
uv run python manage.py backfill_credit_to_firebase
uv run python manage.py compare_credit_sources --show-mismatches 20
uv run python manage.py smoke_test_credit_bill_firebase
```

## 7. Patti

```powershell
$env:USE_FIREBASE_PATTI='True'

uv run python manage.py backfill_patti_to_firebase --dry-run
uv run python manage.py backfill_patti_to_firebase
uv run python manage.py compare_patti_sources --show-mismatches 20
uv run python manage.py smoke_test_patti_firebase
```

## 8. Expenditure

```powershell
$env:USE_FIREBASE_EXPENDITURE='True'

uv run python manage.py backfill_expenditure_to_firebase --dry-run
uv run python manage.py backfill_expenditure_to_firebase
uv run python manage.py compare_expenditure_sources --show-mismatches 20
uv run python manage.py smoke_test_expenditure_firebase
```

## 9. Customer Ledger

```powershell
$env:USE_FIREBASE_CUSTOMER_LEDGER='True'

uv run python manage.py backfill_customer_ledger_to_firebase --dry-run
uv run python manage.py backfill_customer_ledger_to_firebase
uv run python manage.py compare_customer_ledger_sources --show-mismatches 20
uv run python manage.py smoke_test_customer_ledger_firebase
```

## 10. Farmer Ledger

```powershell
$env:USE_FIREBASE_FARMER_LEDGER='True'

uv run python manage.py backfill_farmer_ledger_to_firebase --dry-run
uv run python manage.py backfill_farmer_ledger_to_firebase
uv run python manage.py compare_farmer_ledger_sources --show-mismatches 20
uv run python manage.py smoke_test_farmer_ledger_firebase
```

## 11. Mobile Sales

```powershell
$env:USE_FIREBASE_MOBILE_SALES='True'

uv run python manage.py backfill_mobile_sales_to_firebase --dry-run
uv run python manage.py backfill_mobile_sales_to_firebase
uv run python manage.py compare_mobile_sales_sources --show-mismatches 20
uv run python manage.py smoke_test_mobile_sales_firebase
```

## 12. Full Report Validation

Run these only after the required dependent slices above are already enabled.

```powershell
uv run python manage.py smoke_test_shilk_patti_firebase
uv run python manage.py smoke_test_report_firebase
uv run python manage.py smoke_test_report_http_firebase
uv run python manage.py smoke_test_report_pdf_firebase
```

## 13. Staging Rollout Validation

With all migrated flags enabled, run:

```powershell
uv run python manage.py check
uv run python manage.py smoke_test_report_http_firebase
uv run python manage.py smoke_test_report_pdf_firebase
```

## 14. Stop Rules

Stop immediately if any of these happen:

- a `backfill_*` command reports failures
- a `compare_*` command reports mismatches
- a `smoke_test_*` command fails

Do not continue to the next slice until the failing slice is fixed and rerun cleanly.

## 15. Completion Condition

You can treat business-data migration as operationally complete only when:

- every backfill command completes successfully
- every compare command reports parity
- the full smoke suite passes with Firebase flags enabled
- staging validation passes on migrated data
