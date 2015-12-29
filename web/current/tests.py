##
# @file web/current/tests.py
# @brief Unit tests for current state of application

import datetime
import django.test
from . import views
from django.http import HttpRequest
from django.utils.importlib import import_module
from django.contrib.auth.models import User
from django.conf import settings

class CurrentModelTestCase(django.test.TestCase):
    pass

class CurrentViewTestCase(django.test.TestCase):

    def test01time(self):
        self.assertEqual( views.time({}),
                          str(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")) )

    def test02get(self):
        request = HttpRequest()

        engine = import_module(settings.SESSION_ENGINE)
        session_key = None

        request.session = engine.SessionStore(session_key)
        d = views.get(request)
        self.assertEqual( len(d), 2)

        request.user = User.objects.create_user('sweetspot', '', 'sweetspot')
        d = views.get(request)
        self.assertEqual( len(d), 4)
        self.assertEqual(d['username'], 'sweetspot')
