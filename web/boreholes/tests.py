## @file web/boreholes/tests.py
# @brief unit tests for boreholes.views services

import django.test, json, six
from .models import Borehole
import django.core.management
from django.http import HttpRequest
from django.core.exceptions import ValidationError
from django.db import DataError
from boreholes.models import BoreholesDuplicated
from django.contrib.auth.models import User, AnonymousUser
from . import models, views

def createTestObject(user, **kwargs):
    '''
    inserts 1 object into DB, using boreholes.views (like AJAX request)
    '''
    request = HttpRequest()
    request.method = 'POST'
    request.read = lambda: json.dumps({k : kwargs[k] for k in kwargs.keys() if k in ('name', 'latitude', 'longitude', 'description')}).encode()
    request.user = user
    return views.boreholes(request, None)

class BoreholesViewTestCase(django.test.TestCase):
    '''
    Main test case for testing boreholes services
    '''

    #local variables used for tests
    test_name = "test_borehole"
    test_desc = "this is a test description"
    test_long_name = "long_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_name \
                        long_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_name \
                        long_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_namelong_name"
    test_lat = 12.34567
    test_lon = 123.45678

    #number of objects to insert into DB
    test_num = 3
    test_username = 'sweetspot'
    test_password = 'sweetspot'

    def setUp(self):
        #recreate DB before every test
        django.core.management.call_command('flush', interactive=False)
        self.user = User.objects.create_user(self.test_username, '', self.test_password)

    def insertNumObjects(self):
        '''
        inserts $self.test_num objects into DB
        naming: test_name = self.test_name + str(i), for i e {0...$self.test_num - 1}
                test_lat = self.test_lat + i
        '''
        for i in range(self.test_num):
            createTestObject(self.user, name = self.test_name + str(i), latitude = self.test_lat + i, longitude = self.test_lon + i)

    def modifyAndGetById(self, _id, query):
        '''
        modifies an objects using views.modify (like AJAX request)
        and returns object by id, using django's objects' get
        '''
        request = HttpRequest()
        request.method = 'PUT'
        request.read = lambda: json.dumps(query).encode()
        request.user = self.user
        views.boreholes(request, _id)
        return Borehole.objects.get(id=_id)

    def test01new(self):
        #TESTING NORMAL INSERT
        #get data version
        global version
        currver = models.version
        request = HttpRequest()
        request.method = 'GET'
        
        self.assertRaises(DataError, createTestObject, self.user, name = self.test_long_name, latitude = self.test_lat, longitude = self.test_lon)

        self.insertNumObjects()
        b = Borehole.objects.all()

        #test if correct amount of objects was inserted
        self.assertEqual(len(b), self.test_num)

        self.assertEqual(models.version, currver + self.test_num)
        currver += self.test_num

        #test $self.test_num elements insertion
        for i in range(self.test_num):
            #get ALL objects by given parameters...
            b = Borehole.objects.filter(name = self.test_name + str(i), latitude = str(self.test_lat + i), longitude = str(self.test_lon + i))

            #... but only one should be returned
            self.assertEqual(len(b), 1)
            #if assertions were passed, we can assume that views.new() (used by self.insertNumObjects) works correctly

        #TEST ALL DATA INSERT(with description)
        test_name = self.test_name + str(self.test_num)
        createTestObject(self.user, name = test_name, latitude = self.test_lat, longitude = self.test_lon, description = self.test_desc)

        b = Borehole.objects.filter(name = test_name, latitude = str(self.test_lat), longitude = str(self.test_lon), description = self.test_desc)

        self.assertEqual(len(b), 1)
        self.assertEqual(models.version, currver + 1)
        currver += 1

        #TESTING DUPLICATE
        #insert object with same data as firsFt object inserted before
        self.assertRaises(BoreholesDuplicated, createTestObject, self.user, name = self.test_name + str(0), latitude = self.test_lat, longitude = self.test_lon)
        b = Borehole.objects.filter(name = self.test_name + str(0), latitude = str(self.test_lat), longitude = str(self.test_lon))

        self.assertEqual(models.version, currver)

        #only one object should be returned as above insertion should fail (no duplicates)
        self.assertEqual(len(b), 1)

        #TESTING INSERT WITH ONLY NAME FIELD GIVEN
        test_name = self.test_name

        self.assertRaises(KeyError, createTestObject, self.user, name = test_name)
        self.assertEqual(models.version, currver)

        #TEST WITH INCORRECT DATA (LATITUDE as 'f')
        #ValidationError should be thrown
        self.assertRaises(ValidationError, createTestObject, self.user, name = self.test_name, latitude = 'f', longitude = 'a')
        self.assertEqual(models.version, currver)

    def test02get(self):
        global version
        currver = models.version

        #if previous test passed, we can use insertNumObjects and rely that it will correctly create objects in DB
        self.insertNumObjects()

        #TESTING get FUNCTION
        resp = json.loads(views.get().content.decode('utf-8'))
        b = resp['boreholes']

        #version should match
        self.assertEqual(resp['boreholes_version'], currver + self.test_num)
        #array size should match
        self.assertEqual(len(b), self.test_num)

        for i in range(self.test_num):
            curr = b[i]
            #names should match
            self.assertEqual(curr['name'], self.test_name + str(i))
            #latitude should match, 5 digits precision
            self.assertAlmostEqual(float(curr['latitude']), self.test_lat + i, 5)
            #longitude should match
            self.assertAlmostEqual(float(curr['longitude']), self.test_lon + i, 5)

        #TESTING get SERVICE
        request = HttpRequest()
        request.method = 'GET'
        request.user = self.user
        bs = json.loads(views.boreholes(request).content.decode('utf-8'))['boreholes']
        self.assertEqual(len(bs), self.test_num)

        #TESTING get(id) FUNCTION
        currb = b[0]
        b = views.boreholes(request, currb['id'])
        self.assertTrue(b)
        self.assertEqual(currb['name'], self.test_name + str(0))
        self.assertAlmostEqual(float(currb['latitude']), self.test_lat, 5)
        self.assertAlmostEqual(float(currb['longitude']), self.test_lon, 5)

        #TESTING get(id) with nonexisting ID
        self.assertRaises(Borehole.DoesNotExist, views.boreholes, request, self.test_num + 1)

    def test03delete(self):
        #insert some objects
        self.insertNumObjects()

        #try deleting last one
        request = HttpRequest()
        request.method='DELETE'
        request.user = self.user
        views.boreholes(request, self.test_num)

        #get all objects
        #views.get works correctly as previous test passed
        res = json.loads(views.get().content.decode('utf-8'))

        #number of objects should be now $self.test_num - 1
        self.assertEqual(len(res), self.test_num - 1)

        #delete non-existing object

        request = HttpRequest()
        request.method='DELETE'
        request.user = self.user
        self.assertRaises(Borehole.DoesNotExist, views.boreholes, request, self.test_num + 1)

    def test04modify(self):
        #insert test objects
        self.insertNumObjects()

        self.assertRaises(TypeError, self.modifyAndGetById, self.test_num, 5)

        self.assertRaises(DataError, self.modifyAndGetById, self.test_num, {'name' : self.test_long_name})
        
        #we will modify last one
        params = {'name' : self.test_name + '_modified'}
        params['latitude'] = self.test_lat * 2
        params['longitude'] = self.test_lon * 3
        params['description'] = self.test_desc
        params['coordinateX'] = 'X'
        params['coordinateY'] = 'Y'

        #trigger views.modify() and return modified element
        b = self.modifyAndGetById(self.test_num, params)

        #all the fields should be modified
        self.assertEqual(b.name, self.test_name + '_modified')
        self.assertAlmostEqual(float(b.latitude), self.test_lat * 2, 5)
        self.assertAlmostEqual(float(b.longitude), self.test_lon * 3, 5)
        self.assertEqual(b.description, self.test_desc)

        #modification with wrong data type (latitude = 'a')
        param = {'latitude' : 'a'}

        self.assertRaises(ValidationError, self.modifyAndGetById, self.test_num, param)
                         
        #modify non-existing object
        params = {'description' : self.test_desc}

        self.assertRaises(Borehole.DoesNotExist, self.modifyAndGetById, self.test_num + 1, params)