# UV Conversion Plan

## Completed now

- Added `pyproject.toml` at the repository root.
- Moved runtime dependencies into `[project.dependencies]`.
- Added `django-orm-firebase` to the dependency set.
- Resolved dependencies successfully with `uv lock`.

## Repository rules going forward

- Treat `pyproject.toml` as the source of truth for dependencies.
- Commit `uv.lock` so installs are reproducible.
- Keep `requirements.txt` only as a temporary compatibility file until all deployment surfaces use uv.

## Standard commands

```powershell
uv sync
uv run python vegitable/manage.py check
uv run python vegitable/manage.py migrate
uv run python vegitable/manage.py runserver
```

## Follow-up cleanup

1. Replace any deployment script that still calls `pip install -r requirements.txt`.
2. Decide whether PythonAnywhere will install with uv directly or via an exported requirements file.
3. Remove `requirements.txt` only after the deployment path is updated and verified.