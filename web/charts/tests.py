## @file web/charts/tests.py
# @brief Unit tests for charts.views services

import json
import os
import shutil

from boreholes.models import Borehole
from django.contrib.auth.models import User, AnonymousUser
from django.http import HttpRequest, QueryDict
from meanings.models import MeaningSection, MeaningValue, MeaningDict, \
    MeaningDictValue
from values.models import RealMeasurement, NoDictionaryFile
import django.test
from . import views
from dictionaries.models import DictionaryMeasurement

class ChartsViewsTestCase(django.test.TestCase):
    tests_num = 2
    test_value = 0.5
    test_meaning_name = 'MEANING_NAME'
    test_dict_value = 'DICT_VALUE'
    test_section_name = 'section_name'
    test_unit = '%'
    test_borehole_name = 'borehole_name'
    test_lat = 12.34567
    test_lon = 123.45678
    test_depth = 10000
    test_geophysical_depth = 10100
    
    csv_sample_path = 'test/sample.csv'
    csv_correct_column = 7
    csv_really_big_column = 100
    test_username = 'sweetspot'
    test_password = 'sweetspot'

    @classmethod
    def setUpClass(self):
        if not os.path.exists('values/dicts'):
            os.makedirs('values/dicts')
        
        with open('values/dicts/en_normal.json', 'w+') as out:
            json.dump({k : v for (k, v) in [(self.test_dict_value + str(i), self.test_dict_value.lower() + str(i)) 
                                             for i in range(1, self.tests_num + 1)] + 
                                            [('GEOPHYSICAL_DEPTH_FROM', 'Geophysical depth from'),
                                             ('geophysical_depth', 'Drilling depth from')] +
                                            [(self.test_meaning_name + str(i), self.test_meaning_name.lower() + str(i)) 
                                             for i in range(1, self.tests_num + 10)]}, out)
        
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree('values')
        
    def setUp(self):
        django.core.management.call_command('flush', interactive=False)
        self.createTestValues()
        self.request = HttpRequest()
        self.user = self.request.user = User.objects.create_user(self.test_username, '', self.test_password)

    def createTestValues(self):
        sects = list()
        meanings = list();
        bhs = list()
        
        for i in range(self.tests_num):
            sects.append(MeaningSection.objects.create(name = self.test_section_name + str(i)))
        MeaningSection.objects.create(name = 'Stratygrafia')
        for i in range(1, self.tests_num + 1):
            meanings.append(MeaningValue.objects.create(name = self.test_meaning_name + str(i), unit = self.test_unit + str(i), 
                                        section = sects[i % self.tests_num]))
            
        meanings.append(MeaningValue.objects.create(name = self.test_meaning_name + str(self.tests_num + 1), unit = self.test_unit + str(1), 
                                        section = sects[i % self.tests_num]))
        
        meanings.append(MeaningDict.objects.create(name = self.test_meaning_name + str(self.tests_num + 2),
                                                   unit = 'DICT', section = sects[0]))
        for i in range(1, self.tests_num + 1):
            MeaningDictValue.objects.create(dict_id = meanings[-1], value = self.test_dict_value + str(i)) 

        for i in range(self.tests_num):
            bhs.append(Borehole.objects.create(name = self.test_borehole_name + str(i), latitude = self.test_lat + i,
                                               longitude = self.test_lon + i))
            
        for i in range(self.tests_num):
            for j in range(self.tests_num):
                RealMeasurement.objects.create(value = self.test_value + float(i + j), meaning = meanings[j], 
                                               borehole = bhs[i], depth_from = self.test_depth + j* 100, 
                                               depth_to = self.test_depth + (1 + j) * 100, 
                                               geophysical_depth = self.test_geophysical_depth + j * 100)
        RealMeasurement.objects.create(value = self.test_value + float(self.tests_num**2 + 1), meaning = meanings[self.tests_num], 
                                               borehole = bhs[0], depth_from = 0, depth_to = 1, geophysical_depth = 0)
        RealMeasurement.objects.create(value = self.test_value + float(self.tests_num**2 + 1), meaning = meanings[0], 
                                               borehole = bhs[1], depth_from = 0, depth_to = 1, geophysical_depth = 0)
        
        meanings.append(MeaningDict.objects.create(id = 606, name = self.test_meaning_name + str(self.tests_num + 3),
                                                   unit = 'DICT', section = MeaningSection.objects.get(name='Stratygrafia')))

        DictionaryMeasurement.objects.create(depth_from = 0, depth_to = 500000, meaning = meanings[-1], borehole = bhs[0],
                                             geophysical_depth = 0,
                                             dictionary = MeaningDictValue.objects.create(dict_id = meanings[-1], value = "test_value"))

    def test01getCharts(self):
        self.request.method = 'POST'
        self.assertEqual(views.charts(self.request, 1).status_code, 405)
        
        self.request.method = 'GET'
        self.request.GET = QueryDict('lang=en').copy()
        self.assertListEqual(json.loads(views.charts(self.request, 2).content.decode('utf-8')),
                             [{u'data': [[[0, self.test_value + float(self.tests_num**2 + 1), 0.01, 0, 6], 
                                          [self.test_depth / 100, self.test_value + 1, self.test_depth/100 + 1, self.test_geophysical_depth/100,
                                            3]]], 
                               u'name': self.test_meaning_name.lower()+'1', u'unit': self.test_unit+'1'},
                              {u'name' : self.test_meaning_name.lower()+'2', u'unit' : self.test_unit + '2',
                               u'data' : [[[self.test_depth /100+ 1, self.test_value + 2, self.test_depth/100+2, 
                                            self.test_geophysical_depth/100+1, 4]]]}])
        
        self.request.GET['lang'] = 'a'
        self.assertRaises(NoDictionaryFile, views.charts, self.request, 2)
        
        self.request.GET = QueryDict('unit_pair=1&lang=en')
        self.assertListEqual(json.loads(views.charts(self.request, 2).content.decode('utf-8')),
                             [{u'data': [[[0, self.test_value + float(self.tests_num**2 + 1), 0.01, 0, 6], 
                                          [self.test_depth/100, self.test_value + 1, self.test_depth/100 + 1, self.test_geophysical_depth/100,
                                            3]]], 
                               u'names': [{'label' : self.test_meaning_name.lower()+'1'}], u'unit': self.test_unit+'1'},
                              {u'names' : [{'label' : self.test_meaning_name.lower()+'2'}], u'unit' : self.test_unit + '2',
                               u'data' : [[[self.test_depth/100 + 1, self.test_value + 2, self.test_depth/100+2, 
                                            self.test_geophysical_depth/100+1, 4]]]}])

        self.assertListEqual(json.loads(views.charts(self.request, 1).content.decode('utf-8')),
                             [{u'names' : [{'label' : self.test_meaning_name.lower()+'1'}, 
                                           {'label' : self.test_meaning_name.lower() + str(self.tests_num + 1)}], u'unit' : self.test_unit + '1',
                               u'data' : [[[self.test_depth/100, self.test_value, self.test_depth/100+1, self.test_geophysical_depth/100, 1]], 
                                          [[0, self.test_value + float(self.tests_num**2 + 1), 0.01, 0, 5]]]},
                              {u'names' : [{'label' : self.test_meaning_name.lower()+'2'}], u'unit' : self.test_unit + '2',
                               u'data' : [[[self.test_depth/100 + 1, self.test_value + 1, self.test_depth/100+2, self.test_geophysical_depth/100+1, 2]]]}])
        
        self.request.GET = QueryDict('lang=en&start_depth=%d' % (self.test_depth / 100 + 1))
        self.assertListEqual(json.loads(views.charts(self.request, 1).content.decode('utf-8')),
                             [{u'name' : self.test_meaning_name.lower() + '1', u'unit' : self.test_unit + '1',
                               u'data' : [[[self.test_depth/100, self.test_value, self.test_depth/100 + 1, self.test_geophysical_depth/100, 1]]]},
                              {u'name' : self.test_meaning_name.lower()+'2', u'unit' : self.test_unit + '2',
                               u'data' : [[[self.test_depth/100 + 1, self.test_value + 1, self.test_depth/100+2, self.test_geophysical_depth/100+1, 2]]]}])

        self.request.GET = QueryDict('lang=en&stop_depth=%d' % (self.test_depth / 100 + 1))
        self.assertListEqual(json.loads(views.charts(self.request, 1).content.decode('utf-8')),
                             [{u'name' : self.test_meaning_name.lower()+'1', u'unit' : self.test_unit + '1',
                               u'data' : [[[self.test_depth/100, self.test_value, self.test_depth/100+1, self.test_geophysical_depth/100, 1]]]},
                              {u'name' : self.test_meaning_name.lower() + str(self.tests_num + 1), u'unit' : self.test_unit + '1',
                               u'data' : [[[0, self.test_value + float(self.tests_num**2 + 1), 0.01, 0, 5]]]},
                              {u'name' : self.test_meaning_name.lower() + '2', u'unit' : self.test_unit + '2',
                               u'data' : [[[self.test_depth/100+1, self.test_value+1, self.test_depth/100+2, self.test_geophysical_depth/100+1, 2]]]}])
        
        self.request.GET = QueryDict('lang=en&stop_depth=%d&strat=3&start_depth=0' % (self.test_depth / 100 + 1))
        self.assertListEqual(json.loads(views.charts(self.request, 1).content.decode('utf-8')),
                             [{u'name' : self.test_meaning_name.lower()+'1', u'unit' : self.test_unit + '1',
                               u'data' : [[[self.test_depth/100, self.test_value, self.test_depth/100+1, self.test_geophysical_depth/100, 1]]]},
                              {u'name' : self.test_meaning_name.lower() + str(self.tests_num + 1), u'unit' : self.test_unit + '1',
                               u'data' : [[[0, self.test_value + float(self.tests_num**2 + 1), 0.01, 0, 5]]]},
                              {u'name' : self.test_meaning_name.lower() + '2', u'unit' : self.test_unit + '2',
                               u'data' : [[[self.test_depth/100+1, self.test_value+1, self.test_depth/100+2, self.test_geophysical_depth/100+1, 2]]]}])
        