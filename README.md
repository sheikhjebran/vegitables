# Vegitables Project

## Local setup

1. Install `uv`.
2. Sync dependencies.
3. Configure environment values.
4. Run migrations and start server.

Example (PowerShell):

```powershell
uv sync
Set-Location vegitable
```

`pyproject.toml` and `uv.lock` are now the primary dependency sources. `requirements.txt` is kept temporarily for compatibility with older deployment flows.

Create a `.env` file in `vegitable/` with at least:

```env
DEBUG=True
SECRET_KEY=replace-with-long-random-key

# Local DB defaults to sqlite, no extra values required.
# Optional for local MySQL:
# LOCAL_DB_ENGINE=django.db.backends.mysql
# LOCAL_DB_NAME=vegitable_shop
# LOCAL_DB_USER=your_user
# LOCAL_DB_PASSWORD=your_password
# LOCAL_DB_HOST=127.0.0.1
# LOCAL_DB_PORT=3306
```

Run:

```powershell
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
uv run python manage.py runserver
```

If you prefer to work from inside `vegitable/`, use:

```powershell
Set-Location vegitable
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

## Firebase migration note

The repo now includes `django-orm-firebase` in its managed dependencies, but the current codebase still uses Django's relational ORM extensively. See the plan documents in `plan/` before attempting a backend cutover.

## Firebase Phase 1 wiring

The repo now includes Firebase initialization hooks that are disabled by default.

Add these values to `vegitable/.env` when you are ready to test Firebase infrastructure:

```env
FIREBASE_ENABLED=True
FIREBASE_AUTO_INIT=False
USE_FIREBASE_MOBILE_SALES=False
USE_FIREBASE_CUSTOMER_LEDGER=False
USE_FIREBASE_FARMER_LEDGER=False
USE_FIREBASE_ARRIVAL=False
USE_FIREBASE_SALES=False
FIREBASE_CREDENTIAL_PATH=serviceAccountKey.json
FIREBASE_WEB_CONFIG_PATH=../firebase.json
FIREBASE_PROJECT_ID=your-project-id
# Optional JSON object for firebase_admin.initialize_app(...)
FIREBASE_OPTIONS_JSON=
```

If the repo-root `firebase.json` exists, the backend now auto-detects `projectId` from it. That file is still not a backend credential file. It is web/client config and cannot authorize Django admin SDK access by itself.

For backend Firestore access you still need one of these:

1. A Firebase service account JSON file, referenced by `FIREBASE_CREDENTIAL_PATH`.
2. Google Application Default Credentials already configured on the machine.

### What you have now

Your repo-root `firebase.json` is enough for these values:

- `FIREBASE_WEB_CONFIG_PATH=../firebase.json`
- `FIREBASE_PROJECT_ID=prahar-d5a02`

It is not enough for backend admin access.

### What you need next

From Firebase Console:

1. Open Project settings.
2. Open Service accounts.
3. Click Generate new private key.
4. Download the JSON file.
5. Place it at `vegitable/serviceAccountKey.json`.
6. Set `FIREBASE_CREDENTIAL_PATH=serviceAccountKey.json` in `vegitable/.env`.

Then use:

```env
FIREBASE_ENABLED=True
FIREBASE_AUTO_INIT=False
USE_FIREBASE_MOBILE_SALES=True
FIREBASE_WEB_CONFIG_PATH=../firebase.json
FIREBASE_CREDENTIAL_PATH=serviceAccountKey.json
FIREBASE_PROJECT_ID=prahar-d5a02
```

Then validate in this order:

```powershell
uv run python vegitable/manage.py check_firebase
uv run python vegitable/manage.py check
```

Run the health check:

```powershell
uv run python vegitable/manage.py check_firebase
```

Or, from inside `vegitable/`:

```powershell
uv run python manage.py check_firebase
```

This validates Firebase initialization and attempts a basic Firestore collection listing without changing the current SQL-backed Django models.

The first feature-flagged slice is `MobileSalesBill`. To route only that cache-like flow through Firestore after credentials are working:

```env
FIREBASE_ENABLED=True
USE_FIREBASE_MOBILE_SALES=True
```

With that flag off, the existing SQL-backed `MobileSalesBill` model path remains active.

The next slice is `CustomerLedger`. To route that ledger CRUD/search flow through Firestore:

```env
FIREBASE_ENABLED=True
USE_FIREBASE_CUSTOMER_LEDGER=True
```

The next ledger slice after that is `FarmerLedger`:

```env
FIREBASE_ENABLED=True
USE_FIREBASE_FARMER_LEDGER=True
```

The next inventory-facing slice is `ArrivalEntry` plus embedded `ArrivalGoods`:

```env
FIREBASE_ENABLED=True
USE_FIREBASE_ARRIVAL=True
```

The next sales-domain slice is a Firestore-native `SalesBillEntry` with embedded items that reference Firestore arrival goods directly:

```env
FIREBASE_ENABLED=True
USE_FIREBASE_ARRIVAL=True
USE_FIREBASE_SALES=True
```

After Firestore API access is working, you can backfill existing SQL mobile-sales rows with:

```powershell
uv run python vegitable/manage.py backfill_mobile_sales_to_firebase --dry-run
uv run python vegitable/manage.py backfill_mobile_sales_to_firebase
```

Then compare SQL and Firestore parity for the migrated slice:

```powershell
uv run python vegitable/manage.py compare_mobile_sales_sources
```

If you want to validate the Firestore-backed path without any SQL source data, run the Firebase-only smoke test:

```powershell
uv run python vegitable/manage.py smoke_test_mobile_sales_firebase
uv run python vegitable/manage.py smoke_test_customer_ledger_firebase
uv run python vegitable/manage.py smoke_test_farmer_ledger_firebase
uv run python vegitable/manage.py smoke_test_arrival_firebase
uv run python vegitable/manage.py smoke_test_sales_bill_firebase
```

If backfill or parity-check commands fail while reading SQL data, the source-side fix is usually one of these:

1. Set `USE_CLOUD_DB=False` to read from local SQLite.
2. Run migrations and load the source SQL data into the local SQLite database first.
3. Or run the commands from the environment that can reach the real PythonAnywhere MySQL database.

## PythonAnywhere setup (new account)

1. Create a Python 3.14 web app (Manual config, Django).
2. Open a Bash console and clone repo:

```bash
git clone https://github.com/sheikhjebran/vegitables.git
cd vegitables/vegitable
curl -LsSf https://astral.sh/uv/install.sh | sh
cd ..
uv sync
cd vegitable
```

3. Create `vegitable/.env`:

```env
DEBUG=False
SECRET_KEY=replace-with-long-random-key
ALLOWED_HOSTS=mbillingtool.pythonanywhere.com
USE_CLOUD_DB=True
CLOUD_DB_NAME=mbillingtool$vegitableshop
CLOUD_DB_USER=mbillingtool
CLOUD_DB_PASSWORD=replace-with-your-db-password
CLOUD_DB_HOST=mbillingtool.mysql.pythonanywhere-services.com
```

4. In PythonAnywhere Web tab:
1. Set source code path to `/home/mbillingtool/vegitables`.
2. Set working directory to `/home/mbillingtool/vegitables/vegitable`.
3. Set virtualenv path to `/home/mbillingtool/vegitables/vegitable/.venv`.
4. Set static files mapping: URL `/static/` -> `/home/mbillingtool/vegitables/vegitable/assets`.

5. Update WSGI file to load Django app from this project path and settings module `vegitable.settings`.
	A ready-to-paste template is provided at `script/pythonanywhere_wsgi_template.py`.
6. Run:

```bash
cd ~/vegitables/vegitable
uv run python manage.py migrate
uv run python manage.py collectstatic --noinput
```

7. Reload the web app from PythonAnywhere Web tab.

## PythonAnywhere API scripts

Two helper scripts are available in `script/`:

- `build_cloud.py`: send deployment commands to an existing PythonAnywhere console.
- `reload_webapp.py`: trigger web app reload via API.

Required env vars:

```env
PYTHONANYWHERE_USERNAME=mbillingtool
PYTHONANYWHERE_API_TOKEN=replace-with-api-token
PYTHONANYWHERE_WEBAPP=mbillingtool.pythonanywhere.com
PYTHONANYWHERE_PYTHON=python3.14
```

Use `vegitable/.env.example` as a base template and create your real `vegitable/.env`.
