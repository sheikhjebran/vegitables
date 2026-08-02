# Vegitables Project

## Local setup

1. Create and activate virtualenv.
2. Install dependencies.
3. Configure environment values.
4. Run migrations and start server.

Example (PowerShell):

```powershell
cd vegitable
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r ..\requirements.txt
```

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
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

## PythonAnywhere setup (new account)

1. Create a Python 3.10+ web app (Manual config, Django).
2. Open a Bash console and clone repo:

```bash
git clone https://github.com/sheikhjebran/vegitables.git
cd vegitables/vegitable
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
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
python3 manage.py migrate
python3 manage.py collectstatic --noinput
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
```

Use `vegitable/.env.example` as a base template and create your real `vegitable/.env`.
