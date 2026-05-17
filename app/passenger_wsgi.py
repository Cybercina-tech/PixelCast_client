import os
import sys
from pathlib import Path

# Ensure the Django project root is importable in cPanel/Passenger.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Screengram.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
