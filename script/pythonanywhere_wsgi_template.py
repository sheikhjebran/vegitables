"""
PythonAnywhere WSGI template for this project.

How to use:
1) Open the PythonAnywhere Web tab.
2) Open your WSGI configuration file.
3) Replace its content with this template.
4) Reload the web app.
"""

import os
import sys


# --- adjust only if your username or checkout path differs ---
PA_USERNAME = "mbillingtool"
PROJECT_ROOT = f"/home/{PA_USERNAME}/vegitables"
DJANGO_ROOT = f"{PROJECT_ROOT}/vegitable"

# Ensure both project paths are importable.
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if DJANGO_ROOT not in sys.path:
    sys.path.insert(0, DJANGO_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vegitable.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

