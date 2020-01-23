##
# @file web/wsgi.py
# @brief WSGI config for sweetspot.

from django.core.wsgi import get_wsgi_application
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

application = get_wsgi_application()
