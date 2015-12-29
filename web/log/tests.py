## @file web/charts/tests.py
# @brief Unit tests for charts.views services

import os

from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpRequest
from initlog import LOG_FILE_NAME
import django.test
from . import views

class LogViewsTestCase(django.test.TestCase):
    test_username = 'sweetspot'
    test_password = 'sweetspot'

    @classmethod
    def setUpClass(self):
        with open('%s/%s' % (os.environ['SWEETSPOT_LOG_DIR'], LOG_FILE_NAME), 'w') as f:
            f.writelines(['THIS IS LOG TEST LINE NUMBER %d\n' % i for i in range(1, 1001)])
                
    @classmethod
    def tearDownClass(cls):
        os.remove('%s/%s' % (os.environ['SWEETSPOT_LOG_DIR'], LOG_FILE_NAME))
        
    def setUp(self):
        django.core.management.call_command('flush', interactive=False)
        self.request = HttpRequest()
        self.user = self.request.user = User.objects.create_user(self.test_username, '', self.test_password)

    def test01getLogs(self):
        self.request.method = 'GET'
        self.assertEqual(views.logs(self.request, 1).content.decode('utf-8'), "\n".join(['THIS IS LOG TEST LINE NUMBER %d' % i for i in range(991, 1001)]) + "\n")
        self.assertEqual(views.logs(self.request, 10).content.decode('utf-8'), "\n".join(['THIS IS LOG TEST LINE NUMBER %d' % i for i in range(991, 1001)]) + "\n")
        self.assertEqual(views.logs(self.request, 20).content.decode('utf-8'), "\n".join(['THIS IS LOG TEST LINE NUMBER %d' % i for i in range(981, 1001)]) + "\n")
        self.assertEqual(views.logs(self.request, 100).content.decode('utf-8'), "\n".join(['THIS IS LOG TEST LINE NUMBER %d' % i for i in range(901, 1001)]) + "\n")