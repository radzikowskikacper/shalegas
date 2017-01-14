##
# @file web/version/tests.py
# @brief Unit tests for version module

import django.test
from . import models, views

class VersionModelTestCase(django.test.TestCase):

    def test01getVersionString(self):
        self.assertTrue( len(models.getVersionString()) > 0 )

    def test02getDBName(self):
        self.assertTrue( len(models.getDBName()) > 0)

    def test03getDBUser(self):
        self.assertTrue( len(models.getDBUser()) > 0)

    def test04getDBPassword(self):
        self.assertTrue( len(models.getDBPassword()) > 0)

    def test05getDBVersionString(self):
        v = models.getDBVersionString()
        self.assertTrue( len(v) > 0)
        self.assertNotEqual( str(v), 'unknown' )

    def test06versionFromRow(self):
        self.assertEqual( models._versionFromRow(''), 'unknown' )
        t = ('ver,xxx',)
        self.assertEqual( models._versionFromRow(t), 'ver')

class VersionViewTestCase(django.test.TestCase):

    def test01get(self):
        d = views.get({})
        # co ten test sprawdza? o_O Logicznie nic. Sprawdza jedynie konkretna implementacje i trzeba go zmieniac przy kazdej zmianie
        self.assertEqual( len(d), 8)



