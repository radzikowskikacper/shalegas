## @file web/data/tests.py
# @brief Unit tests for data.views application

from django.contrib.auth.models import User, AnonymousUser
from django.http.request import QueryDict, HttpRequest
import django.test
import json

from boreholes.models import Borehole
from data import views
from dictionaries.models import DictionaryMeasurement
from meanings.models import MeaningSection, MeaningValue, MeaningDict, \
    MeaningDictValue
from values.models import RealMeasurement


class DataModelTestCase(django.test.TestCase):
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
    
    def createTestMeasurements(self):
        sects = list()
        meanings = list();
        bhs = list()
        dictvals = list()
        
        for i in range(self.tests_num):
            sects.append(MeaningSection.objects.create(name = self.test_section_name + str(i + self.tests_num)))
                
        for i in range(1, self.tests_num + 1):
            meanings.append(MeaningValue.objects.create(name = self.test_meaning_name + str(i), unit = self.test_unit + str(i), 
                                        section = sects[i % self.tests_num]))

        for i in range(1, self.tests_num + 1):
            meanings.append(MeaningDict.objects.create(name = self.test_meaning_name + str(i + self.tests_num), unit = 'DICT', 
                                        section = sects[i % self.tests_num]))

        for i in range(1, self.tests_num + 1):
            dictvals.append(MeaningDictValue.objects.create(dict_id = meanings[self.tests_num + i - 1], value = self.test_dict_value + str(i))) 
        
        for i in range(self.tests_num):
            bhs.append(Borehole.objects.create(name = self.test_borehole_name + str(i + self.tests_num), latitude = self.test_lat + i,
                                               longitude = self.test_lon + i))

        for i in range(self.tests_num):
            for j in range(self.tests_num):
                RealMeasurement.objects.create(value = self.test_value + float(i + j), meaning = meanings[j], 
                                               borehole = bhs[i], depth_from = self.test_depth + j* 100, 
                                               depth_to = self.test_depth + (1 + j) * 100, 
                                               geophysical_depth = self.test_geophysical_depth + j * 100)
                DictionaryMeasurement.objects.create(dictionary = dictvals[j], meaning = meanings[j + self.tests_num], borehole = bhs[i],
                                                     depth_from = self.test_depth + (j + 1) * 100,
                                                     depth_to = self.test_depth + (1 + j) * 100 + 1,
                                                     geophysical_depth = self.test_geophysical_depth + j * 100 + 1)
    
    def setUp(self):
        django.core.management.call_command('flush', interactive=False)
        self.request = HttpRequest()
        self.user = User.objects.create_user(self.test_username, '', self.test_password)
        self.request.user = AnonymousUser()
        
    def test01allBoreholesData(self):
        self.createTestMeasurements()
        self.request.method = 'GET'
        
        self.request.user = self.user
        self.request.GET = QueryDict('type=ALL_BHS&filter=1')
        self.assertDictEqual(json.loads(views.data(self.request).content.decode('utf-8')), 
                             {u'boreholes' : [self.test_borehole_name + '2', self.test_borehole_name + '3'],
                              u'data' : [[self.test_depth / 100.0, self.test_value, self.test_value + 1]],
                              u'meanings' : [{u'name' : self.test_meaning_name + '1', u'unit' : self.test_unit + '1'}]})

        self.request.GET = QueryDict('type=ALL_BHS&filter=1&filter=2')
        self.assertDictEqual(json.loads(views.data(self.request).content.decode('utf-8')),
                             {u'boreholes' : [self.test_borehole_name + '2', self.test_borehole_name + '3'],
                              u'data' : [[self.test_depth / 100.0, self.test_value, '', self.test_value + 1, ''], 
                                         [self.test_depth / 100.0 + 1, '', self.test_value + 1, '', self.test_value + 2]],
                              u'meanings' : [{u'name' : self.test_meaning_name + '1', u'unit' : self.test_unit + '1'},
                                             {u'name' : self.test_meaning_name + '2', u'unit' : self.test_unit + '2'}]})
        
        self.request.GET = QueryDict('type=ALL_BHS')
        res = json.loads(views.data(self.request).content.decode('utf-8'))
        self.assertListEqual(res['meanings'], [{'name' : self.test_meaning_name + str(i), 'unit' : self.test_unit + str(i)} for i in range(1, 3)] +
                                                [{'name' : self.test_meaning_name + str(i), 'unit' : 'DICT'} for i in range(3, 5)])
        self.assertListEqual(res['boreholes'], [self.test_borehole_name + str(i) for i in range(self.tests_num, self.tests_num * 2)])
        self.assertListEqual(res['data'], [[100, 0.5, '', '', '', 1.5, '', '', ''], 
                                           [101, '', 1.5, self.test_dict_value + '1', '', '', 2.5, self.test_dict_value + '1', ''],
                                           [102, '', '', '', self.test_dict_value + '2', '', '', '', self.test_dict_value + '2']])
        
        self.request.GET = QueryDict('type=ALL_BHS&strat=1')
        res = json.loads(views.data(self.request).content.decode('utf-8'))
        self.assertListEqual(res['meanings'], [{'name' : self.test_meaning_name + str(i), 'unit' : self.test_unit + str(i)} for i in range(1, 3)] +
                                                [{'name' : self.test_meaning_name + str(i), 'unit' : 'DICT'} for i in range(3, 5)])
        self.assertListEqual(res['boreholes'], [])
        self.assertListEqual(res['data'], [])