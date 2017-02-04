## @file web/stratigraphy/tests.py
# @brief Unit tests for stratigraphy.views services

import json

from boreholes.models import Borehole
from dictionaries.models import DictionaryMeasurement
from django.db import transaction
from django.http import QueryDict, HttpRequest
import django.test
from meanings.models import MeaningDictValue, MeaningSection, MeaningDict
from stratigraphy import views
from django.contrib.auth.models import User, AnonymousUser

stratigraphy_list = [603, 604, 605, 606]

class MeasurementsModelTestCase(django.test.TestCase):
    tests_num = 2
    test_value = 0.5
    test_meaning_name = 'meaning_name'
    test_dict_value = 'DICT_VALUE'
    test_section_name = 'section_name'
    test_unit = '%'
    test_borehole_name = 'borehole_name'
    test_lat = 12.34567
    test_lon = 123.45678
    test_depth = 10000
    test_geophysical_depth = 10100
    test_username = 'sweetspot'
    test_password = 'sweetspot'
    csv_sample_path = 'test/sample.csv'
    csv_really_big_column = 100
    csv_correct_column = 7
    
    def createTestDictionaries(self, stratigraphy = False):
        sects = list()
        meanings = list();
        bhs = list()
        dictvals= list()
        
        for i in range(self.tests_num):
            sects.append(MeaningSection.objects.create(name = self.test_section_name + str(i)))
        MeaningSection.objects.create(name='Stratygrafia')
        for i in range(1, self.tests_num + 1):
            meanings.append(MeaningDict.objects.create(name = self.test_meaning_name + str(i), unit = 'DICT', 
                                        section = sects[i % self.tests_num]))
        meanings.append(MeaningDict.objects.create(name = self.test_meaning_name + str(self.tests_num + 1), unit = 'DICT', 
                                   section = sects[i % self.tests_num]))            
            
        for i in range(1, self.tests_num + 1):
            dictvals.append(MeaningDictValue.objects.create(dict_id = meanings[i - 1], value = self.test_dict_value + str(i))) 
            
        for i in range(self.tests_num):
            bhs.append(Borehole.objects.create(name = self.test_borehole_name + str(i), latitude = self.test_lat + i,
                                               longitude = self.test_lon + i))
            
        for i in range(self.tests_num):
            for j in range(self.tests_num):
                DictionaryMeasurement.objects.create(dictionary = dictvals[j], meaning = meanings[j], 
                                               borehole = bhs[i], depth_from = self.test_depth + j * 100, 
                                               depth_to = self.test_depth + (1 + j) * 100, 
                                               geophysical_depth = self.test_geophysical_depth + j *100)

        meanings, dictvals = list(), list()
        if stratigraphy:
            for index, i in enumerate(stratigraphy_list):
                meanings.append(MeaningDict.objects.create(name = self.test_meaning_name + str(i), section = MeaningSection.objects.get(name='Stratygrafia'), unit = 'DICT', id = i))
                for i in range(20 + index * 2, 20 + self.tests_num + index * 2):
                    dictvals.append(MeaningDictValue.objects.create(dict_id = meanings[-1], value = self.test_dict_value + str(i), id = i))
                    for j in range(2):
                        DictionaryMeasurement.objects.create(dictionary = dictvals[-1], meaning = meanings[-1], borehole = bhs[0],
                                                         depth_from = self.test_depth + j * 100, depth_to = self.test_depth + (j + i) * 100,
                                                         geophysical_depth = self.test_geophysical_depth + j * 100)

    def setUp(self):
        django.core.management.call_command('flush', interactive=False)
        self.request = HttpRequest()
        self.user = self.request.user = User.objects.create_user(self.test_username, '', self.test_password)

    def test01getStratigrahpy(self):
        self.createTestDictionaries(True)
        
        self.request.method = 'GET'
        self.request.GET = QueryDict('type=STRAT').copy()

        res = json.loads(views.stratigraphy(self.request, 1).content.decode('utf-8'))
        id = 5
        for index, did in enumerate(stratigraphy_list):
            for i in range(20 + index * 2, 20 + self.tests_num + index * 2):
                for j in range(2):
                    self.assertTrue({'thill' : self.test_depth + j * 100, 'ceil' : self.test_depth + (j + i) * 100, 
                                     str(did) : self.test_dict_value + str(i)} in res)
                    id += 1
        
    def test02addStratigraphy(self):
        self.createTestDictionaries(True)
        
        self.request.method = 'POST'
        errortab = [KeyError for i in range(5)] + [MeaningDictValue.DoesNotExist]
        
        for j, val in enumerate([{}, {'depth_from' : '%d' % self.test_depth}, {'meaning' : 11},
                    {604 : '22', 'geophysical_depth' : '%d' % (self.test_depth / 100), 'query' : {'type' : 'STRAT'}, 'depth_to' : '%d' % 11},
                    {'depth' : '%d' % self.test_depth},
                    {603 : '22', 'depth_from' : '%d' % (self.test_depth / 100), 'query' : {'type' : 'STRAT'}, 'depth_to' : '%d' % 12}
                    ]):
            self.request.read = lambda: json.dumps(val).encode()
            self.assertRaises(errortab[j], views.stratigraphy, self.request, 1)

        DictionaryMeasurement.objects.filter(borehole_id = 1).delete()

        self.request.read = lambda : json.dumps({603 : '20', 604 : '22', 'depth_from' : '%d' % (self.test_depth / 100), 'depth_to' : '%d' % (self.test_depth / 100 + 20),
                                                 'geophysical_depth' : '%d' % (self.test_geophysical_depth / 100), 'query' : {'type' : 'STRAT'}}).encode()
        res = json.loads(views.stratigraphy(self.request, 1).content.decode('utf-8')) 
        self.assertListEqual(res, [{'thill' : self.test_depth, 'ceil' : self.test_depth + 2000, 
                               '603' : self.test_dict_value + '20',
                               '604' : self.test_dict_value + '22'}])
                            
        self.request.read = lambda : json.dumps({603 : '20', 'depth_from' : '%d' % (self.test_depth / 100), 'depth_to' : '%d' % (self.test_depth / 100 + 21),
                                                 'geophysical_depth' : '%d' % (self.test_geophysical_depth / 100), 'query' : {'type' : 'STRAT'}}).encode()
        self.assertEqual(len(json.loads(views.stratigraphy(self.request, 1).content.decode('utf-8'))), 2)
        
        self.request.read = lambda : json.dumps({603 : '20', 'depth_from' : '0', 'depth_to' : '5000',
                                                 'geophysical_depth' : '%d' % (self.test_geophysical_depth / 100), 'query' : {'type' : 'STRAT'}}).encode()
        self.assertEqual(len(json.loads(views.stratigraphy(self.request, 1).content.decode('utf-8'))), 3)    