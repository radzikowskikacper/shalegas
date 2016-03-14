## @file web/tables/tests.py
# @brief Unit tests for tables.views services

from django.contrib.auth.models import User, AnonymousUser
from django.http.request import HttpRequest, QueryDict
import django.test
import json

from boreholes.models import Borehole
from dictionaries.models import DictionaryMeasurement, stratigraphy_list
from meanings.models import MeaningSection, MeaningValue, MeaningDict, \
    MeaningDictValue
from tables import views
from values.models import RealMeasurement


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
                
        meanings.append(MeaningDict.objects.create(id = stratigraphy_list[-1], name = self.test_meaning_name + str(self.tests_num + 3),
                                                   unit = 'DICT', section = sects[0]))

        DictionaryMeasurement.objects.create(depth_from = 0, depth_to = 500000, meaning = meanings[-1], borehole = bhs[0],
                                             geophysical_depth = 0,
                                             dictionary = MeaningDictValue.objects.create(dict_id = meanings[-1], value = "test_value"))
                
    def setUp(self):
        django.core.management.call_command('flush', interactive=False)
        self.request = HttpRequest()
        self.user = self.request.user = User.objects.create_user(self.test_username, '', self.test_password)
    
    def test01tableView(self):
        self.createTestMeasurements()
        
        self.request.method = 'GET'
        self.request.GET = QueryDict('')
        
        res = json.loads(views.tables(self.request, 1).content.decode('utf-8'))
        self.assertListEqual(res['header'], [{'name' : 'DEPTH_FROM'}, {'name' : self.test_meaning_name + '1', 'unit' : self.test_unit + '1'},
                                      {'name' : self.test_meaning_name + '2', 'unit' : self.test_unit + '2'},
                                      {'name' : self.test_meaning_name + '3', 'unit' : 'DICT'},
                                      {'name' : self.test_meaning_name + '4', 'unit' : 'DICT'}])
        self.assertListEqual(res['data'][0], [100, 0.5, '', '', ''])
        self.assertListEqual(res['data'][1], [101, '', 1.5, self.test_dict_value + '1', ''])
        self.assertListEqual(res['data'][2], [102, '', '', '', self.test_dict_value + '2'])
        
        meaning = MeaningValue.objects.create(name = self.test_meaning_name + 'a', unit = self.test_unit + 'b', 
                                    section = MeaningSection.objects.create(name=self.test_section_name + 'c'))
        RealMeasurement.objects.create(value = self.test_value + 100, meaning = meaning, borehole = Borehole.objects.get(id=1), 
                                       depth_from = 100, depth_to = 101, geophysical_depth = 99)
        
        res = json.loads(views.tables(self.request, 1).content.decode('utf-8'))
        self.assertListEqual(res['header'], [{'name' : 'DEPTH_FROM'},
                                    {'name' : self.test_meaning_name + '1', 'unit' : self.test_unit + '1'},
                                      {'name' : self.test_meaning_name + '2', 'unit' : self.test_unit + '2'},
                                      {'name' : self.test_meaning_name + '3', 'unit' : 'DICT'},
                                      {'name' : self.test_meaning_name + '4', 'unit' : 'DICT'},
                                             {'name' : self.test_meaning_name + 'a', 'unit' : self.test_unit + 'b'},])
        self.assertListEqual(res['data'][0], [1, '', '', '', '', self.test_value + 100])
        self.assertListEqual(res['data'][1], [100, 0.5, '', '', '', ''])
        self.assertListEqual(res['data'][2], [101, '', 1.5, self.test_dict_value + '1', '', ''])
        self.assertListEqual(res['data'][3], [102, '', '', '', self.test_dict_value + '2', ''])
        self.assertEqual(len(res['data']), 4)
        
        self.request.GET = QueryDict('stop_depth=101').copy()
        res = json.loads(views.tables(self.request, 1).content.decode('utf-8'))
        self.assertListEqual(res['header'], [{'name' : 'DEPTH_FROM'},
                                    {'name' : self.test_meaning_name + '1', 'unit' : self.test_unit + '1'},
                                      {'name' : self.test_meaning_name + '2', 'unit' : self.test_unit + '2'},
                                      {'name' : self.test_meaning_name + '3', 'unit' : 'DICT'},
                                             {'name' : self.test_meaning_name + 'a', 'unit' : self.test_unit + 'b'}])
        self.assertListEqual(res['data'][0], [1, '', '', '', self.test_value + 100])
        self.assertListEqual(res['data'][1], [100, 0.5, '', '', ''])
        self.assertListEqual(res['data'][2], [101, '', 1.5, self.test_dict_value + '1', ''])
        self.assertEqual(len(res['data']), 3)

        self.request.GET['start_depth'] = 50
        res = json.loads(views.tables(self.request, 1).content.decode('utf-8'))
        self.assertListEqual(res['header'], [{'name' : 'DEPTH_FROM'},
                                    {'name' : self.test_meaning_name + '1', 'unit' : self.test_unit + '1'},
                                      {'name' : self.test_meaning_name + '2', 'unit' : self.test_unit + '2'},
                                      {'name' : self.test_meaning_name + '3', 'unit' : 'DICT'}])
        self.assertListEqual(res['data'][0], [100, 0.5, '', ''])
        self.assertListEqual(res['data'][1], [101, '', 1.5, self.test_dict_value + '1'])
        self.assertEqual(len(res['data']), 2)
        
        self.request.GET = QueryDict('start_depth=50&stop_depth=5000&filter=1&filter=3&strat=3').copy()
        res = json.loads(views.tables(self.request, 1).content.decode('utf-8'))
        self.assertListEqual(res['header'], [{'name' : 'DEPTH_FROM'},
                                    {'name' : self.test_meaning_name + '1', 'unit' : self.test_unit + '1'},
                                      {'name' : self.test_meaning_name + '3', 'unit' : 'DICT'}])
        self.assertListEqual(res['data'][0], [100, 0.5, ''])
        self.assertListEqual(res['data'][1], [101, '', self.test_dict_value + '1'])
        self.assertEqual(len(res['data']), 2)