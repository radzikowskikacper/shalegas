import datetime
from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpRequest
import django.test
import json
import os
import shutil

from reset.views import DUMPS_DIRNAME, getDumpFiles

from . import views
from reset.models import TooManyDumpFiles


class ResetViewsTestCase(django.test.TestCase):
    test_username = "test_username"
    test_password = "test_password"
    
    def setUp(self):
        django.core.management.call_command('flush', interactive=False)
        self.request = HttpRequest()
        self.user = self.request.user = User.objects.create_user(self.test_username, '', self.test_password)
        for fileName in os.listdir(DUMPS_DIRNAME):
            os.remove(DUMPS_DIRNAME + "/%s" % fileName)
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree('reset')
            
    def test01prepareDumpName(self):
        self.assertEqual(views.prepareDumpName(), "%s/SweetSpot_%s.sql" % 
                         (DUMPS_DIRNAME, datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")))
        
        f = open('reset/dumps/SweetSpot_%s.sql' % datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S"), 'w+')
        f.close()
        
        self.assertEqual(views.prepareDumpName(), "%s/SweetSpot_%s (1).sql" % 
                         (DUMPS_DIRNAME, datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")))
        
        for i in range(1, 6):
            f = open('reset/dumps/SweetSpot_%s (%d).sql' % (datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S"), i), 'w+')
            f.close()
            
        self.assertEqual(views.prepareDumpName(), "%s/SweetSpot_%s (6).sql" % 
                         (DUMPS_DIRNAME, datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")))
        
    def test02getDumpFiles(self):
        fnames = dict()
        for i in range(1, 6):
            fnames[i] = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            f = open('reset/dumps/SweetSpot_%s (%d).sql' % (fnames[i], i), 'w+')
            f.close()
            f = open('reset/dumps/SweetSpot (%d).sql' % i, 'w+')
            f.close()
            
        self.assertListEqual(sorted(views.getDumpFiles()), sorted(['SweetSpot_%s (%d)' % (fnames[i], i) for i in fnames] +
                                                                  ['SweetSpot (%d)' % i for i in range(1, 6)]))
        
    def test03dumpDB(self):
        for i in range(1, 10):
            f = open('%s/SweetSpot (%d).sql' % (DUMPS_DIRNAME, i), 'w+')
            f.close()
        self.assertEqual(len(getDumpFiles()), 9)
        
        self.request.user = self.user
        self.request.method = 'POST'
        views.reset(self.request)
        self.assertEqual(len(getDumpFiles()), 10)

        self.assertRaises(TooManyDumpFiles, views.reset, self.request)
                
    def test04deleteFile(self):
        for i in range(1, 11):
            f = open('%s/SweetSpot (%d).sql' % (DUMPS_DIRNAME, i), 'w+')
            f.close()

        self.assertEqual(len(getDumpFiles()), 10)

        self.request.method = 'DELETE'
        self.request.read = lambda : json.dumps('SweetSpot (%d)' % 1).encode()
        views.reset(self.request)
        
        self.assertEqual(len(getDumpFiles()), 9)

    def test05getDumpFiles(self):
        for i in range(1, 11):
            f = open('%s/SweetSpot (%d).sql' % (DUMPS_DIRNAME, i), 'w+')
            f.close()

        self.request.method = 'GET'
        self.assertEqual(len(json.loads(views.reset(self.request).content.decode('utf-8'))), 10)
