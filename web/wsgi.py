##
# @file web/wsgi.py
# @brief WSGI config for sweetspot.

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
